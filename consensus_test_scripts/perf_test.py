import os
import sys
import time
import subprocess
import json
import requests
import threading
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from statistics import mean, stdev
import socket

# Configuration
DEFAULT_TXS_LIST = [100, 1000, 10000]
DEFAULT_NODE_LIST = [3, 4, 6, 8, 10, 16]
DEFAULT_ALGO_LABEL = "default"
PROJECT_ROOT = "/home/hcp-dev/hcp-project"
BINARY = f"{PROJECT_ROOT}/hcp-consensus-build/hcpd"
DATA_ROOT = f"{PROJECT_ROOT}/.hcp_nodes"
LOG_DIR = f"{PROJECT_ROOT}/logs/consensus_test"
SETUP_SCRIPT = f"{PROJECT_ROOT}/hcp/consensus_test_scripts/setup_testnet.sh"

# Ensure paths
os.makedirs(LOG_DIR, exist_ok=True)


def build_report_filename(num_nodes: int, total_txs: int, algo_label: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"consensus_perf_report_nodes{num_nodes}_tx{total_txs}_algo-{algo_label}_{timestamp}.md"
    return os.path.join(LOG_DIR, filename)


def wait_for_ports(num_nodes: int, timeout_sec: int = 120) -> bool:
    deadline = time.time() + timeout_sec
    last_rpc_port = 26657 + (num_nodes - 1) * 10
    while time.time() < deadline:
        ok_first = False
        ok_last = False
        for port in (26657, last_rpc_port):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(("127.0.0.1", port))
                if port == 26657:
                    ok_first = result == 0
                else:
                    ok_last = result == 0
        if ok_first and ok_last:
            return True
        time.sleep(2)
    return False


def wait_for_network_ready(num_nodes: int, timeout_sec: int = 180) -> bool:
    deadline = time.time() + timeout_sec
    last_rpc_port = 26657 + (num_nodes - 1) * 10
    while time.time() < deadline:
        try:
            resp1 = requests.get("http://127.0.0.1:26657/status", timeout=3)
            resp2 = requests.get(f"http://127.0.0.1:{last_rpc_port}/status", timeout=3)
            if resp1.status_code == 200 and resp2.status_code == 200:
                h1 = int(resp1.json()["result"]["sync_info"]["latest_block_height"])
                h2 = int(resp2.json()["result"]["sync_info"]["latest_block_height"])
                if h1 >= 1 and h2 >= 1:
                    return True
        except Exception:
            pass
        time.sleep(2)
    return False


def start_network(num_nodes: int):
    log_path = os.path.join(LOG_DIR, f"network_nodes{num_nodes}.log")
    log_file = open(log_path, "w")
    proc = subprocess.Popen(
        ["bash", SETUP_SCRIPT, str(num_nodes)],
        stdout=log_file,
        stderr=subprocess.STDOUT,
    )
    return proc, log_file


def stop_network(proc, log_file):
    try:
        subprocess.run(["pkill", "-f", "hcpd"], check=False)
    finally:
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
        if log_file:
            log_file.close()

class SystemMonitor:
    def __init__(self):
        self.running = False
        self.stats = []
        self._thread = None

    def start(self):
        self.running = True
        self._thread = threading.Thread(target=self._monitor_loop)
        self._thread.start()

    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join()

    def _monitor_loop(self):
        while self.running:
            try:
                # Read Load Avg
                with open("/proc/loadavg", "r") as f:
                    load_avg = f.read().split()[:3]
                
                # Read Memory
                mem_info = {}
                with open("/proc/meminfo", "r") as f:
                    for line in f:
                        parts = line.split()
                        if len(parts) >= 2:
                            mem_info[parts[0].rstrip(':')] = int(parts[1])
                
                mem_used = mem_info.get('MemTotal', 0) - mem_info.get('MemAvailable', 0)
                
                self.stats.append({
                    'timestamp': time.time(),
                    'load_1m': float(load_avg[0]),
                    'mem_used_kb': mem_used
                })
            except Exception as e:
                print(f"Monitor error: {e}")
            
            time.sleep(1)

class TestRunner:
    def __init__(self, total_txs: int, num_nodes: int, report_file: str, algo_label: str):
        self.total_txs = total_txs
        self.num_nodes = num_nodes
        self.report_file = report_file
        self.algo_label = algo_label
        self.nodes = []
        self.monitor = SystemMonitor()
        self.tx_results = []
        self.start_time = 0
        self.end_time = 0

    def load_node_info(self):
        self.nodes = []
        print("Loading node information...")
        for i in range(1, self.num_nodes + 1):
            addr_file = f"{DATA_ROOT}/node{i}/address"
            if os.path.exists(addr_file):
                with open(addr_file, 'r') as f:
                    address = f.read().strip()
                self.nodes.append({
                    'id': i,
                    'address': address,
                    'home': f"{DATA_ROOT}/node{i}",
                    'rpc': f"http://127.0.0.1:{26657 + (i-1)*10}"
                })
        print(f"Loaded {len(self.nodes)} nodes.")

    def check_network_health(self):
        print("Checking network health...")
        if not self.nodes:
            print("No nodes loaded.")
            return False
        # Check node 1 and node 12
        for node in [self.nodes[0], self.nodes[-1]]:
            try:
                resp = requests.get(f"{node['rpc']}/status", timeout=5)
                if resp.status_code != 200:
                    print(f"Node {node['id']} returned {resp.status_code}")
                    return False
                
                status = resp.json()
                latest_block = int(status['result']['sync_info']['latest_block_height'])
                if latest_block < 1:
                    print(f"Node {node['id']} is at block 0")
                    return False
            except Exception as e:
                print(f"Failed to reach node {node['id']}: {e}")
                return False
        return True

    def get_account_info(self, node_idx):
        node = self.nodes[node_idx]
        api_port = 1317 + (node['id'] - 1)
        url = f"http://127.0.0.1:{api_port}/cosmos/auth/v1beta1/accounts/{node['address']}"
        
        try:
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                data = res.json()
                # data['account'] usually contains the info
                # If it's a BaseAccount, it has account_number and sequence directly
                # If it's wrapped in Any (common in v0.50), we might need to look inside
                account = data.get('account', {})
                
                # Handle standard BaseAccount or ModuleAccount
                acc_num = account.get('account_number')
                seq = account.get('sequence')
                
                # If not found directly, check if it's nested (e.g. wrapper)
                if acc_num is None and 'base_account' in account:
                    acc_num = account['base_account'].get('account_number')
                    seq = account['base_account'].get('sequence')
                
                return int(acc_num or 0), int(seq or 0)
            else:
                print(f"API Error {res.status_code}: {res.text}")
        except Exception as e:
            print(f"Error fetching account info via API for node {node['id']}: {e}")
        try:
            cmd = [
                BINARY,
                "query",
                "auth",
                "account",
                node["address"],
                "--node",
                node["rpc"],
                "--home",
                node["home"],
                "--output",
                "json",
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                data = json.loads(res.stdout)
                account = data.get("account", {})
                acc_num = account.get("account_number")
                seq = account.get("sequence")
                if acc_num is None and "base_account" in account:
                    acc_num = account["base_account"].get("account_number")
                    seq = account["base_account"].get("sequence")
                return int(acc_num or 0), int(seq or 0)
            else:
                print(f"CLI Error fetching account info for node {node['id']}: {res.stderr}")
        except Exception as e:
            print(f"Error fetching account info via CLI for node {node['id']}: {e}")
        return 0, 0

    def send_tx(self, from_node_idx, count):
        """
        Sends 'count' transactions from a specific node to the next node.
        Using subprocess to call hcpd.
        """
        sender = self.nodes[from_node_idx]
        receiver = self.nodes[(from_node_idx + 1) % self.num_nodes]
        results = []

        print(f"Node {sender['id']} starting tx submissions")

        # Pre-calculate command base
        # We use --broadcast-mode sync to wait for CheckTx but not Commit (faster)
        # or block (slowest). 'sync' is good for throughput testing.
        cmd_base = [
            BINARY, "tx", "bank", "send",
            f"node{sender['id']}", receiver['address'], "1stake",
            "--chain-id", "hcp-testnet-1",
            "--home", sender['home'],
            "--node", sender['rpc'],
            "--keyring-backend", "test",
            "--output", "json",
            "--yes",
            "--broadcast-mode", "sync",
            "--gas", "200000",
            "--gas-prices", "0.025stake"
        ]

        for i in range(count):
            start_ts = time.time()
            try:
                # Append sequence and unique note
                cmd = cmd_base + ["--note", f"tx-{start_ts}-{i}"]
                
                res = subprocess.run(cmd, capture_output=True, text=True)
                duration = time.time() - start_ts
                
                if res.returncode == 0:
                    try:
                        out = json.loads(res.stdout)
                        code = out.get('code', 0)
                        txhash = out.get('txhash', '')
                        results.append({
                            'success': code == 0,
                            'hash': txhash,
                            'duration': duration,
                            'timestamp': start_ts,
                            'raw': out,
                            'error': out.get('raw_log', str(code)) if code != 0 else None
                        })
                    except:
                        results.append({'success': False, 'error': 'json_parse_error', 'raw': res.stdout})
                else:
                    if len(results) == 0 and i == 0:
                         print(f"CLI Error (first attempt): {res.stderr}")
                    results.append({'success': False, 'error': 'cli_error', 'stderr': res.stderr})
            except Exception as e:
                results.append({'success': False, 'error': str(e)})
        
        return results

    def run_load_test(self):
        print(f"Starting load test: {self.total_txs} txs across {self.num_nodes} nodes...")
        txs_per_node = self.total_txs // self.num_nodes
        remainder = self.total_txs % self.num_nodes
        
        self.monitor.start()
        self.start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=self.num_nodes) as executor:
            futures = []
            for i in range(self.num_nodes):
                count = txs_per_node + (1 if i < remainder else 0)
                futures.append(executor.submit(self.send_tx, i, count))
            
            for future in as_completed(futures):
                self.tx_results.extend(future.result())
        
        self.end_time = time.time()
        self.monitor.stop()
        print("Load test completed.")

    def analyze_consensus(self):
        # Fetch block times to calculate consensus latency/throughput
        print("Analyzing consensus metrics...")
        blocks = []
        try:
            # Fetch last 50 blocks from Node 1
            status = requests.get(f"{self.nodes[0]['rpc']}/status").json()
            latest = int(status['result']['sync_info']['latest_block_height'])
            start_block = max(1, latest - 50)
            
            for h in range(start_block, latest + 1):
                b_resp = requests.get(f"{self.nodes[0]['rpc']}/block?height={h}").json()
                if 'result' in b_resp and 'block' in b_resp['result']:
                    ts_str = b_resp['result']['block']['header']['time']
                    # Parse ISO format (e.g., 2023-10-27T10:00:00.000000Z)
                    # Python 3.10 handles ISO well but sometimes nanoseconds can be tricky
                    ts_str = ts_str.split('.')[0] + "Z" # Simplify for basic stats if needed
                    # Better: use regex to handle varying precision
                    blocks.append({
                        'height': h,
                        'time': b_resp['result']['block']['header']['time'],
                        'txs': len(b_resp['result']['block']['data']['txs'])
                    })
        except Exception as e:
            print(f"Error fetching blocks: {e}")
        return blocks

    def generate_report(self):
        success_count = sum(1 for r in self.tx_results if r.get('success'))
        fail_count = len(self.tx_results) - success_count
        duration = self.end_time - self.start_time
        tps = success_count / duration if duration > 0 else 0
        
        durations = [r['duration'] for r in self.tx_results if 'duration' in r]
        avg_latency = mean(durations) if durations else 0
        max_latency = max(durations) if durations else 0
        min_latency = min(durations) if durations else 0

        blocks = self.analyze_consensus()
        
        # System stats
        avg_load = mean([s['load_1m'] for s in self.monitor.stats]) if self.monitor.stats else 0
        max_mem = max([s['mem_used_kb'] for s in self.monitor.stats]) / 1024 if self.monitor.stats else 0 # MB

        report = f"""# HCP Consensus Performance Report
**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Nodes:** {self.num_nodes}
**Total Transactions:** {self.total_txs}
**Consensus Algorithm:** {self.algo_label}

## 1. Executive Summary
- **Success Rate:** {success_count}/{len(self.tx_results)} ({(success_count/len(self.tx_results))*100:.2f}%)
- **Total Duration:** {duration:.2f} seconds
- **Throughput (TPS):** {tps:.2f} tx/sec (Submission rate)
- **Average Submission Latency:** {avg_latency:.4f} seconds

## 2. Transaction Analysis
- **Min Latency:** {min_latency:.4f}s
- **Max Latency:** {max_latency:.4f}s
- **Failures:** {fail_count}
"""

        if fail_count > 0:
            errors = {}
            for r in self.tx_results:
                if not r.get('success'):
                    err = r.get('error', 'unknown')
                    errors[err] = errors.get(err, 0) + 1
            report += "\n### Error Distribution\n"
            for k, v in errors.items():
                report += f"- {k}: {v}\n"

        report += f"""
## 3. System Resource Usage
- **Average Load (1m):** {avg_load:.2f}
- **Peak Memory Usage:** {max_mem:.2f} MB (Total System)

## 4. Consensus Metrics (Last 50 Blocks)
"""
        if blocks:
            # Calculate block times
            # Note: Parsing RFC3339 timestamps in Python < 3.11 without external libs can be verbose
            # We will approximate or just list the heights
            report += f"- **Sampled Blocks:** {blocks[0]['height']} to {blocks[-1]['height']}\n"
            report += f"- **Total Txs in Sample:** {sum(b['txs'] for b in blocks)}\n"
        else:
            report += "- No block data available.\n"

        report += """
## 5. Observations & Recommendations
- **Bottlenecks:** CPU/Network latency during concurrent submission.
- **Optimization:** Increase batch size or use gRPC for higher throughput.
"""

        with open(self.report_file, "w") as f:
            f.write(report)
        print(f"Report generated at {self.report_file}")

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        total_txs = int(sys.argv[1])
        num_nodes = int(sys.argv[2])
        report_file = build_report_filename(num_nodes, total_txs, DEFAULT_ALGO_LABEL)
        runner = TestRunner(total_txs, num_nodes, report_file, DEFAULT_ALGO_LABEL)
        runner.load_node_info()
        if not runner.check_network_health():
            print("Network not ready. Please run 'setup_testnet.sh' first or wait for nodes to sync.")
            sys.exit(1)
        runner.run_load_test()
        runner.generate_report()
    else:
        for num_nodes in DEFAULT_NODE_LIST:
            for total_txs in DEFAULT_TXS_LIST:
                report_file = build_report_filename(num_nodes, total_txs, DEFAULT_ALGO_LABEL)
                proc, log_file = start_network(num_nodes)
                if not wait_for_ports(num_nodes):
                    stop_network(proc, log_file)
                    print(f"Network not ready for {num_nodes} nodes. Please check {LOG_DIR}/network_nodes{num_nodes}.log")
                    sys.exit(1)
                if not wait_for_network_ready(num_nodes):
                    stop_network(proc, log_file)
                    print(f"Network not ready for {num_nodes} nodes. Please check {LOG_DIR}/network_nodes{num_nodes}.log")
                    sys.exit(1)
                runner = TestRunner(total_txs, num_nodes, report_file, DEFAULT_ALGO_LABEL)
                runner.load_node_info()
                if not runner.check_network_health():
                    stop_network(proc, log_file)
                    print(f"Network not ready for {num_nodes} nodes. Please check {LOG_DIR}/network_nodes{num_nodes}.log")
                    sys.exit(1)
                runner.run_load_test()
                runner.generate_report()
                stop_network(proc, log_file)
