import logging
from pathlib import Path
from typing import List

import yaml


def run() -> dict:
    data = {"artifact_produced": False}
    # Determine if GitHub Actions workflow files produce Veracode
    # artifacts.
    for workflow_file in _get_workflow_files():
        if _workflow_has_veracode_artifact(workflow_file):
            data["artifact_produced"] = True
            break
    return data


def _get_workflow_files() -> List[Path]:
    """
    Get a list of paths of GitHub Actions workflow files.

    Workflows are always defined in the `.github/workflows` directory in a
    repository. A repository can have multiple workflows.
    """
    path = ".github/workflows"
    try:
        return [f for f in Path(path).iterdir() if f.is_file()]
    except FileNotFoundError:
        return []


def _workflow_has_veracode_artifact(path: Path) -> bool:
    """
    Whether the workflow file produces a Veracode artifact.

    Workflow files that produce a Veracode artifact leverage
    Workiva/gha-store-artifacts to upload artifacts to Workiva Build.

    Example:

      ...
      steps:
        - name: Upload Veracode Artifact
          uses: Workiva/gha-store-artifacts@v1.0.0
          with:
            VERACODE: /path/to/artifact
    """

    def contains_key(data: dict, key: str) -> bool:
        """
        Determine if a dict (data) contains a key (key).
        """
        if isinstance(data, dict):
            if key in data:
                return True
            return any(contains_key(v, key) for v in data.values())
        elif isinstance(data, list):
            return any(contains_key(i, key) for i in data)
        return False

    try:
        with open(path, "r") as file:
            data = yaml.safe_load(file)
            return contains_key(data, "VERACODE")
    except yaml.YAMLError as ex:
        logging.warning(f"Error parsing the YAML file: {ex}")
        return False
