"""Verify new 0.2.0 symbols are part of the public modus package."""

import modus


def test_chat_and_run_exports():
    for name in (
        "ChatResult",
        "SkillContextComposition",
        "AgentRun",
        "AgentRunListItem",
        "RunCancelledError",
        "StreamTimeoutError",
        "IngestedDataUploadResult",
        "SqlIngestedDataRequest",
        "HttpIngestedDataRequest",
        "TokenEvent",
        "DoneEvent",
        "ErrorEvent",
        "CancelledEvent",
        "StreamTimeoutEvent",
    ):
        assert hasattr(modus, name), f"modus.{name} must be exported"
        assert name in modus.__all__
