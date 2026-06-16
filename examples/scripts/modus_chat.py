"""
Modus chat: buffered reply, thread follow-up, streaming, context compose, conversations.

Uses API credits. Requires a token with skills:invoke.

Setup:
    export MODUS_API_KEY=modus_xxx
    python examples/scripts/modus_chat.py
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

    result = client.modus.chat("Say hello in one sentence.", model=MODEL)
    print(f"Buffered: {result.content}")
    print(f"  thread_id={result.thread_id}  run_id={result.run_id}")

    follow_up = client.modus.chat(
        "What did I just ask?",
        model=MODEL,
        thread_id=result.thread_id,
    )
    print(f"\nFollow-up: {follow_up.content}")
    print(f"  thread_id={follow_up.thread_id}")

    print("\nStreaming:")
    with client.modus.chat_stream("Reply with exactly three words.", model=MODEL) as stream:
        for chunk in stream.text_stream:
            print(chunk, end="")
    print()

    ctx = client.modus.get_context("What context relates to revenue?", limit=5)
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
