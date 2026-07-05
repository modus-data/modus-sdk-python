"""
Scope chat: ask a revenue / ARR question, then follow up on the same thread.

For org-wide Modus chat (home-page assistant), see modus_chat.py.

Uses API credits. Requires a token with scopes:invoke.
Optional: MODUS_SCOPE_ID to target a specific active scope.

Setup:
    export MODUS_API_KEY=modus_xxx
    python examples/scripts/chat.py
"""

import os
import sys

import modus

MODEL = "claude-sonnet-5"
FIRST_MESSAGE = (
    "What is our current ARR and how has it trended over the last four quarters?"
)
FOLLOW_UP = "Which customer segments contributed most to that growth?"


def _scope_id_matches(scope_id: object, raw: str) -> bool:
    try:
        return float(scope_id) == float(raw)
    except (TypeError, ValueError):
        return str(scope_id) == raw


def _pick_scope(scopes: list) -> object:
    raw = os.environ.get("MODUS_SCOPE_ID")
    if raw:
        for scope in scopes:
            if _scope_id_matches(scope.id, raw):
                if scope.status != "active":
                    sys.exit(f"MODUS_SCOPE_ID={raw} found, but the scope is not active.")
                return scope
        sys.exit(f"MODUS_SCOPE_ID={raw} not found in listed scopes.")

    stable = [
        s
        for s in scopes
        if s.status == "active" and not s.has_unpublished_changes
    ]
    if stable:
        return stable[0]

    active = [s for s in scopes if s.status == "active"]
    if active:
        return active[0]

    sys.exit("No active scopes found — deploy a scope first.")


def main() -> None:
    if not os.environ.get("MODUS_API_KEY"):
        sys.exit(
            "Export MODUS_API_KEY before running:\n"
            "  export MODUS_API_KEY=modus_xxx"
        )

    client = modus.Modus()
    scopes = list(client.scopes.list().auto_paging_iter())
    if not scopes:
        sys.exit("No scopes found — create and deploy one in the Modus app first.")

    scope = _pick_scope(scopes)
    print(f"Scope: {scope.name} (id={scope.id})")

    result = client.scopes.chat(scope.id, FIRST_MESSAGE, model=MODEL)
    print(f"\nQuestion: {FIRST_MESSAGE}")
    print(f"Answer: {result.content}")
    print(f"  thread_id={result.thread_id}")

    follow_up = client.scopes.chat(
        scope.id,
        FOLLOW_UP,
        model=MODEL,
        thread_id=result.thread_id,
    )
    print(f"\nFollow-up: {FOLLOW_UP}")
    print(f"Answer: {follow_up.content}")
    print(f"  thread_id={follow_up.thread_id}")


if __name__ == "__main__":
    main()
