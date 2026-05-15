import os
import json
import matplotlib.pyplot as plt
import matplotlib
import numpy as np

matplotlib.rcParams['font.sans-serif'] = ['AR PL UMing CN', 'AR PL SungtiL GB', 'Droid Sans Fallback', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

output_dir = '/home/hcp-dev/hcp-project-experiment/hcp/进展报告3/output'
os.makedirs(output_dir, exist_ok=True)

# Data from Table 4-1
rows = [
    {"algo": "PBFT", "nodes": 8, "tps": 58.23, "p50": 85.4, "p95": 321.7, "p99": 421.3, "cpu": 78.52, "net": 45.28},
    {"algo": "PBFT", "nodes": 16, "tps": 42.57, "p50": 121.8, "p95": 482.5, "p99": 653.2, "cpu": 82.37, "net": 68.43},
    {"algo": "PBFT", "nodes": 32, "tps": 28.64, "p50": 181.6, "p95": 723.3, "p99": 983.8, "cpu": 85.14, "net": 89.61},
    {"algo": "HotStuff", "nodes": 8, "tps": 48.53, "p50": 111.2, "p95": 423.4, "p99": 583.6, "cpu": 75.28, "net": 38.64},
    {"algo": "HotStuff", "nodes": 16, "tps": 36.27, "p50": 151.5, "p95": 583.8, "p99": 793.4, "cpu": 79.83, "net": 52.37},
    {"algo": "HotStuff", "nodes": 32, "tps": 24.86, "p50": 211.3, "p95": 823.6, "p99": 1123.7, "cpu": 83.45, "net": 71.52},
    {"algo": "Raft", "nodes": 8, "tps": 35.84, "p50": 141.7, "p95": 523.5, "p99": 723.4, "cpu": 72.16, "net": 32.48},
    {"algo": "Raft", "nodes": 16, "tps": 26.58, "p50": 191.4, "p95": 723.7, "p99": 983.5, "cpu": 76.53, "net": 45.86},
    {"algo": "Raft", "nodes": 32, "tps": 18.29, "p50": 261.8, "p95": 983.4, "p99": 1353.6, "cpu": 80.27, "net": 58.64},
    {"algo": "CometBFT", "nodes": 8, "tps": 45.67, "p50": 101.3, "p95": 383.6, "p99": 523.4, "cpu": 74.58, "net": 36.85},
    {"algo": "CometBFT", "nodes": 16, "tps": 33.86, "p50": 141.7, "p95": 543.3, "p99": 743.8, "cpu": 78.26, "net": 49.57},
    {"algo": "CometBFT", "nodes": 32, "tps": 22.58, "p50": 201.5, "p95": 783.7, "p99": 1063.4, "cpu": 81.64, "net": 65.38},
    {"algo": "tPBFT", "nodes": 8, "tps": 62.58, "p50": 75.3, "p95": 283.4, "p99": 383.7, "cpu": 76.85, "net": 42.56},
    {"algo": "tPBFT", "nodes": 16, "tps": 48.27, "p50": 95.6, "p95": 363.8, "p99": 493.5, "cpu": 80.56, "net": 58.27},
    {"algo": "tPBFT", "nodes": 32, "tps": 32.58, "p50": 131.4, "p95": 523.6, "p99": 723.3, "cpu": 84.28, "net": 76.85},
]

algos = ['PBFT', 'HotStuff', 'Raft', 'CometBFT', 'tPBFT']
algo_colors = {'PBFT': '#1f77b4', 'HotStuff': '#ff7f0e', 'Raft': '#2ca02c', 'CometBFT': '#d62728', 'tPBFT': '#9467bd'}
nodes_list = [8, 16, 32]
metrics = ['tps', 'p50', 'p95', 'p99', 'cpu', 'net']
metric_labels = ['TPS (tx/s)', 'P50 (ms)', 'P95 (ms)', 'P99 (ms)', 'CPU (%)', '网络 (Mbps)']

# Create a 3x2 subplot grid
fig, axes = plt.subplots(3, 2, figsize=(16, 18))
fig.suptitle('各共识算法性能指标综合对比', fontsize=16, fontweight='bold')

for idx, (metric, label) in enumerate(zip(metrics, metric_labels)):
    ax = axes[idx // 2, idx % 2]
    
    for algo in algos:
        algo_data = [r for r in rows if r['algo'] == algo]
        x = [r['nodes'] for r in algo_data]
        y = [r[metric] for r in algo_data]
        ax.plot(x, y, marker='o', label=algo, color=algo_colors[algo], linewidth=2, markersize=8)
    
    ax.set_xlabel('节点数 N')
    ax.set_ylabel(label)
    ax.set_title(f'{label} vs 节点数')
    ax.set_xticks(nodes_list)
    ax.legend()
    ax.grid(True, alpha=0.3)

plt.tight_layout(rect=[0, 0, 1, 0.96])

img_path = os.path.join(output_dir, 'comprehensive_metrics.png')
fig.savefig(img_path, dpi=300, bbox_inches='tight')
plt.close(fig)

meta = {
    "caption": "图4-X 各共识算法性能指标综合对比",
    "description": "3x2子图展示PBFT、HotStuff、Raft、CometBFT和tPBFT在8/16/32节点下的TPS、P50、P95、P99、CPU、网络带宽六项指标对比。",
}

with open(img_path + '.meta.json', 'w', encoding='utf-8') as f:
    json.dump(meta, f, ensure_ascii=False)

print('Created comprehensive chart: ' + img_path)
