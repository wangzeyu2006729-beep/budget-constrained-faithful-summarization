"""Backward-compat shim — canonical location: assets/loader.py"""
from assets.loader import *  # noqa: F401,F403
from assets.loader import (  # explicit re-exports for static analysis
    ASSETS_ENV_VAR,
    DEFAULT_ASSETS_ROOT,
    LOCAL_CONFIG_FILE,
    PROJECT_ROOT,
    ensure_asset_repo_on_sys_path,
    ensure_path_on_sys_path,
    get_asset_dir,
    get_assets_root,
    require_asset_dir,
)
