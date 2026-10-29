"""Generated string enums print their wire value, as the TypeScript SDK does."""

import importlib.util
import inspect
from enum import Enum
from pathlib import Path

from modus._generated import models
from modus._generated.models import ResourceLifecycleStatus

_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "generate-sdk-from-openapi.py"


def _generator():
    spec = importlib.util.spec_from_file_location("generate_sdk_from_openapi", _SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_status_prints_its_value() -> None:
    status = ResourceLifecycleStatus.active
    assert str(status) == "active"
    assert f"{status}" == "active"
    assert status == "active"
    assert repr(status) == "<ResourceLifecycleStatus.active: 'active'>"


def test_every_generated_string_enum_prints_its_value() -> None:
    enums = [
        cls
        for _, cls in inspect.getmembers(models, inspect.isclass)
        if issubclass(cls, Enum) and issubclass(cls, str) and cls.__module__ == models.__name__
    ]
    assert enums, "no generated string enums found"
    for cls in enums:
        for member in cls:
            assert str(member) == member.value, cls.__name__


def test_generator_adds_str_once() -> None:
    source = "class Status(str, Enum):\n    active = 'active'\n"
    once = _generator()._str_enums_print_their_value(source)
    assert once == "class Status(str, Enum):\n    __str__ = str.__str__\n    active = 'active'\n"
    assert _generator()._str_enums_print_their_value(once) == once
