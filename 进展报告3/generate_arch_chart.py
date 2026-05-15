import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib
import os

matplotlib.rcParams['font.sans-serif'] = ['AR PL UMing CN', 'AR PL SungtiL GB', 'Droid Sans Fallback', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

output_dir = '/home/hcp-dev/hcp-project-experiment/hcp/进展报告3/output'
os.makedirs(output_dir, exist_ok=True)

fig, ax = plt.subplots(1, 1, figsize=(14, 10))
ax.set_xlim(0, 14)
ax.set_ylim(0, 10)
ax.axis('off')

# Title
ax.text(7, 9.5, 'HCP-Bench 总体架构图', fontsize=18, fontweight='bold', ha='center', va='center')

# Colors
color_engine = '#E3F2FD'
color_load = '#E8F5E9'
color_orchestration = '#FFF3E0'
color_fairness = '#FCE4EC'
color_border_engine = '#1976D2'
color_border_load = '#388E3C'
color_border_orchestration = '#F57C00'
color_border_fairness = '#C2185B'

# === Layer 1: Consensus Engine Subsystem (Top) ===
engine_box = FancyBboxPatch((1, 6.5), 12, 2.2, boxstyle="round,pad=0.1", 
                             facecolor=color_engine, edgecolor=color_border_engine, linewidth=2)
ax.add_patch(engine_box)
ax.text(7, 8.3, '共识引擎子系统', fontsize=14, fontweight='bold', ha='center', va='center', color=color_border_engine)

# Engine components
engine_comps = [
    (2.5, 7.2, 'PBFT'),
    (4.5, 7.2, 'HotStuff'),
    (6.5, 7.2, 'Raft'),
    (8.5, 7.2, 'CometBFT'),
    (10.5, 7.2, 'tPBFT'),
    (3.5, 6.8, '分层tPBFT'),
    (7, 6.8, '并行Merkle'),
    (10.5, 6.8, '轻量tPBFT'),
]
for x, y, name in engine_comps:
    box = FancyBboxPatch((x-0.8, y-0.15), 1.6, 0.3, boxstyle="round,pad=0.02",
                         facecolor='white', edgecolor=color_border_engine, linewidth=1)
    ax.add_patch(box)
    ax.text(x, y, name, fontsize=9, ha='center', va='center')

# === Layer 2: Load Generation Subsystem (Middle Left) ===
load_box = FancyBboxPatch((1, 3.8), 5.5, 2.2, boxstyle="round,pad=0.1",
                           facecolor=color_load, edgecolor=color_border_load, linewidth=2)
ax.add_patch(load_box)
ax.text(3.75, 5.6, '负载生成子系统', fontsize=14, fontweight='bold', ha='center', va='center', color=color_border_load)

load_comps = [
    (2.5, 5.0, '交易生成器'),
    (5.0, 5.0, '速率控制器'),
    (2.5, 4.5, '负载模式库'),
    (5.0, 4.5, '性能采集器'),
    (3.75, 4.1, '数据库隔离层'),
]
for x, y, name in load_comps:
    box = FancyBboxPatch((x-0.9, y-0.15), 1.8, 0.3, boxstyle="round,pad=0.02",
                         facecolor='white', edgecolor=color_border_load, linewidth=1)
    ax.add_patch(box)
    ax.text(x, y, name, fontsize=9, ha='center', va='center')

# === Layer 3: Experiment Orchestration Subsystem (Middle Right) ===
orch_box = FancyBboxPatch((7.5, 3.8), 5.5, 2.2, boxstyle="round,pad=0.1",
                           facecolor=color_orchestration, edgecolor=color_border_orchestration, linewidth=2)
ax.add_patch(orch_box)
ax.text(10.25, 5.6, '实验编排子系统', fontsize=14, fontweight='bold', ha='center', va='center', color=color_border_orchestration)

orch_comps = [
    (8.8, 5.0, '实验矩阵配置'),
    (11.7, 5.0, '执行调度器'),
    (8.8, 4.5, '结果分析器'),
    (11.7, 4.5, '报告生成器'),
    (10.25, 4.1, 'Web 控制台'),
]
for x, y, name in orch_comps:
    box = FancyBboxPatch((x-0.9, y-0.15), 1.8, 0.3, boxstyle="round,pad=0.02",
                         facecolor='white', edgecolor=color_border_orchestration, linewidth=1)
    ax.add_patch(box)
    ax.text(x, y, name, fontsize=9, ha='center', va='center')

# === Layer 4: Fairness Guarantee (Bottom) ===
fairness_box = FancyBboxPatch((1, 1.5), 12, 1.8, boxstyle="round,pad=0.1",
                               facecolor=color_fairness, edgecolor=color_border_fairness, linewidth=2)
ax.add_patch(fairness_box)
ax.text(7, 3.0, '公平性保证层', fontsize=14, fontweight='bold', ha='center', va='center', color=color_border_fairness)

fairness_comps = [
    (2.5, 2.3, '统一硬件环境'),
    (5.5, 2.3, '统一网络环境'),
    (8.5, 2.3, '统一负载模式'),
    (11.5, 2.3, '热插拔机制'),
    (4.0, 1.9, '相同代码路径'),
    (7.0, 1.9, '相同配置框架'),
    (10.0, 1.9, '消除条件差异'),
]
for x, y, name in fairness_comps:
    box = FancyBboxPatch((x-0.9, y-0.15), 1.8, 0.3, boxstyle="round,pad=0.02",
                         facecolor='white', edgecolor=color_border_fairness, linewidth=1)
    ax.add_patch(box)
    ax.text(x, y, name, fontsize=9, ha='center', va='center')

# === Arrows ===
arrow_style = dict(arrowstyle='->', color='#666666', lw=1.5, connectionstyle="arc3,rad=0")

# Load -> Engine
ax.annotate('', xy=(3.75, 6.5), xytext=(3.75, 6.0),
            arrowprops=dict(arrowstyle='->', color=color_border_load, lw=2))
ax.text(3.75, 6.25, '注入交易', fontsize=8, ha='center', va='center', color=color_border_load)

# Engine -> Load (metrics)
ax.annotate('', xy=(5.5, 6.0), xytext=(5.5, 6.5),
            arrowprops=dict(arrowstyle='->', color=color_border_engine, lw=2))
ax.text(5.5, 6.25, '性能指标', fontsize=8, ha='center', va='center', color=color_border_engine)

# Orchestration -> Engine
ax.annotate('', xy=(10.25, 6.5), xytext=(10.25, 6.0),
            arrowprops=dict(arrowstyle='->', color=color_border_orchestration, lw=2))
ax.text(10.25, 6.25, '配置/调度', fontsize=8, ha='center', va='center', color=color_border_orchestration)

# Orchestration -> Load
ax.annotate('', xy=(7.5, 4.9), xytext=(7.0, 4.9),
            arrowprops=dict(arrowstyle='<->', color='#666666', lw=1.5))
ax.text(7.25, 5.1, '参数同步', fontsize=8, ha='center', va='center', color='#666666')

# Fairness -> All (dashed lines)
ax.annotate('', xy=(3.75, 3.8), xytext=(3.75, 3.3),
            arrowprops=dict(arrowstyle='->', color=color_border_fairness, lw=1.5, linestyle='--'))
ax.annotate('', xy=(10.25, 3.8), xytext=(10.25, 3.3),
            arrowprops=dict(arrowstyle='->', color=color_border_fairness, lw=1.5, linestyle='--'))
ax.annotate('', xy=(7, 3.8), xytext=(7, 3.3),
            arrowprops=dict(arrowstyle='->', color=color_border_fairness, lw=1.5, linestyle='--'))

# Bottom note
ax.text(7, 0.8, '图3-1  HCP-Bench 三子系统架构与公平性保证设计', 
        fontsize=11, ha='center', va='center', style='italic', color='#333333')

plt.tight_layout()
img_path = os.path.join(output_dir, 'fig3_1_architecture.png')
fig.savefig(img_path, dpi=300, bbox_inches='tight')
plt.close(fig)

import json
meta = {
    "caption": "图3-1 HCP-Bench总体架构图",
    "description": "展示HCP-Bench的三子系统架构：共识引擎子系统、负载生成子系统、实验编排子系统，以及底部的公平性保证层。"
}
with open(img_path + '.meta.json', 'w', encoding='utf-8') as f:
    json.dump(meta, f, ensure_ascii=False)

print('Created architecture chart: ' + img_path)
