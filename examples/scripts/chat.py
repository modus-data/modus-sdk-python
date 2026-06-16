"""
Skill chat: buffered reply then follow-up on the same thread.

For org-wide Modus chat (home-page assistant), see modus_chat.py.

Uses API credits. Requires a token with skills:invoke.

Setup:
    export MODUS_API_KEY=modus_xxx
    python examples/scripts/chat.py
"""

import os
import sys

import modus

MODEL = "claude-sonnet-4.6"


def main() -> None:
    if not os.environ.get("MODUS_API_KEY"):
        sys.exit(
            "Export MODUS_API_KEY before running:\n"
            "  export MODUS_API_KEY=modus_xxx"
        )

    client = modus.Modus()
    skills = list(client.skills.list().auto_paging_iter())
    if not skills:
        sys.exit("No skills found — create and deploy one in the Modus app first.")

    skill = next((s for s in skills if s.status == "active"), skills[0])
    print(f"Skill: {skill.name} (id={skill.id})")

    result = client.skills.chat(skill.id, "Say hello in one sentence.", model=MODEL)
    print(f"\nBuffered: {result.content}")
    print(f"  thread_id={result.thread_id}")

    follow_up = client.skills.chat(
        skill.id,
        "What did I just ask?",
        model=MODEL,
        thread_id=result.thread_id,
    )
    print(f"\nFollow-up: {follow_up.content}")
    print(f"  thread_id={follow_up.thread_id}")


if __name__ == "__main__":
    main()
