"""Nullable enum RootModels stay ``Enum | None`` after generator postprocessing."""

import importlib.util
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "generate-sdk-from-openapi.py"

# datamodel-codegen shape: nullability lives on the RootModel, and a $ref or
# array item names that wrapper with no extra outer ``| None``.
_REFERENCED = """
from enum import Enum

from pydantic import BaseModel, Field, RootModel


class ReviewNullableReasonEnum(str, Enum):
    review_a = 'review_a'
    review_b = 'review_b'


class ReviewNullableReason(RootModel[ReviewNullableReasonEnum | None]):
    root: ReviewNullableReasonEnum | None = Field(None)


class ReviewReasonHolder(BaseModel):
    reason: ReviewNullableReason = Field(...)
    reasons: list[ReviewNullableReason] = Field(...)
"""

# Same members already exist under the published name, and the field annotation
# already admits null. Collapse must keep that name and a single ``| None``.
_CANONICAL = """
from enum import Enum

from pydantic import BaseModel, Field, RootModel


class ManageDenial(str, Enum):
    not_owner = 'not_owner'
    needs_group_manage = 'needs_group_manage'


class ManageDenial1Enum(str, Enum):
    not_owner = 'not_owner'
    needs_group_manage = 'needs_group_manage'


class ManageDenial1(RootModel[ManageDenial1Enum | None]):
    root: ManageDenial1Enum | None = Field(None)


class WorkflowDto(BaseModel):
    manage_denial: ManageDenial1 | None = Field(...)
"""


def _collapse(text: str) -> str:
    spec = importlib.util.spec_from_file_location("generate_sdk_from_openapi", _SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module._collapse_nullable_enum_root_models(text)


def _load(source: str, class_name: str):
    namespace: dict[str, object] = {}
    exec(_collapse(source), namespace)  # noqa: S102 — fixture is the generator output under test
    return namespace[class_name]


def test_nullable_referenced_enum_keeps_none() -> None:
    collapsed = _collapse(_REFERENCED)
    assert "reason: ReviewNullableReasonEnum | None" in collapsed
    holder = _load(_REFERENCED, "ReviewReasonHolder")
    parsed = holder.model_validate({"reason": None, "reasons": ["review_a"]})
    assert parsed.reason is None
    assert parsed.reasons[0] == "review_a"


def test_nullable_enum_array_element_keeps_none() -> None:
    collapsed = _collapse(_REFERENCED)
    assert "reasons: list[ReviewNullableReasonEnum | None]" in collapsed
    holder = _load(_REFERENCED, "ReviewReasonHolder")
    parsed = holder.model_validate({"reason": "review_b", "reasons": [None]})
    assert parsed.reason == "review_b"
    assert parsed.reasons == [None]


def test_collapse_reuses_canonical_enum_name() -> None:
    collapsed = _collapse(_CANONICAL)
    assert "manage_denial: ManageDenial | None = Field(" in collapsed
    assert "ManageDenial | None | None" not in collapsed
    assert "class ManageDenial1(" not in collapsed
    assert "class ManageDenial1Enum(" not in collapsed
    workflow = _load(_CANONICAL, "WorkflowDto")
    assert workflow.model_validate({"manage_denial": None}).manage_denial is None
    assert workflow.model_validate({"manage_denial": "not_owner"}).manage_denial == "not_owner"
