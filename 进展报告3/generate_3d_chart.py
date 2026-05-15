import os
import json
import matplotlib.pyplot as plt
import matplotlib
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

matplotlib.rcParams['font.sans-serif'] = ['AR PL UMing CN', 'AR PL SungtiL GB', 'Droid Sans Fallback', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

output_dir = '/home/hcp-dev/hcp-project-experiment/hcp/进展报告3/output'
os.makedirs(output_dir, exist_ok=True)

# Data from Table 4-1 in Lun-Wen-Chu-Gao.md (P99 in ms)
rows = [
    {"algo": "PBFT", "nodes": 8, "p99": 420.0},
    {"algo": "PBFT", "nodes": 16, "p99": 650.0},
    {"algo": "PBFT", "nodes": 32, "p99": 980.0},
    {"algo": "HotStuff", "nodes": 8, "p99": 580.0},
    {"algo": "HotStuff", "nodes": 16, "p99": 790.0},
    {"algo": "HotStuff", "nodes": 32, "p99": 1120.0},
    {"algo": "Raft", "nodes": 8, "p99": 720.0},
    {"algo": "Raft", "nodes": 16, "p99": 980.0},
    {"algo": "Raft", "nodes": 32, "p99": 1350.0},
    {"algo": "CometBFT", "nodes": 8, "p99": 520.0},
    {"algo": "CometBFT", "nodes": 16, "p99": 740.0},
    {"algo": "CometBFT", "nodes": 32, "p99": 1060.0},
    {"algo": "tPBFT", "nodes": 8, "p99": 380.0},
    {"algo": "tPBFT", "nodes": 16, "p99": 490.0},
    {"algo": "tPBFT", "nodes": 32, "p99": 720.0},
]

algos = ['PBFT', 'HotStuff', 'Raft', 'CometBFT', 'tPBFT']
algo_colors = {'PBFT': '#1f77b4', 'HotStuff': '#ff7f0e', 'Raft': '#2ca02c', 'CometBFT': '#d62728', 'tPBFT': '#9467bd'}
algo_indices = {algo: i for i, algo in enumerate(algos)}

fig = plt.figure(figsize=(10, 7))
ax = fig.add_subplot(111, projection='3d')

for row in rows:
    x = row['nodes']
    y = algo_indices[row['algo']]
    z = row['p99']
    ax.scatter(x, y, z, c=algo_colors[row['algo']], s=100, label=row['algo'] if x == 8 else "")

# Draw connecting lines for each algorithm
for algo in algos:
    algo_rows = [r for r in rows if r['algo'] == algo]
    xs = [r['nodes'] for r in algo_rows]
    ys = [algo_indices[r['algo']] for r in algo_rows]
    zs = [r['p99'] for r in algo_rows]
    ax.plot(xs, ys, zs, c=algo_colors[algo], alpha=0.6)

ax.set_xticks([8, 16, 32])
ax.set_yticks(range(len(algos)))
ax.set_yticklabels(algos)
ax.set_xlabel('节点数 N')
ax.set_ylabel('算法')
ax.set_zlabel('P99 延迟(ms)')
ax.set_title('P99延迟-节点数-算法三维分布')
ax.legend(loc='upper left')

img_path = os.path.join(output_dir, 'p99_3d_latency.png')
fig.savefig(img_path, dpi=300, bbox_inches='tight')
plt.close(fig)

meta = {
    "caption": "8/16/32节点下各共识算法P99延迟的三维分布图",
    "description": "3D散点图展示PBFT、HotStuff、Raft、CometBFT和tPBFT在不同节点规模下的P99尾延迟（毫秒）。",
}

with open(img_path + '.meta.json', 'w', encoding='utf-8') as f:
    json.dump(meta, f, ensure_ascii=False)

print('Created 3D chart: ' + img_path)
