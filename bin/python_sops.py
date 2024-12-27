import os
import subprocess
from typing import Any

import yaml


def decrypt_sops_file(file_path: str) -> dict[Any, Any] | Any:
    """
    Decrypt a SOPS-encrypted YAML file using subprocess.

    Parameter:
    ----------
    file_path (str): Path to the encrypted secrets file

    Returns
    -------
    dict: Decrypted secrets

    """
    try:
        # Use subprocess to run sops decryption
        decrypted_output = subprocess.run(
            ["sops", "-d", file_path], capture_output=True, text=True, check=True
        )

        # Parse the decrypted YAML
        secrets = yaml.safe_load(decrypted_output.stdout)
        return secrets

    except subprocess.CalledProcessError as e:
        print(f"Decryption error: {e}")
        return {}
    except yaml.YAMLError as e:
        print(f"YAML parsing error: {e}")
        return {}


def get_secret(value):
    # Path to your encrypted secrets file
    secrets_path = os.path.expanduser("~/scripts/secrets.enc.yaml")

    # Decrypt secrets
    secrets = decrypt_sops_file(secrets_path)

    # Access specific secrets
    return secrets.get(value)
