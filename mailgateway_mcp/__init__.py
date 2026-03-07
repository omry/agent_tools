"""Workspace bridge for src-layout imports.

This makes ``import mailgateway_mcp.*`` resolve to ``src/mailgateway_mcp``
even when tooling places the project root ahead of ``src`` on ``sys.path``.
"""

from __future__ import annotations

from pathlib import Path


_PACKAGE_ROOT = Path(__file__).resolve().parent / "src" / "mailgateway_mcp"
_PACKAGE_INIT = _PACKAGE_ROOT / "__init__.py"

if not _PACKAGE_INIT.is_file():
    raise ImportError(f"Could not find package init at {_PACKAGE_INIT}")

__path__ = [str(_PACKAGE_ROOT)]
__file__ = str(_PACKAGE_INIT)

exec(compile(_PACKAGE_INIT.read_text(), __file__, "exec"), globals())
