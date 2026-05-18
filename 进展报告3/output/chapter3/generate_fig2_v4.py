# -*- coding: utf-8 -*-
"""
HCP-Bench 区块链数据存储架构图 v4
修复：缩小中间块、放大周围元素、严格对齐
"""

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.patches import FancyBboxPatch, Rectangle
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


def create_blockchain_storage_v4():
    """图2: 区块链数据存储架构（优化版）"""

    # 画布设置
    fig, ax = plt.subplots(1, 1, figsize=(17, 14))
    ax.set_xlim(0, 17)
    ax.set_ylim(0, 14)
    ax.axis('off')
    fig.patch.set_facecolor('white')

    # ========== 标题区 (y=13-13.8) ==========
    ax.text(8.5, 13.6, '区块链数据存储架构',
            fontsize=20, fontweight='bold', ha='center', color='#1b5e20')
    ax.text(8.5, 13.1, 'RocksDB + IAVL+Tree 四层存储栈',
            fontsize=12, ha='center', color='#43a047')

    # ========== 布局参数定义 ==========
    # 中间区域：x ∈ [4, 13]，宽度9，中心 x=8.5
    center_x = 8.5
    left_edge = 4.0      # 中间区域左边界
    right_edge = 13.0    # 中间区域右边界
    mid_width = right_edge - left_edge  # 9

    # 左侧区域：x ∈ [0.3, 3.5]，宽度3.2，中心 x=1.9
    left_center_x = 1.9

    # 右侧区域：x ∈ [13.5, 16.7]，宽度3.2，中心 x=15.1
    right_center_x = 15.1

    # 四层存储的 Y 坐标（紧凑排列，避免重叠）
    layers_config = [
        {'name': '共识子系统',
         'sub': 'tPBFT / HotStuff / Raft / Hierarchical',
         'y': 11.4, 'height': 1.15,
         'color': '#c8e6c9', 'edge_color': '#2e7d32',
         'text_color': '#1b5e20'},
        {'name': '应用层 (ABCI)',
         'sub': 'BeginBlock → DeliverTx → EndBlock → Commit',
         'y': 9.95, 'height': 1.25,
         'color': '#dcedc8', 'edge_color': '#558b2f',
         'text_color': '#33691e'},
        {'name': 'IAVL+Tree 键值存储',
         'sub': '版本化 · Merkle验证 · 快照回溯 · 缓存优化(781250)',
         'y': 8.35, 'height': 1.35,
         'color': '#fff9c4', 'edge_color': '#f9a825',
         'text_color': '#f57f17'},
        {'name': 'RocksDB 存储引擎',
         'sub': 'WAL预写日志 · MemTable内存表 · SSTable磁盘 · Compaction压缩合并',
         'y': 6.65, 'height': 1.45,
         'color': '#b39ddb', 'edge_color': '#512da8',
         'text_color': '#311b92'},
    ]

    # ========== 绘制中间四层存储 ==========
    for i, layer in enumerate(layers_config):
        y_top = layer['y']
        h = layer['height']
        y_bottom = y_top - h

        # 绘制矩形框
        box = FancyBboxPatch(
            (left_edge, y_bottom), mid_width, h,
            boxstyle="round,pad=0.05",
            facecolor=layer['color'],
            edgecolor=layer['edge_color'],
            linewidth=2.5
        )
        ax.add_patch(box)

        # 层名称（上半部分）
        ax.text(center_x, y_top - h*0.38,
                layer['name'],
                fontsize=13, fontweight='bold',
                ha='center', va='center',
                color=layer['text_color'])

        # 子描述（下半部分）
        ax.text(center_x, y_top - h*0.72,
                layer['sub'],
                fontsize=9.5,
                ha='center', va='center',
                color=layer['text_color'])

    # ========== 物理存储层 (y=5.0-5.75) ==========
    phys_y_top = 5.65
    phys_height = 0.85
    phys_box = FancyBboxPatch(
        (left_edge + 1.5, phys_y_top - phys_height),
        mid_width - 3, phys_height,
        boxstyle="round,pad=0.04",
        facecolor='#cfd8dc',
        edgecolor='#546e7a',
        linewidth=2
    )
    ax.add_patch(phys_box)

    ax.text(center_x, phys_y_top - phys_height/2 + 0.08,
            '物理磁盘: block_store.db | state.db | application.db | wal/',
            fontsize=10, fontweight='bold',
            ha='center', color='#37474f')

    # ========== 左侧：数据类型详情（放大版）==========
    data_types_title_y = 11.55
    ax.text(left_center_x, data_types_title_y + 0.45,
            '数据类型',
            fontsize=13, fontweight='bold',
            ha='center', color='#004d40')

    # 数据类型列表（与中间层垂直对齐）
    data_types = [
        ('交易数据', '订单/账户\n价格/数量\n时间戳'),
        ('区块数据', '高度/哈希\n交易列表\n提交证明'),
        ('应用状态', '账户余额\n订单状态\nKV状态'),
        ('验证者集', '节点列表\n公钥地址\n投票权重'),
        ('信任评分', '评分值\n成功率\n100轮窗口'),
    ]

    # 计算每个数据类型的Y坐标，与对应层对齐
    type_start_y = 10.95
    type_height = 1.18
    type_spacing = 0.02

    for i, (type_name, type_desc) in enumerate(data_types):
        y_pos = type_start_y - i * (type_height + type_spacing)

        # 数据类型框（放大版）
        type_box = FancyBboxPatch(
            (left_center_x - 1.45, y_pos - type_height/2),
            2.9, type_height,
            boxstyle="round,pad=0.03",
            facecolor='#e0f2f1',
            edgecolor='#00796b',
            linewidth=1.8
        )
        ax.add_patch(type_box)

        # 类型名称（加粗放大）
        ax.text(left_center_x, y_pos + 0.22,
                type_name,
                fontsize=11, fontweight='bold',
                ha='center', color='#00695c')

        # 类型描述（放大）
        ax.text(left_center_x, y_pos - 0.28,
                type_desc,
                fontsize=9, ha='center',
                color='#00796b', linespacing=1.35)

    # ========== 右侧：关键配置（放大版）==========
    config_title_y = 11.55
    ax.text(right_center_x, config_title_y + 0.45,
            '关键配置',
            fontsize=13, fontweight='bold',
            ha='center', color='#bf360c')

    # 配置项列表（与中间层垂直对齐）
    configs = [
        ('db_backend', '= rocksdb'),
        ('StoreType', '= IAVL'),
        ('iavl-cache-size', '= 781250'),
        ('discard_abci_responses', '= false'),
        ('tx_indexer', '= kv'),
    ]

    config_start_y = 10.85
    config_height = 1.1
    config_spacing = 0.04

    for i, (config_key, config_val) in enumerate(configs):
        y_pos = config_start_y - i * (config_height + config_spacing)

        # 配置框（放大版）
        config_box = FancyBboxPatch(
            (right_center_x - 1.45, y_pos - config_height/2),
            2.9, config_height,
            boxstyle="round,pad=0.03",
            facecolor='#fbe9e7',
            edgecolor='#d84315',
            linewidth=1.8
        )
        ax.add_patch(config_box)

        # 配置键名（等宽字体，放大）
        ax.text(right_center_x, y_pos + 0.2,
                config_key,
                fontsize=10, fontweight='bold',
                ha='center', family='monospace', color='#bf360c')

        # 配置值（等宽字体，放大）
        ax.text(right_center_x, y_pos - 0.22,
                config_val,
                fontsize=10.5, ha='center',
                family='monospace', color='#d84315')

    # ========== 垂直连接箭头（从上到下）==========
    arrow_positions = [
        (layers_config[0]['y'] - layers_config[0]['height'],  # 第1层底部
         layers_config[1]['y']),                                # 第2层顶部
        (layers_config[1]['y'] - layers_config[1]['height'],  # 第2层底部
         layers_config[2]['y']),                                # 第3层顶部
        (layers_config[2]['y'] - layers_config[2]['height'],  # 第3层底部
         layers_config[3]['y']),                                # 第4层顶部
        (layers_config[3]['y'] - layers_config[3]['height'],  # 第4层底部
         phys_y_top),                                           # 物理层顶部
    ]

    for y_start, y_end in arrow_positions:
        ax.annotate('',
                   xy=(center_x, y_end),
                   xytext=(center_x, y_start),
                   arrowprops=dict(
                       arrowstyle='->',
                       lw=2.5,
                       color='#455a64'
                   ))

    # ========== 底部说明 ==========
    bottom_y = 4.6
    design_goal = (
        '核心目标：保证共识执行过程的正确性 · 可验证性 · 可追溯性'
    )
    ax.text(center_x, bottom_y, design_goal,
            fontsize=11, ha='center',
            color='#616161', style='italic',
            bbox=dict(
                boxstyle='round,pad=0.4',
                facecolor='#fafafa',
                edgecolor='#bdbdbd',
                linewidth=1
            ))

    plt.tight_layout(pad=0.8)
    return fig


if __name__ == '__main__':
    # 输出到脚本所在目录
    output_dir = os.path.dirname(os.path.abspath(__file__))

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 配置中文字体
    font_used = setup_chinese_font()
    print(f"使用字体: {font_used}")

    print("\n正在生成区块链数据存储架构图 v4...")

    # 生成优化后的图2
    fig = create_blockchain_storage_v4()
    output_path = os.path.join(output_dir, 'fig3_2_blockchain_data_storage.png')
    fig.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white',
                pad_inches=0.3)
    plt.close(fig)

    print(f"\n✅ 图片已成功生成！")
    print(f"   路径: {output_path}")
