import pytest

import nix_flake_health.main as flake_health
from nix_flake_health import compare_versions


@pytest.mark.parametrize(
    ("current", "latest", "expected"),
    [
        ("1.2", "1.2.0", "equal"),
        ("1.2.9", "1.3", "outdated"),
        ("not found", "1.3", "unknown"),
    ],
)
def test_compare_versions_classifies_package_versions(current, latest, expected):
    assert compare_versions(current, latest) == expected


def test_package_version_cache_avoids_a_second_nix_evaluation(monkeypatch, tmp_path):
    commands = []

    def run_command(command):
        commands.append(command)
        return 0, "1.2.3\n", ""

    monkeypatch.setattr(flake_health, "get_cache_dir", lambda: tmp_path)
    monkeypatch.setattr(flake_health, "run_command", run_command)

    flake_ref = "github:nixos/nixpkgs/unstable"
    input_name = "legacyPackages.x86_64-linux"
    first = flake_health.get_package_version(flake_ref, input_name, "hello", True)
    cached = flake_health.get_package_version(flake_ref, input_name, "hello", True)

    assert first == ("1.2.3", False)
    assert cached == ("1.2.3", True)
    assert len(commands) == 1
