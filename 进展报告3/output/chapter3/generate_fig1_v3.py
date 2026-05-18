# -*- coding: utf-8 -*-
"""
HCP-Bench 数据分层与流转架构图 v3
修复：排版优化、消除空白、避免重叠
"""

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle, Polygon
import numpy as np
import os
import platform


def setup_chinese_font():
    """配置中文字体"""
    system = platform.system()

    if system == 'Windows':
        font_list = ['Microsoft YaHei', 'SimHei', 'SimSun', 'KaiTi']
    elif system == 'Darwin':
        font_list = ['PingFang SC', 'Heiti SC']
    else:
        font_list = ['WenQuanYi Micro Hei', 'Noto Sans CJK SC']

    available_fonts = {f.name for f in fm.fontManager.ttflist}

    for font_name in font_list:
        if font_name in available_fonts:
            plt.rcParams['font.sans-serif'] = [font_name]
            break

    plt.rcParams['axes.unicode_minus'] = False

    return plt.rcParams['font.sans-serif'][0] if plt.rcParams['font.sans-serif'] else 'DejaVu Sans'


def create_data_classification_flow_v3():
    """图1: 数据分类与整体流转（重新排版版）"""

    # 使用更紧凑的画布
    fig, ax = plt.subplots(1, 1, figsize=(16, 12))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 12)
    ax.axis('off')
    fig.patch.set_facecolor('white')

    # ========== 标题区 (y=11-12) ==========
    ax.text(8, 11.5, 'HCP-Bench 数据分层与流转',
            fontsize=20, fontweight='bold', ha='center', color='#1a237e')

    # ========== 第一层：数据源 (y=9.5-10.8) ==========
    source_y = 10.2
    source_box = FancyBboxPatch((0.5, source_y-0.6), 15, 1.4,
                                 boxstyle="round,pad=0.05",
                                 facecolor='#e3f2fd', edgecolor='#1565c0',
                                 linewidth=2)
    ax.add_patch(source_box)

    ax.text(8, source_y+0.45, '数据输入源', fontsize=13, fontweight='bold',
            ha='center', color='#0d47a1')

    sources = [
        ('HCP-Loadgen\n负载生成器', 2.5),
        ('HCP-Consensus\n共识引擎', 6),
        ('SystemMonitor\n系统监控', 9.5),
        ('HCP-Lab\n参数矩阵', 13)
    ]

    for label, x in sources:
        box = FancyBboxPatch((x-1.5, source_y-0.35), 3, 0.9,
                            boxstyle="round,pad=0.03",
                            facecolor='#bbdefb', edgecolor='#1976d2',
                            linewidth=1.5)
        ax.add_patch(box)
        ax.text(x, source_y+0.1, label, fontsize=9, ha='center', va='center',
                color='#0d47a1', fontweight='bold', linespacing=1.2)

    # ========== 第二层：分类决策 (y=7.8-9) ==========
    decision_y = 8.4
    decision_box = FancyBboxPatch((3, decision_y-0.65), 10, 1.3,
                                  boxstyle="round,pad=0.05",
                                  facecolor='#fff3e0', edgecolor='#e65100',
                                  linewidth=2.5)
    ax.add_patch(decision_box)

    ax.text(8, decision_y+0.35, '分类决策层', fontsize=14, fontweight='bold',
            ha='center', color='#e65100')
    ax.text(8, decision_y-0.15, '是否参与链上共识决策？',
            fontsize=11, ha='center', color='#bf360c')

    # 分支箭头
    ax.annotate('', xy=(4.5, 7.5), xytext=(6, 7.75),
               arrowprops=dict(arrowstyle='->', lw=3, color='#2e7d32'))
    ax.text(5.25, 7.88, '是', fontsize=11, fontweight='bold', color='#2e7d32')

    ax.annotate('', xy=(11.5, 7.5), xytext=(10, 7.75),
               arrowprops=dict(arrowstyle='->', lw=3, color='#c62828'))
    ax.text(10.75, 7.88, '否', fontsize=11, fontweight='bold', color='#c62828')

    # ========== 第三层左：区块链数据域 (x=0.5-7.5, y=1.5-7.3) ==========
    bc_x_center = 4
    bc_y_top = 7
    bc_height = 5.3

    bc_box = FancyBboxPatch((0.5, bc_y_top-bc_height), 7, bc_height,
                             boxstyle="round,pad=0.08",
                             facecolor='#e8f5e9', edgecolor='#2e7d32',
                             linewidth=3)
    ax.add_patch(bc_box)

    # 区块链数据标题
    ax.text(bc_x_center, bc_y_top-0.4, '区块链数据', fontsize=16, fontweight='bold',
            ha='center', color='#1b5e20')
    ax.text(bc_x_center, bc_y_top-0.85,
            '维护者: HCP-Consensus | 存储: RocksDB + IAVL',
            fontsize=9.5, ha='center', color='#388e3c')

    # 区块链数据类型 - 两行三列网格
    bc_items_row1 = [
        ('交易数据', 1.83),
        ('区块数据', 4),
        ('应用状态', 6.17),
    ]
    bc_items_row2 = [
        ('验证者集合', 1.83),
        ('信任评分', 4),
        ('提交证明', 6.17),
    ]

    row1_y = bc_y_top - 1.8
    row2_y = bc_y_top - 3.2

    for label, x in bc_items_row1:
        box = FancyBboxPatch((x-1.2, row1_y-0.55), 2.4, 1.1,
                            boxstyle="round,pad=0.02",
                            facecolor='#c8e6c9', edgecolor='#66bb6a',
                            linewidth=1.5)
        ax.add_patch(box)
        ax.text(x, row1_y, label, fontsize=10, ha='center', va='center',
                color='#1b5e20', fontweight='bold')

    for label, x in bc_items_row2:
        box = FancyBboxPatch((x-1.2, row2_y-0.55), 2.4, 1.1,
                            boxstyle="round,pad=0.02",
                            facecolor='#a5d6a7', edgecolor='#66bb6a',
                            linewidth=1.5)
        ax.add_patch(box)
        ax.text(x, row2_y, label, fontsize=10, ha='center', va='center',
                color='#1b5e20', fontweight='bold')

    # 特性标签框
    features_bc_y = bc_y_top - bc_height + 0.8
    features_bc_text = '[+] 参与共识  [+] 影响状态转移  [+] 可验证可追溯'
    ax.text(bc_x_center, features_bc_y, features_bc_text, fontsize=9,
            ha='center', color='#2e7d32',
            bbox=dict(boxstyle='round,pad=0.35', facecolor='#f1f8e9',
                     edgecolor='#81c784', linewidth=1))

    # ========== 第三层右：系统数据域 (x=8.5-15.5, y=1.5-7.3) ==========
    sys_x_center = 12
    sys_y_top = 7
    sys_height = 5.3

    sys_box = FancyBboxPatch((8.5, sys_y_top-sys_height), 7, sys_height,
                              boxstyle="round,pad=0.08",
                              facecolor='#fce4ec', edgecolor='#c62828',
                              linewidth=3)
    ax.add_patch(sys_box)

    # 系统数据标题
    ax.text(sys_x_center, sys_y_top-0.4, '系统数据', fontsize=16, fontweight='bold',
            ha='center', color='#b71c1c')
    ax.text(sys_x_center, sys_y_top-0.85,
            '维护者: HCP-Loadgen + HCP-Lab | 存储: PostgreSQL + File',
            fontsize=9.5, ha='center', color='#d32f2f')

    # 系统数据类型 - 两行三列网格
    sys_items_row1 = [
        ('实验配置', 9.83),
        ('节点监控', 12),
        ('性能指标', 14.17),
    ]
    sys_items_row2 = [
        ('日志追踪', 9.83),
        ('Schema隔离', 12),
        ('JSON/CSV', 14.17),
    ]

    for label, x in sys_items_row1:
        box = FancyBboxPatch((x-1.2, row1_y-0.55), 2.4, 1.1,
                            boxstyle="round,pad=0.02",
                            facecolor='#f8bbd0', edgecolor='#ef5350',
                            linewidth=1.5)
        ax.add_patch(box)
        ax.text(x, row1_y, label, fontsize=10, ha='center', va='center',
                color='#b71c1c', fontweight='bold')

    for label, x in sys_items_row2:
        box = FancyBboxPatch((x-1.2, row2_y-0.55), 2.4, 1.1,
                            boxstyle="round,pad=0.02",
                            facecolor='#f48fb1', edgecolor='#ef5350',
                            linewidth=1.5)
        ax.add_patch(box)
        ax.text(x, row2_y, label, fontsize=10, ha='center', va='center',
                color='#b71c1c', fontweight='bold')

    # 特性标签框
    features_sys_text = '[-] 不参与共识  [+] 实验可复现  [+] 性能分析完整'
    ax.text(sys_x_center, features_bc_y, features_sys_text, fontsize=9,
            ha='center', color='#c62828',
            bbox=dict(boxstyle='round,pad=0.35', facecolor='#ffebee',
                     edgecolor='#e57373', linewidth=1))

    # ========== 连接箭头：数据源到决策层 ==========
    arrow_y_start = source_y - 0.6
    arrow_y_end = decision_y + 0.65
    for x in [2.5, 6, 9.5, 13]:
        ax.annotate('', xy=(x, arrow_y_end), xytext=(x, arrow_y_start),
                   arrowprops=dict(arrowstyle='->', lw=1.8, color='#1565c0'))

    # ========== 底部说明 (y=0.3-1) ==========
    bottom_y = 0.6
    design_goal = (
        '设计目标：降低实验系统与共识路径耦合 | '
        '区块链数据保证一致性 | 系统数据支撑实验分析'
    )
    ax.text(8, bottom_y, design_goal, fontsize=10, ha='center',
            color='#616161', style='italic')

    plt.tight_layout(pad=0.5)
    return fig


if __name__ == '__main__':
    # 输出到脚本所在目录
    output_dir = os.path.dirname(os.path.abspath(__file__))

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 配置中文字体
    font_used = setup_chinese_font()
    print(f"使用字体: {font_used}")

    print("\n正在生成数据分层与流转图 v3...")

    # 生成优化后的图1
    fig = create_data_classification_flow_v3()
    output_path = os.path.join(output_dir, 'fig3_1_data_classification_flow.png')
    fig.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white',
                pad_inches=0.3)
    plt.close(fig)

    print(f"\n✅ 图片已成功生成！")
    print(f"   路径: {output_path}")
