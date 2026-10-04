"""Chat request/response types for Modus and scope conversations.

Pass a **model id** as ``model`` to ``client.modus.chat(...)``,
``client.scopes.chat(...)``, and matching stream methods. Unsupported values
raise ``ValueError`` before the request is sent.

Allowed model ids:

- ``claude-sonnet-5``, ``claude-sonnet-5.5``, ``claude-sonnet-4.6``, ``claude-opus-4.8``, ``claude-opus-5.5``
- ``gpt-5.2``, ``gpt-5.5``, ``gpt-5-mini``, ``gpt-5.6-luna``, ``gpt-oss-120b``, ``gpt-oss-20b``
- ``qwen3-235b-a22b-2507``, ``qwen3-coder``, ``qwen3-32b``
- ``deepseek-chat-v3.1``, ``deepseek-v4-pro``, ``deepseek-v4-flash-latest``, ``minimax-m2.7``
- ``llama-4-maverick``, ``llama-4-scout``, ``llama-3.3-70b-instruct``
- ``gemini-3.1-pro-preview``, ``gemini-3-flash-preview``
- ``grok-4.3-fast``, ``grok-4.3``, ``grok-4.7``, ``kimi-k3``

``ChatResult`` fields:

- ``content`` — final assistant text for the run
- ``thread_id`` — conversation id for follow-up messages
- ``run_id`` — opaque run id for logging or correlation
"""

from __future__ import annotations

from .._generated.models import SkillChatRequestDto, SkillChatResponseDto

ChatResult = SkillChatResponseDto

__all__ = ["ChatResult", "SkillChatRequestDto", "SkillChatResponseDto"]
