"""Required fields the spec marks nullable accept null.

The nullable patch in the generator only rewrote fields with a ``Field(...)`` default, so a
required nullable field stayed ``str`` and a real ``null`` failed validation: staging's
``list_member_groups()`` raised on a group with no description.
"""

from __future__ import annotations

from modus._generated.models import MemberGroupDto, OrgMemberDto


def test_member_group_without_description_parses() -> None:
    group = MemberGroupDto.model_validate({
        "uid": "g1", "name": "Finance", "description": None,
        "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z",
    })

    assert group.description is None


def test_org_member_without_image_parses() -> None:
    member = OrgMemberDto.model_validate({
        "user_id": "u1", "first_name": "Ana", "last_name": "Lee", "email": "ana@example.com",
        "image_url": None, "role": "org:member",
    })

    assert member.image_url is None
