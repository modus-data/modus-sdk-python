"""Skill toolset configuration.

A skill's toolset declares which tools it may use at run time: connected
integrations (Slack, ClickUp, GitHub, and others), SQL access, persistent
memory, and custom MCP connections.

Build a toolset with the factory methods and combine several with
``Toolset.combine`` (or chain with ``.merge``)::

    from modus.management import Toolset

    toolset = Toolset.combine(
        Toolset.slack(actions=["SendMessage"]),
        Toolset.sql_runner(["SELECT:conn-123:analytics:public"]),
        Toolset.memory(),
    )
    mgmt.scopes.create(name="Analyst", model="gpt-4o", toolset=toolset)
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

from pydantic import BaseModel, ConfigDict

from ._serialize import dump_optional_model

#: Integrations a skill can use once connected to your workspace.
INTEGRATIONS = (
    "clickup",
    "confluence",
    "github",
    "google_drive",
    "jira",
    "notion",
    "power_bi",
    "salesforce",
    "slack",
    "teams",
    "zendesk",
)

class Toolset(BaseModel):
    """The tools a skill may use at run time.

    Create one with the factory methods (``Toolset.slack(...)``,
    ``Toolset.sql_runner(...)``, ``Toolset.memory()``, and others) and combine
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
            raise ValueError(
                f"{field} must be a list of strings, not a single string "
                f"(did you mean [{values!r}]?)."
            )
        items = list(values)
        if not items:
            raise ValueError(f"{field} requires at least one value.")
        return items

    # ---- connected integrations (Slack, ClickUp, GitHub, ...) ----

    @classmethod
    def integration(
        cls,
        name: str,
        *,
        actions: Iterable[str],
        rules: Optional[Dict[str, Any]] = None,
    ) -> "Toolset":
        """Enable a connected integration for the given actions.

        Args:
            name:    Integration name, e.g. ``"slack"`` or ``"clickup"``. See ``INTEGRATIONS``.
            actions: The action names the skill may call on that integration.
                     The API binds the entry to the organization's newest workspace
                     connection of that integration and returns it as ``byConnection``.
            rules:   Optional per-integration restrictions (for example, a Slack
                     channel allow-list).

        Raises:
            ValueError: If ``name`` is not a supported integration or ``actions`` is empty.
        """
        key = name.strip().lower()
        if key not in INTEGRATIONS:
            allowed = ", ".join(INTEGRATIONS)
            raise ValueError(
                f"Unknown integration {name!r}. Supported integrations: {allowed}."
            )
        action_list = cls._require_str_list(actions, field=f"{key} actions")
        entry: Dict[str, Any] = {"actions": action_list}
        if rules is not None:
            entry["rules"] = rules
        return cls(**{key: entry})

    @classmethod
    def slack(
        cls, *, actions: Iterable[str], rules: Optional[Dict[str, Any]] = None
    ) -> "Toolset":
        """Enable Slack for the given actions (e.g. ``["SendMessage"]``)."""
        return cls.integration("slack", actions=actions, rules=rules)

    @classmethod
    def clickup(cls, *, actions: Iterable[str]) -> "Toolset":
        """Enable ClickUp for the given actions."""
        return cls.integration("clickup", actions=actions)

    @classmethod
    def github(cls, *, actions: Iterable[str]) -> "Toolset":
        """Enable GitHub for the given actions."""
        return cls.integration("github", actions=actions)

    @classmethod
    def jira(cls, *, actions: Iterable[str]) -> "Toolset":
        """Enable Jira for the given actions."""
        return cls.integration("jira", actions=actions)

    @classmethod
    def confluence(cls, *, actions: Iterable[str]) -> "Toolset":
        """Enable Confluence for the given actions."""
        return cls.integration("confluence", actions=actions)

    @classmethod
    def zendesk(cls, *, actions: Iterable[str]) -> "Toolset":
        """Enable Zendesk for the given actions."""
        return cls.integration("zendesk", actions=actions)

    @classmethod
    def notion(cls, *, actions: Iterable[str]) -> "Toolset":
        """Enable Notion for the given actions."""
        return cls.integration("notion", actions=actions)

    @classmethod
    def salesforce(cls, *, actions: Iterable[str]) -> "Toolset":
        """Enable Salesforce for the given actions."""
        return cls.integration("salesforce", actions=actions)

    @classmethod
    def teams(cls, *, actions: Iterable[str]) -> "Toolset":
        """Enable Microsoft Teams for the given actions."""
        return cls.integration("teams", actions=actions)

    @classmethod
    def google_drive(cls, *, actions: Iterable[str]) -> "Toolset":
        """Enable Google Drive for the given actions."""
        return cls.integration("google_drive", actions=actions)

    @classmethod
    def power_bi(cls, *, actions: Iterable[str]) -> "Toolset":
        """Enable Power BI for the given actions."""
        return cls.integration("power_bi", actions=actions)

    # ---- built-in tools ----

    @classmethod
    def sql_runner(cls, selectors: Iterable[str]) -> "Toolset":
        """Allow the skill to run SQL against the given data selectors.

        Args:
            selectors: Selector strings that grant read access to a connection
                       and schema, e.g. ``"SELECT:conn-123:analytics:public"``.

        Raises:
            ValueError: If ``selectors`` is empty.
        """
        selector_list = cls._require_str_list(selectors, field="sql_runner selectors")
        return cls(**{"sql_runner": selector_list})

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
        """Return a toolset with no tools."""
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
    """Serialize a toolset for the request body, omitting an empty toolset."""
    dumped = dump_optional_model(value, field_name="toolset", typed_label="Toolset")
    if isinstance(dumped, dict):
        return dumped or None
    return None


def parse_toolset(raw: object) -> Optional[Toolset]:
    """Parse a toolset returned by the API."""
    if raw is None:
        return None
    return Toolset.model_validate(raw)
