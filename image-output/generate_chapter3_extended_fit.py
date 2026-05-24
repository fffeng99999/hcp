#!/usr/bin/env python3
"""Draw Section 3.7 extended-fit figures without touching existing outputs."""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = ROOT / "hcp-lab" / "experiments" / "exp7_extended_fit" / "report"
SUMMARY_PATH = REPORT_DIR / "summary.json"
FIT_PATH = REPORT_DIR / "fit_summary.json"
OUT_DIR = Path(__file__).resolve().parent / "chapter3_extended_fit"

NODES = [8, 16, 24, 32, 40, 48, 56, 64, 72, 80, 88, 96]
ALGO_ORDER = ["PBFT", "HotStuff", "Raft", "CometBFT-light", "tPBFT"]
LABELS = {
    "pbft": "PBFT",
    "hotstuff": "HotStuff",
    "raft": "Raft",
    "cometbft-light": "CometBFT-light",
    "tpbft": "tPBFT",
}
KEYS = {label: key for key, label in LABELS.items()}
COLORS = {
    "PBFT": "#3B6EA8",
    "HotStuff": "#D9802E",
    "Raft": "#4E9A62",
    "CometBFT-light": "#9B5B50",
    "tPBFT": "#C44E52",
}


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
            "legend.frameon": False,
        }
    )


def load_inputs() -> tuple[dict, dict]:
    if not SUMMARY_PATH.exists():
        raise FileNotFoundError(f"missing extended summary: {SUMMARY_PATH}")
    if not FIT_PATH.exists():
        raise FileNotFoundError(f"missing extended fit summary: {FIT_PATH}")
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    fits = json.loads(FIT_PATH.read_text(encoding="utf-8"))
    return summary, fits


def raw_metric_values(summary: dict, engine: str, node: int, metric: str) -> list[float]:
    values: list[float] = []
    for item in summary[engine][str(node)].get("raw", []):
        value = item.get("metrics", {}).get(metric)
        if value is not None:
            values.append(float(value))
    return values


def write_points_csv(summary: dict) -> None:
    path = OUT_DIR / "extended_fit_raw_points.csv"
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["algorithm", "engine", "N", "repeat", "TPS(tx/s)", "P99(ms)", "success_rate"])
        for label in ALGO_ORDER:
            engine = KEYS[label]
            for node in NODES:
                for i, item in enumerate(summary[engine][str(node)].get("raw", []), start=1):
                    metrics = item.get("metrics", {})
                    writer.writerow(
                        [
                            label,
                            engine,
                            node,
                            i,
                            f"{float(metrics.get('tps', 0.0)):.6f}",
                            f"{float(metrics.get('p99_ms', 0.0)):.6f}",
                            f"{float(metrics.get('success_rate', 0.0)):.6f}",
                        ]
                    )


def write_fit_summary(fits: dict) -> None:
    path = OUT_DIR / "extended_fit_summary_used.json"
    path.write_text(json.dumps(fits, ensure_ascii=False, indent=2), encoding="utf-8")


def save(fig: plt.Figure, name: str) -> None:
    path = OUT_DIR / name
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"created {path}")


def scatter_raw(ax: plt.Axes, summary: dict, label: str, metric: str, color: str) -> None:
    engine = KEYS[label]
    for node in NODES:
        values = raw_metric_values(summary, engine, node, metric)
        if not values:
            continue
        offsets = np.linspace(-1.35, 1.35, len(values))
        ax.scatter(
            node + offsets,
            values,
            s=22,
            color=color,
            alpha=0.58,
            edgecolor="white",
            linewidth=0.35,
            zorder=3,
        )


def plot_tsat_fit(summary: dict, fits: dict) -> None:
    xfit = np.linspace(min(NODES), max(NODES), 400)
    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    for label in ALGO_ORDER:
        engine = KEYS[label]
        color = COLORS[label]
        fit = fits["throughput"][engine]
        yfit = fit["intercept"] + fit["slope"] * xfit
        ax.plot(xfit, yfit, ls="-", lw=2.2, color=color, label=f"{label} 拟合")
        scatter_raw(ax, summary, label, "tps", color)

    ax.set_title("扩展实验吞吐量饱和边界拟合")
    ax.set_xlabel("节点数 N")
    ax.set_ylabel("T_sat (tx/s)")
    ax.set_xticks(NODES)
    ax.set_xlim(min(NODES) - 4, max(NODES) + 4)
    ax.set_ylim(bottom=0)
    ax.legend(ncol=2)
    fig.tight_layout()
    save(fig, "fig3_11_extended_tsat_fit_scatter.png")


def p99_limit_n(fit: dict, limit: float = 2000.0) -> float | None:
    a = float(fit["alpha"])
    b = float(fit["beta"])
    c = float(fit["gamma"]) - limit
    if abs(a) < 1e-12:
        if abs(b) < 1e-12:
            return None
        root = -c / b
        return root if root > 0 else None
    disc = b * b - 4 * a * c
    if disc < 0:
        return None
    roots = [(-b + math.sqrt(disc)) / (2 * a), (-b - math.sqrt(disc)) / (2 * a)]
    positive = [root for root in roots if root > 0]
    return min(positive) if positive else None


def plot_p99_fit(summary: dict, fits: dict) -> None:
    x_max = max(
        110.0,
        max((p99_limit_n(fit) or 0.0) for fit in fits["p99"].values()) + 8.0,
    )
    xfit = np.linspace(min(NODES), x_max, 500)
    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    for label in ALGO_ORDER:
        engine = KEYS[label]
        color = COLORS[label]
        fit = fits["p99"][engine]
        yfit = fit["alpha"] * xfit**2 + fit["beta"] * xfit + fit["gamma"]
        ax.plot(xfit, yfit, ls="-", lw=2.2, color=color, label=f"{label} 拟合")
        scatter_raw(ax, summary, label, "p99_ms", color)

    ax.axhline(2000, color="#777777", lw=1.1, ls=":", label="P99=2000ms")
    ax.set_title("扩展实验P99尾延迟退化模型拟合")
    ax.set_xlabel("节点数 N")
    ax.set_ylabel("P99 (ms)")
    ax.set_xticks(NODES + [112, 128, 144])
    ax.set_xlim(min(NODES) - 4, x_max)
    ax.set_ylim(bottom=0)
    ax.legend(ncol=2)
    fig.tight_layout()
    save(fig, "fig3_12_extended_p99_fit_scatter.png")


def write_manifest() -> None:
    path = OUT_DIR / "README.md"
    path.write_text(
        "\n".join(
            [
                "# Chapter 3.7 Extended Fit Figures",
                "",
                "Source: hcp-lab/experiments/exp7_extended_fit/report/summary.json",
                "",
                "Generated files:",
                "- fig3_11_extended_tsat_fit_scatter.png",
                "- fig3_12_extended_p99_fit_scatter.png",
                "- extended_fit_raw_points.csv",
                "- extended_fit_summary_used.json",
                "",
                "This directory is separate from hcp/image-output/chapter3 and does not overwrite original figures or data.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    setup_style()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summary, fits = load_inputs()
    write_points_csv(summary)
    write_fit_summary(fits)
    write_manifest()
    plot_tsat_fit(summary, fits)
    plot_p99_fit(summary, fits)


if __name__ == "__main__":
    main()
