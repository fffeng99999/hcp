#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HCP-Consensus 共识引擎热插拔机制架构图生成脚本
基于 app/app.go 中的实际代码实现
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
from matplotlib.lines import Line2D
import numpy as np
import os

# 设置字体 - 使用系统可用字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def create_consensus_hotswap_diagram():
    fig, ax = plt.subplots(1, 1, figsize=(20, 15))
    ax.set_xlim(0, 20)
    ax.set_ylim(0, 15)
    ax.set_aspect('equal')
    ax.axis('off')

    # 颜色定义
    color_sdk = '#E3F2FD'
    color_interface = '#FFF9C4'
    color_switch = '#E8F5E9'
    color_engine = '#FCE4EC'
    color_text = '#212121'
    color_accent = '#1976D2'
    color_highlight = '#FF6F00'

    # ==================== 1. 基础框架层 (顶部) ====================
    framework_box = FancyBboxPatch((1.5, 13), 17, 1.6,
                                    boxstyle="round,pad=0.05,rounding_size=0.15",
                                    facecolor=color_sdk, edgecolor='#1565C0',
                                    linewidth=2.5, alpha=0.95)
    ax.add_patch(framework_box)
    ax.text(10, 14.1, 'Cosmos SDK v0.50 + CometBFT v0.38',
            ha='center', va='center', fontsize=14, fontweight='bold', color=color_accent)
    ax.text(10, 13.45, 'BaseApp | ABCI Application | KV Store | Module Manager',
            ha='center', va='center', fontsize=10.5, color='#546E7A')

    # ==================== 2. ConsensusEngine 接口定义 (接口层) ====================
    interface_box = FancyBboxPatch((2, 10.5), 16, 2,
                                    boxstyle="round,pad=0.03,rounding_size=0.12",
                                    facecolor=color_interface, edgecolor='#F9A825',
                                    linewidth=2.5, alpha=0.95)
    ax.add_patch(interface_box)

    ax.text(10, 11.95, 'ConsensusEngine Interface  (consensus/common/interface.go)',
            ha='center', va='center', fontsize=12.5, fontweight='bold', color='#F57F17')

    methods = ['Start()', 'Stop()', 'BeginBlock(ctx)', 'EndBlock(ctx) -> []ValidatorUpdate']
    method_x_positions = [4.2, 7.5, 11.5, 15.5]
    for method, x in zip(methods, method_x_positions):
        rect = FancyBboxPatch((x-1.6, 10.65), 3.2, 0.6,
                              boxstyle="round,pad=0.02,rounding_size=0.08",
                              facecolor='white', edgecolor='#FFB300',
                              linewidth=1.5, alpha=0.9)
        ax.add_patch(rect)
        ax.text(x, 10.95, method, ha='center', va='center', fontsize=9,
                fontfamily='monospace', color=color_text)

    # ==================== 3. 热插拔切换机制 (核心) ====================
    switch_box = FancyBboxPatch((3.5, 7.8), 13, 2.3,
                                 boxstyle="round,pad=0.04,rounding_size=0.15",
                                 facecolor=color_switch, edgecolor='#388E3C',
                                 linewidth=3, alpha=0.95)
    ax.add_patch(switch_box)

    ax.text(10, 9.75, '[Hot-Swap Mechanism]  app/app.go',
            ha='center', va='center', fontsize=12.5, fontweight='bold', color='#2E7D32')

    config_rect = FancyBboxPatch((4.2, 9.05), 11.6, 0.55,
                                  boxstyle="round,pad=0.02,rounding_size=0.08",
                                  facecolor='white', edgecolor='#66BB6A',
                                  linewidth=1.5, alpha=0.9)
    ax.add_patch(config_rect)
    ax.text(10, 9.32, 'engineType := appOpts.Get("consensus-engine")   // default: "tpbft"',
            ha='center', va='center', fontsize=10, fontfamily='monospace', color=color_text)

    code_lines = [
        ('switch engineType {', '#1B5E20'),
        ('  case "tpbft"              -> tpbft.NewTPBFT(cfg)', '#388E3C'),
        ('  case "hierarchical-tpbft" -> hierarchical_tpbft.New...(cfg)', '#388E3C'),
        ('  case "hotstuff"           -> hotstuff.NewHotStuffConsensus(cfg)', '#388E3C'),
        ('  case "raft"               -> raft.NewRaftConsensus(cfg)', '#388E3C'),
        ('  ... (total: 13 engines supported)', '#558B2F'),
        ('}', '#1B5E20'),
    ]
    code_y_start = 8.85
    for i, (line, color) in enumerate(code_lines):
        weight = 'bold' if i in [0, len(code_lines)-1] else 'normal'
        ax.text(4.5, code_y_start - i*0.27, line,
                ha='left', va='center', fontsize=8.5, fontfamily='monospace',
                color=color, fontweight=weight)

    # ==================== 4. 共识引擎实现池 (底部) ====================
    engines = [
        ('tPBFT\n(default)', 'tpbft/', 'Base Consensus', True),
        ('Hierarchical\nTPBFT', 'hierarchical_tpbft/', 'Layered Aggregation', False),
        ('HotStuff\nPipeline', 'hotstuff/', 'Pipeline Protocol', False),
        ('Raft', 'raft/', 'Leader Election', False),
        ('tPBFT\nParallel', 'tpbft_parallel/', 'Parallel Verify', False),
        ('tPBFT Parallel\nBlock', 'tpbft_parallel_block/', 'Parallel Block', False),
        ('Hierarchical\nLightweight', 'hierarchical_lightweight_tpbft/', 'Light Layered', False),
        ('Hierarchical\nHotspot', 'hierarchical_hotspot_tpbft/', 'Hotspot Opt.', False),
        ('Hierarchical\nTPBFT+Block', 'hierarchical_tpbft_parallel_block/', 'Layered+Block', False),
        ('PoW', 'pow/', 'Proof of Work', False),
        ('IBFT', 'ibft/', 'Byzantine FT', False),
        ('Votor', 'votor/', 'Voting Mechanism', False),
        ('Parallel\nMerkle', 'parallelmerkle/', 'Merkle Parallel', False),
    ]

    n_cols = 5
    n_rows = 3
    engine_width = 3.0
    engine_height = 1.35
    start_x = 1.0
    start_y = 5.85
    gap_x = 0.28
    gap_y = 0.18

    for idx, (name, path, desc, is_default) in enumerate(engines):
        row = idx // n_cols
        col = idx % n_cols
        x = start_x + col * (engine_width + gap_x)
        y = start_y - row * (engine_height + gap_y)

        border_color = color_highlight if is_default else '#C2185B'
        border_width = 2.8 if is_default else 1.8

        engine_box = FancyBboxPatch((x, y), engine_width, engine_height,
                                     boxstyle="round,pad=0.03,rounding_size=0.1",
                                     facecolor=color_engine, edgecolor=border_color,
                                     linewidth=border_width, alpha=0.92)
        ax.add_patch(engine_box)

        name_color = color_highlight if is_default else '#AD1457'
        ax.text(x + engine_width/2, y + engine_height*0.62, name,
                ha='center', va='center', fontsize=9.5, fontweight='bold', color=name_color)
        ax.text(x + engine_width/2, y + engine_height*0.25, path,
                ha='center', va='center', fontsize=7.5, fontfamily='monospace', color='#795548')
        ax.text(x + engine_width/2, y + engine_height*0.08, f'({desc})',
                ha='center', va='center', fontsize=7.2, color='#9E9E9E')

    # 从switch到引擎的连接线（代表性连线）
    sample_indices = [0, 1, 2, 3, 4]
    for idx in sample_indices:
        row = idx // n_cols
        col = idx % n_cols
        x = start_x + col * (engine_width + gap_x)
        y = start_y - row * (engine_height + gap_y)
        arrow = FancyArrowPatch(
            (x + engine_width/2, y + engine_height),
            (10, 7.8),
            connectionstyle=f"arc3,rad={-0.18 + idx*0.07}",
            arrowstyle='-|>',
            mutation_scale=9,
            color='#81C784',
            linewidth=1.3,
            alpha=0.55
        )
        ax.add_patch(arrow)

    # ==================== 5. 关键特性标注 (右侧) ====================
    features = [
        ('[Trust System]', 'TrustScorer.UpdateScore()\nHistory Window: 100 rounds'),
        ('[Validator Filter]', 'ValidatorSelector\nminTrustScore threshold'),
        ('[Layered Proof]', 'SubCommitProof Aggregation\nGroupCount x GroupSize\nInner Raft + Outer tPBFT'),
        ('[Dual Signature]', 'Ed25519 (primary)\nBLS (future integration)\nParallel WaitGroup verify'),
    ]

    feature_y = 5.65
    for i, (title, detail) in enumerate(features):
        fx = 17.8
        fy = feature_y - i * 1.42

        feat_box = FancyBboxPatch((fx-1.75, fy-0.58), 3.5, 1.16,
                                   boxstyle="round,pad=0.03,rounding_size=0.1",
                                   facecolor='#E1F5FE', edgecolor='#0277BD',
                                   linewidth=1.5, alpha=0.92)
        ax.add_patch(feat_box)

        ax.text(fx, fy + 0.24, title, ha='center', va='center',
                fontsize=9, fontweight='bold', color='#01579B')
        ax.text(fx, fy - 0.22, detail, ha='center', va='center',
                fontsize=7.5, color='#455A64', linespacing=1.25)

    # ==================== 6. 连接箭头 ====================
    arrow0 = FancyArrowPatch((10, 13), (10, 12.5),
                             connectionstyle="arc3,rad=0",
                             arrowstyle='-|>', mutation_scale=16,
                             color='#1565C0', linewidth=2.5)
    ax.add_patch(arrow0)

    arrow1 = FancyArrowPatch((10, 10.5), (10, 10.05),
                             connectionstyle="arc3,rad=0",
                             arrowstyle='-|>', mutation_scale=16,
                             color='#F57F17', linewidth=2.5)
    ax.add_patch(arrow1)

    arrow2 = FancyArrowPatch((10, 7.8), (10, 7.2),
                             connectionstyle="arc3,rad=0",
                             arrowstyle='-|>', mutation_scale=16,
                             color='#388E3C', linewidth=2.5)
    ax.add_patch(arrow2)

    # ==================== 7. 标题和图例 ====================
    ax.text(10, 14.8, 'HCP-Consensus Hot-Swap Architecture',
            ha='center', va='center', fontsize=17, fontweight='bold', color='#263238')
    ax.text(10, 14.4, 'Pluggable Consensus Engine Subsystem',
            ha='center', va='center', fontsize=11.5, color='#607D8B')

    legend_elements = [
        mpatches.Patch(facecolor=color_sdk, edgecolor='#1565C0', label='Cosmos SDK Framework'),
        mpatches.Patch(facecolor=color_interface, edgecolor='#F9A825', label='ConsensusEngine Interface'),
        mpatches.Patch(facecolor=color_switch, edgecolor='#388E3C', label='Hot-Switch Mechanism'),
        mpatches.Patch(facecolor=color_engine, edgecolor='#C2185B', label='Consensus Engine Implementation'),
        Line2D([0], [0], marker='s', color='w', markerfacecolor=color_highlight,
               markersize=12, label='Default Engine (tPBFT)'),
    ]
    legend = ax.legend(handles=legend_elements, loc='lower left',
                       bbox_to_anchor=(0.02, 0.01), fontsize=9.5,
                       framealpha=0.95, edgecolor='#BDBDBD')
    legend.get_frame().set_linewidth(1.5)

    ax.text(19.3, 0.25, 'v1.0 | Source: app/app.go',
            ha='right', va='center', fontsize=8.5, color='#9E9E9E', style='italic')

    plt.tight_layout()
    return fig, ax


if __name__ == '__main__':
    output_dir = r'f:\hcp-project-experiment\hcp\进展报告3\output'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    output_path = os.path.join(output_dir, 'fig_consensus_hotswap_architecture.png')

    fig, ax = create_consensus_hotswap_diagram()
    fig.savefig(output_path, dpi=300, bbox_inches='tight',
                facecolor='white', edgecolor='none', pad_inches=0.2)
    print(f'[OK] Architecture diagram saved to: {output_path}')
    plt.close(fig)
