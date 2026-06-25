from __future__ import annotations

from typing import Iterable, Sequence


def indent_block(text: str, levels: int = 1) -> str:
    pad = "    " * levels
    return "\n".join(pad + line if line.strip() else line for line in text.splitlines())


def fmt_vec3f(x: float, y: float, z: float) -> str:
    return f"({x:g}, {y:g}, {z:g})"


def fmt_points(points: Sequence[tuple[float, float, float]]) -> str:
    inner = ", ".join(fmt_vec3f(*p) for p in points)
    return f"[{inner}]"


def fmt_widths(widths: Sequence[float]) -> str:
    inner = ", ".join(f"{w:g}" for w in widths)
    return f"[{inner}]"


def join_lines(parts: Iterable[str]) -> str:
    return "\n\n".join(p for p in parts if p)
