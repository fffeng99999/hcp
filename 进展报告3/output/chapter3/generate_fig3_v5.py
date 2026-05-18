# -*- coding: utf-8 -*-
"""
HCP-Bench 系统数据存储架构图 v5
修复：文件系统改为嵌套容器图 + 全局文字放大
"""

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.patches import FancyBboxPatch, Rectangle, Ellipse, Circle
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


def create_system_storage_v5():
    """图3: 系统数据存储架构（优化版）"""

    # 画布设置 - 稍微加高以容纳嵌套容器
    fig, ax = plt.subplots(1, 1, figsize=(18, 15))
    ax.set_xlim(0, 18)
    ax.set_ylim(0, 15)
    ax.axis('off')
    fig.patch.set_facecolor('white')

    # ========== 标题区 (y=14-14.8) ==========
    ax.text(9, 14.6, '系统数据存储架构',
            fontsize=21, fontweight='bold', ha='center', color='#b71c1c')
    ax.text(9, 14.05, 'PostgreSQL 结构化存储 + 文件系统结果存储',
            fontsize=13, ha='center', color='#d32f2f')

    # ========== 布局参数 ==========
    center_x = 9

    # 左侧 PostgreSQL 区域：x ∈ [0.5, 8]，宽度7.5，中心 x=4.25
    pg_left = 0.5
    pg_right = 8.0
    pg_center = 4.25

    # 右侧文件系统区域：x ∈ [10, 17.5]，宽度7.5，中心 x=13.75
    fs_left = 10.0
    fs_right = 17.5
    fs_center = 13.75

    # ========== 第一层：数据源 (y=12.4-13.3) ==========
    source_y = 12.85
    source_box = FancyBboxPatch(
        (1, source_y - 0.55), 16, 1.1,
        boxstyle="round,pad=0.05",
        facecolor='#ffcdd2', edgecolor='#c62828',
        linewidth=2.5
    )
    ax.add_patch(source_box)

    ax.text(center_x, source_y + 0.28, '系统数据产生源',
            fontsize=14, fontweight='bold', ha='center', color='#b71c1c')

    sources = [
        ('HCP-Loadgen\n负载生成器', 3.5),
        ('HCP-Lab\n实验控制器', 9),
        ('SystemMonitor\n系统监控模块', 14.5)
    ]

    for label, x in sources:
        box = FancyBboxPatch(
            (x - 1.8, source_y - 0.35), 3.6, 0.75,
            boxstyle="round,pad=0.03",
            facecolor='#ef9a9a', edgecolor='#e53935',
            linewidth=1.8
        )
        ax.add_patch(box)
        ax.text(x, source_y, label, fontsize=11, ha='center', va='center',
                color='#b71c1c', fontweight='bold', linespacing=1.25)

    # ========== 第二层左：PostgreSQL 存储引擎 (y=6.2-11.6) ==========
    pg_top = 11.4
    pg_height = 5.0

    pg_main_box = FancyBboxPatch(
        (pg_left, pg_top - pg_height),
        pg_right - pg_left, pg_height,
        boxstyle="round,pad=0.08",
        facecolor='#e3f2fd', edgecolor='#1565c0',
        linewidth=3
    )
    ax.add_patch(pg_main_box)

    # PostgreSQL 标题
    ax.text(pg_center, pg_top - 0.45, 'PostgreSQL 存储引擎',
            fontsize=16, fontweight='bold', ha='center', color='#0d47a1')
    ax.text(pg_center, pg_top - 0.95, '(HCP-Loadgen 负载数据)',
            fontsize=12, ha='center', color='#1976d2')

    # Schema 隔离机制框
    schema_y = pg_top - 1.55
    schema_box = FancyBboxPatch(
        (pg_left + 0.6, schema_y - 0.55),
        (pg_right - pg_left) - 1.2, 1.1,
        boxstyle="round,pad=0.04",
        facecolor='#bbdefb', edgecolor='#1976d2',
        linewidth=2
    )
    ax.add_patch(schema_box)
    ax.text(pg_center, schema_y, 'Schema 隔离机制 · 每个实验独立命名空间',
            fontsize=12, fontweight='bold', ha='center', color='#0d47a1')

    # 四张表结构（2×2 网格，放大版）
    tables = [
        {'name': 'accounts', 'desc': '账户信息表', 'x': 2.3, 'y': pg_top - 2.95},
        {'name': 'balances', 'desc': '余额快照表', 'x': 6.2, 'y': pg_top - 2.95},
        {'name': 'orders', 'desc': '订单记录表', 'x': 2.3, 'y': pg_top - 4.35},
        {'name': 'trades', 'desc': '交易记录表', 'x': 6.2, 'y': pg_top - 4.35},
    ]

    for table in tables:
        # 表框体（放大）
        table_box = FancyBboxPatch(
            (table['x'] - 1.5, table['y'] - 0.65),
            3.0, 1.3,
            boxstyle="round,pad=0.03",
            facecolor='#90caf9', edgecolor='#1976d2',
            linewidth=2
        )
        ax.add_patch(table_box)

        # 表名（放大加粗）
        ax.text(table['x'], table['y'] + 0.28,
                table['name'],
                fontsize=13, fontweight='bold',
                ha='center', color='#0d47a1')

        # 表描述（放大）
        ax.text(table['x'], table['y'] - 0.22,
                table['desc'],
                fontsize=11, ha='center', color='#1565c0')

    # 技术特点标签
    tech_y = pg_top - pg_height + 0.75
    tech_text = '[+] 连接池管理  [+] Binary Copy批量写入  [+] UPSERT幂等操作'
    ax.text(pg_center, tech_y, tech_text, fontsize=11, ha='center', color='#0d47a1',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#e1f5fe',
                     edgecolor='#64b5f6', linewidth=1.5))

    # ========== 第二层右：文件系统存储 (y=6.2-11.6) ==========
    fs_top = 11.4
    fs_height = 5.0

    fs_main_box = FancyBboxPatch(
        (fs_left, fs_top - fs_height),
        fs_right - fs_left, fs_height,
        boxstyle="round,pad=0.08",
        facecolor='#fff3e0', edgecolor='#e65100',
        linewidth=3
    )
    ax.add_patch(fs_main_box)

    # 文件系统标题
    ax.text(fs_center, fs_top - 0.45, '文件系统存储',
            fontsize=16, fontweight='bold', ha='center', color='#e65100')
    ax.text(fs_center, fs_top - 0.95, '(HCP-Lab 实验结果)',
            fontsize=12, ha='center', color='#ef6c00')

    # ===== 嵌套容器图：目录结构 =====
    # 最外层：report/ 目录
    report_x = fs_center
    report_y = fs_top - 2.8
    report_w = 6.2
    report_h = 3.4

    report_box = FancyBboxPatch(
        (report_x - report_w/2, report_y - report_h/2),
        report_w, report_h,
        boxstyle="round,pad=0.06",
        facecolor='#ffe0b2', edgecolor='#ff9800',
        linewidth=2.5
    )
    ax.add_patch(report_box)

    # report/ 标签
    ax.text(report_x, report_y + report_h/2 - 0.3,
            '📁 report/',
            fontsize=14, fontweight='bold',
            ha='center', color='#e65100')

    # 第二层：exp{N}_{算法}/ 实验目录（左右两个子文件夹）
    exp_w = 2.7
    exp_h = 2.3
    exp_spacing = 0.4
    exp_y = report_y - 0.15

    # 左侧实验目录
    exp1_x = report_x - exp_w/2 - exp_spacing/2
    exp1_box = FancyBboxPatch(
        (exp1_x - exp_w/2, exp_y - exp_h/2),
        exp_w, exp_h,
        boxstyle="round,pad=0.04",
        facecolor='#ffcc80', edgecolor='#ffa726',
        linewidth=2
    )
    ax.add_patch(exp1_box)
    ax.text(exp1_x, exp_y + exp_h/2 - 0.25,
            '📁 exp{N}',
            fontsize=12, fontweight='bold',
            ha='center', color='#ef6c00')

    # 右侧图表目录
    fig_dir_x = report_x + exp_w/2 + exp_spacing/2
    fig_dir_box = FancyBboxPatch(
        (fig_dir_x - exp_w/2, exp_y - exp_h/2),
        exp_w, exp_h,
        boxstyle="round,pad=0.04",
        facecolor='#ffcc80', edgecolor='#ffa726',
        linewidth=2
    )
    ax.add_patch(fig_dir_box)
    ax.text(fig_dir_x, exp_y + exp_h/2 - 0.25,
            '📁 figures/',
            fontsize=12, fontweight='bold',
            ha='center', color='#ef6c00')

    # 第三层：nodes_{节点数}/ 子目录（在左侧实验目录内）
    nodes_w = 2.1
    nodes_h = 1.4
    nodes_x = exp1_x
    nodes_y = exp_y - 0.35

    nodes_box = FancyBboxPatch(
        (nodes_x - nodes_w/2, nodes_y - nodes_h/2),
        nodes_w, nodes_h,
        boxstyle="round,pad=0.03",
        facecolor='#ffb74d', edgecolor='#ff9800',
        linewidth=1.8
    )
    ax.add_patch(nodes_box)
    ax.text(nodes_x, nodes_y + nodes_h/2 - 0.18,
            '📁 nodes_{n}',
            fontsize=11, fontweight='bold',
            ha='center', color='#e65100')

    # 第四层：具体文件（在 nodes 目录内）- 用小方块表示
    file_items = [
        {'icon': '📄', 'name': 'result.json', 'x_offset': -0.55},
        {'icon': '📊', 'name': 'metrics.csv', 'x_offset': 0},
        {'icon': '📋', 'name': 'logs/', 'x_offset': 0.55},
    ]

    file_y = nodes_y - 0.4
    for item in file_items:
        file_x = nodes_x + item['x_offset']
        file_box = FancyBboxPatch(
            (file_x - 0.42, file_y - 0.28),
            0.84, 0.56,
            boxstyle="round,pad=0.02",
            facecolor='#fff8e1', edgecolor='#ffc107',
            linewidth=1.2
        )
        ax.add_patch(file_box)
        ax.text(file_x, file_y,
                f"{item['icon']} {item['name']}",
                fontsize=7.5, ha='center', va='center',
                color='#f57f17', family='monospace')

    # 第五层：figures/ 内的文件（在右侧图表目录内）
    fig_files = [
        {'icon': '🖼️', 'name': '*.png'},
        {'icon': '📈', 'name': '*.svg'},
    ]
    fig_file_y = exp_y - 0.35

    for i, item in enumerate(fig_files):
        ff_x = fig_dir_x + (i - 0.5) * 0.9
        ff_box = FancyBboxPatch(
            (ff_x - 0.42, fig_file_y - 0.28),
            0.84, 0.56,
            boxstyle="round,pad=0.02",
            facecolor='#fff8e1', edgecolor='#ffc107',
            linewidth=1.2
        )
        ax.add_patch(ff_box)
        ax.text(ff_x, fig_file_y,
                f"{item['icon']} {item['name']}",
                fontsize=7.5, ha='center', va='center',
                color='#f57f17', family='monospace')

    # 输出格式说明
    format_y = fs_top - fs_height + 0.75
    format_text = '输出格式: JSON性能指标 + CSV详细数据 + PNG/SVG图表'
    ax.text(fs_center, format_y, format_text, fontsize=11, ha='center',
            color='#e65100',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#fff3e0',
                     edgecolor='#ffb74d', linewidth=1.5))

    # ========== 连接箭头：数据源到两个存储引擎 ==========
    arrow_source_y = source_y - 0.55
    arrow_target_y = pg_top

    # 到 PostgreSQL
    ax.annotate('',
               xy=(pg_center, arrow_target_y),
               xytext=(3.5, arrow_source_y),
               arrowprops=dict(arrowstyle='->', lw=2.8, color='#1565c0'))

    # 到文件系统（两条线）
    ax.annotate('',
               xy=(fs_center, arrow_target_y),
               xytext=(9, arrow_source_y),
               arrowprops=dict(arrowstyle='->', lw=2.8, color='#e65100'))
    ax.annotate('',
               xy=(fs_center, arrow_target_y),
               xytext=(14.5, arrow_source_y),
               arrowprops=dict(arrowstyle='->', lw=2.8, color='#e65100'))

    # ========== 第三层底部：四大数据类型详解 (y=1.2-4.6) ==========
    types_top = 4.3
    types_height = 2.9

    types_box = FancyBboxPatch(
        (0.5, types_top - types_height),
        17, types_height,
        boxstyle="round,pad=0.06",
        facecolor='#f3e5f5', edgecolor='#7b1fa2',
        linewidth=2.5
    )
    ax.add_patch(types_box)

    ax.text(center_x, types_top - 0.4, '系统数据四大类型',
            fontsize=15, fontweight='bold', ha='center', color='#4a148c')

    # 四大数据类型卡片（放大版）
    sys_types = [
        {
            'title': '实验配置',
            'content': '算法类型\n节点规模\n交易数量\n负载模式\n重复次数',
            'x': 2.75
        },
        {
            'title': '节点运行',
            'content': 'CPU利用率\n内存占用\n网络吞吐\n磁盘I/O\n在线状态',
            'x': 6.95
        },
        {
            'title': '性能指标',
            'content': 'TPS吞吐量\nP50/P95/P99延迟\n交易成功率\n超时率\n带宽开销',
            'x': 11.15
        },
        {
            'title': '日志追踪',
            'content': '区块提交日志\n交易确认日志\n共识阶段切换\n错误/超时日志\n节点启停记录',
            'x': 15.35
        }
    ]

    card_width = 3.6
    card_height = 2.0
    card_y = types_top - 1.75

    for stype in sys_types:
        # 卡片框（放大）
        card_box = FancyBboxPatch(
            (stype['x'] - card_width/2, card_y - card_height/2),
            card_width, card_height,
            boxstyle="round,pad=0.04",
            facecolor='#e1bee7', edgecolor='#9c27b0',
            linewidth=2
        )
        ax.add_patch(card_box)

        # 类型标题（放大加粗）
        ax.text(stype['x'], card_y + card_height/2 - 0.3,
                stype['title'],
                fontsize=13, fontweight='bold',
                ha='center', color='#6a1b9a')

        # 内容列表（放大）
        ax.text(stype['x'], card_y - 0.15,
                stype['content'],
                fontsize=10, ha='center', va='center',
                color='#7b1fa2', linespacing=1.35)

    # ========== 底部说明 (y=0.4-1) ==========
    bottom_y = 0.7
    design_goal = (
        '设计目标：不干扰链上共识过程 | '
        '完整记录实验环境、负载输入、系统状态和性能输出 | '
        '保证实验结果可追溯性和可解释性'
    )
    ax.text(center_x, bottom_y, design_goal,
            fontsize=11, ha='center', color='#616161', style='italic',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#fafafa',
                     edgecolor='#bdbdbd', linewidth=1))

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

    print("\n正在生成系统数据存储架构图 v5...")

    # 生成优化后的图3
    fig = create_system_storage_v5()
    output_path = os.path.join(output_dir, 'fig3_3_system_data_storage.png')
    fig.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white',
                pad_inches=0.3)
    plt.close(fig)

    print(f"\n✅ 图片已成功生成！")
    print(f"   路径: {output_path}")
