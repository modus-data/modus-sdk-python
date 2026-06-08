"""Tests for the Toolset factories and (de)serialization."""

import pytest
from modus.management import Toolset
from modus.management.types.toolset import dump_toolset, parse_toolset


def test_integration_factory_emits_actions_shape():
    ts = Toolset.slack(actions=["SendMessage", "ListChannels"])
    assert ts.tools() == {"slack": {"actions": ["SendMessage", "ListChannels"]}}


def test_integration_factory_with_rules():
    ts = Toolset.slack(
        actions=["SendMessage"],
        rules={"allowedChannelIds": ["C123"]},
    )
    assert ts.tools() == {
        "slack": {"actions": ["SendMessage"], "rules": {"allowedChannelIds": ["C123"]}}
    }


def test_integration_rejects_unknown_surface():
    with pytest.raises(ValueError, match="Unknown integration"):
        Toolset.integration("not-a-tool", actions=["x"])


def test_integration_rejects_empty_actions():
    with pytest.raises(ValueError, match="at least one value"):
        Toolset.clickup(actions=[])


def test_sql_runner_factory():
    ts = Toolset.sql_runner(["SELECT:conn-1:analytics:public"])
    assert ts.tools() == {"sql_runner": ["SELECT:conn-1:analytics:public"]}


def test_sql_runner_rejects_empty():
    with pytest.raises(ValueError, match="at least one value"):
        Toolset.sql_runner([])


@pytest.mark.parametrize(
    "factory",
    [
        lambda: Toolset.slack(actions="SendMessage"),
        lambda: Toolset.sql_runner("SELECT:conn-1:analytics:public"),
        lambda: Toolset.custom_mcps("conn-a"),
    ],
)
def test_iterable_factories_reject_scalar_string(factory):
    # A bare string would otherwise be iterated character-by-character.
    with pytest.raises(ValueError, match="not a single string"):
        factory()


def test_memory_factory():
    assert Toolset.memory().tools() == {"memory": {"enabled": True}}
    assert Toolset.memory(enabled=False).tools() == {"memory": {"enabled": False}}


def test_custom_mcps_factory():
    ts = Toolset.custom_mcps(["conn-a", "conn-b"])
    assert ts.tools() == {
        "custom_mcps": [{"connectionId": "conn-a"}, {"connectionId": "conn-b"}]
    }


def test_custom_mcps_rejects_empty():
    with pytest.raises(ValueError, match="at least one value"):
        Toolset.custom_mcps([])


def test_combine_merges_surfaces():
    ts = Toolset.combine(
        Toolset.slack(actions=["SendMessage"]),
        Toolset.sql_runner(["SELECT:conn-1:analytics:public"]),
        Toolset.memory(),
    )
    assert ts.tools() == {
        "slack": {"actions": ["SendMessage"]},
        "sql_runner": ["SELECT:conn-1:analytics:public"],
        "memory": {"enabled": True},
    }


def test_combine_later_surface_wins():
    ts = Toolset.combine(
        Toolset.slack(actions=["A"]),
        Toolset.slack(actions=["B"]),
    )
    assert ts.tools() == {"slack": {"actions": ["B"]}}


def test_merge_instance_method():
    ts = Toolset.slack(actions=["SendMessage"]).merge(Toolset.memory())
    assert ts.tools() == {
        "slack": {"actions": ["SendMessage"]},
        "memory": {"enabled": True},
    }


def test_dump_toolset_omits_empty():
    assert dump_toolset(Toolset.empty()) is None
    assert dump_toolset(None) is None


def test_dump_toolset_emits_surface_map():
    assert dump_toolset(Toolset.memory()) == {"memory": {"enabled": True}}


def test_parse_toolset_round_trips_surface_map():
    raw = {"slack": {"actions": ["SendMessage"]}, "sql_runner": ["SELECT:a:b"]}
    parsed = parse_toolset(raw)
    assert parsed is not None
    assert parsed.tools() == raw


def test_parse_toolset_none():
    assert parse_toolset(None) is None
