"""
Modus chat: revenue / ARR questions with buffered, streaming, and context compose.

Uses API credits. Requires a token with scopes:invoke.

Setup:
    export MODUS_API_KEY=modus_xxx
    python examples/scripts/modus_chat.py
"""

import os
import sys

import modus

MODEL = "claude-sonnet-5"
FIRST_MESSAGE = "What were our top revenue drivers last quarter?"
FOLLOW_UP = "Break that down by region."
STREAM_MESSAGE = "Summarize ARR growth trends in three bullet points."
CONTEXT_INTENT = (
    "What tables, dashboards, and saved queries describe revenue and ARR?"
)


def main() -> None:
    if not os.environ.get("MODUS_API_KEY"):
        sys.exit(
            "Export MODUS_API_KEY before running:\n"
            "  export MODUS_API_KEY=modus_xxx"
        )

    client = modus.Modus()

    result = client.modus.chat(FIRST_MESSAGE, model=MODEL)
    print(f"Question: {FIRST_MESSAGE}")
    print(f"Answer: {result.content}")
    print(f"  thread_id={result.thread_id}  run_id={result.run_id}")

    follow_up = client.modus.chat(
        FOLLOW_UP,
        model=MODEL,
        thread_id=result.thread_id,
    )
    print(f"\nFollow-up: {FOLLOW_UP}")
    print(f"Answer: {follow_up.content}")
    print(f"  thread_id={follow_up.thread_id}")

    print(f"\nStreaming ({STREAM_MESSAGE}):")
    with client.modus.chat_stream(STREAM_MESSAGE, model=MODEL) as stream:
        for chunk in stream.text_stream:
            print(chunk, end="")
    print()

    ctx = client.modus.get_context(CONTEXT_INTENT, limit=5)
    print(
        f"\nContext compose: {ctx.original_count} item(s) considered, "
        f"{len(ctx.context)} chars, session_id={ctx.session_id}"
    )

    page = client.modus.conversations.list(kind="modus", page_size=5)
    print(f"\nModus conversations (page): {len(page.items)} row(s)")
    for row in page:
        preview = (row.first_message or "")[:60]
        print(f"  {row.thread_id}: {preview!r}")


if __name__ == "__main__":
    main()
