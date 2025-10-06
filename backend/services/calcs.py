from __future__ import annotations

import math
import re
from typing import Dict, Optional, Tuple

from sympy import Eq, Symbol, solve


_NUM_RE = re.compile(r"([a-zA-Z]+)\s*[=:]\s*([\-+]?\d+(?:\.\d+)?(?:e[\-+]?\d+)?)\s*([a-zA-Z^/\d]*)")


def _to_float(value: str) -> float:
    try:
        return float(value)
    except Exception:
        return float("nan")


def _unit_to_si(value: float, unit: str) -> Tuple[float, str]:
    u = unit.strip()
    # Pressure
    if u.lower() in {"pa"}:
        return value, "Pa"
    if u.lower() in {"kpa"}:
        return value * 1e3, "Pa"
    if u.lower() in {"mpa"}:
        return value * 1e6, "Pa"
    # Area
    if u.lower() in {"m2", "m^2"}:
        return value, "m^2"
    if u.lower() in {"cm2", "cm^2"}:
        return value * 1e-4, "m^2"
    if u.lower() in {"mm2", "mm^2"}:
        return value * 1e-6, "m^2"
    # Force
    if u.lower() in {"n"}:
        return value, "N"
    # Length
    if u.lower() in {"m"}:
        return value, "m"
    if u.lower() in {"cm"}:
        return value * 1e-2, "m"
    if u.lower() in {"mm"}:
        return value * 1e-3, "m"
    # Flow
    if u.lower() in {"m3/s", "m^3/s"}:
        return value, "m3/s"
    if u.lower() in {"l/s", "L/s"}:
        return value * 1e-3, "m3/s"
    if u.lower() in {"l/min", "L/min"}:
        return value * (1e-3 / 60.0), "m3/s"
    return value, u


def _parse_assignments(text: str) -> Dict[str, Tuple[float, str]]:
    vars_si: Dict[str, Tuple[float, str]] = {}
    for name, num, unit in _NUM_RE.findall(text):
        name_u = name.strip().lower()
        val = _to_float(num)
        val_si, unit_si = _unit_to_si(val, unit)
        vars_si[name_u] = (val_si, unit_si)
    return vars_si


def _format_value(val: float, unit: str) -> str:
    if math.isnan(val):
        return "-"
    if abs(val) >= 1e3 or (0 < abs(val) < 1e-3):
        return f"{val:.3e} {unit}".strip()
    return f"{val:.4g} {unit}".strip()


def _compute_pressure_force_area(vars_si: Dict[str, Tuple[float, str]]) -> Optional[str]:
    # P = F / A
    P = Symbol("P")
    F = Symbol("F")
    A = Symbol("A")

    given = {k: v for k, v in vars_si.items() if k in {"p", "f", "a"}}
    if len(given) < 2:
        return None

    P_val = given.get("p", (math.nan, "Pa"))[0]
    F_val = given.get("f", (math.nan, "N"))[0]
    A_val = given.get("a", (math.nan, "m^2"))[0]

    if math.isnan(P_val):
        sol = solve(Eq(P, F / A), P, dict=True)[0]
        P_val = sol[P].subs({F: F_val, A: A_val})
        return (
            "Given F and A, pressure P is computed as P = F/A.\n"
            f"P = {_format_value(float(P_val), 'Pa')}"
        )
    if math.isnan(F_val):
        sol = solve(Eq(P, F / A), F, dict=True)[0]
        F_val = sol[F].subs({P: P_val, A: A_val})
        return (
            "Given P and A, force F is computed as F = P*A.\n"
            f"F = {_format_value(float(F_val), 'N')}"
        )
    if math.isnan(A_val):
        sol = solve(Eq(P, F / A), A, dict=True)[0]
        A_val = sol[A].subs({P: P_val, F: F_val})
        return (
            "Given P and F, area A is computed as A = F/P.\n"
            f"A = {_format_value(float(A_val), 'm^2')}"
        )
    return None


def _compute_diameter_from_flow(vars_si: Dict[str, Tuple[float, str]]) -> Optional[str]:
    # From continuity: Q = v * A, A = pi d^2 / 4 -> d = sqrt(4Q/(pi v))
    given = {k: v for k, v in vars_si.items() if k in {"q", "v"}}
    if "q" not in given:
        return None
    Q = given["q"][0]  # m3/s
    v = given.get("v", (1.0, "m/s"))[0]  # default 1 m/s if unspecified
    if Q <= 0 or v <= 0:
        return None
    d = math.sqrt(4.0 * Q / (math.pi * v))
    return (
        "Using continuity (Q = v*A) with A = π d^2/4 and default v=1 m/s if absent.\n"
        f"d = {_format_value(d, 'm')}"
    )


def try_compute(question: str) -> Optional[str]:
    """Attempt simple physics computations from free-text assignments.

    Recognized patterns include:
    - P, F, A with units (e.g., P=100kPa, A=10 cm^2)
    - Q and v for pipe sizing (e.g., Q=2 L/s, v=1 m/s)
    """
    text = question.strip()
    if not text:
        return None

    vars_si = _parse_assignments(text)

    # Priority: direct formula completions first
    out = _compute_pressure_force_area(vars_si)
    if out:
        return out

    out = _compute_diameter_from_flow(vars_si)
    if out:
        return out

    return None
