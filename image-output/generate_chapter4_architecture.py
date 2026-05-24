#!/usr/bin/env python3
"""Generate corrected Chapter 4 architecture figures.

The figures describe the current HCP-Bench implementation:
HCP-Lab orchestrates experiments, HCP-Loadgen generates SDK transaction bytes
and persists load records, HCP-Consensus engine nodes order/commit blocks, and
the SDK execution adapter writes node data after state commit.
"""
from __future__ import annotations

import math
import shutil
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont


OUT_DIR = Path(__file__).resolve().parent / "chapter4"

W, H = 1800, 1180
BG = "#FFFFFF"
TEXT = "#17324D"
MUTED = "#5E7182"
BLUE = "#2F6FAB"
BLUE_L = "#EAF3FF"
GREEN = "#3E8E5A"
GREEN_L = "#EAF7EF"
ORANGE = "#D88422"
ORANGE_L = "#FFF4E4"
PURPLE = "#7D5FB2"
PURPLE_L = "#F3EEFF"
RED = "#C65353"
RED_L = "#FFF0F0"
GRAY = "#7A8792"
GRAY_L = "#F4F6F8"
TEAL = "#2E8C99"
TEAL_L = "#EAF8FA"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/simsun.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if path and Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


F_TITLE = font(42, True)
F_SUB = font(23)
F_H = font(25, True)
F_B = font(21)
F_S = font(18)
F_XS = font(15)


def new_canvas(title: str, subtitle: str = "") -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.text((W / 2, 44), title, fill=TEXT, font=F_TITLE, anchor="mm")
    if subtitle:
        d.text((W / 2, 92), subtitle, fill=MUTED, font=F_SUB, anchor="mm")
    return img, d


def text_size(d: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont) -> tuple[int, int]:
    box = d.textbbox((0, 0), text, font=fnt)
    return box[2] - box[0], box[3] - box[1]


def wrap_text(d: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    lines: list[str] = []
    for raw in text.split("\n"):
        current = ""
        for ch in raw:
            trial = current + ch
            if text_size(d, trial, fnt)[0] <= max_w or not current:
                current = trial
            else:
                lines.append(current)
                current = ch
        if current:
            lines.append(current)
    return lines or [""]


def rounded(d: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill: str, outline: str, width: int = 3, r: int = 24) -> None:
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


def label_box(
    d: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    title: str,
    lines: Iterable[str] = (),
    fill: str = GRAY_L,
    outline: str = GRAY,
    title_color: str | None = None,
    align: str = "center",
) -> None:
    x1, y1, x2, y2 = box
    rounded(d, box, fill, outline)
    title_color = title_color or outline
    title_lines = wrap_text(d, title, F_H, x2 - x1 - 40)
    body_lines: list[str] = []
    for line in lines:
        body_lines.extend(wrap_text(d, line, F_S, x2 - x1 - 44))
    total_h = len(title_lines) * 34 + (10 if body_lines else 0) + len(body_lines) * 25
    y = y1 + max(22, ((y2 - y1) - total_h) // 2)
    anchor = "ma" if align == "center" else "la"
    tx = (x1 + x2) // 2 if align == "center" else x1 + 24
    for line in title_lines:
        d.text((tx, y), line, fill=title_color, font=F_H, anchor=anchor)
        y += 34
    y += 8
    for line in body_lines:
        d.text((tx, y), line, fill=TEXT, font=F_S, anchor=anchor)
        y += 25


def chip(d: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, color: str, fill: str) -> tuple[int, int, int, int]:
    x, y = xy
    tw, th = text_size(d, text, F_S)
    box = (x, y, x + tw + 32, y + th + 20)
    rounded(d, box, fill, color, width=2, r=18)
    d.text((x + 16, y + 10), text, fill=color, font=F_S, anchor="la")
    return box


def arrow(d: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int], color: str = BLUE, width: int = 5) -> None:
    d.line([start, end], fill=color, width=width)
    sx, sy = start
    ex, ey = end
    ang = math.atan2(ey - sy, ex - sx)
    length = 18
    spread = 0.45
    p1 = (ex - length * math.cos(ang - spread), ey - length * math.sin(ang - spread))
    p2 = (ex - length * math.cos(ang + spread), ey - length * math.sin(ang + spread))
    d.polygon([end, p1, p2], fill=color)


def section(d: ImageDraw.ImageDraw, box: tuple[int, int, int, int], title: str, fill: str, outline: str) -> None:
    rounded(d, box, fill, outline, width=3, r=26)
    d.text(((box[0] + box[2]) // 2, box[1] + 34), title, fill=outline, font=F_H, anchor="mm")


def mini_box(
    d: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    title: str,
    body: str,
    fill: str,
    outline: str,
) -> None:
    x1, y1, x2, y2 = box
    rounded(d, box, fill, outline, width=2, r=18)
    d.text(((x1 + x2) // 2, y1 + 27), title, fill=outline, font=F_B, anchor="mm")
    y = y1 + 55
    for line in wrap_text(d, body, F_XS, x2 - x1 - 28):
        d.text(((x1 + x2) // 2, y), line, fill=TEXT, font=F_XS, anchor="ma")
        y += 21


def save(img: Image.Image, name: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    img.save(OUT_DIR / name, quality=95)
    print(f"created {OUT_DIR / name}")


def fig1() -> None:
    img, d = new_canvas("HCP-Bench总体架构", "三子系统协同：负载生成、共识执行、实验编排")
    section(d, (55, 145, 535, 955), "负载生成子系统", GREEN_L, GREEN)
    section(d, (660, 145, 1140, 955), "共识执行子系统", BLUE_L, BLUE)
    section(d, (1265, 145, 1745, 955), "实验编排与分析子系统", PURPLE_L, PURPLE)
    for y, t, l in [
        (260, "交易构造", ["生成SDK交易字节", "约250字节负载"]),
        (430, "账户选择", ["均匀模式", "热点模式"]),
        (600, "发送调度", ["固定速率", "持续/突发/抖动"]),
        (770, "结果持久化", ["PostgreSQL按实验隔离"]),
    ]:
        label_box(d, (105, y, 485, y + 118), t, l, "#FFFFFF", GREEN)
    for y, t, l in [
        (250, "本地多节点引擎集群", ["PBFT、HotStuff、Raft", "CometBFT-light、tPBFT"]),
        (440, "内存网络与消息统计", ["统一延迟与带宽参数", "记录消息数和字节数"]),
        (630, "SDK执行适配层", ["提交后执行交易", "写入应用状态"]),
        (790, "官方CometBFT对照", ["独立多进程节点", "用于工程基线比较"]),
    ]:
        label_box(d, (710, y, 1090, y + 124), t, l, "#FFFFFF", BLUE)
    for y, t, l in [
        (260, "实验矩阵", ["算法、节点规模", "负载模式、重复次数"]),
        (430, "运行调度", ["启动节点与负载", "清理中间数据"]),
        (600, "指标计算", ["TPS、P50、P95、P99", "成功率、消息开销"]),
        (770, "报告输出", ["表格、图形、汇总文件"]),
    ]:
        label_box(d, (1315, y, 1695, y + 118), t, l, "#FFFFFF", PURPLE)
    arrow(d, (520, 540), (675, 540))
    arrow(d, (1125, 540), (1280, 540))
    chip(d, (170, 985), "统一硬件", BLUE, BLUE_L)
    chip(d, (410, 985), "统一负载入口", GREEN, GREEN_L)
    chip(d, (700, 985), "统一节点规模", ORANGE, ORANGE_L)
    chip(d, (990, 985), "统一统计口径", PURPLE, PURPLE_L)
    chip(d, (1280, 985), "中间与最终数据分离", RED, RED_L)
    label_box(d, (180, 1050, 1620, 1135), "核心原则", ["所有算法共享同一编排、负载、统计和报告链路；官方CometBFT作为独立工程基线，对照自研轻量实现"], "#FAFBFC", GRAY)
    save(img, "fig4_1_hcp_bench_overall_architecture.png")


def fig2() -> None:
    img, d = new_canvas("单轮实验数据流", "从实验配置到指标汇总的端到端流程")
    boxes = [
        ("实验配置", "读取矩阵\n确定算法与节点规模", ORANGE, ORANGE_L),
        ("负载生成", "生成SDK交易字节\n写入负载记录", GREEN, GREEN_L),
        ("交易入口", "HTTP或gRPC提交\n接收交易字节", TEAL, TEAL_L),
        ("共识排序", "引擎打包区块\n完成共识提交", BLUE, BLUE_L),
        ("状态执行", "SDK应用层执行\n写入节点数据", PURPLE, PURPLE_L),
        ("指标汇总", "计算TPS与分位延迟\n生成表格和图片", RED, RED_L),
    ]
    x0, y0, bw, bh, gap = 75, 205, 250, 170, 40
    for i, (title, body, color, fill) in enumerate(boxes):
        x = x0 + i * (bw + gap)
        label_box(d, (x, y0, x + bw, y0 + bh), f"{i+1}. {title}", body.split("\n"), fill, color)
        if i < len(boxes) - 1:
            arrow(d, (x + bw, y0 + bh // 2), (x + bw + gap - 10, y0 + bh // 2), color=GRAY)
    label_box(d, (120, 485, 540, 650), "负载侧数据", ["账户、余额、订单/交易记录", "每轮实验使用独立数据库命名空间"], "#FFFFFF", GREEN)
    label_box(d, (690, 485, 1110, 650), "链上侧数据", ["节点目录、区块摘要、交易执行结果", "应用状态哈希与最新高度"], "#FFFFFF", BLUE)
    label_box(d, (1260, 485, 1680, 650), "分析侧数据", ["原始结果、负载日志、统计表格", "实验总表与论文图片"], "#FFFFFF", PURPLE)
    for x, color in [(330, GREEN), (900, BLUE), (1470, PURPLE)]:
        arrow(d, (x, 650), (x, 735), color)
    mini_box(d, (120, 745, 375, 850), "发送侧时间戳", "交易发出与响应时间，用于校验负载侧观测", "#FFFFFF", GREEN)
    mini_box(d, (405, 745, 660, 850), "数据库记录", "交易记录、账户状态与实验隔离信息", "#FFFFFF", GREEN)
    mini_box(d, (690, 745, 945, 850), "提交窗口", "首笔真实提交到最后一笔真实提交", "#FFFFFF", BLUE)
    mini_box(d, (975, 745, 1230, 850), "分位延迟", "按真实交易确认延迟计算P50/P95/P99", "#FFFFFF", BLUE)
    mini_box(d, (1260, 745, 1515, 850), "结果表格", "每个实验输出论文对应表格", "#FFFFFF", PURPLE)
    mini_box(d, (1545, 745, 1680, 850), "图形", "统一风格图片", "#FFFFFF", PURPLE)
    label_box(d, (180, 960, 1620, 1070), "闭环说明", ["当前实现采用实验矩阵顺序运行：结果进入报告与汇总文件，用于后续分析和人工调整，不在单轮运行中自动改变负载"], GRAY_L, GRAY)
    save(img, "fig4_2_experiment_data_flow.png")


def fig3() -> None:
    img, d = new_canvas("共识执行子系统结构", "自研共识引擎驱动SDK执行层，官方CometBFT作为独立对照")
    section(d, (85, 150, 600, 1020), "负载入口", GREEN_L, GREEN)
    label_box(d, (150, 300, 540, 435), "交易提交接口", ["接收负载生成器发送的SDK交易字节"], "#FFFFFF", GREEN)
    label_box(d, (150, 510, 540, 645), "交易池", ["缓存待排序交易", "供领导节点打包"], "#FFFFFF", GREEN)
    label_box(d, (150, 720, 540, 855), "状态查询接口", ["返回提交数量、延迟分位", "返回网络消息统计"], "#FFFFFF", GREEN)
    section(d, (650, 150, 1210, 1020), "自研共识本地集群", BLUE_L, BLUE)
    label_box(d, (705, 280, 1155, 410), "内存网络", ["模拟低延迟局域网", "统计广播消息与字节"], "#FFFFFF", BLUE)
    for i, y in enumerate([470, 650, 830]):
        label_box(d, (710, y, 940, y + 120), f"节点{i}", ["共识引擎", "交易池"], "#FFFFFF", BLUE)
        label_box(d, (970, y, 1150, y + 120), "执行适配", ["状态提交", "数据落盘"], "#FFFFFF", TEAL)
        arrow(d, (940, y + 60), (970, y + 60), TEAL)
    mini_box(d, (705, 965, 1155, 1015), "扩展能力", "节点数量按实验矩阵扩展，保持同一网络参数", "#FFFFFF", BLUE)
    section(d, (1260, 150, 1715, 1020), "执行与对照", PURPLE_L, PURPLE)
    label_box(d, (1315, 280, 1655, 430), "SDK应用执行层", ["执行交易", "更新应用状态", "生成应用哈希"], "#FFFFFF", PURPLE)
    label_box(d, (1315, 500, 1655, 650), "节点数据", ["区块摘要", "交易结果", "最新高度与状态哈希"], "#FFFFFF", PURPLE)
    label_box(d, (1315, 760, 1655, 930), "官方CometBFT路径", ["多进程节点单独运行", "仅用于与轻量实现对比"], "#FFFFFF", ORANGE)
    arrow(d, (600, 555), (650, 555), GREEN)
    arrow(d, (1210, 555), (1260, 555), BLUE)
    save(img, "fig4_3_consensus_execution_subsystem.png")


def fig4() -> None:
    img, d = new_canvas("共识引擎选择与执行路径", "同一负载入口下切换算法，保持统一测量口径")
    label_box(d, (110, 190, 420, 340), "实验配置", ["选择算法A", "设置节点规模N与负载λ"], ORANGE_L, ORANGE)
    label_box(d, (560, 190, 1240, 340), "统一负载入口", ["交易字节进入共识子系统，所有算法使用相同提交口径"], TEAL_L, TEAL)
    label_box(d, (1380, 190, 1690, 340), "指标输出", ["TPS、P50、P95、P99", "成功率、消息开销"], PURPLE_L, PURPLE)
    arrow(d, (420, 265), (560, 265), GRAY)
    arrow(d, (1240, 265), (1380, 265), GRAY)
    label_box(d, (140, 435, 790, 635), "自研共识算法组", ["PBFT、HotStuff、Raft、CometBFT-light", "tPBFT、分层tPBFT、轻量子层"], "#FFFFFF", BLUE)
    label_box(d, (1010, 435, 1660, 635), "官方CometBFT对照组", ["使用官方网络、内存池、区块提议、投票与节点数据", "用于工程基线比较"], "#FFFFFF", ORANGE)
    arrow(d, (900, 340), (465, 435), BLUE)
    arrow(d, (900, 340), (1335, 435), ORANGE)
    stages = [
        ("交易池", "缓存交易"),
        ("领导节点出块", "形成区块"),
        ("共识提交", "多数确认"),
        ("SDK执行", "状态提交"),
        ("节点数据", "高度与哈希"),
    ]
    x, y = 180, 760
    for i, (title, body) in enumerate(stages):
        label_box(d, (x + i * 320, y, x + i * 320 + 240, y + 120), title, [body], BLUE_L if i < 3 else PURPLE_L, BLUE if i < 3 else PURPLE)
        if i < len(stages) - 1:
            arrow(d, (x + i * 320 + 240, y + 60), (x + i * 320 + 315, y + 60), GRAY)
    label_box(d, (250, 1020, 1550, 1120), "说明", ["算法切换发生在自研共识实验入口；官方CometBFT不与轻量实现混跑，而是单独作为对照实验"], GRAY_L, GRAY)
    save(img, "fig4_4_engine_selection_and_execution_path.png")


def fig5() -> None:
    img, d = new_canvas("负载生成子系统结构", "生成SDK交易字节，记录负载侧过程数据")
    label_box(d, (730, 165, 1070, 280), "实验参数", ["交易总量、发送节奏、账户分布、数据库命名空间"], ORANGE_L, ORANGE)
    section(d, (90, 330, 1710, 1040), "HCP-Loadgen", GREEN_L, GREEN)
    label_box(d, (155, 440, 500, 590), "账户池", ["均匀选择", "热点选择", "本地维护序号"], "#FFFFFF", GREEN)
    label_box(d, (560, 440, 905, 590), "调度器", ["固定速率", "持续、突发、抖动", "交易总量控制"], "#FFFFFF", GREEN)
    label_box(d, (965, 440, 1310, 590), "工作线程", ["构造交易", "签名与编码", "本地缓冲"], "#FFFFFF", GREEN)
    label_box(d, (1370, 440, 1645, 590), "广播器", ["HTTP提交", "gRPC提交", "响应计时"], "#FFFFFF", GREEN)
    arrow(d, (500, 540), (570, 540), GRAY)
    arrow(d, (900, 540), (970, 540), GRAY)
    arrow(d, (1300, 540), (1370, 540), GRAY)
    mini_box(d, (180, 705, 450, 825), "交易内容", "账户、方向、数量、随机负载与发送时间", "#FFFFFF", GREEN)
    mini_box(d, (490, 705, 760, 825), "交易字节", "默认生成SDK可执行交易字节", "#FFFFFF", TEAL)
    mini_box(d, (1040, 705, 1310, 825), "负载记录", "交易哈希、账户、延迟与时间戳", "#FFFFFF", ORANGE)
    mini_box(d, (1350, 705, 1620, 825), "数据库写入", "批量写入并按实验隔离", "#FFFFFF", ORANGE)
    label_box(d, (300, 900, 780, 995), "热路径", ["交易字节直接发送到共识入口"], "#FFFFFF", TEAL)
    label_box(d, (1020, 900, 1500, 995), "冷路径", ["负载侧记录异步持久化"], "#FFFFFF", ORANGE)
    arrow(d, (1490, 590), (1490, 705), ORANGE)
    arrow(d, (1100, 590), (625, 705), TEAL)
    save(img, "fig4_5_load_generation_subsystem.png")


def fig6() -> None:
    img, d = new_canvas("实验编排与分析子系统结构", "实验文件夹负责编排，测试目录保存中间产物")
    section(d, (90, 165, 1710, 1090), "HCP-Lab", PURPLE_L, PURPLE)
    label_box(d, (145, 270, 525, 440), "实验目录", ["每个实验独立文件夹", "包含测试、运行、分析脚本"], "#FFFFFF", PURPLE)
    label_box(d, (710, 270, 1090, 440), "参数矩阵", ["算法、节点规模", "交易量、负载模式、重复次数"], "#FFFFFF", PURPLE)
    label_box(d, (1275, 270, 1655, 440), "运行控制", ["暂存二进制", "启动节点与负载生成器", "清理旧中间数据"], "#FFFFFF", PURPLE)
    arrow(d, (520, 370), (710, 370), GRAY)
    arrow(d, (1090, 370), (1280, 370), GRAY)
    mini_box(d, (130, 565, 360, 690), "节点数据", "每个节点保存状态、区块和交易结果", "#FFFFFF", BLUE)
    mini_box(d, (390, 565, 620, 690), "运行日志", "引擎日志、负载日志和详细记录", "#FFFFFF", BLUE)
    label_box(d, (720, 575, 1080, 725), "指标聚合", ["吞吐量", "分位延迟", "成功率与消息开销"], "#FFFFFF", TEAL)
    mini_box(d, (1190, 565, 1420, 690), "实验表格", "按论文表格编号输出", "#FFFFFF", ORANGE)
    mini_box(d, (1450, 565, 1680, 690), "论文图片", "读取汇总数据并统一绘图", "#FFFFFF", ORANGE)
    arrow(d, (620, 630), (720, 650), GRAY)
    arrow(d, (1080, 650), (1190, 630), GRAY)
    label_box(d, (270, 900, 1530, 1015), "数据落点", ["中间过程统一放入测试目录；最终实验数据落入各实验文件夹的报告目录；总表再汇总给论文绘图使用"], GRAY_L, GRAY)
    save(img, "fig4_6_lab_orchestration_subsystem.png")


def fig7() -> None:
    img, d = new_canvas("HCP-Bench数据分层与流转", "链上执行数据与链下实验数据职责分离")
    label_box(d, (130, 170, 520, 300), "数据输入源", ["负载生成器、共识引擎、实验编排器"], BLUE_L, BLUE)
    label_box(d, (705, 170, 1095, 300), "分类规则", ["是否参与状态提交与共识验证"], ORANGE_L, ORANGE)
    label_box(d, (1280, 170, 1670, 300), "分析输出", ["表格、图形、模型参数"], PURPLE_L, PURPLE)
    arrow(d, (520, 235), (705, 235), GRAY)
    arrow(d, (1095, 235), (1280, 235), GRAY)
    section(d, (105, 405, 840, 1015), "区块链执行数据", GREEN_L, GREEN)
    for i, (title, body) in enumerate([
        ("交易字节", "进入区块并被执行"),
        ("区块摘要", "高度、哈希、交易列表"),
        ("应用状态", "应用哈希与状态库"),
        ("交易结果", "执行结果与消耗记录"),
    ]):
        x = 170 + (i % 2) * 330
        y = 520 + (i // 2) * 185
        label_box(d, (x, y, x + 270, y + 120), title, [body], "#FFFFFF", GREEN)
    mini_box(d, (250, 890, 700, 970), "特征", "参与状态提交，支撑一致性和可追溯性", "#FFFFFF", GREEN)
    section(d, (960, 405, 1695, 1015), "系统实验数据", RED_L, RED)
    for i, (title, body) in enumerate([
        ("实验配置", "算法与参数矩阵"),
        ("负载记录", "数据库交易记录"),
        ("运行日志", "节点与脚本日志"),
        ("统计结果", "TPS、延迟、成功率"),
    ]):
        x = 1025 + (i % 2) * 330
        y = 520 + (i // 2) * 185
        label_box(d, (x, y, x + 270, y + 120), title, [body], "#FFFFFF", RED)
    mini_box(d, (1105, 890, 1555, 970), "特征", "不参与共识，仅用于实验复现和性能分析", "#FFFFFF", RED)
    save(img, "fig4_7_data_layers_and_flow.png")


def fig8() -> None:
    img, d = new_canvas("区块链节点数据存储架构", "共识提交后由SDK执行层写入真实节点数据")
    label_box(d, (150, 170, 520, 330), "共识提交", ["自研引擎完成排序与提交", "形成已确认区块"], BLUE_L, BLUE)
    label_box(d, (715, 170, 1085, 330), "SDK执行适配层", ["执行交易", "提交应用状态"], PURPLE_L, PURPLE)
    label_box(d, (1280, 170, 1650, 330), "节点数据目录", ["每个节点独立保存", "高度、哈希和执行结果"], GREEN_L, GREEN)
    arrow(d, (520, 250), (715, 250), GRAY)
    arrow(d, (1085, 250), (1280, 250), GRAY)
    section(d, (110, 450, 835, 1045), "自研共识实验路径", BLUE_L, BLUE)
    label_box(d, (175, 555, 770, 665), "应用数据库", ["保存SDK应用状态"], "#FFFFFF", BLUE)
    label_box(d, (175, 710, 445, 835), "区块文件", ["高度、区块哈希", "交易列表"], "#FFFFFF", BLUE)
    label_box(d, (500, 710, 770, 835), "交易结果", ["执行状态", "消耗记录"], "#FFFFFF", BLUE)
    label_box(d, (175, 880, 770, 990), "最新状态", ["最新高度、应用哈希、提交交易数"], "#FFFFFF", BLUE)
    section(d, (965, 450, 1690, 1045), "官方CometBFT对照路径", ORANGE_L, ORANGE)
    label_box(d, (1030, 565, 1625, 690), "完整节点数据", ["网络、内存池、区块提议、投票、区块存储和状态库由官方节点维护"], "#FFFFFF", ORANGE)
    label_box(d, (1030, 740, 1625, 865), "使用边界", ["只用于CometBFT工程基线对比", "不代表自研共识内部结构"], "#FFFFFF", ORANGE)
    label_box(d, (1030, 910, 1625, 990), "对比意义", ["连接自研轻量实现与成熟工程项目"], "#FFFFFF", ORANGE)
    save(img, "fig4_8_blockchain_node_storage.png")


def fig9() -> None:
    img, d = new_canvas("系统实验数据存储架构", "PostgreSQL保存负载侧数据，文件系统保存实验产物")
    section(d, (90, 160, 830, 1000), "PostgreSQL结构化存储", BLUE_L, BLUE)
    label_box(d, (160, 275, 760, 410), "实验隔离", ["每轮实验使用独立命名空间", "运行开始前重建数据表"], "#FFFFFF", BLUE)
    for i, name in enumerate(["账户信息", "余额快照", "订单记录", "交易记录"]):
        x = 180 + (i % 2) * 300
        y = 510 + (i // 2) * 165
        label_box(d, (x, y, x + 250, y + 110), name, ["负载生成器写入"], "#FFFFFF", BLUE)
    label_box(d, (160, 855, 760, 950), "写入方式", ["连接池、批量写入、批量更新"], "#FFFFFF", BLUE)
    section(d, (970, 160, 1710, 1000), "文件系统结果存储", ORANGE_L, ORANGE)
    label_box(d, (1040, 275, 1640, 410), "中间过程目录", ["二进制、节点数据、日志、明细记录"], "#FFFFFF", ORANGE)
    label_box(d, (1040, 510, 1320, 650), "节点数据", ["状态摘要", "区块与交易结果"], "#FFFFFF", ORANGE)
    label_box(d, (1360, 510, 1640, 650), "实验日志", ["引擎日志", "负载日志"], "#FFFFFF", ORANGE)
    label_box(d, (1040, 735, 1320, 875), "最终表格", ["实验表格", "汇总数据"], "#FFFFFF", ORANGE)
    label_box(d, (1360, 735, 1640, 875), "论文图片", ["独立图片文件", "统一风格输出"], "#FFFFFF", ORANGE)
    label_box(d, (250, 1040, 1550, 1130), "存储原则", ["链上数据用于验证状态提交；系统数据用于复现实验过程与支撑性能分析"], GRAY_L, GRAY)
    save(img, "fig4_9_system_data_storage.png")


def main() -> None:
    if OUT_DIR.exists():
        for item in OUT_DIR.iterdir():
            if item.is_file() and item.suffix.lower() in {".png", ".jpg", ".jpeg", ".svg", ".pdf"}:
                item.unlink()
    else:
        OUT_DIR.mkdir(parents=True)
    for fn in [fig1, fig2, fig3, fig4, fig5, fig6, fig7, fig8, fig9]:
        fn()


if __name__ == "__main__":
    main()
