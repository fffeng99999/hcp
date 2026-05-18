import matplotlib.pyplot as plt
import matplotlib
import json
import os

matplotlib.rcParams['font.sans-serif'] = ['AR PL UMing CN', 'AR PL SungtiL GB', 'Droid Sans Fallback', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

# 输出到脚本所在目录
output_dir = os.path.dirname(os.path.abspath(__file__))
os.makedirs(output_dir, exist_ok=True)

# 数据根据论文表格手动录入
Ns = [8, 16, 32]

# 图4-1 TPS-N性能曲线
algos = ['PBFT', 'HotStuff', 'Raft', 'CometBFT', 'tPBFT']
TPS = {
    'PBFT': [58.20, 42.50, 28.60],
    'HotStuff': [48.50, 36.20, 24.80],
    'Raft': [35.80, 26.50, 18.20],
    'CometBFT': [45.60, 33.80, 22.50],
    'tPBFT': [62.50, 48.20, 32.50],
}

fig1, ax1 = plt.subplots(figsize=(8, 5))
for algo in algos:
    ax1.plot(Ns, TPS[algo], marker='o', label=algo)
ax1.set_title('TPS vs 节点数 (8–32节点)')
ax1.set_xlabel('节点数')
ax1.set_ylabel('TPS (tx/s)')
ax1.legend()
ax1.grid(True)
fig1.savefig(os.path.join(output_dir, 'fig4_1_tps_vs_nodes.png'), dpi=300, bbox_inches='tight')
with open(os.path.join(output_dir, 'fig4_1_tps_vs_nodes.png.meta.json'), 'w') as f:
    json.dump({"caption": "图4-1 不同共识算法TPS随节点数变化曲线", "description": "折线图展示PBFT、HotStuff、Raft、CometBFT、tPBFT在8、16、32节点下的TPS表现"}, f, ensure_ascii=False)
plt.close(fig1)

# 图4-2 P99-N延迟曲线
P99 = {
    'PBFT': [420.0, 650.0, 980.0],
    'HotStuff': [580.0, 790.0, 1120.0],
    'Raft': [720.0, 980.0, 1350.0],
    'CometBFT': [520.0, 740.0, 1060.0],
    'tPBFT': [380.0, 490.0, 720.0],
}

fig2, ax2 = plt.subplots(figsize=(8, 5))
for algo in algos:
    ax2.plot(Ns, P99[algo], marker='o', label=algo)
ax2.set_title('P99延迟 vs 节点数 (8–32节点)')
ax2.set_xlabel('节点数')
ax2.set_ylabel('P99延迟 (ms)')
ax2.legend()
ax2.grid(True)
fig2.savefig(os.path.join(output_dir, 'fig4_2_p99_vs_nodes.png'), dpi=300, bbox_inches='tight')
with open(os.path.join(output_dir, 'fig4_2_p99_vs_nodes.png.meta.json'), 'w') as f:
    json.dump({"caption": "图4-2 不同共识算法P99延迟随节点数变化曲线", "description": "折线图展示各算法在8、16、32节点下的P99尾延迟"}, f, ensure_ascii=False)
plt.close(fig2)

# 图4-3 退化率对比柱状图
algos2 = ['PBFT', 'HotStuff', 'Raft', 'CometBFT', 'tPBFT']
R_deg = [50.86, 48.87, 49.16, 50.66, 48.00]

fig3, ax3 = plt.subplots(figsize=(8, 5))
ax3.bar(algos2, R_deg, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'])
ax3.set_title('8到32节点TPS退化率对比')
ax3.set_xlabel('算法')
ax3.set_ylabel('退化率 (%)')
ax3.grid(True, axis='y')
fig3.savefig(os.path.join(output_dir, 'fig4_3_degradation_rates.png'), dpi=300, bbox_inches='tight')
with open(os.path.join(output_dir, 'fig4_3_degradation_rates.png.meta.json'), 'w') as f:
    json.dump({"caption": "图4-3 各共识算法TPS退化率对比", "description": "柱状图展示PBFT、HotStuff、Raft、CometBFT、tPBFT从8到32节点的TPS退化率"}, f, ensure_ascii=False)
plt.close(fig3)

# 图4-4 分组参数扫描 (K 对 TPS & P99)
K_vals = [1, 2, 4, 8, 16]
TPS_K = [28.60, 31.20, 34.50, 30.80, 24.60]
P99_K = [980.0, 580.0, 320.0, 280.0, 310.0]

fig4, ax4 = plt.subplots(figsize=(8, 5))
ax4.plot(K_vals, TPS_K, marker='o', label='TPS')
ax4.plot(K_vals, P99_K, marker='s', label='P99(ms)')
ax4.set_title('分组数K对TPS和P99的影响 (N=32)')
ax4.set_xlabel('分组数 K')
ax4.set_ylabel('数值')
ax4.legend()
ax4.grid(True)
fig4.savefig(os.path.join(output_dir, 'fig4_4_group_scan.png'), dpi=300, bbox_inches='tight')
with open(os.path.join(output_dir, 'fig4_4_group_scan.png.meta.json'), 'w') as f:
    json.dump({"caption": "图4-4 分组数K对TPS和P99的影响", "description": "折线图同时展示在N=32时分组数K变化对TPS和P99延迟的影响"}, f, ensure_ascii=False)
plt.close(fig4)

# 图4-6 TPS天花板曲线 (吞吐量饱和边界)
algos3 = ['PBFT', 'HotStuff', 'Raft', 'CometBFT', 'tPBFT', '分层tPBFT']
T_sat = {
    'PBFT': [58.2, 43.5, 28.6],
    'HotStuff': [48.5, 37.2, 24.8],
    'Raft': [35.8, 27.1, 18.2],
    'CometBFT': [45.6, 35.0, 22.5],
    'tPBFT': [62.5, 49.5, 32.5],
    '分层tPBFT': [68.0, 55.0, 38.6],
}
fig5, ax5 = plt.subplots(figsize=(8, 5))
for algo in algos3:
    ax5.plot(Ns, T_sat[algo], marker='o', label=algo)
ax5.set_title('各算法吞吐量饱和点随节点数变化')
ax5.set_xlabel('节点数')
ax5.set_ylabel('T_sat (tx/s)')
ax5.legend()
ax5.grid(True)
fig5.savefig(os.path.join(output_dir, 'fig4_6_tsat_vs_nodes.png'), dpi=300, bbox_inches='tight')
with open(os.path.join(output_dir, 'fig4_6_tsat_vs_nodes.png.meta.json'), 'w') as f:
    json.dump({"caption": "图4-6 各算法吞吐量饱和点随节点数变化曲线", "description": "折线图展示PBFT、HotStuff、Raft、CometBFT、tPBFT及分层tPBFT在8、16、32节点下的吞吐量饱和点"}, f, ensure_ascii=False)
plt.close(fig5)

print('Created charts: ' + ', '.join(sorted(os.listdir(output_dir))))
