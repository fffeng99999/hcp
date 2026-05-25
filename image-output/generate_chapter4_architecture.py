#!/usr/bin/env python3
"""Generate corrected Chapter 4 HCP-Bench architecture figures."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable
import math

from PIL import Image, ImageDraw, ImageFont


OUT_DIR = Path(__file__).resolve().parent / "chapter4"
W, H = 1800, 1180

BG = "#FFFFFF"
TEXT = "#17324D"
MUTED = "#5D7080"
GRAY = "#7C8791"
GRAY_L = "#F3F6F8"
BLUE = "#2F6FAB"
BLUE_L = "#EAF3FF"
BLUE_M = "#DCEBFA"
GREEN = "#3D8D59"
GREEN_L = "#EAF7EF"
GREEN_M = "#DDF0E5"
ORANGE = "#D8811D"
ORANGE_L = "#FFF2DE"
ORANGE_M = "#FFE5BF"
PURPLE = "#7D61B3"
PURPLE_L = "#F2ECFF"
PURPLE_M = "#E7DCF8"
RED = "#C75151"
RED_L = "#FFF0F0"
RED_M = "#F9DCDC"
TEAL = "#2A8C96"
TEAL_L = "#E7F8FA"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/simsun.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


F_TITLE = font(42, True)
F_SUB = font(22)
F_SECTION = font(25, True)
F_HEAD = font(23, True)
F_BODY = font(17)
F_SMALL = font(15)


def text_size(d: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont) -> tuple[int, int]:
    box = d.textbbox((0, 0), text, font=fnt)
    return box[2] - box[0], box[3] - box[1]


def wrap(d: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    out: list[str] = []
    for raw in text.split("\n"):
        cur = ""
        for ch in raw:
            trial = cur + ch
            if not cur or text_size(d, trial, fnt)[0] <= max_w:
                cur = trial
            else:
                out.append(cur)
                cur = ch
        if cur:
            out.append(cur)
    return out or [""]


def canvas(title: str, subtitle: str = "") -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.text((W // 2, 46), title, fill=TEXT, font=F_TITLE, anchor="mm")
    if subtitle:
        d.text((W // 2, 88), subtitle, fill=MUTED, font=F_SUB, anchor="mm")
    return img, d


def rounded(d: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill: str, outline: str, width: int = 3, r: int = 22) -> None:
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


def section(d: ImageDraw.ImageDraw, box: tuple[int, int, int, int], title: str, fill: str, outline: str) -> None:
    rounded(d, box, fill, outline, 3, 26)
    d.text(((box[0] + box[2]) // 2, box[1] + 34), title, fill=outline, font=F_SECTION, anchor="mm")


def box(
    d: ImageDraw.ImageDraw,
    rect: tuple[int, int, int, int],
    title: str,
    lines: Iterable[str] = (),
    fill: str = "#FFFFFF",
    outline: str = BLUE,
    title_color: str | None = None,
    body_font: ImageFont.FreeTypeFont = F_BODY,
) -> None:
    rounded(d, rect, fill, outline, 2, 18)
    x1, y1, x2, y2 = rect
    title_color = title_color or outline
    body_lines: list[str] = []
    for line in lines:
        body_lines.extend(wrap(d, line, body_font, x2 - x1 - 34))
    title_lines = wrap(d, title, F_HEAD, x2 - x1 - 34)
    total = len(title_lines) * 30 + (8 if body_lines else 0) + len(body_lines) * 21
    y = y1 + max(16, ((y2 - y1) - total) // 2)
    for t in title_lines:
        d.text(((x1 + x2) // 2, y), t, fill=title_color, font=F_HEAD, anchor="ma")
        y += 30
    y += 6
    for line in body_lines:
        d.text(((x1 + x2) // 2, y), line, fill=TEXT, font=body_font, anchor="ma")
        y += 21


def small_box(d: ImageDraw.ImageDraw, rect: tuple[int, int, int, int], title: str, body: str, fill: str, outline: str) -> None:
    box(d, rect, title, wrap(d, body, F_SMALL, rect[2] - rect[0] - 30), fill, outline, body_font=F_SMALL)


def chip(d: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, color: str, fill: str) -> tuple[int, int, int, int]:
    x, y = xy
    tw, th = text_size(d, text, F_SMALL)
    rect = (x, y, x + tw + 30, y + th + 18)
    rounded(d, rect, fill, color, 2, 18)
    d.text((x + 15, y + 9), text, fill=color, font=F_SMALL, anchor="la")
    return rect


def arrow(d: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int], color: str = GRAY, width: int = 4) -> None:
    d.line([start, end], fill=color, width=width)
    sx, sy = start
    ex, ey = end
    ang = math.atan2(ey - sy, ex - sx)
    length = 16
    spread = 0.45
    p1 = (ex - length * math.cos(ang - spread), ey - length * math.sin(ang - spread))
    p2 = (ex - length * math.cos(ang + spread), ey - length * math.sin(ang + spread))
    d.polygon([end, p1, p2], fill=color)


def save(img: Image.Image, name: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    img.save(OUT_DIR / name, quality=95)
    print(f"created {OUT_DIR / name}")


def fig1() -> None:
    img, d = canvas("HCP-Bench总体架构", "统一负载、统一共识入口、统一指标口径的高频共识性能测试平台")
    section(d, (55, 135, 540, 940), "负载生成子系统", GREEN_L, GREEN)
    section(d, (660, 135, 1145, 940), "共识执行子系统", BLUE_L, BLUE)
    section(d, (1260, 135, 1745, 940), "实验编排与分析子系统", PURPLE_L, PURPLE)

    for y, title, lines in [
        (205, "交易构造", ["生成SDK交易字节", "模拟高频转账负载"]),
        (350, "账户选择", ["均匀账户访问", "热点账户访问"]),
        (495, "发送调度", ["固定速率、持续高压", "突发与抖动负载"]),
        (640, "提交广播", ["HTTP或gRPC提交", "记录响应时间"]),
        (785, "负载侧存储", ["数据库隔离", "账户与交易记录"]),
    ]:
        box(d, (105, y, 490, y + 105), title, lines, "#FFFFFF", GREEN)

    for y, title, lines in [
        (205, "本地多节点引擎集群", ["PBFT、HotStuff、Raft", "CometBFT-light、tPBFT"]),
        (365, "统一模拟网络", ["低延迟局域网模型", "统计消息数与字节数"]),
        (525, "共识提交", ["领导节点出块", "多数确认后提交"]),
        (685, "SDK执行适配层", ["提交后执行交易", "更新应用状态"]),
        (825, "官方CometBFT对照", ["独立多进程节点", "作为工程基线"]),
    ]:
        box(d, (710, y, 1095, y + 105), title, lines, "#FFFFFF", BLUE)

    for y, title, lines in [
        (205, "实验矩阵", ["算法、节点规模", "交易量与负载模式"]),
        (350, "运行调度", ["启动引擎与负载", "清理旧中间数据"]),
        (495, "节点管理", ["维护节点目录", "采集运行状态"]),
        (640, "指标计算", ["TPS、P50、P95、P99", "成功率与消息开销"]),
        (785, "结果归档", ["保存实验结果", "支撑后续建模"]),
    ]:
        box(d, (1310, y, 1695, y + 105), title, lines, "#FFFFFF", PURPLE)

    arrow(d, (540, 540), (660, 540), GREEN)
    arrow(d, (1145, 540), (1260, 540), BLUE)
    for x, label, color, fill in [
        (190, "统一硬件", BLUE, BLUE_L),
        (390, "统一负载入口", GREEN, GREEN_L),
        (640, "统一节点规模", ORANGE, ORANGE_L),
        (890, "统一统计口径", PURPLE, PURPLE_L),
        (1140, "独立数据隔离", TEAL, TEAL_L),
        (1390, "可重复执行", RED, RED_L),
    ]:
        chip(d, (x, 980), label, color, fill)
    box(d, (210, 1040, 1590, 1125), "设计原则", ["自研算法共享同一负载入口和统计链路；官方CometBFT作为独立工程基线，不与轻量实现混跑"], GRAY_L, GRAY)
    save(img, "fig4_1_hcp_bench_overall_architecture.png")


def fig2() -> None:
    img, d = canvas("单轮实验数据流", "从参数配置到共识确认、状态执行和指标归档的端到端数据路径")
    flow = [
        ("实验配置", ["读取实验矩阵", "确定算法与规模"], ORANGE, ORANGE_L),
        ("负载生成", ["生成SDK交易字节", "写入负载记录"], GREEN, GREEN_L),
        ("交易入口", ["提交到共识入口", "进入交易池"], TEAL, TEAL_L),
        ("共识排序", ["领导节点打包", "多数节点确认"], BLUE, BLUE_L),
        ("状态执行", ["SDK应用执行", "更新应用状态"], PURPLE, PURPLE_L),
        ("指标归档", ["计算性能指标", "保存实验结果"], RED, RED_L),
    ]
    x0, y0, bw, bh, gap = 65, 170, 245, 150, 35
    for i, (title, lines, color, fill) in enumerate(flow):
        x = x0 + i * (bw + gap)
        box(d, (x, y0, x + bw, y0 + bh), title, lines, fill, color)
        if i < len(flow) - 1:
            arrow(d, (x + bw, y0 + bh // 2), (x + bw + gap - 5, y0 + bh // 2))

    box(d, (100, 420, 520, 600), "负载侧数据", ["账户信息与余额快照", "交易发送记录", "响应时间与状态码", "独立数据库命名空间"], GREEN_L, GREEN)
    box(d, (690, 420, 1110, 600), "链上侧数据", ["区块高度与哈希", "交易执行结果", "应用状态哈希", "节点最新状态"], BLUE_L, BLUE)
    box(d, (1280, 420, 1700, 600), "观测侧数据", ["提交窗口", "延迟分位", "成功率", "消息数与字节数"], PURPLE_L, PURPLE)
    for x, color in [(310, GREEN), (900, BLUE), (1490, PURPLE)]:
        arrow(d, (x, 600), (x, 690), color)

    small_box(d, (110, 710, 360, 820), "发送侧时间", "发送、响应、超时记录", "#FFFFFF", GREEN)
    small_box(d, (390, 710, 640, 820), "数据库记录", "账户、余额、交易明细", "#FFFFFF", GREEN)
    small_box(d, (680, 710, 930, 820), "提交窗口", "首笔提交到最后一笔提交", "#FFFFFF", BLUE)
    small_box(d, (960, 710, 1210, 820), "分位延迟", "按真实确认延迟统计", "#FFFFFF", BLUE)
    small_box(d, (1250, 710, 1500, 820), "统计结果", "多轮重复实验聚合", "#FFFFFF", PURPLE)
    small_box(d, (1530, 710, 1690, 820), "异常记录", "失败与超时记录", "#FFFFFF", PURPLE)

    for x, label in [(250, "TPS"), (360, "P50"), (470, "P95"), (580, "P99"), (705, "成功率"), (850, "消息数"), (985, "字节数"), (1120, "提交数量")]:
        chip(d, (x, 875), label, BLUE if x < 650 else ORANGE, BLUE_L if x < 650 else ORANGE_L)
    box(d, (180, 980, 1620, 1075), "闭环说明", ["当前实现按实验矩阵顺序运行；统计结果用于实验分析和参数校验，不在单轮运行中自动调整负载"], GRAY_L, GRAY)
    save(img, "fig4_2_experiment_data_flow.png")


def fig3() -> None:
    img, d = canvas("共识执行子系统结构", "自研共识引擎驱动SDK执行层，官方CometBFT作为独立对照")
    section(d, (60, 135, 500, 1030), "负载入口", GREEN_L, GREEN)
    for y, title, lines in [
        (205, "交易提交接口", ["接收SDK交易字节", "支持HTTP与gRPC"]),
        (350, "交易池", ["缓存待排序交易", "供领导节点打包"]),
        (495, "状态查询接口", ["提交数量", "延迟分位", "节点状态"]),
        (640, "广播响应", ["返回接收状态", "记录响应耗时"]),
        (785, "负载记录关联", ["连接发送侧记录", "用于延迟校验"]),
    ]:
        box(d, (95, y, 465, y + 110), title, lines, "#FFFFFF", GREEN)

    section(d, (545, 135, 1135, 1030), "自研共识本地集群", BLUE_L, BLUE)
    box(d, (585, 205, 1095, 300), "内存模拟网络", ["统一延迟与带宽参数", "统计广播消息数与字节数"], "#FFFFFF", BLUE)
    for idx, y in enumerate([345, 500, 655]):
        box(d, (585, y, 825, y + 115), f"节点{idx}", ["共识引擎", "交易池", "消息处理"], "#FFFFFF", BLUE)
        box(d, (870, y, 1095, y + 115), "执行适配", ["执行交易", "写入节点状态"], "#FFFFFF", TEAL)
        arrow(d, (825, y + 58), (870, y + 58), TEAL)
    box(d, (585, 820, 1095, 925), "共识流程", ["交易池 → 领导节点出块 → 多轮确认 → 共识提交"], BLUE_M, BLUE)

    section(d, (1180, 135, 1740, 1030), "执行与对照", PURPLE_L, PURPLE)
    for y, title, lines, color in [
        (205, "SDK应用执行层", ["执行交易", "更新账户状态", "生成应用哈希"], PURPLE),
        (365, "节点数据", ["区块摘要", "交易结果", "最新高度"], PURPLE),
        (525, "消息统计", ["广播消息数量", "广播字节总量"], PURPLE),
        (690, "官方CometBFT路径", ["完整多进程节点", "独立工程基线"], ORANGE),
        (855, "对照意义", ["连接自研轻量实现", "比较成熟工程系统"], ORANGE),
    ]:
        box(d, (1225, y, 1695, y + 115), title, lines, "#FFFFFF", color)

    arrow(d, (500, 580), (545, 580), GREEN)
    arrow(d, (1135, 580), (1180, 580), BLUE)
    save(img, "fig4_3_consensus_execution_subsystem.png")


def fig4() -> None:
    img, d = canvas("共识引擎选择与执行路径", "同一负载入口下切换算法，保持统一测量口径")
    box(d, (100, 150, 430, 270), "实验配置", ["算法类型", "节点规模", "负载强度"], ORANGE_L, ORANGE)
    box(d, (560, 150, 1240, 270), "统一负载入口", ["交易字节进入共识子系统", "所有算法使用相同提交口径"], TEAL_L, TEAL)
    box(d, (1370, 150, 1700, 270), "指标输出", ["TPS、P50、P95、P99", "成功率、消息开销"], PURPLE_L, PURPLE)
    arrow(d, (430, 210), (560, 210))
    arrow(d, (1240, 210), (1370, 210))

    section(d, (90, 365, 830, 690), "自研共识算法组", BLUE_L, BLUE)
    algos = ["PBFT", "HotStuff", "Raft", "CometBFT-light", "tPBFT", "分层tPBFT", "轻量子层"]
    for i, name in enumerate(algos):
        col, row = i % 3, i // 3
        x, y = 130 + col * 230, 440 + row * 95
        box(d, (x, y, x + 200, y + 70), name, [], "#FFFFFF", BLUE)

    section(d, (970, 365, 1710, 690), "官方CometBFT对照组", ORANGE_L, ORANGE)
    for y, title, lines in [
        (440, "官方网络", ["完整P2P网络协议栈"]),
        (530, "内存池与区块提议", ["交易缓存、提议、广播"]),
        (620, "投票与节点数据", ["多阶段投票、完整节点状态"]),
    ]:
        box(d, (1030, y, 1650, y + 65), title, lines, "#FFFFFF", ORANGE)

    arrow(d, (900, 270), (460, 365), BLUE)
    arrow(d, (900, 270), (1340, 365), ORANGE)
    stages = [
        ("交易池", "缓存交易"),
        ("领导节点出块", "形成区块"),
        ("共识提交", "多数确认"),
        ("SDK执行", "状态提交"),
        ("节点数据", "高度与哈希"),
    ]
    x0, y0 = 140, 805
    for i, (title, body) in enumerate(stages):
        color, fill = (BLUE, BLUE_L) if i < 3 else (PURPLE, PURPLE_L)
        box(d, (x0 + i * 320, y0, x0 + i * 320 + 245, y0 + 105), title, [body], fill, color)
        if i < len(stages) - 1:
            arrow(d, (x0 + i * 320 + 245, y0 + 52), (x0 + i * 320 + 315, y0 + 52))
    box(d, (260, 1000, 1540, 1085), "执行边界", ["自研算法在统一实验入口切换；官方CometBFT独立运行，不与轻量实现混合"], GRAY_L, GRAY)
    save(img, "fig4_4_engine_selection_and_execution_path.png")


def fig5() -> None:
    img, d = canvas("负载生成子系统结构", "生成SDK交易字节，记录负载侧过程数据")
    box(d, (650, 135, 1150, 235), "实验参数", ["交易总量、发送节奏、账户分布、实验标识"], ORANGE_L, ORANGE)
    section(d, (80, 300, 1720, 1010), "HCP-Loadgen", GREEN_L, GREEN)
    modules = [
        (150, "账户池", ["均匀选择", "热点选择", "本地维护账户序号"]),
        (520, "调度器", ["固定速率", "持续、突发、抖动", "交易总量控制"]),
        (890, "工作线程", ["构造交易", "签名与编码", "本地缓冲"]),
        (1260, "广播器", ["HTTP提交", "gRPC提交", "响应计时"]),
    ]
    for x, title, lines in modules:
        box(d, (x, 405, x + 310, 555), title, lines, "#FFFFFF", GREEN)
    for x in [460, 830, 1200]:
        arrow(d, (x, 480), (x + 60, 480))

    small_box(d, (150, 625, 420, 735), "交易内容", "账户、数量、随机负载与时间戳", "#FFFFFF", GREEN)
    small_box(d, (470, 625, 760, 735), "SDK交易字节", "可由SDK执行层解析并执行", "#FFFFFF", TEAL)
    small_box(d, (1020, 625, 1290, 735), "负载记录", "交易标识、账户、延迟与状态", "#FFFFFF", ORANGE)
    small_box(d, (1340, 625, 1600, 735), "数据库写入", "批量写入并按实验隔离", "#FFFFFF", ORANGE)
    arrow(d, (620, 555), (620, 625), TEAL)
    arrow(d, (1135, 555), (1135, 625), ORANGE)

    box(d, (250, 830, 750, 925), "热路径", ["交易字节直接发送到共识入口", "优先保证发送效率"], TEAL_L, TEAL)
    box(d, (1050, 830, 1550, 925), "冷路径", ["负载侧记录异步持久化", "不参与共识主路径"], ORANGE_L, ORANGE)
    save(img, "fig4_5_load_generation_subsystem.png")


def fig6() -> None:
    img, d = canvas("实验编排与分析子系统结构", "负责实验矩阵、运行调度、指标聚合和结果归档")
    section(d, (70, 135, 1730, 1030), "HCP-Lab", PURPLE_L, PURPLE)
    for x, title, lines in [
        (140, "实验定义", ["每个实验独立配置", "包含运行与验证脚本"]),
        (585, "参数矩阵", ["算法、节点规模", "交易量、负载模式", "重复次数"]),
        (1120, "运行控制", ["准备二进制", "启动引擎与负载", "等待完成"]),
    ]:
        box(d, (x, 220, x + 420, 360), title, lines, "#FFFFFF", PURPLE)
    arrow(d, (560, 290), (585, 290))
    arrow(d, (1005, 290), (1120, 290))

    small_box(d, (150, 490, 410, 620), "节点数据", "每个节点保存状态、区块和交易结果", "#FFFFFF", BLUE)
    small_box(d, (450, 490, 710, 620), "运行日志", "引擎日志、负载日志、错误记录", "#FFFFFF", BLUE)
    box(d, (770, 475, 1030, 635), "指标聚合", ["TPS", "P50 / P95 / P99", "成功率", "消息与字节开销"], TEAL_L, TEAL)
    small_box(d, (1090, 490, 1350, 620), "实验结果", "每组实验的统计结果与原始样本", "#FFFFFF", ORANGE)
    small_box(d, (1390, 490, 1650, 620), "结果校验", "检查缺失、失败和异常值", "#FFFFFF", ORANGE)
    arrow(d, (710, 555), (770, 555))
    arrow(d, (1030, 555), (1090, 555))

    box(d, (160, 735, 800, 865), "中间过程数据区", ["二进制文件、节点数据、运行日志、明细记录", "用于复现实验过程和排查异常"], GRAY_L, GRAY)
    box(d, (1000, 735, 1640, 865), "结果数据区", ["每轮统计样本、聚合结果、模型输入数据", "用于后续实验分析和边界建模"], ORANGE_L, ORANGE)
    box(d, (220, 950, 1580, 1025), "数据原则", ["中间过程与结果数据分区保存；实验结果必须能追溯到对应参数、负载记录和节点状态"], GRAY_L, GRAY)
    save(img, "fig4_6_lab_orchestration_subsystem.png")


def fig7() -> None:
    img, d = canvas("HCP-Bench数据分层与流转", "链上执行数据与链下实验数据职责分离，降低观测路径耦合")
    box(d, (130, 150, 520, 260), "数据输入源", ["负载生成器", "共识引擎", "SDK执行层"], BLUE_L, BLUE)
    box(d, (705, 150, 1095, 260), "分类规则", ["是否参与状态提交", "是否参与共识验证"], ORANGE_L, ORANGE)
    box(d, (1280, 150, 1670, 260), "分析使用", ["性能统计", "异常定位", "边界建模"], PURPLE_L, PURPLE)
    arrow(d, (520, 205), (705, 205))
    arrow(d, (1095, 205), (1280, 205))

    section(d, (100, 380, 825, 1000), "区块链执行数据", GREEN_L, GREEN)
    for i, (title, body) in enumerate([
        ("交易字节", "进入区块并被SDK执行"),
        ("区块摘要", "高度、哈希、交易列表"),
        ("应用状态", "账户状态与应用哈希"),
        ("交易结果", "执行状态与消耗记录"),
    ]):
        x = 165 + (i % 2) * 330
        y = 500 + (i // 2) * 170
        small_box(d, (x, y, x + 270, y + 115), title, body, "#FFFFFF", GREEN)
    box(d, (195, 845, 730, 940), "特征", ["参与状态提交，支撑一致性与可追溯性"], GREEN_M, GREEN)

    section(d, (975, 380, 1700, 1000), "系统实验数据", RED_L, RED)
    for i, (title, body) in enumerate([
        ("实验配置", "算法、规模、负载与重复次数"),
        ("负载记录", "账户、交易、响应时间"),
        ("运行日志", "节点日志与错误记录"),
        ("统计结果", "TPS、延迟、成功率、消息开销"),
    ]):
        x = 1040 + (i % 2) * 330
        y = 500 + (i // 2) * 170
        small_box(d, (x, y, x + 270, y + 115), title, body, "#FFFFFF", RED)
    box(d, (1070, 845, 1605, 940), "特征", ["不参与共识，仅用于复现、观测和性能分析"], RED_M, RED)
    save(img, "fig4_7_data_layers_and_flow.png")


def fig8() -> None:
    img, d = canvas("区块链节点数据存储架构", "共识提交后由SDK执行层写入真实节点数据")
    box(d, (150, 160, 520, 300), "共识提交", ["自研引擎完成排序", "形成已确认区块"], BLUE_L, BLUE)
    box(d, (715, 160, 1085, 300), "SDK执行适配层", ["执行交易", "提交应用状态"], PURPLE_L, PURPLE)
    box(d, (1280, 160, 1650, 300), "节点数据目录", ["每个节点独立保存", "高度、哈希与执行结果"], GREEN_L, GREEN)
    arrow(d, (520, 230), (715, 230))
    arrow(d, (1085, 230), (1280, 230))

    section(d, (110, 430, 835, 1025), "自研共识实验路径", BLUE_L, BLUE)
    box(d, (175, 535, 770, 645), "应用数据库", ["保存SDK应用状态", "账户状态与应用哈希"], "#FFFFFF", BLUE)
    small_box(d, (175, 700, 445, 825), "区块文件", "高度、区块哈希、交易列表", "#FFFFFF", BLUE)
    small_box(d, (500, 700, 770, 825), "交易结果", "执行状态、消耗记录、失败信息", "#FFFFFF", BLUE)
    box(d, (175, 875, 770, 975), "最新状态", ["最新高度、应用哈希、提交交易数"], "#FFFFFF", BLUE)

    section(d, (965, 430, 1690, 1025), "官方CometBFT对照路径", ORANGE_L, ORANGE)
    box(d, (1030, 535, 1625, 660), "完整节点数据", ["网络、内存池、区块提议、投票", "区块存储和状态库由官方节点维护"], "#FFFFFF", ORANGE)
    box(d, (1030, 730, 1625, 845), "使用边界", ["只用于CometBFT工程基线对比", "不代表自研共识内部结构"], "#FFFFFF", ORANGE)
    box(d, (1030, 900, 1625, 980), "对比意义", ["连接自研轻量实现与成熟工程项目"], "#FFFFFF", ORANGE)
    save(img, "fig4_8_blockchain_node_storage.png")


def fig9() -> None:
    img, d = canvas("系统实验数据存储架构", "PostgreSQL保存负载侧结构化数据，文件系统保存实验过程与结果数据")
    section(d, (90, 155, 830, 1010), "PostgreSQL结构化存储", BLUE_L, BLUE)
    box(d, (160, 270, 760, 390), "实验隔离", ["每轮实验使用独立数据命名空间", "运行开始前重建数据表"], "#FFFFFF", BLUE)
    for i, title in enumerate(["账户信息", "余额快照", "订单记录", "交易记录"]):
        x = 180 + (i % 2) * 300
        y = 500 + (i // 2) * 165
        small_box(d, (x, y, x + 250, y + 110), title, "负载生成器写入", "#FFFFFF", BLUE)
    box(d, (160, 850, 760, 945), "写入方式", ["连接池、批量写入、批量更新"], "#FFFFFF", BLUE)

    section(d, (970, 155, 1710, 1010), "文件系统结果存储", ORANGE_L, ORANGE)
    box(d, (1040, 270, 1640, 390), "中间过程数据", ["二进制、节点数据、运行日志、明细记录"], "#FFFFFF", ORANGE)
    small_box(d, (1040, 500, 1320, 635), "节点数据", "状态摘要、区块与交易结果", "#FFFFFF", ORANGE)
    small_box(d, (1360, 500, 1640, 635), "实验日志", "引擎日志、负载日志", "#FFFFFF", ORANGE)
    small_box(d, (1040, 740, 1320, 875), "统计样本", "每轮实验指标样本", "#FFFFFF", ORANGE)
    small_box(d, (1360, 740, 1640, 875), "聚合结果", "多轮重复后的均值与波动", "#FFFFFF", ORANGE)
    box(d, (250, 1045, 1550, 1125), "存储原则", ["链上数据用于验证状态提交；系统数据用于复现实验过程与支撑性能分析"], GRAY_L, GRAY)
    save(img, "fig4_9_system_data_storage.png")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for item in OUT_DIR.glob("fig4_*.png"):
        item.unlink()
    for fn in [fig1, fig2, fig3, fig4, fig5, fig6, fig7, fig8, fig9]:
        fn()


if __name__ == "__main__":
    main()
