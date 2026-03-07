from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def _load_package(package_name: str, package_root: Path) -> None:
    if package_name in sys.modules:
        return

    package_init = package_root / "__init__.py"
    spec = importlib.util.spec_from_file_location(
        package_name,
        package_init,
        submodule_search_locations=[str(package_root)],
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not create spec for {package_name} from {package_init}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[package_name] = module
    spec.loader.exec_module(module)


def _discover_packages() -> list[tuple[str, Path]]:
    packages: list[tuple[str, Path]] = []

    for project_dir in sorted(ROOT.iterdir()):
        if not project_dir.is_dir() or project_dir.name.startswith("."):
            continue

        if not (project_dir / "pyproject.toml").is_file():
            continue

        src_dir = project_dir / "src"
        if not src_dir.is_dir():
            continue

        for package_init in sorted(src_dir.glob("*/__init__.py")):
            packages.append((package_init.parent.name, package_init.parent))

    return packages


for package_name, package_root in _discover_packages():
    _load_package(package_name, package_root)
