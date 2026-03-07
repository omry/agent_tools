from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def _load_package(package_name: str, package_root: Path) -> None:
    existing = sys.modules.get(package_name)
    expected_init = (package_root / "__init__.py").resolve()
    if existing is not None:
        existing_file = getattr(existing, "__file__", None)
        existing_paths = [Path(path).resolve() for path in getattr(existing, "__path__", [])]
        if (
            existing_file is not None
            and Path(existing_file).resolve() == expected_init
        ) or package_root.resolve() in existing_paths:
            return

        for module_name in list(sys.modules):
            if module_name == package_name or module_name.startswith(f"{package_name}."):
                del sys.modules[module_name]

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


def _discover_src_dirs() -> list[Path]:
    src_dirs: list[Path] = []

    for project_dir in sorted(ROOT.iterdir()):
        if not project_dir.is_dir() or project_dir.name.startswith("."):
            continue

        if not (project_dir / "pyproject.toml").is_file():
            continue

        src_dir = project_dir / "src"
        if src_dir.is_dir():
            src_dirs.append(src_dir)

    return src_dirs


for src_dir in reversed(_discover_src_dirs()):
    src_dir_str = str(src_dir)
    if src_dir_str not in sys.path:
        sys.path.insert(0, src_dir_str)


for package_name, package_root in _discover_packages():
    _load_package(package_name, package_root)
