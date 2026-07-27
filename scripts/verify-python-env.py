#!/usr/bin/env python3
"""Verify that the active interpreter exactly matches the pinned environment."""

from __future__ import annotations

import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

try:
    from packaging.requirements import InvalidRequirement, Requirement
    from packaging.utils import canonicalize_name
except ImportError:
    print(
        "[ERROR] Falta 'packaging'; repare el entorno con ./meiga-school install.",
        file=sys.stderr,
    )
    raise SystemExit(1)


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
        try:
            requirement = Requirement(line)
        except InvalidRequirement as error:
            raise SystemExit(
                f"[ERROR] {REQUIREMENTS}:{number}: requisito inválido: {error}"
            ) from error
        if requirement.marker and not requirement.marker.evaluate():
            continue
        specifiers = list(requirement.specifier)
        if len(specifiers) != 1 or specifiers[0].operator != "==":
            raise SystemExit(
                f"[ERROR] {REQUIREMENTS}:{number}: la dependencia no está fijada: {line}"
            )
        name = canonicalize_name(requirement.name)
        if name in pinned:
            raise SystemExit(
                f"[ERROR] {REQUIREMENTS}:{number}: requisito activo duplicado: {name}"
            )
        pinned[name] = specifiers[0].version
    return pinned


def main() -> int:
    if not (sys.version_info >= (3, 10) and sys.version_info < (3, 15)):
        print(
            f"[ERROR] Se requiere Python 3.10-3.14; encontrado {sys.version.split()[0]}",
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
