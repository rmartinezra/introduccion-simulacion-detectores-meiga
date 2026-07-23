#!/usr/bin/env python3
"""Checks for the portable installation and user-facing quick start."""

from __future__ import annotations

import hashlib
import subprocess
import tarfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class InstallationTests(unittest.TestCase):
    def test_public_shell_scripts_have_valid_bash_syntax(self) -> None:
        scripts = [
            ROOT / "meiga-school",
            ROOT / "scripts" / "install.sh",
            ROOT / "scripts" / "setup-python.sh",
            ROOT / "scripts" / "check-requirements.sh",
            ROOT / "scripts" / "run-wcd-campaign.sh",
            ROOT / "container" / "install-meiga-school.sh",
            ROOT
            / "external-apps"
            / "g4gro"
            / "integration"
            / "install-g4gro.sh",
        ]
        for script in scripts:
            with self.subTest(script=script.name):
                subprocess.run(["bash", "-n", str(script)], check=True)

    def test_cli_help_starts_with_install_and_wcd(self) -> None:
        result = subprocess.run(
            ["bash", str(ROOT / "meiga-school"), "help"],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("./meiga-school install", result.stdout)
        self.assertIn("./meiga-school run wcd-30s --smoke 60", result.stdout)

    def test_readme_quick_start_is_near_the_top(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        first_lines = "\n".join(
            readme.splitlines()[:65]
        )
        install_position = first_lines.index("./meiga-school install")
        run_position = first_lines.index("./meiga-school run wcd-30s --smoke 60")
        self.assertLess(install_position, run_position)
        self.assertIn("results/runs/<run-id>/", readme)

    def test_readme_explains_docker_for_first_time_students(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        expected_explanations = (
            "nunca ha utilizado Docker",
            "Imagen Docker",
            "Contenedor",
            "docker info",
            "No necesita una cuenta de Docker Hub",
            "./meiga-school install --pull",
            "--force-build",
            "¿Reconstruir la imagen Docker?",
        )
        for explanation in expected_explanations:
            with self.subTest(explanation=explanation):
                self.assertIn(explanation, readme)

    def test_readme_result_gallery_assets_exist(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        gallery = ROOT / "docs" / "images" / "wcd"
        expected = (
            "wcd_flux_composition.png",
            "wcd_energy_vs_charge.png",
            "wcd_time_response.png",
        )
        for filename in expected:
            with self.subTest(filename=filename):
                image = gallery / filename
                self.assertTrue(image.is_file())
                self.assertGreater(image.stat().st_size, 50_000)
                self.assertIn(f"docs/images/wcd/{filename}", readme)

    def test_dockerfile_is_standalone_and_stays_running(self) -> None:
        dockerfile = (ROOT / "container" / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("FROM ubuntu:22.04", dockerfile)
        self.assertNotIn("FROM ${BASE_IMAGE}", dockerfile)
        self.assertNotIn("meiga_school:3.0", dockerfile)
        self.assertIn("nlohmann-json3-dev", dockerfile)
        self.assertIn('CMD ["sleep", "infinity"]', dockerfile)

    def test_applications_use_a_compatible_serial_run_manager(self) -> None:
        school_installer = (
            ROOT / "container" / "install-meiga-school.sh"
        ).read_text(encoding="utf-8")
        g4gro_patch = (
            ROOT
            / "external-apps"
            / "g4gro"
            / "integration"
            / "meiga-isolation.patch"
        ).read_text(encoding="utf-8")
        serial_factory = (
            "G4RunManagerFactory::CreateRunManager(G4RunManagerType::Serial)"
        )
        self.assertIn(serial_factory, school_installer)
        self.assertIn(serial_factory, g4gro_patch)

    def test_meiga_source_snapshot_is_clean_and_verified(self) -> None:
        archive = ROOT / "container" / "meiga-school-source.tar.gz"
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        self.assertEqual(
            digest,
            "bb36423c377e2fffe604c693df4ce8849d0455ec498691f39ed1c1342d7367b2",
        )
        with tarfile.open(archive, "r:gz") as source:
            names = source.getnames()
        self.assertTrue(
            any(name.endswith("Applications/G4WCDSimulator/G4WCDSimulator.cc") for name in names)
        )
        self.assertFalse(any("/.git/" in f"/{name}/" for name in names))
        self.assertFalse(any(name.startswith("./cmake/") for name in names))
        self.assertFalse(any(name.endswith((".pyc", ".wrl", ".log")) for name in names))

    def test_installer_does_not_delete_existing_docker_resources(self) -> None:
        installer = (ROOT / "scripts" / "install.sh").read_text(encoding="utf-8")
        forbidden = ("docker rm", "docker container rm", "docker image rm", "docker rmi")
        for command in forbidden:
            with self.subTest(command=command):
                self.assertNotIn(command, installer)
        self.assertIn("docker create", installer)

    def test_campaign_runner_uses_project_virtualenv(self) -> None:
        runner = (ROOT / "scripts" / "run-wcd-campaign.sh").read_text(
            encoding="utf-8"
        )
        self.assertIn('.venv/bin/python', runner)
        self.assertIn('"$PYTHON" "$ANALYZER" prepare', runner)
        self.assertIn('"$PYTHON" "$ANALYZER" analyze', runner)
        self.assertIn("varios WRL con contenidos diferentes", runner)
        self.assertIn('mv -- "$visualization_source"', runner)


if __name__ == "__main__":
    unittest.main()
