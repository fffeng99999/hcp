import argparse
import os
import shutil
import signal
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, List

from experiment_lib import ExperimentPoint, ExperimentResult, write_json, render_table, format_float

import psutil
import statistics

PROJECT_ROOT = Path("/home/hcp-dev/hcp-project")
HCP_DIR = PROJECT_ROOT / "hcp"
BINARY_PATH = PROJECT_ROOT / "hcp-consensus-build" / "hcpd"


def wait_for_rpc(port: int, timeout: int = 60) -> bool:
    url = f"http://127.0.0.1:{port}/status"
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(1)
    return False


def is_rpc_in_use(port: int = 26657) -> bool:
    url = f"http://127.0.0.1:{port}/status"
    try:
        with urllib.request.urlopen(url, timeout=2) as resp:
            return resp.status == 200
    except Exception:
        return False


def start_cluster(num_nodes: int, data_root: Path, log_dir: Path) -> subprocess.Popen:
    if is_rpc_in_use(26657):
        raise RuntimeError("检测到本机 26657 端口已有共识节点在运行，请先停止当前 HCP-Bench 系统后再运行实验一。")

    if data_root.exists():
        shutil.rmtree(data_root)
    log_dir.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["DATA_ROOT"] = str(data_root)
    env["LOG_DIR"] = str(log_dir)
    env["USE_CPU_AFFINITY"] = "true"  # 启用 CPU 亲和性

    proc = subprocess.Popen(
        ["bash", "start_nodes.sh", str(num_nodes)],
        cwd=str(HCP_DIR),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    if not wait_for_rpc(26657, timeout=90):
        proc.send_signal(signal.SIGINT)
        proc.wait(timeout=10)
        raise RuntimeError("在超时时间内未等到 26657 RPC 端口就绪，启动共识集群失败。")

    return proc


def stop_cluster(proc: subprocess.Popen) -> None:
    try:
        proc.send_signal(signal.SIGINT)
    except Exception:
        return
    try:
        proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        try:
            proc.kill()
        except Exception:
            pass


def load_address(node_dir: Path) -> str:
    addr_file = node_dir / "address"
    return addr_file.read_text(encoding="utf-8").strip()


def measure_cpu_bandwidth(pid_list: List[int], duration: float) -> tuple[float, float]:
    """
    测量给定进程列表在 duration 时间内的平均 CPU 使用率和网络带宽。
    返回: (cpu_percent, network_bytes_per_sec)
    """
    if not pid_list:
        return 0.0, 0.0

    procs = []
    for pid in pid_list:
        try:
            p = psutil.Process(pid)
            procs.append(p)
        except psutil.NoSuchProcess:
            continue

    # 初始网络计数
    net_start = psutil.net_io_counters()
    
    # 初始 CPU (调用一次以重置计数)
    for p in procs:
        try:
            p.cpu_percent()
        except:
            pass

    time.sleep(duration)

    # 结束 CPU
    cpu_total = 0.0
    for p in procs:
        try:
            cpu_total += p.cpu_percent()
        except:
            pass
    
    # 结束网络计数
    net_end = psutil.net_io_counters()
    
    avg_cpu = cpu_total / len(procs) if procs else 0.0
    
    # 计算总带宽 (发送+接收)
    bytes_sent = net_end.bytes_sent - net_start.bytes_sent
    bytes_recv = net_end.bytes_recv - net_start.bytes_recv
    bandwidth = (bytes_sent + bytes_recv) / duration

    return avg_cpu, bandwidth

def get_node_pids(n: int) -> List[int]:
    """获取当前运行的共识节点进程 PID"""
    pids = []
    # 查找 hcpd 进程
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if 'hcpd' in proc.info['name']:
                pids.append(proc.info['pid'])
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return pids

def send_transactions(num_txs: int, data_root: Path, chain_id: str = "hcp-testnet-1") -> tuple[float, float, float]:
    """
    发送交易并返回指标。
    返回: (duration, avg_latency, p99_latency)
    """
    node1_home = data_root / "node1"
    node2_home = data_root / "node2"

    if not node1_home.exists() or not node2_home.exists():
        raise RuntimeError("节点目录不存在，请确认集群已正确初始化。")

    receiver_addr = load_address(node2_home)

    cmd_base: List[str] = [
        str(BINARY_PATH),
        "tx",
        "bank",
        "send",
        str(load_address(node1_home)),
        receiver_addr,
        "1stake",
        "--home",
        str(node1_home),
        "--keyring-backend",
        "test",
        "--chain-id",
        chain_id,
        "--yes",
        "--broadcast-mode",
        "sync",
        "--output",
        "json"
    ]

    latencies = []
    start_total = time.perf_counter()
    
    for i in range(num_txs):
        tx_start = time.perf_counter()
        while True:
            result = subprocess.run(
                cmd_base,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            if result.returncode == 0:
                # 交易提交成功 (sync模式只保证CheckTx通过)
                # 简单估算：认为从发送到返回的时间近似为确认延迟的一部分
                # 真实确认需要查询区块，这里做简化近似
                latencies.append((time.perf_counter() - tx_start) * 1000) # ms
                break
                
            output = result.stdout or ""
            if "hcpd is not ready" in output or "account sequence mismatch" in output:
                time.sleep(1)
                continue
            # print(f"Warning: tx failed: {output}")
            # 失败重试，不计入延迟统计以免偏差太大，或者记为高延迟
            time.sleep(0.5)

    end_total = time.perf_counter()
    duration = end_total - start_total
    
    avg_latency = statistics.mean(latencies) if latencies else 0.0
    p99_latency = statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 2 else avg_latency

    return duration, avg_latency, p99_latency

def estimate_rocksdb_latency(data_root: Path) -> float:
    """
    通过在数据目录进行简单的文件写入来模拟/估算 RocksDB 写延迟基准。
    (真实 RocksDB 延迟需要通过 LOG 文件或 PerfContext 获取，这里做近似基准测试)
    """
    test_file = data_root / "io_test.dat"
    latencies = []
    try:
        for _ in range(50):
            start = time.perf_counter()
            with open(test_file, "wb") as f:
                f.write(os.urandom(1024)) # 1KB write
                f.flush()
                os.fsync(f.fileno())
            latencies.append((time.perf_counter() - start) * 1000)
    except:
        return 0.0
    finally:
        if test_file.exists():
            test_file.unlink()
            
    return statistics.mean(latencies) if latencies else 0.0


import threading

def run_real_experiment(node_counts: List[int], tx_counts: List[int]) -> ExperimentResult:
    points: List[ExperimentPoint] = []

    for n in node_counts:
        data_root = PROJECT_ROOT / f".hcp_exp1_nodes_{n}"
        log_dir = PROJECT_ROOT / "logs" / f"exp1_nodes_{n}"
        proc = None
        try:
            print(f"启动 {n} 节点共识集群...")
            proc = start_cluster(n, data_root, log_dir)
            time.sleep(5)
            
            pids = get_node_pids(n)

            for t in tx_counts:
                print(f"  发送 {t} 笔交易进行测试...")
                
                # 在后台线程启动 CPU/带宽 监控
                # 由于 send_transactions 是阻塞的，我们在它运行期间采样
                # 简单起见，这里先运行交易，交易结束后再单独采样一段(不准确)
                # 或者：使用 threading 在 send_transactions 同时运行 measure_cpu_bandwidth
                
                metrics_container = {}
                def monitor_task():
                    cpu, bw = measure_cpu_bandwidth(pids, duration=5.0) # 采样 5 秒
                    metrics_container['cpu'] = cpu
                    metrics_container['bw'] = bw
                
                monitor_thread = threading.Thread(target=monitor_task)
                monitor_thread.start()
                
                # 执行交易发送
                duration, avg_lat, p99_lat = send_transactions(t, data_root)
                
                monitor_thread.join()
                
                # 估算 RocksDB 延迟 (在交易完成后测量，避免争抢IO，但可能反映不出并发压力)
                # 改进：如果想要反映交易期间的IO压力，应该并行测量，但文件IO操作本身会引入额外负载
                # 这里我们假设在交易刚结束时测量，能捕捉到 RocksDB 刷盘的一些尾部效应，或者作为基准参考
                rocks_lat = estimate_rocksdb_latency(data_root / "node1" / "data")
                
                tps = float(t) / duration if duration > 0 else 0.0
                
                print(f"    TPS: {tps:.2f}, AvgLat: {avg_lat:.2f}ms, P99: {p99_lat:.2f}ms, CPU: {metrics_container.get('cpu',0):.1f}%, BW: {metrics_container.get('bw',0)/1024:.2f}KB/s")

                points.append(
                    ExperimentPoint(
                        params={"nodes": n, "tx": t},
                        metrics={
                            "duration_s": duration,
                            "tps": tps,
                            "avg_latency_ms": avg_lat,
                            "p99_latency_ms": p99_lat,
                            "cpu_percent": metrics_container.get('cpu', 0.0),
                            "bandwidth_bps": metrics_container.get('bw', 0.0),
                            "rocksdb_latency_ms": rocks_lat
                        },
                    )
                )
        finally:
            if proc is not None:
                print(f"停止 {n} 节点集群...")
                stop_cluster(proc)
            time.sleep(5)

    result = ExperimentResult(
        name="exp1_real_chain",
        description="基于 Cosmos-SDK 实际共识网络的交易量 × 节点规模 TPS 实验",
        points=points,
        metadata={
            "note": "使用 hcp-consensus (Cosmos-SDK) + bank 模块真实交易，包含 CPU/带宽/磁盘IO 监控。",
        },
    )
    return result

def generate_report_md(result: ExperimentResult) -> str:
    headers = ["节点数", "交易数", "总耗时(s)", "TPS", "平均延迟(ms)", "P99延迟(ms)", "CPU(%)", "带宽(KB/s)", "RocksDB(ms)"]
    rows: List[List[str]] = []
    for p in result.points:
        rows.append(
            [
                p.params["nodes"],
                p.params["tx"],
                format_float(p.metrics["duration_s"], 2),
                format_float(p.metrics["tps"], 2),
                format_float(p.metrics["avg_latency_ms"], 2),
                format_float(p.metrics["p99_latency_ms"], 2),
                format_float(p.metrics["cpu_percent"], 1),
                format_float(p.metrics["bandwidth_bps"] / 1024.0, 1),
                format_float(p.metrics["rocksdb_latency_ms"], 2),
            ]
        )

    table = render_table(headers, rows)

    lines: List[str] = []
    lines.append("# 实验一（真实链）：交易量 × 节点规模\n")
    lines.append("本实验直接在基于 Cosmos-SDK 的 hcp-consensus 多节点测试网上，通过 bank 模块发送真实交易，测量不同交易量与节点规模下的各项性能指标。\n")
    lines.append("## 实验配置\n")
    lines.append("- **交易类型**：bank send (1stake)\n")
    lines.append("- **共识引擎**：tPBFT (Cosmos SDK 模块)\n")
    lines.append("- **广播模式**：Sync (CheckTx通过即返回)\n")
    lines.append("- **监控指标**：\n")
    lines.append("  - TPS: 交易总数 / 发送总耗时\n")
    lines.append("  - 延迟: CLI 发送至返回的时间 (近似)\n")
    lines.append("  - CPU: 所有共识节点进程平均 CPU 使用率\n")
    lines.append("  - 带宽: 系统网卡总流量 (Bytes/s)\n")
    lines.append("  - RocksDB: 模拟 1KB 随机同步写入延迟\n")
    lines.append("\n## 实验结果\n")
    lines.append(table)
    lines.append("\n## 分析\n")
    lines.append("- **通信复杂度**：随着节点数增加，带宽占用应呈上升趋势 (O(n²))。")
    lines.append("- **延迟瓶颈**：在节点数较多时，P99 延迟可能会因共识轮次增加而显著上升。")
    lines.append("- **存储压力**：RocksDB 延迟反映了本地磁盘 IO 压力，若 CPU 不高但 TPS 低，可能是 IO 瓶颈。")
    
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="实验一：在真实 hcp-consensus 链上测试 TPS。")
    parser.add_argument(
        "--full",
        action="store_true",
        help="运行完整实验矩阵（节点数 4/8/16/32，交易数 100/500/1000），可能耗时较长。",
    )
    args = parser.parse_args()

    if args.full:
        node_counts = [4, 8, 16, 32]
        tx_counts = [100, 500, 1000]
    else:
        node_counts = [4, 8]
        tx_counts = [100]

    result = run_real_experiment(node_counts, tx_counts)
    out_json = Path("exp1_real_results.json")
    out_md = Path("exp1_real_report.md")

    write_json(str(out_json), result)
    report = generate_report_md(result)
    out_md.write_text(report, encoding="utf-8")

    print(f"JSON 结果已写入: {out_json}")
    print(f"Markdown 报告已写入: {out_md}")


if __name__ == "__main__":
    main()
