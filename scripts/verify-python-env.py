#!/usr/bin/env python3
"""Verify that the active interpreter exactly matches the pinned environment."""

from __future__ import annotations

import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = ROOT / "analysis" / "requirements.txt"


def pinned_requirements() -> dict[str, str]:
    pinned: dict[str, str] = {}
    for number, raw_line in enumerate(
        REQUIREMENTS.read_text(encoding="utf-8").splitlines(), start=1
    ):
        line = raw_line.partition("#")[0].strip()
        if not line:
            continue
        if "==" not in line:
            raise SystemExit(
                f"[ERROR] {REQUIREMENTS}:{number}: la dependencia no está fijada: {line}"
            )
        name, expected = (part.strip() for part in line.split("==", maxsplit=1))
        if not name or not expected:
            raise SystemExit(
                f"[ERROR] {REQUIREMENTS}:{number}: requisito inválido: {line}"
            )
        pinned[name.casefold()] = expected
    return pinned


def main() -> int:
    if sys.version_info < (3, 10):
        print(
            f"[ERROR] Se requiere Python >= 3.10; encontrado {sys.version.split()[0]}",
            file=sys.stderr,
        )
        return 1

    mismatches: list[str] = []
    for name, expected in pinned_requirements().items():
        try:
            installed = version(name)
        except PackageNotFoundError:
            mismatches.append(f"{name}: falta (esperada {expected})")
            continue
        if installed != expected:
            mismatches.append(f"{name}: {installed} (esperada {expected})")

    if mismatches:
        print("[ERROR] El entorno Python no coincide con analysis/requirements.txt:", file=sys.stderr)
        for mismatch in mismatches:
            print(f"        - {mismatch}", file=sys.stderr)
        return 1

    import matplotlib
    import numpy

    print(
        f"[OK] Python {sys.version.split()[0]}; "
        f"NumPy {numpy.__version__}; Matplotlib {matplotlib.__version__}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
