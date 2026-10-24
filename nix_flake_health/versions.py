"""Compare nixpkgs package versions."""

import re


def _parse_version(version_str: str) -> tuple[list[int], str]:
    """Split a version into its numeric prefix and remaining suffix."""
    match = re.match(r"^(\d+(?:\.\d+)*)", version_str)
    if match:
        numeric_part = match.group(1)
        numeric_parts = [int(part) for part in numeric_part.split(".")]
        return numeric_parts, version_str[len(numeric_part) :]

    return [], version_str


def compare_versions(current: str, latest: str) -> str:
    """Return ``equal``, ``outdated``, or ``unknown`` for two versions."""
    if current == "not found" or latest == "not found":
        return "unknown"

    if current == latest:
        return "equal"

    try:
        current_parts, current_suffix = _parse_version(current)
        latest_parts, latest_suffix = _parse_version(latest)

        if current_parts and latest_parts:
            max_len = max(len(current_parts), len(latest_parts))
            current_parts += [0] * (max_len - len(current_parts))
            latest_parts += [0] * (max_len - len(latest_parts))

            for current_part, latest_part in zip(current_parts, latest_parts, strict=True):
                if current_part < latest_part:
                    return "outdated"
                if current_part > latest_part:
                    return "equal"

            if current_suffix != latest_suffix:
                return "outdated"

            return "equal"
    except Exception:
        pass

    return "outdated"
