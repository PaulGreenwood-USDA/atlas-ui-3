
import os

from modules.config.config_manager import ConfigManager


def test_search_paths_prefer_project_config_dirs():
    cm = ConfigManager()
    paths = cm._search_paths("llmconfig.yml")
    # Ensure both overrides/defaults and legacy paths are present in the list
    # Normalize paths to use forward slashes for cross-platform comparison
    str_paths = [str(p).replace(os.sep, "/") for p in paths]
    assert any("config/overrides" in s for s in str_paths)
    assert any("config/defaults" in s for s in str_paths)
    assert any("backend/configfiles" in s for s in str_paths)
