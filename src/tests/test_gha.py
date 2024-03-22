import unittest
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import yaml

from .. import gha


class TestRun(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.mock_get_workflow_files = patch.object(gha, "_get_workflow_files").start()
        self.mock_workflow_has_veracode_artifact = patch.object(
            gha, "_workflow_has_veracode_artifact"
        ).start()

    def tearDown(self):
        self.addCleanup(patch.stopall)

    def test_no_workflow_files(self):
        self.mock_get_workflow_files.return_value = []
        ret = gha.run()
        self.assertEqual(ret, {"artifact_produced": False})

    def test_no_veracode_artifacts(self):
        self.mock_get_workflow_files.return_value = ["file-1.yaml", "file-2.yaml"]
        self.mock_workflow_has_veracode_artifact.side_effect = [False, False]
        ret = gha.run()
        self.assertEqual(ret, {"artifact_produced": False})

    def test_has_veracode_artifact(self):
        self.mock_get_workflow_files.return_value = ["file-1.yaml", "file-2.yaml"]
        self.mock_workflow_has_veracode_artifact.side_effect = [False, True]
        ret = gha.run()
        self.assertEqual(ret, {"artifact_produced": True})


class TestGetWorkflowFiles(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.mock_iterdir = patch.object(Path, "iterdir").start()

    def tearDown(self):
        self.addCleanup(patch.stopall)

    def test_empty_directory(self):
        """
        Test `.github/workflows` exists, but is empty.
        """
        self.mock_iterdir.return_value = []
        ret = gha._get_workflow_files()
        self.assertEqual(ret, [])

    def test_directory_with_files(self):
        """
        Test `.github/workflows` exists and is not empty.
        """
        mock_file = Mock(spec=Path)
        mock_file.is_file.return_value = True
        self.mock_iterdir.return_value = [mock_file, mock_file]
        ret = gha._get_workflow_files()
        self.assertEqual(len(ret), 2)

    def test_directory_with_files_and_subdirectories(self):
        """
        Test `.github/workflows` exists and is not empty.

        Only return files, not directories.
        """
        mock_file = Mock(spec=Path)
        mock_file.is_file.return_value = True
        mock_directory = Mock(spec=Path)
        mock_directory.is_file.return_value = False
        self.mock_iterdir.return_value = [mock_file, mock_directory, mock_file]
        result = gha._get_workflow_files()
        self.assertEqual(len(result), 2)

    def test_directory_not_exist(self):
        """
        Test `.github/workflows` does not exist.

        Handle exception (FileNotFoundError) and return empty list.
        """
        self.mock_iterdir.side_effect = FileNotFoundError
        ret = gha._get_workflow_files()
        self.assertEqual(ret, [])


class TestWorkflowHasVeracodeArtifact(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.mock_logging = patch.object(gha, "logging").start()

    def tearDown(self):
        self.addCleanup(patch.stopall)

    def test_has_no_veracode_artifact(self):
        read_data = """
steps:
  - name: Some Step
    uses: some-action@v1
        """
        with patch("builtins.open", mock_open(read_data=read_data)):
            path = Path("ci.yaml")
            self.assertFalse(gha._workflow_has_veracode_artifact(path))

    def test_has_veracode_artifact(self):
        read_data = """
steps:
  - name: Upload Veracode Artifact
    uses: Workiva/gha-store-artifacts@v1.0.0
    with:
      VERACODE: /path/to/artifact
        """
        with patch("builtins.open", mock_open(read_data=read_data)):
            path = Path("ci.yaml")
            self.assertTrue(gha._workflow_has_veracode_artifact(path))

    def test_invalid_yaml(self):
        patch.object(yaml, "safe_load", side_effect=yaml.YAMLError()).start()
        read_data = """
Not a valid YAML
        """
        with patch("builtins.open", mock_open(read_data=read_data)):
            path = Path("ci.yaml")
            self.assertFalse(gha._workflow_has_veracode_artifact(path))
            self.mock_logging.warning.assert_called
