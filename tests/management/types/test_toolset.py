"""Tests for the Toolset factories and (de)serialization."""

import pytest
from modus.management import Toolset
from modus.management.types.toolset import (
    INTEGRATIONS,
    dump_toolset,
    parse_toolset,
)

CONNECTION_ID = "11111111-1111-4111-8111-111111111111"
SQL_CONNECTION_ID = "22222222-2222-4222-8222-222222222222"


def test_integration_factory_emits_connection_slot():
    ts = Toolset.integration(
        "slack", connection_id=CONNECTION_ID, actions=["SendMessage", "ListChannels"]
    )
    assert ts.tools() == {
        "slack": {
            "byConnection": {CONNECTION_ID: {"actions": ["SendMessage", "ListChannels"]}}
        }
    }


def test_integration_factory_with_rules():
    ts = Toolset.slack(
        connection_id=CONNECTION_ID,
        actions=["SendMessage"],
        rules={"allowedChannelIds": ["C123"], "allowedChannelNames": {"C123": "General"}},
    )
    assert ts.tools() == {
        "slack": {
            "byConnection": {
                CONNECTION_ID: {
                    "actions": ["SendMessage"],
                    "rules": {
                        "allowedChannelIds": ["C123"],
                        "allowedChannelNames": {"C123": "General"},
                    },
                }
            }
        }
    }


@pytest.mark.parametrize("name", INTEGRATIONS)
def test_integration_accepts_catalog_platforms(name):
    assert Toolset.integration(
        name, connection_id=CONNECTION_ID, actions=["read"]
    ).tools() == {name: {"byConnection": {CONNECTION_ID: {"actions": ["read"]}}}}


@pytest.mark.parametrize(
    "name",
    ["slack", "clickup", "github", "jira", "confluence", "zendesk", "notion",
     "salesforce", "teams", "google_drive", "power_bi"],
)
def test_shortcuts_require_and_preserve_connection_id(name):
    factory = getattr(Toolset, name)
    with pytest.raises(TypeError, match="connection_id"):
        factory(actions=["read"])
    assert factory(connection_id=CONNECTION_ID, actions=["read"]).tools() == {
        name: {"byConnection": {CONNECTION_ID: {"actions": ["read"]}}}
    }


def test_integration_requires_connection_id_or_personal():
    with pytest.raises(ValueError, match="exactly one of connection_id and personal"):
        Toolset.integration("slack", actions=["SendMessage"])


def test_personal_emits_the_personal_slot_beside_an_empty_by_connection():
    ts = Toolset.integration(
        "gmail", personal=True, actions=["search-threads"], rules={"allowedChannelIds": []}
    )
    assert ts.tools() == {
        "gmail": {
            "byConnection": {},
            "personal": {"actions": ["search-threads"], "rules": {"allowedChannelIds": []}},
        }
    }
    assert parse_toolset(dump_toolset(ts)).tools() == ts.tools()


def test_personal_and_connection_id_together_are_refused():
    with pytest.raises(ValueError, match="exactly one of connection_id and personal"):
        Toolset.integration(
            "google_drive", connection_id=CONNECTION_ID, personal=True, actions=["find-file"]
        )


@pytest.mark.parametrize(
    "name", ["not-a-tool", "sql_runner", "looker_bi", "langfuse_observability", "amplitude_analytics"]
)
def test_integration_rejects_unknown_surface(name):
    with pytest.raises(ValueError, match="Unknown integration"):
        Toolset.integration(name, connection_id=CONNECTION_ID, actions=["x"])


def test_integration_rejects_empty_actions():
    with pytest.raises(ValueError, match="at least one value"):
        Toolset.clickup(connection_id=CONNECTION_ID, actions=[])


@pytest.mark.parametrize(
    "platform",
    ["bigquery", "clickhouse", "databricks", "postgresql", "presto", "redshift",
     "snowflake", "starburst", "trino"],
)
def test_sql_factory(platform):
    assert Toolset.sql(platform, connection_id=SQL_CONNECTION_ID).tools() == {
        platform: {"byConnection": {SQL_CONNECTION_ID: {"actions": ["query"]}}}
    }


def test_sql_requires_connection_id():
    with pytest.raises(TypeError, match="connection_id"):
        Toolset.sql("postgresql")


def test_sql_runner_removed():
    assert not hasattr(Toolset, "sql_runner")


@pytest.mark.parametrize(
    "factory",
    [
        lambda: Toolset.slack(connection_id=CONNECTION_ID, actions="SendMessage"),
        lambda: Toolset.custom_mcps("conn-a"),
    ],
)
def test_iterable_factories_reject_scalar_string(factory):
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
        Toolset.slack(connection_id=CONNECTION_ID, actions=["SendMessage"]),
        Toolset.sql("postgresql", connection_id=SQL_CONNECTION_ID),
        Toolset.memory(),
    )
    assert ts.tools() == {
        "slack": {"byConnection": {CONNECTION_ID: {"actions": ["SendMessage"]}}},
        "postgresql": {"byConnection": {SQL_CONNECTION_ID: {"actions": ["query"]}}},
        "memory": {"enabled": True},
    }


def test_combine_later_surface_wins():
    ts = Toolset.combine(
        Toolset.slack(connection_id=CONNECTION_ID, actions=["A"]),
        Toolset.slack(connection_id=CONNECTION_ID, actions=["B"]),
    )
    assert ts.tools() == {"slack": {"byConnection": {CONNECTION_ID: {"actions": ["B"]}}}}


def test_merge_instance_method():
    ts = Toolset.slack(connection_id=CONNECTION_ID, actions=["SendMessage"]).merge(Toolset.memory())
    assert ts.tools() == {
        "slack": {"byConnection": {CONNECTION_ID: {"actions": ["SendMessage"]}}},
        "memory": {"enabled": True},
    }


def test_dump_toolset_keeps_empty_so_it_clears_tools():
    assert dump_toolset(Toolset.empty()) == {}
    assert dump_toolset(None) is None


def test_dump_toolset_emits_surface_map():
    assert dump_toolset(Toolset.memory()) == {"memory": {"enabled": True}}


def test_dump_toolset_rejects_raw_dict():
    with pytest.raises(TypeError, match="Toolset"):
        dump_toolset({"postgresql": {"byConnection": {SQL_CONNECTION_ID: {"actions": ["query"]}}}})


def test_parse_toolset_round_trips_surface_map():
    raw = {
        "slack": {"byConnection": {CONNECTION_ID: {"actions": ["SendMessage"]}}},
        "postgresql": {"byConnection": {SQL_CONNECTION_ID: {"actions": ["query"]}}},
    }
    parsed = parse_toolset(raw)
    assert parsed is not None
    assert parsed.tools() == raw


def test_parse_toolset_none():
    assert parse_toolset(None) is None


def test_personal_is_left_to_the_api_on_any_integration():
    assert Toolset.integration("slack", personal=True, actions=["SendMessage"]).tools() == {
        "slack": {"byConnection": {}, "personal": {"actions": ["SendMessage"]}}
    }
