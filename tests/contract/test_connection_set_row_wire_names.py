"""A connectionSet entry read from scopes.get goes back on update with its snake_case wire names."""

from __future__ import annotations

from modus._generated.models import ConnectionSetItemReadDto
from modus.management.types.json_blob import dump_json_object_list

PREFERENCES = {"mode": "all", "include": [], "exclude": []}


def test_read_entry_round_trips_on_its_wire_names() -> None:
    entry = ConnectionSetItemReadDto.model_validate({"connection_id": "c1", "preferences": PREFERENCES})

    assert dump_json_object_list([entry], field_name="connection_set") == [{"connection_id": "c1", "preferences": PREFERENCES}]
