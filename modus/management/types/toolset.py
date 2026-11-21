"""Skill toolset configuration.

A skill's toolset declares which tools it may use at run time: connected
integrations (Slack, ClickUp, GitHub, and others), SQL access, persistent
memory, and custom MCP connections.

Build a toolset with the factory methods and combine several with
``Toolset.combine`` (or chain with ``.merge``)::

    from modus.management import Toolset

    toolset = Toolset.combine(
        Toolset.slack(
            connection_id="11111111-1111-4111-8111-111111111111",
            actions=["SendMessage"],
        ),
        Toolset.sql(
            "postgresql", connection_id="22222222-2222-4222-8222-222222222222"
        ),
        Toolset.integration("gmail", personal=True, actions=["search-threads"]),
        Toolset.memory(),
    )
    mgmt.scopes.create(name="Analyst", model="gpt-4o", toolset=toolset)
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

from pydantic import BaseModel, ConfigDict

from ..._exceptions import ValidationError
from ._serialize import dump_optional_model

#: Integration platform keys supported by the toolset builder.
INTEGRATIONS = (
    "airflow",
    "amplitude",
    "attio",
    "bigquery",
    "clickhouse",
    "clickup",
    "confluence",
    "confluence_data_center",
    "databricks",
    "datadog",
    "dbt_cloud",
    "dbt_core",
    "dropbox",
    "fathom",
    "fellow",
    "fireflies",
    "fivetran",
    "gainsight",
    "gemini_notebook",
    "github",
    "gitlab",
    "gmail",
    "gong",
    "google_calendar",
    "google_drive",
    "hubspot",
    "intercom",
    "jira",
    "jira_data_center",
    "langfuse",
    "looker",
    "lookml",
    "microsoft_entra_id",
    "mixpanel",
    "monday",
    "mongodb",
    "netsuite",
    "notion",
    "onedrive",
    "openmetadata",
    "postgresql",
    "posthog",
    "power_bi",
    "presto",
    "redshift",
    "salesforce",
    "sap",
    "sentry",
    "sisense",
    "slack",
    "snowflake",
    "starburst",
    "tableau",
    "teams",
    "trino",
    "zendesk",
    "zendesk_docs",
)



class Toolset(BaseModel):
    """The tools a skill may use at run time.

    Create one with the factory methods (``Toolset.slack(...)``,
    ``Toolset.sql(...)``, ``Toolset.memory()``, and others) and combine
    several with ``Toolset.combine(...)`` or ``.merge(...)``. ``Toolset.empty()``
    is a skill with no tools.
    """

    model_config = ConfigDict(extra="allow")

    def tools(self) -> Dict[str, Any]:
        """Return the configured tools as a plain dictionary, keyed by tool name."""
        return dict(self.__pydantic_extra__ or {})

    @staticmethod
    def _require_str_list(values: Iterable[str], *, field: str) -> list[str]:
        """Materialize an iterable of strings, rejecting empty input and scalar strings.

        A bare ``str`` is iterable character-by-character, so accepting one here would
        silently produce malformed single-character entries; reject it explicitly.
        """
        if isinstance(values, str):
            raise ValidationError(
                f"{field} must be a list of strings, not a single string "
                f"(did you mean [{values!r}]?)."
            )
        items = list(values)
        if not items:
            raise ValidationError(f"{field} requires at least one value.")
        return items

    # ---- connected integrations (Slack, ClickUp, GitHub, ...) ----

    @classmethod
    def integration(
        cls,
        name: str,
        *,
        connection_id: Optional[str] = None,
        personal: bool = False,
        actions: Iterable[str],
        rules: Optional[Dict[str, Any]] = None,
    ) -> "Toolset":
        """Enable actions on the integration connection you choose, or on each runner's own one.

        Pass exactly one of ``connection_id`` and ``personal=True``.

        Args:
            name: Integration platform, e.g. ``"slack"`` or ``"clickup"``. See ``INTEGRATIONS``.
            connection_id: Modus connection UUID of a shared connection. No other connection
                is substituted; a runner who cannot access it cannot use its tools. The API
                refuses a save that adds a personal connection's UUID here, or adds actions to one
                already stored; use ``personal=True`` for those.
            personal: Grant the actions on the personal connection of whoever runs the skill.
                A runner who has not connected the platform is asked to connect it (or gets a
                tool error outside chat); nobody else's connection is used. The API accepts it
                only on platforms people connect personally, such as Gmail or Google Drive.
            actions: Operation names the skill may call, without connection or path suffixes.
            rules: Optional restrictions for this connection, such as a Slack channel allow-list.

        Examples:
            Toolset.integration(
                "slack", connection_id="11111111-1111-4111-8111-111111111111",
                actions=["SendMessage"],
            )
            Toolset.integration("gmail", personal=True, actions=["search-threads"])

        Raises:
            ValueError: If ``name`` is not a supported integration, ``actions`` is empty,
                or both or neither of ``connection_id`` and ``personal`` are given.
        """
        key = name.strip().lower()
        if key not in INTEGRATIONS:
            allowed = ", ".join(INTEGRATIONS)
            raise ValidationError(
                f"Unknown integration {name!r}. Supported integrations: {allowed}."
            )
        if personal == (connection_id is not None):
            raise ValidationError(
                f"{key}: pass exactly one of connection_id and personal=True."
            )
        action_list = cls._require_str_list(actions, field=f"{key} actions")
        entry: Dict[str, Any] = {"actions": action_list}
        if rules is not None:
            entry["rules"] = rules
        if personal:
            return cls(**{key: {"byConnection": {}, "personal": entry}})
        return cls(**{key: {"byConnection": {connection_id: entry}}})

    @classmethod
    def slack(
        cls, *, connection_id: str, actions: Iterable[str], rules: Optional[Dict[str, Any]] = None
    ) -> "Toolset":
        """Enable Slack on the chosen connection for the given actions (e.g. ``["SendMessage"]``)."""
        return cls.integration("slack", connection_id=connection_id, actions=actions, rules=rules)

    @classmethod
    def clickup(cls, *, connection_id: str, actions: Iterable[str]) -> "Toolset":
        """Enable ClickUp on the chosen connection for the given actions."""
        return cls.integration("clickup", connection_id=connection_id, actions=actions)

    @classmethod
    def github(cls, *, connection_id: str, actions: Iterable[str]) -> "Toolset":
        """Enable GitHub on the chosen connection for the given actions."""
        return cls.integration("github", connection_id=connection_id, actions=actions)

    @classmethod
    def jira(cls, *, connection_id: str, actions: Iterable[str]) -> "Toolset":
        """Enable Jira on the chosen connection for the given actions."""
        return cls.integration("jira", connection_id=connection_id, actions=actions)

    @classmethod
    def confluence(cls, *, connection_id: str, actions: Iterable[str]) -> "Toolset":
        """Enable Confluence on the chosen connection for the given actions."""
        return cls.integration("confluence", connection_id=connection_id, actions=actions)

    @classmethod
    def zendesk(cls, *, connection_id: str, actions: Iterable[str]) -> "Toolset":
        """Enable Zendesk on the chosen connection for the given actions."""
        return cls.integration("zendesk", connection_id=connection_id, actions=actions)

    @classmethod
    def notion(cls, *, connection_id: str, actions: Iterable[str]) -> "Toolset":
        """Enable Notion on the chosen connection for the given actions."""
        return cls.integration("notion", connection_id=connection_id, actions=actions)

    @classmethod
    def salesforce(cls, *, connection_id: str, actions: Iterable[str]) -> "Toolset":
        """Enable Salesforce on the chosen connection for the given actions."""
        return cls.integration("salesforce", connection_id=connection_id, actions=actions)

    @classmethod
    def teams(cls, *, connection_id: str, actions: Iterable[str]) -> "Toolset":
        """Enable Microsoft Teams on the chosen connection for the given actions."""
        return cls.integration("teams", connection_id=connection_id, actions=actions)

    @classmethod
    def google_drive(cls, *, connection_id: str, actions: Iterable[str]) -> "Toolset":
        """Enable Google Drive on the chosen connection for the given actions."""
        return cls.integration("google_drive", connection_id=connection_id, actions=actions)

    @classmethod
    def power_bi(cls, *, connection_id: str, actions: Iterable[str]) -> "Toolset":
        """Enable Power BI on the chosen connection for the given actions."""
        return cls.integration("power_bi", connection_id=connection_id, actions=actions)

    @classmethod
    def sql(cls, platform: str, *, connection_id: str) -> "Toolset":
        """Grant SQL queries on the chosen platform connection.

        Args:
            platform: SQL platform key: ``bigquery``, ``clickhouse``, ``databricks``,
                ``postgresql``, ``presto``, ``redshift``, ``snowflake``, ``starburst``, or ``trino``.
            connection_id: Modus connection UUID. The scope's selections control data access.

        Examples:
            Toolset.sql("snowflake", connection_id="11111111-1111-4111-8111-111111111111")
        """
        return cls.integration(platform, connection_id=connection_id, actions=["query"])

    # ---- built-in tools ----

    @classmethod
    def memory(cls, enabled: bool = True) -> "Toolset":
        """Enable persistent memory so the skill can remember across conversations."""
        return cls(**{"memory": {"enabled": enabled}})

    @classmethod
    def custom_mcps(cls, connection_ids: Iterable[str]) -> "Toolset":
        """Attach custom MCP connections by their connection IDs.

        Args:
            connection_ids: IDs of the MCP connections to attach.

        Raises:
            ValueError: If ``connection_ids`` is empty.
        """
        ids = cls._require_str_list(connection_ids, field="custom_mcps connection_ids")
        return cls(**{"custom_mcps": [{"connectionId": cid} for cid in ids]})

    # ---- composition ----

    @classmethod
    def empty(cls) -> "Toolset":
        """Return a toolset with no tools. Pass it to ``scopes.update`` to clear every tool."""
        return cls()

    @classmethod
    def combine(cls, *toolsets: "Toolset") -> "Toolset":
        """Combine several toolsets into one.

        When two toolsets configure the same tool, the later one wins.
        """
        merged: Dict[str, Any] = {}
        for toolset in toolsets:
            merged.update(toolset.tools())
        return cls(**merged)

    def merge(self, *others: "Toolset") -> "Toolset":
        """Return a new toolset with ``others`` merged on top of this one."""
        return Toolset.combine(self, *others)


ToolsetInput = Toolset


def dump_toolset(value: Optional[ToolsetInput]) -> Optional[Dict[str, Any]]:
    """Serialize a toolset for the request body. ``Toolset.empty()`` stays ``{}``, which clears every tool."""
    return dump_optional_model(value, field_name="toolset", typed_label="Toolset")


def parse_toolset(raw: object) -> Optional[Toolset]:
    """Parse a toolset returned by the API."""
    if raw is None:
        return None
    return Toolset.model_validate(raw)
