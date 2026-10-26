"""A connectionSet row read from scopes.get goes back on update with its snake_case wire names."""

from __future__ import annotations

from modus._generated.models import ConnectionSetItemReadDto
from modus.management.types.json_blob import dump_json_object_list

PREFERENCES = {"mode": "all", "include": [], "exclude": []}


def test_read_row_round_trips_on_its_wire_names() -> None:
    row = ConnectionSetItemReadDto.model_validate(
        {"connection_id": "c1", "path": [], "preferences": PREFERENCES, "context_enabled": False}
    )

    assert dump_json_object_list([row], field_name="connection_set") == [
        {"connection_id": "c1", "path": [], "preferences": PREFERENCES, "context_enabled": False}
    ]
