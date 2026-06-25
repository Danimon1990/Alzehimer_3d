"""Thin wrapper layers for study metadata (healthy vs Alzheimer's) over the network scene."""

from __future__ import annotations

import argparse
from pathlib import Path


def emit_condition_layer(*, network_layer: str, condition: str, note: str) -> str:
    """Sublayer the packaged network and stamp `NeuralNetwork.customData`."""
    return f'''#usda 1.0
(
    doc = """{note}"""
    defaultPrim = "NeuralNetwork"
    metersPerUnit = 0.01
    upAxis = "Y"
    subLayers = [
        @{network_layer}@
    ]
)

over "NeuralNetwork" (
    customData = {{
        string disease_state = "{condition}"
        string study = "healthy_vs_alz"
    }}
)
{{
}}
'''


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "condition",
        choices=("healthy", "alzheimers"),
    )
    p.add_argument(
        "--network-layer",
        default="./Network.usda",
        help="Which network USDA to sublayer (default: monolithic output/Network.usda)",
    )
    p.add_argument("--out-dir", type=Path, default=Path("output"))
    p.add_argument("--force", action="store_true")
    args = p.parse_args(argv)

    note = (
        "Healthy control — metadata overlay for comparative rendering."
        if args.condition == "healthy"
        else "Alzheimer's model context — metadata overlay (visual overrides use separate layers)."
    )
    name = f"condition_{args.condition}.usda"
    out = args.out_dir / name
    if out.exists() and not args.force:
        raise SystemExit(f"Refusing to overwrite {out} (pass --force).")

    text = emit_condition_layer(
        network_layer=args.network_layer,
        condition=args.condition,
        note=note,
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
