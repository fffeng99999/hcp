#!/usr/bin/env python3
"""Generate thesis figures from hcp-lab/experiments/report/summary_all.md."""
from __future__ import annotations

import re
from pathlib import Path
import json

import matplotlib
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
SUMMARY = ROOT / "hcp-lab" / "experiments" / "report" / "summary_all.md"
EXP1_SUMMARY = ROOT / "hcp-lab" / "experiments" / "exp1_benchmark" / "report" / "summary.json"
OUT_DIR = Path(__file__).resolve().parent / "chapter3"

ALGO_ORDER = ["PBFT", "HotStuff", "Raft", "CometBFT-light", "tPBFT"]
COLORS = {
    "PBFT": "#3B6EA8",
    "HotStuff": "#D9802E",
    "Raft": "#4E9A62",
    "CometBFT": "#7F63B8",
    "CometBFT-light": "#9B5B50",
    "tPBFT": "#C44E52",
    "分层tPBFT": "#7F63B8",
    "A": "#8C8C8C",
    "B": "#5B8DB8",
    "C": "#4E9A62",
    "D": "#D9802E",
}

BAR_WIDTH_2_3 = 0.8 * 2 / 3


def setup_style() -> None:
    matplotlib.rcParams["font.sans-serif"] = [
        "Microsoft YaHei",
        "SimHei",
        "Noto Sans CJK SC",
        "Arial Unicode MS",
        "DejaVu Sans",
    ]
    matplotlib.rcParams["axes.unicode_minus"] = False
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
            "axes.edgecolor": "#333333",
            "axes.grid": False,
            "grid.color": "#DDDDDD",
            "grid.linestyle": "--",
            "grid.linewidth": 0.6,
            "legend.frameon": False,
        }
    )


def clean_outputs() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for pattern in ("*.png", "*.jpg", "*.jpeg", "*.svg", "*.pdf", "*.csv", "*.json"):
        for path in OUT_DIR.glob(pattern):
            path.unlink()


def parse_mean(value: str) -> float:
    text = str(value).split("±", 1)[0].replace("%", "").replace(",", "").strip()
    match = re.search(r"[-+]?\d+(?:\.\d+)?(?:e[-+]?\d+)?", text, re.I)
    return float(match.group(0)) if match else 0.0


def algo_name(value: str) -> str:
    mapping = {
        "pbft": "PBFT",
        "hotstuff": "HotStuff",
        "raft": "Raft",
        "cometbft-light": "CometBFT-light",
        "tpbft": "tPBFT",
    }
    return mapping.get(value.strip(), value.strip())


def extract_table(markdown: str, number: str) -> list[dict[str, str]]:
    marker = f"## 表{number} "
    start = markdown.find(marker)
    if start < 0:
        raise ValueError(f"missing table {number}: {SUMMARY}")
    lines = markdown[start:].splitlines()
    table_lines: list[str] = []
    in_table = False
    for line in lines:
        if line.startswith("|"):
            in_table = True
            table_lines.append(line)
        elif in_table:
            break
    if len(table_lines) < 3:
        raise ValueError(f"table {number} has no body")
    header = [c.strip() for c in table_lines[0].strip("|").split("|")]
    rows = []
    for line in table_lines[2:]:
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) == len(header):
            rows.append(dict(zip(header, cells)))
    return rows


def save(fig: plt.Figure, name: str, _caption: str, _description: str, *, pad_inches: float = 0.1) -> None:
    path = OUT_DIR / name
    fig.savefig(path, dpi=300, bbox_inches="tight", pad_inches=pad_inches)
    plt.close(fig)
    print(f"created {path}")


def pick(row: dict[str, str], *names: str) -> str:
    for name in names:
        if name in row:
            return row[name]
    raise KeyError(f"missing any of columns {names}")


def load_benchmark_raw_points() -> dict[str, dict[int, dict[str, list[float]]]]:
    if not EXP1_SUMMARY.exists():
        return {}
    summary = json.loads(EXP1_SUMMARY.read_text(encoding="utf-8"))
    points: dict[str, dict[int, dict[str, list[float]]]] = {}
    for engine, by_node in summary.items():
        algo = algo_name(engine.replace("_", "-"))
        for node_text, stats in by_node.items():
            node = int(node_text)
            metrics = points.setdefault(algo, {}).setdefault(node, {"tps": [], "p99": []})
            for item in stats.get("raw", []):
                raw_metrics = item.get("metrics", {})
                metrics["tps"].append(float(raw_metrics.get("tps", 0.0)))
                metrics["p99"].append(float(raw_metrics.get("p99_ms", 0.0)))
    return points


def plot_load_pattern(rows: list[dict[str, str]]) -> None:
    grouped: dict[str, dict[str, dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault(row["算法"], {})[row["负载模式D"]] = row
    algos = [a for a in ALGO_ORDER if a in grouped]
    uniform_tps = [parse_mean(grouped[a]["Uniform"]["TPS(tx/s)"]) for a in algos]
    zipf_tps = [parse_mean(grouped[a]["Zipf"]["TPS(tx/s)"]) for a in algos]
    uniform_p99 = [parse_mean(grouped[a]["Uniform"]["P99(ms)"]) for a in algos]
    zipf_p99 = [parse_mean(grouped[a]["Zipf"]["P99(ms)"]) for a in algos]
    x = np.arange(len(algos))
    w = 0.36
    bw = w * 2 / 3
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8))
    axes[0].bar(x - w / 2, uniform_tps, bw, label="Uniform", color="#5B8DB8")
    axes[0].bar(x + w / 2, zipf_tps, bw, label="Zipf", color="#D9802E")
    axes[0].set_title("负载模式对TPS的影响")
    axes[0].set_ylabel("TPS (tx/s)")
    axes[0].set_xticks(x, algos, rotation=18, ha="right")
    axes[0].legend()
    axes[1].bar(x - w / 2, uniform_p99, bw, label="Uniform", color="#5B8DB8")
    axes[1].bar(x + w / 2, zipf_p99, bw, label="Zipf", color="#D9802E")
    axes[1].set_title("负载模式对P99的影响")
    axes[1].set_ylabel("P99 (ms)")
    axes[1].set_xticks(x, algos, rotation=18, ha="right")
    axes[1].legend()
    fig.tight_layout()
    save(fig, "fig3_1_load_pattern_sensitivity.png", "图3-1 Uniform与Zipf负载模式敏感性对比", "基于表3-3绘制。")


def plot_comet(rows: list[dict[str, str]]) -> None:
    data: dict[str, dict[int, dict[str, float]]] = {}
    for row in rows:
        algo = row["算法"]
        n = int(parse_mean(row["节点数N"]))
        data.setdefault(algo, {})[n] = {"tps": parse_mean(row["TPS(tx/s)"]), "p99": parse_mean(row["P99(ms)"])}
    nodes = [8, 16, 32]
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.8))
    for algo in ["CometBFT", "CometBFT-light"]:
        axes[0].plot(nodes, [data[algo][n]["tps"] for n in nodes], marker="o", ls=":", lw=2.2, label=algo, color=COLORS.get(algo))
        axes[1].plot(nodes, [data[algo][n]["p99"] for n in nodes], marker="o", ls=":", lw=2.2, label=algo, color=COLORS.get(algo))
    axes[0].set_title("CometBFT与CometBFT-light TPS")
    axes[0].set_xlabel("节点数 N")
    axes[0].set_ylabel("TPS (tx/s)")
    axes[1].set_title("CometBFT与CometBFT-light P99")
    axes[1].set_xlabel("节点数 N")
    axes[1].set_ylabel("P99 (ms)")
    for ax in axes:
        ax.set_xticks(nodes)
        ax.legend()
    fig.tight_layout()
    save(fig, "fig3_2_cometbft_vs_light.png", "图3-2 CometBFT与CometBFT-light对比", "基于表3-4绘制。")


def matrix(rows: list[dict[str, str]]) -> dict[str, dict[int, dict[str, float]]]:
    out: dict[str, dict[int, dict[str, float]]] = {}
    for row in rows:
        algo = algo_name(row["算法"])
        n = int(parse_mean(row["节点数N"]))
        out.setdefault(algo, {})[n] = {
            "tps": parse_mean(row["TPS(tx/s)"]),
            "p50": parse_mean(row["P50(ms)"]),
            "p95": parse_mean(row["P95(ms)"]),
            "p99": parse_mean(row["P99(ms)"]),
        }
    return out


def plot_benchmark(data: dict[str, dict[int, dict[str, float]]]) -> None:
    nodes = [8, 16, 32]
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8))
    for algo in ALGO_ORDER:
        axes[0].plot(nodes, [data[algo][n]["tps"] for n in nodes], marker="o", ls=":", lw=2.2, label=algo, color=COLORS.get(algo))
        axes[1].plot(nodes, [data[algo][n]["p99"] for n in nodes], marker="o", ls=":", lw=2.2, label=algo, color=COLORS.get(algo))
    axes[0].set_title("基准实验TPS随节点规模变化")
    axes[0].set_xlabel("节点数 N")
    axes[0].set_ylabel("TPS (tx/s)")
    axes[1].set_title("基准实验P99随节点规模变化")
    axes[1].set_xlabel("节点数 N")
    axes[1].set_ylabel("P99 (ms)")
    axes[1].axhline(200, color="#777777", lw=1, ls=":")
    for ax in axes:
        ax.set_xticks(nodes)
        ax.grid(False)
        ax.legend(ncol=2)
    fig.tight_layout()
    save(fig, "fig3_3_benchmark_tps_p99_nodes.png", "图3-3 基准实验TPS与P99随节点规模变化", "基于表3-5绘制。")


def plot_latency(data: dict[str, dict[int, dict[str, float]]]) -> None:
    nodes = [8, 16, 32]
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.3), sharey=True)
    for i, n in enumerate(nodes):
        algos = ALGO_ORDER
        x = np.arange(len(algos))
        w = 0.24
        bw = w * 2 / 3
        axes[i].bar(x - w, [data[a][n]["p50"] for a in algos], bw, label="P50", color="#8AB6D6")
        axes[i].bar(x, [data[a][n]["p95"] for a in algos], bw, label="P95", color="#F2B880")
        axes[i].bar(x + w, [data[a][n]["p99"] for a in algos], bw, label="P99", color="#C44E52")
        axes[i].set_title(f"N={n}")
        axes[i].set_xticks(x, algos, rotation=24, ha="right")
        axes[i].axhline(200, color="#777777", lw=1, ls=":")
        if i == 0:
            axes[i].set_ylabel("延迟 (ms)")
            axes[i].legend()
    fig.suptitle("不同节点规模下的分位延迟对比", y=1.02)
    fig.tight_layout()
    save(fig, "fig3_4_latency_percentiles.png", "图3-4 基准实验分位延迟对比", "基于表3-5绘制。")


def plot_p99_3d(data: dict[str, dict[int, dict[str, float]]]) -> None:
    nodes = [8, 16, 32]
    algos = ALGO_ORDER
    fig = plt.figure(figsize=(10.8, 7.4))
    ax = fig.add_subplot(111, projection="3d")

    for y, algo in enumerate(algos):
        xs = np.array(nodes)
        ys = np.full(len(nodes), y)
        zs = np.array([data[algo][n]["p99"] for n in nodes])
        ax.plot(xs, ys, zs, marker="o", ls=":", lw=2.3, color=COLORS.get(algo), label=algo)
        ax.scatter(xs, ys, zs, s=46, color=COLORS.get(algo), depthshade=True)

    ax.set_title("P99延迟-节点数-算法三维分布")
    ax.set_xlabel("节点数 N", labelpad=12)
    ax.set_ylabel("共识算法", labelpad=12)
    ax.set_zlabel("P99延迟 (ms)", labelpad=2)
    ax.set_xticks([8, 16, 24, 32])
    ax.set_yticks(range(len(algos)))
    ax.set_yticklabels(algos)
    ax.view_init(elev=23, azim=-50)
    ax.set_box_aspect((1.35, 1.0, 0.9))
    fig.subplots_adjust(left=0.04, right=0.96, bottom=0.07, top=0.91)
    ax.legend(loc="upper left", bbox_to_anchor=(0.02, 0.98))
    save(fig, "fig3_5_p99_3d_latency_distribution.png", "图3-5 P99延迟-节点数-算法三维分布", "基于表3-5绘制。", pad_inches=0.25)


def plot_degradation(rows: list[dict[str, str]]) -> None:
    algos = [row["算法"] for row in rows]
    vals = [parse_mean(row["Rdeg (%)"]) for row in rows]
    fig, ax = plt.subplots(figsize=(8.8, 4.8))
    bars = ax.bar(algos, vals, width=BAR_WIDTH_2_3, color=[COLORS.get(a, "#777777") for a in algos])
    ax.set_title("8至32节点TPS规模退化率")
    ax.set_ylabel("Rdeg (%)")
    ax.set_ylim(0, max(vals) * 1.18)
    ax.set_xticks(np.arange(len(algos)), algos, rotation=18, ha="right")
    ax.grid(False)
    for bar, val in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 1, f"{val:.1f}%", ha="center", fontsize=9)
    fig.tight_layout()
    save(fig, "fig3_6_scale_degradation.png", "图3-6 节点规模扩展退化率对比", "基于表3-6绘制。")


def plot_saturation(rows: list[dict[str, str]]) -> None:
    lambdas = [250, 500, 1000, 1500, 2000, 2500]
    fig, ax = plt.subplots(figsize=(9.2, 5.2))
    for row in rows:
        algo = row["算法\\lambda"]
        ax.plot(lambdas, [parse_mean(row[str(v)]) for v in lambdas], marker="o", ls=":", lw=2.1, label=algo, color=COLORS.get(algo))
    ax.set_title("负载强度扫描下的吞吐饱和趋势")
    ax.set_xlabel("负载强度 λ (tx/s)")
    ax.set_ylabel("TPS (tx/s)")
    ax.legend(ncol=2)
    fig.tight_layout()
    save(fig, "fig3_7_saturation_scan.png", "图3-7 共识算法吞吐饱和点扫描", "基于表3-7绘制。")


def plot_group(rows: list[dict[str, str]], comp: list[dict[str, str]]) -> None:
    ks = [int(parse_mean(row["K（分组数）"])) for row in rows]
    ms = [int(parse_mean(row["M=32/K"])) for row in rows]
    tps = [parse_mean(row["TPS (tx/s)"]) for row in rows]
    p99 = [parse_mean(row["P99 (ms)"]) for row in rows]
    measured = [parse_mean(row["实测消息数每轮"]) for row in rows]
    theoretical = [k * m * m + k * k for k, m in zip(ks, ms)]
    errors = [abs(actual - theory) / theory * 100 if theory else 0 for actual, theory in zip(measured, theoretical)]
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8))
    twin = axes[0].twinx()
    axes[0].plot(ks, tps, marker="o", ls=":", lw=2.2, color="#4E9A62", label="TPS")
    twin.plot(ks, p99, marker="s", ls=":", lw=2.2, color="#C44E52", label="P99")
    axes[0].set_title("分组数K对TPS与P99的影响")
    axes[0].set_xlabel("分组数 K")
    axes[0].set_ylabel("TPS (tx/s)")
    twin.set_ylabel("P99 (ms)")
    axes[0].set_xticks(ks)
    h1, l1 = axes[0].get_legend_handles_labels()
    h2, l2 = twin.get_legend_handles_labels()
    axes[0].legend(h1 + h2, l1 + l2)
    axes[1].plot(ks, theoretical, marker="o", ls=":", lw=2.0, label="理论消息数", color="#5B8DB8")
    axes[1].plot(ks, measured, marker="s", ls=":", lw=2.0, label="实测消息数", color="#D9802E")
    for k, err, y in zip(ks, errors, measured):
        axes[1].text(k, y + max(measured) * 0.03, f"{err:.2f}%", ha="center", fontsize=8)
    axes[1].set_title("理论消息数与实测消息数对比")
    axes[1].set_xlabel("分组数 K")
    axes[1].set_ylabel("消息数")
    axes[1].set_xticks(ks)
    axes[1].legend()
    fig.tight_layout()
    save(fig, "fig3_8_group_and_complexity_scan.png", "图3-8 分组参数扫描与复杂度验证", "基于表3-8和表3-9绘制。")


def plot_ablation(rows: list[dict[str, str]]) -> None:
    groups = [row["组别"][0] for row in rows]
    x = np.arange(len(groups))
    w = 0.36
    bw = w * 2 / 3
    fig, axes = plt.subplots(1, 2, figsize=(12.8, 4.8))
    axes[0].bar(x - w / 2, [parse_mean(r["16节点TPS"]) for r in rows], bw, label="N=16", color="#5B8DB8")
    axes[0].bar(x + w / 2, [parse_mean(r["32节点TPS"]) for r in rows], bw, label="N=32", color="#4E9A62")
    axes[0].set_title("消融配置TPS对比")
    axes[0].set_ylabel("TPS (tx/s)")
    axes[0].set_xticks(x, groups)
    axes[0].legend()
    axes[1].bar(x - w / 2, [parse_mean(r["16节点P99"]) for r in rows], bw, label="N=16", color="#F2B880")
    axes[1].bar(x + w / 2, [parse_mean(r["32节点P99"]) for r in rows], bw, label="N=32", color="#C44E52")
    axes[1].set_title("消融配置P99对比")
    axes[1].set_ylabel("P99 (ms)")
    axes[1].set_xticks(x, groups)
    axes[1].axhline(200, color="#777777", lw=1, ls=":")
    axes[1].legend()
    fig.tight_layout()
    save(fig, "fig3_9_ablation_tps_p99.png", "图3-9 消融实验TPS与P99对比", "基于表3-10绘制。")


def plot_scores(algo_rows: list[dict[str, str]], opt_rows: list[dict[str, str]]) -> None:
    labels = [r["算法配置A"] for r in algo_rows]
    scores = [parse_mean(r["综合评分S"]) for r in algo_rows]
    groups = [r["实验组"] for r in opt_rows]
    opt_scores = [parse_mean(r["综合评分S"]) for r in opt_rows]
    fig, axes = plt.subplots(1, 2, figsize=(12.8, 4.8))
    axes[0].bar(labels, scores, width=BAR_WIDTH_2_3, color=[COLORS.get(a, "#777777") for a in labels])
    axes[0].set_title("算法配置维度PB-CPBQ评分")
    axes[0].set_ylabel("综合评分 S")
    axes[0].set_ylim(0, 1.05)
    axes[0].set_xticks(np.arange(len(labels)), labels, rotation=20, ha="right")
    axes[1].bar(groups, opt_scores, width=BAR_WIDTH_2_3, color=[COLORS.get(g, "#777777") for g in groups])
    axes[1].set_title("优化组件维度PB-CPBQ评分")
    axes[1].set_ylabel("综合评分 S")
    axes[1].set_ylim(0, 1.05)
    for ax in axes:
        ax.grid(False)
        for patch in ax.patches:
            value = patch.get_height()
            ax.text(patch.get_x() + patch.get_width() / 2, value + 0.025, f"{value:.3f}", ha="center", fontsize=9)
    fig.tight_layout()
    save(fig, "fig3_10_pb_cpbq_scores.png", "图3-10 PB-CPBQ边界向量综合评分", "基于表3-19和表3-20绘制。")


def plot_tsat_fit(rows: list[dict[str, str]], raw_points: dict[str, dict[int, dict[str, list[float]]]]) -> None:
    nodes = np.array([8, 16, 32], dtype=float)
    xfit = np.linspace(8, 32, 160)
    fig, ax = plt.subplots(figsize=(9.4, 5.4))

    for row in rows:
        algo = row["算法"]
        alpha = parse_mean(pick(row, "α_A", "alpha", "截距"))
        beta = parse_mean(pick(row, "β_A", "beta", "斜率"))
        color = COLORS.get(algo, "#777777")
        ax.plot(xfit, alpha + beta * xfit, ls="-", lw=2.2, color=color, label=f"{algo} 拟合")
        for node in nodes.astype(int):
            values = raw_points.get(algo, {}).get(node, {}).get("tps", [])
            offsets = np.linspace(-0.28, 0.28, len(values)) if values else []
            ax.scatter(node + offsets, values, s=34, color=color, alpha=0.76, edgecolor="white", linewidth=0.6, zorder=3)

    ax.set_title("吞吐量饱和边界拟合")
    ax.set_xlabel("节点数 N")
    ax.set_ylabel("T_sat (tx/s)")
    ax.set_xticks([8, 16, 24, 32])
    ax.legend(ncol=2)
    fig.tight_layout()
    save(fig, "fig3_11_tsat_fit_scatter.png", "图3-11 吞吐量饱和边界拟合曲线与散点", "基于表3-17绘制。")


def plot_p99_fit(rows: list[dict[str, str]], raw_points: dict[str, dict[int, dict[str, list[float]]]]) -> None:
    nodes = np.array([8, 16, 32], dtype=float)
    xfit = np.linspace(8, 64, 220)
    fig, ax = plt.subplots(figsize=(9.4, 5.4))
    for row in rows:
        algo = row["算法"]
        alpha = parse_mean(pick(row, "alpha", "α"))
        beta = parse_mean(pick(row, "beta", "β"))
        gamma = parse_mean(pick(row, "gamma", "γ"))
        color = COLORS.get(algo, "#777777")
        yfit = alpha * xfit**2 + beta * xfit + gamma
        ax.plot(xfit, yfit, ls="-", lw=2.1, color=color, label=f"{algo} 拟合")
        for node in nodes.astype(int):
            values = raw_points.get(algo, {}).get(node, {}).get("p99", [])
            offsets = np.linspace(-0.28, 0.28, len(values)) if values else []
            ax.scatter(node + offsets, values, s=34, color=color, alpha=0.76, edgecolor="white", linewidth=0.6, zorder=3)

    ax.axhline(2000, color="#777777", lw=1.0, ls=":")
    ax.set_title("P99尾延迟退化模型拟合")
    ax.set_xlabel("节点数 N")
    ax.set_ylabel("P99 (ms)")
    ax.set_xticks([8, 16, 24, 32, 48, 64])
    ax.legend(ncol=2)
    fig.tight_layout()
    save(fig, "fig3_12_p99_fit_scatter.png", "图3-12 P99尾延迟拟合曲线与散点", "基于表3-18绘制。")


def main() -> None:
    setup_style()
    clean_outputs()
    md = SUMMARY.read_text(encoding="utf-8")
    raw_points = load_benchmark_raw_points()
    tables = {f"3-{i}": extract_table(md, f"3-{i}") for i in range(3, 21)}
    plot_load_pattern(tables["3-3"])
    plot_comet(tables["3-4"])
    bench = matrix(tables["3-5"])
    plot_benchmark(bench)
    plot_latency(bench)
    plot_p99_3d(bench)
    plot_degradation(tables["3-6"])
    plot_saturation(tables["3-7"])
    plot_group(tables["3-8"], tables["3-9"])
    plot_ablation(tables["3-10"])
    plot_scores(tables["3-19"], tables["3-20"])
    plot_tsat_fit(tables["3-15"], raw_points)
    plot_p99_fit(tables["3-16"], raw_points)


if __name__ == "__main__":
    main()
