import json
from dataclasses import dataclass, field
from typing import Dict, List, Any

@dataclass
class ExperimentPoint:
    params: Dict[str, Any]
    metrics: Dict[str, float]

@dataclass
class ExperimentResult:
    name: str
    description: str
    points: List[ExperimentPoint]
    metadata: Dict[str, Any] = field(default_factory=dict)

def write_json(path: str, result: ExperimentResult) -> None:
    data = {
        "name": result.name,
        "description": result.description,
        "points": [
            {
                "params": p.params,
                "metrics": p.metrics
            }
            for p in result.points
        ],
        "metadata": result.metadata
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def render_table(headers: List[str], rows: List[List[str]]) -> str:
    # Simple markdown table renderer
    header_line = "| " + " | ".join(headers) + " |"
    sep_line = "| " + " | ".join(["---"] * len(headers)) + " |"
    lines = [header_line, sep_line]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)

def format_float(val: float, precision: int = 2) -> str:
    return f"{val:.{precision}f}"
