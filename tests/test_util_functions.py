import sys
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

from multiqc.utils import util_functions


def _ipython_module(shell: Any) -> ModuleType:
    module = ModuleType("IPython")
    module.get_ipython = lambda: shell  # type: ignore[attr-defined]
    return module


def test_is_running_in_notebook_handles_missing_interactive_shell(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "IPython", _ipython_module(None))

    assert util_functions.is_running_in_notebook() is False


def test_is_running_in_notebook_detects_kernel(monkeypatch: pytest.MonkeyPatch) -> None:
    shell = SimpleNamespace(config={"IPKernelApp": {}})
    monkeypatch.setitem(sys.modules, "IPython", _ipython_module(shell))

    assert util_functions.is_running_in_notebook() is True
