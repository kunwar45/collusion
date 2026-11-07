"""H12: token and cost accounting from Inspect's per-model usage stats."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from collusion_eval.paths import configs_dir


def load_prices(path: str | Path | None = None) -> dict[str, dict[str, float]]:
    """USD per million tokens: {model: {input: x, output: y}}. Unknown models cost NaN."""
    p = Path(path) if path else configs_dir() / "prices.yaml"
    if not p.exists():
        return {}
    return (yaml.safe_load(p.read_text()) or {}).get("models", {})


def base_model(name: str) -> str:
    return name.removeprefix("workplace/")


def usage_rows(
    model_usage: dict[str, Any], prices: dict[str, dict[str, float]]
) -> list[dict[str, Any]]:
    rows = []
    for model, u in (model_usage or {}).items():
        inp = getattr(u, "input_tokens", 0) or 0
        out = getattr(u, "output_tokens", 0) or 0
        price = prices.get(base_model(model))
        cost = (inp * price["input"] + out * price["output"]) / 1e6 if price else float("nan")
        rows.append(
            {
                "model": base_model(model),
                "input_tokens": inp,
                "output_tokens": out,
                "total_tokens": getattr(u, "total_tokens", inp + out) or inp + out,
                "cost_usd": cost,
            }
        )
    return rows
