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

# Configuration
TOTAL_TXS = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
NUM_NODES = int(sys.argv[2]) if len(sys.argv) > 2 else 12
CONCURRENCY = NUM_NODES  # One thread per node to avoid sequence conflicts
PROJECT_ROOT = "/home/hcp-dev/hcp-project"
BINARY = f"{PROJECT_ROOT}/hcp-consensus-build/hcpd"
DATA_ROOT = f"{PROJECT_ROOT}/.hcp_nodes"
LOG_DIR = f"{PROJECT_ROOT}/logs/consensus_test"
REPORT_FILE = os.path.join(os.getcwd(), "consensus_perf_report.md")

# Ensure paths
os.makedirs(LOG_DIR, exist_ok=True)

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
    def __init__(self):
        self.nodes = []
        self.monitor = SystemMonitor()
        self.tx_results = []
        self.start_time = 0
        self.end_time = 0

    def load_node_info(self):
        self.nodes = []
        print("Loading node information...")
        for i in range(1, NUM_NODES + 1):
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
        return 0, 0

    def send_tx(self, from_node_idx, count):
        """
        Sends 'count' transactions from a specific node to the next node.
        Using subprocess to call hcpd.
        """
        sender = self.nodes[from_node_idx]
        receiver = self.nodes[(from_node_idx + 1) % NUM_NODES]
        results = []

        # Fetch initial sequence
        acc_num, current_seq = self.get_account_info(from_node_idx)
        print(f"Node {sender['id']} starting with Account: {acc_num}, Seq: {current_seq}")

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
            "--account-number", str(acc_num),
            "--gas", "200000",
            "--gas-prices", "0.025stake"
        ]

        for i in range(count):
            start_ts = time.time()
            try:
                # Append sequence and unique note
                seq = current_seq + i
                cmd = cmd_base + ["--sequence", str(seq), "--note", f"tx-{start_ts}-{seq}"]
                
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
        print(f"Starting load test: {TOTAL_TXS} txs across {NUM_NODES} nodes...")
        txs_per_node = TOTAL_TXS // NUM_NODES
        remainder = TOTAL_TXS % NUM_NODES
        
        self.monitor.start()
        self.start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=NUM_NODES) as executor:
            futures = []
            for i in range(NUM_NODES):
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
**Nodes:** {NUM_NODES}
**Total Transactions:** {TOTAL_TXS}

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

        with open(REPORT_FILE, "w") as f:
            f.write(report)
        print(f"Report generated at {REPORT_FILE}")

if __name__ == "__main__":
    runner = TestRunner()
    runner.load_node_info()
    
    # Check if nodes are running
    if not runner.check_network_health():
        print("Network not ready. Please run 'setup_testnet.sh' first or wait for nodes to sync.")
        # Optional: Call setup script? 
        # For safety, we expect the user/wrapper to handle setup.
        sys.exit(1)
        
    runner.load_node_info()
    runner.run_load_test()
    runner.generate_report()
