#!/usr/bin/env python3
"""Pruebas deterministas del preparador y analizador del flujo WCD."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "analysis" / "wcd" / "analyze_wcd.py"
SPEC = importlib.util.spec_from_file_location("analyze_wcd", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class FluxTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        source = (
            ROOT
            / "experiments"
            / "wcd"
            / "flux-30s"
            / "input"
            / "bga_30s.shw"
        )
        cls.headers, cls.particles = MODULE.read_flux(source)

    def test_complete_flux_composition(self) -> None:
        self.assertEqual(len(self.particles), 34258)
        self.assertEqual(
            Counter(p.component for p in self.particles),
            {
                "electromagnetic": 26436,
                "muonic": 6849,
                "hadronic": 973,
            },
        )

    def test_smoke_sample_is_stratified(self) -> None:
        sample = MODULE.stratified_sample(self.particles, 30)
        self.assertEqual(len(sample), 30)
        self.assertEqual(
            Counter(p.component for p in sample),
            {"electromagnetic": 10, "muonic": 10, "hadronic": 10},
        )

    def test_particle_mapping(self) -> None:
        self.assertEqual(MODULE.particle_info(1), (22, "gamma", "electromagnetic"))
        self.assertEqual(MODULE.particle_info(6), (13, "mu-", "muonic"))
        self.assertEqual(MODULE.particle_info(14), (2212, "p", "hadronic"))

    def test_five_minute_flux_checksum(self) -> None:
        source = (
            ROOT
            / "experiments"
            / "wcd"
            / "bariloche-5min"
            / "input"
            / "bariloche_5min.shw"
        )
        self.assertEqual(
            MODULE.sha256(source),
            "db4f9e09a2b43898faffc7fea3446cba072777ff3cf9bb6ebe79296da56ced66",
        )

    def test_public_component_labels_are_english(self) -> None:
        self.assertEqual(MODULE.COMPONENT_LABEL["electromagnetic"], "Electromagnetic")
        self.assertEqual(MODULE.COMPONENT_LABEL["muonic"], "Muonic")
        self.assertEqual(MODULE.COMPONENT_LABEL["hadronic"], "Hadronic")

    def test_timing_features(self) -> None:
        timing = MODULE.event_timing([12.0, 10.0, 11.0, 20.0])
        self.assertEqual(timing["n_times"], 4)
        self.assertEqual(timing["time_first_ns"], 10.0)
        self.assertAlmostEqual(timing["time_t50_ns"], 1.5)
        self.assertAlmostEqual(timing["late_fraction_50ns"], 0.0)

    def test_only_main_scenario_enables_visualization(self) -> None:
        main = MODULE.make_meiga_config(123, create_visualization=True)
        component = MODULE.make_meiga_config(124, create_visualization=False)
        self.assertTrue(main["Simulation"]["GeoVisOn"])
        self.assertFalse(component["Simulation"]["GeoVisOn"])
        self.assertFalse(main["Simulation"]["TrajVisOn"])
        self.assertEqual(main["Simulation"]["RenderFile"], "VRML2FILE")


if __name__ == "__main__":
    unittest.main()
