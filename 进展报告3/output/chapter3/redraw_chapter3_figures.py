# -*- coding: utf-8 -*-
"""Redraw Chapter 3 storage figures with stable spacing and readable labels."""

from __future__ import annotations

import os
import platform

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch


OUT_DIR = os.path.dirname(os.path.abspath(__file__))


COLORS = {
    "blue": "#1e63b6",
    "blue_dark": "#0d3d87",
    "blue_fill": "#e8f3ff",
    "blue_fill_2": "#cfe6ff",
    "green": "#2e7d32",
    "green_dark": "#1b5e20",
    "green_fill": "#eaf6eb",
    "green_fill_2": "#cfebd0",
    "orange": "#e66a00",
    "orange_dark": "#bf4d00",
    "orange_fill": "#fff3df",
    "orange_fill_2": "#ffe0ad",
    "red": "#c62828",
    "red_dark": "#9f1d1d",
    "red_fill": "#fde8ec",
    "red_fill_2": "#f7c5cf",
    "purple": "#7b1fa2",
    "purple_dark": "#4a148c",
    "purple_fill": "#f3e5f5",
    "purple_fill_2": "#dfb7e6",
    "yellow": "#f9a825",
    "yellow_fill": "#fff8cf",
    "slate": "#546e7a",
    "slate_fill": "#edf2f5",
    "text": "#263238",
    "muted": "#66707a",
}


def setup_font():
    """Use a Chinese font available on the current host."""
    font_candidates = []
    if platform.system() == "Windows":
        font_candidates = [
            r"C:\Windows\Fonts\msyh.ttc",
            r"C:\Windows\Fonts\SourceHanSansCN-Regular.otf",
            r"C:\Windows\Fonts\NotoSansSC-VF.ttf",
            r"C:\Windows\Fonts\simhei.ttf",
        ]
    else:
        font_candidates = [
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        ]

    selected = None
    for path in font_candidates:
        if os.path.exists(path):
            fm.fontManager.addfont(path)
            selected = fm.FontProperties(fname=path).get_name()
            break

    if selected:
        plt.rcParams["font.sans-serif"] = [selected]
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["figure.dpi"] = 160


def add_box(ax, x, y, w, h, face, edge, lw=2.2, radius=0.08, alpha=1.0):
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle=f"round,pad=0.025,rounding_size={radius}",
        facecolor=face,
        edgecolor=edge,
        linewidth=lw,
        alpha=alpha,
    )
    ax.add_patch(patch)
    return patch


def label(
    ax,
    x,
    y,
    text,
    size=12,
    color=None,
    weight="normal",
    ha="center",
    va="center",
    linespacing=1.25,
    family=None,
):
    ax.text(
        x,
        y,
        text,
        fontsize=size,
        color=color or COLORS["text"],
        fontweight=weight,
        ha=ha,
        va=va,
        linespacing=linespacing,
        family=family,
    )


def arrow(ax, start, end, color, lw=2.2, scale=16, rad=0.0):
    ax.annotate(
        "",
        xy=end,
        xytext=start,
        arrowprops=dict(
            arrowstyle="-|>",
            color=color,
            lw=lw,
            mutation_scale=scale,
            shrinkA=0,
            shrinkB=0,
            connectionstyle=f"arc3,rad={rad}",
        ),
    )


def new_canvas():
    fig, ax = plt.subplots(figsize=(16, 9), dpi=200)
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 9)
    ax.axis("off")
    fig.patch.set_facecolor("white")
    return fig, ax


def add_note(ax, text):
    add_box(ax, 2.1, 0.18, 11.8, 0.42, "#fafafa", "#c7c7c7", lw=1.2, radius=0.06)
    label(ax, 8, 0.39, text, size=9.5, color=COLORS["muted"])


def draw_fig3_1():
    fig, ax = new_canvas()

    label(ax, 8, 8.55, "HCP-Bench 数据分层与流转", 22, COLORS["blue_dark"], "bold")

    add_box(ax, 0.75, 6.72, 14.5, 1.35, COLORS["blue_fill"], COLORS["blue"], lw=2.4)
    label(ax, 8, 7.82, "数据输入源", 12.5, COLORS["blue_dark"], "bold")

    sources = [
        ("HCP-Loadgen\n负载生成器", 1.15, 7.00, 3.0),
        ("HCP-Consensus\n共识引擎", 4.85, 7.00, 3.0),
        ("SystemMonitor\n系统监控", 8.55, 7.00, 3.0),
        ("HCP-Lab\n参数矩阵", 12.25, 7.00, 2.65),
    ]
    for text, x, y, w in sources:
        add_box(ax, x, y, w, 0.62, COLORS["blue_fill_2"], COLORS["blue"], lw=1.7)
        label(ax, x + w / 2, y + 0.31, text, 10.5, COLORS["blue_dark"], "bold")

    bus_y = 6.38
    for _, x, _, w in sources:
        cx = x + w / 2
        arrow(ax, (cx, 6.98), (cx, bus_y), COLORS["blue"], lw=1.6, scale=12)
    ax.plot([2.65, 13.58], [bus_y, bus_y], color=COLORS["blue"], lw=1.8)
    arrow(ax, (8, bus_y), (8, 6.18), COLORS["blue"], lw=1.8, scale=13)

    add_box(ax, 3.25, 5.30, 9.5, 0.88, COLORS["orange_fill"], COLORS["orange"], lw=2.4)
    label(ax, 8, 5.93, "分类决策层", 14.5, COLORS["orange_dark"], "bold")
    label(ax, 8, 5.58, "是否参与链上共识决策？", 10.8, "#9f3a00")

    add_box(ax, 0.82, 1.02, 6.75, 3.65, COLORS["green_fill"], COLORS["green"], lw=2.4)
    label(ax, 4.2, 4.28, "区块链数据", 16, COLORS["green_dark"], "bold")
    label(ax, 4.2, 3.92, "维护者：HCP-Consensus    存储：RocksDB + IAVL", 9.4, COLORS["green"])

    bc_tiles = [
        ("交易数据", 1.18, 3.08),
        ("区块数据", 3.32, 3.08),
        ("应用状态", 5.46, 3.08),
        ("验证者集合", 1.18, 2.06),
        ("信任评分", 3.32, 2.06),
        ("提交证明", 5.46, 2.06),
    ]
    for text, x, y in bc_tiles:
        add_box(ax, x, y, 1.68, 0.62, "#d9f0db", "#66bb6a", lw=1.3, radius=0.05)
        label(ax, x + 0.84, y + 0.31, text, 9.8, COLORS["green_dark"], "bold")
    add_box(ax, 1.32, 1.30, 5.75, 0.42, "#f5fbf5", "#81c784", lw=1.1, radius=0.05)
    label(ax, 4.2, 1.51, "+ 参与共识    + 影响状态转移    + 可验证可追溯", 8.8, COLORS["green"])

    add_box(ax, 8.43, 1.02, 6.75, 3.65, COLORS["red_fill"], COLORS["red"], lw=2.4)
    label(ax, 11.8, 4.28, "系统数据", 16, COLORS["red_dark"], "bold")
    label(ax, 11.8, 3.92, "维护者：HCP-Loadgen / HCP-Lab    存储：PostgreSQL + File", 9.4, COLORS["red"])

    sys_tiles = [
        ("实验配置", 8.78, 3.08),
        ("节点监控", 10.92, 3.08),
        ("性能指标", 13.06, 3.08),
        ("日志追踪", 8.78, 2.06),
        ("Schema 隔离", 10.92, 2.06),
        ("JSON / CSV", 13.06, 2.06),
    ]
    for text, x, y in sys_tiles:
        add_box(ax, x, y, 1.68, 0.62, "#f9d2da", "#ef5350", lw=1.3, radius=0.05)
        label(ax, x + 0.84, y + 0.31, text, 9.8, COLORS["red_dark"], "bold")
    add_box(ax, 8.93, 1.30, 5.75, 0.42, "#fff7f8", "#ef9a9a", lw=1.1, radius=0.05)
    label(ax, 11.8, 1.51, "- 不参与共识    + 实验可复现    + 性能分析完整", 8.8, COLORS["red"])

    arrow(ax, (7.1, 5.28), (4.2, 4.70), COLORS["green"], lw=2.4, scale=16, rad=0.02)
    label(ax, 5.45, 5.02, "是", 11, COLORS["green"], "bold")
    arrow(ax, (8.9, 5.28), (11.8, 4.70), COLORS["red"], lw=2.4, scale=16, rad=-0.02)
    label(ax, 10.55, 5.02, "否", 11, COLORS["red"], "bold")

    add_note(ax, "设计目标：降低实验系统与共识路径耦合 | 区块链数据保证一致性 | 系统数据支撑实验分析")

    fig.savefig(os.path.join(OUT_DIR, "fig3_1_data_classification_flow.png"), facecolor="white")
    plt.close(fig)


def draw_fig3_2():
    fig, ax = new_canvas()

    label(ax, 8, 8.55, "区块链数据存储架构", 22, COLORS["green_dark"], "bold")
    label(ax, 8, 8.16, "RocksDB + IAVL+Tree 四层存储栈", 12.5, COLORS["green"])

    add_box(ax, 0.75, 1.08, 3.0, 6.46, "#e6f6f4", "#00796b", lw=2.0)
    label(ax, 2.25, 7.20, "数据类型", 13.5, "#00564f", "bold")

    data_types = [
        ("交易数据", "订单 / 账户\n价格 / 数量\n时间戳"),
        ("区块数据", "高度 / 哈希\n交易列表\n提交证明"),
        ("应用状态", "账户余额\n订单状态\nKV 状态"),
        ("验证者集", "节点列表\n公钥地址\n投票权重"),
        ("信任评分", "评分值\n成功率\n100 轮窗口"),
    ]
    y = 6.28
    for title, body in data_types:
        add_box(ax, 1.03, y - 0.58, 2.44, 0.96, "#d8efed", "#00897b", lw=1.3, radius=0.05)
        label(ax, 2.25, y + 0.18, title, 10.2, "#00695c", "bold")
        label(ax, 2.25, y - 0.22, body, 7.6, "#00796b", linespacing=1.08)
        y -= 1.13

    label(ax, 8, 7.42, "共识执行到物理落盘", 12, COLORS["muted"], "bold")
    layers = [
        ("共识子系统", "tPBFT / HotStuff / Raft / Hierarchical", 6.50, COLORS["green_fill_2"], COLORS["green"], COLORS["green_dark"]),
        ("应用层（ABCI）", "BeginBlock -> DeliverTx -> EndBlock -> Commit", 5.22, "#dcedc8", "#558b2f", "#33691e"),
        ("IAVL+Tree 键值存储", "版本化 · Merkle 验证 · 快照回溯 · 缓存优化（781250）", 3.94, COLORS["yellow_fill"], COLORS["yellow"], "#ef7d00"),
        ("RocksDB 存储引擎", "WAL 预写日志 · MemTable 内存表 · SSTable 磁盘 · Compaction 压缩合并", 2.66, "#d5c5ef", "#5e35b1", "#311b92"),
    ]
    for title, body, cy, face, edge, text_color in layers:
        add_box(ax, 4.35, cy - 0.47, 7.30, 0.94, face, edge, lw=2.2)
        label(ax, 8, cy + 0.15, title, 12.8, text_color, "bold")
        label(ax, 8, cy - 0.20, body, 9.2, text_color)

    for y0, y1 in [(6.03, 5.69), (4.75, 4.41), (3.47, 3.13), (2.19, 1.82)]:
        arrow(ax, (8, y0), (8, y1), COLORS["slate"], lw=2.1, scale=14)

    add_box(ax, 5.15, 1.14, 5.70, 0.55, COLORS["slate_fill"], COLORS["slate"], lw=1.8, radius=0.05)
    label(ax, 8, 1.42, "物理磁盘：block_store.db | state.db | application.db | wal/", 9, "#37474f", "bold")

    add_box(ax, 12.25, 1.08, 3.0, 6.46, "#fff0e9", "#d84315", lw=2.0)
    label(ax, 13.75, 7.20, "关键配置", 13.5, "#bf360c", "bold")

    configs = [
        ("db_backend", "rocksdb"),
        ("StoreType", "IAVL"),
        ("iavl-cache-size", "781250"),
        ("discard_abci_responses", "false"),
        ("tx_indexer", "kv"),
    ]
    y = 6.28
    for key, value in configs:
        add_box(ax, 12.52, y - 0.55, 2.46, 0.86, "#fde4dc", "#d84315", lw=1.3, radius=0.05)
        label(ax, 13.75, y + 0.08, key, 9.2, "#bf360c", "bold", family="monospace")
        label(ax, 13.75, y - 0.28, f"= {value}", 9.0, "#d84315", family="monospace")
        y -= 1.13

    add_note(ax, "核心目标：保证共识执行过程的正确性、可验证性和可追溯性")

    fig.savefig(os.path.join(OUT_DIR, "fig3_2_blockchain_data_storage.png"), facecolor="white")
    plt.close(fig)


def draw_fig3_3():
    fig, ax = new_canvas()

    label(ax, 8, 8.55, "系统数据存储架构", 22, COLORS["red_dark"], "bold")
    label(ax, 8, 8.16, "PostgreSQL 结构化存储 + 文件系统结果存储", 12.5, COLORS["red"])

    add_box(ax, 0.9, 6.92, 14.2, 0.95, "#ffe1e5", COLORS["red"], lw=2.2)
    label(ax, 8, 7.64, "系统数据产生源", 12.2, COLORS["red_dark"], "bold")
    srcs = [
        ("HCP-Loadgen\n负载生成器", 1.35, 7.08, 3.25),
        ("HCP-Lab\n实验控制器", 6.38, 7.08, 3.25),
        ("SystemMonitor\n系统监控模块", 11.40, 7.08, 3.25),
    ]
    for text, x, y, w in srcs:
        add_box(ax, x, y, w, 0.48, "#f7b6bd", "#e53935", lw=1.5, radius=0.05)
        label(ax, x + w / 2, y + 0.24, text, 9.8, COLORS["red_dark"], "bold")

    add_box(ax, 0.80, 3.16, 6.75, 3.20, COLORS["blue_fill"], COLORS["blue"], lw=2.4)
    label(ax, 4.18, 6.02, "PostgreSQL 存储引擎", 15.2, COLORS["blue_dark"], "bold")
    label(ax, 4.18, 5.66, "HCP-Loadgen 负载数据", 10, COLORS["blue"])

    add_box(ax, 1.25, 5.00, 5.85, 0.46, COLORS["blue_fill_2"], COLORS["blue"], lw=1.5, radius=0.05)
    label(ax, 4.18, 5.23, "Schema 隔离：每个实验独立命名空间", 9.6, COLORS["blue_dark"], "bold")

    tables = [
        ("accounts", "账户信息表", 1.25, 4.26),
        ("balances", "余额快照表", 4.25, 4.26),
        ("orders", "订单记录表", 1.25, 3.62),
        ("trades", "交易记录表", 4.25, 3.62),
    ]
    for name, desc, x, y in tables:
        add_box(ax, x, y, 2.82, 0.50, "#b7dcff", COLORS["blue"], lw=1.4, radius=0.05)
        label(ax, x + 1.41, y + 0.31, name, 9.8, COLORS["blue_dark"], "bold")
        label(ax, x + 1.41, y + 0.12, desc, 8.1, COLORS["blue"])

    add_box(ax, 1.27, 3.20, 5.82, 0.30, "#f2f9ff", "#64b5f6", lw=1.0, radius=0.05)
    label(ax, 4.18, 3.35, "+ 连接池管理    + Binary Copy 批量写入    + UPSERT 幂等操作", 7.4, COLORS["blue_dark"])

    add_box(ax, 8.45, 3.16, 6.75, 3.20, COLORS["orange_fill"], COLORS["orange"], lw=2.4)
    label(ax, 11.82, 6.02, "文件系统存储", 15.2, COLORS["orange_dark"], "bold")
    label(ax, 11.82, 5.66, "HCP-Lab 实验结果", 10, COLORS["orange"])

    add_box(ax, 8.95, 3.66, 5.75, 1.78, COLORS["orange_fill_2"], "#fb8c00", lw=1.9)
    label(ax, 11.82, 5.20, "report/", 11.8, COLORS["orange_dark"], "bold", family="monospace")

    add_box(ax, 9.28, 4.05, 2.42, 0.82, "#ffd28a", "#fb8c00", lw=1.4, radius=0.05)
    label(ax, 10.49, 4.66, "exp{N}/", 10.4, COLORS["orange_dark"], "bold", family="monospace")
    add_box(ax, 9.55, 4.13, 1.88, 0.44, "#fff4d8", "#ffb300", lw=1.0, radius=0.04)
    label(ax, 10.49, 4.35, "nodes_{n}/\nresult.json · metrics.csv · logs/", 6.7, "#ef6c00", linespacing=1.05, family="monospace")

    add_box(ax, 11.95, 4.05, 2.42, 0.82, "#ffd28a", "#fb8c00", lw=1.4, radius=0.05)
    label(ax, 13.16, 4.66, "figures/", 10.4, COLORS["orange_dark"], "bold", family="monospace")
    add_box(ax, 12.25, 4.17, 1.82, 0.36, "#fff4d8", "#ffb300", lw=1.0, radius=0.04)
    label(ax, 13.16, 4.35, "*.png    *.svg", 7.7, "#ef6c00", family="monospace")

    add_box(ax, 9.25, 3.42, 5.15, 0.34, "#fff9ec", "#ffb74d", lw=1.0, radius=0.04)
    label(ax, 11.82, 3.59, "输出格式：JSON 性能指标 + CSV 详细数据 + PNG/SVG 图表", 8.4, COLORS["orange_dark"])

    arrow(ax, (2.98, 6.92), (4.18, 6.38), COLORS["blue"], lw=2.2, scale=15)
    arrow(ax, (8.0, 6.92), (11.82, 6.38), COLORS["orange"], lw=2.2, scale=15)
    arrow(ax, (13.02, 6.92), (11.82, 6.38), COLORS["orange"], lw=2.2, scale=15)

    add_box(ax, 0.8, 0.88, 14.4, 1.82, COLORS["purple_fill"], COLORS["purple"], lw=2.2)
    label(ax, 8, 2.48, "系统数据四大类型", 12.8, COLORS["purple_dark"], "bold")
    type_cards = [
        ("实验配置", "算法类型\n节点规模\n交易数量\n负载模式\n重复次数", 1.15),
        ("节点运行", "CPU 利用率\n内存占用\n网络吞吐\n磁盘 I/O\n在线状态", 4.90),
        ("性能指标", "TPS 吞吐量\nP50/P95/P99 延迟\n交易成功率\n超时率\n带宽开销", 8.65),
        ("日志追踪", "区块提交日志\n交易确认日志\n共识阶段切换\n错误/超时日志\n节点启停记录", 12.40),
    ]
    for title, body, x in type_cards:
        add_box(ax, x, 1.06, 2.95, 1.22, COLORS["purple_fill_2"], "#9c27b0", lw=1.4, radius=0.05)
        label(ax, x + 1.475, 2.02, title, 9.8, COLORS["purple_dark"], "bold")
        label(ax, x + 1.475, 1.54, body, 7.0, COLORS["purple"], linespacing=1.04)

    add_note(ax, "设计目标：不干扰链上共识过程 | 完整记录实验环境、负载输入、系统状态和性能输出 | 保证结果可追溯、可解释")

    fig.savefig(os.path.join(OUT_DIR, "fig3_3_system_data_storage.png"), facecolor="white")
    plt.close(fig)


def main():
    setup_font()
    draw_fig3_1()
    draw_fig3_2()
    draw_fig3_3()
    print("redrew chapter 3 figures")


if __name__ == "__main__":
    main()
