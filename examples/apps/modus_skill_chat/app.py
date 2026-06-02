"""Streamlit demo: streaming vs buffered Modus skill chat.

Configuration is read from the process environment only (no ``.env`` files).
Export ``MODUS_API_KEY`` before starting Streamlit; ``modus.Modus()`` picks it up.
"""

from __future__ import annotations

import os
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any
from urllib.parse import quote

import modus
import streamlit as st
from modus._validation import ALLOWED_CHAT_MODELS
from modus.types.chat import ChatResult

DEFAULT_MODEL = "claude-sonnet-4.6"
CHAT_MODELS = sorted(ALLOWED_CHAT_MODELS)

_SETUP_HINT = """\
export MODUS_API_KEY=modus_xxx
streamlit run app.py\
"""


def chat_path(skill_id: int | str, thread_id: str | None, *, stream: bool) -> str:
    suffix = "/stream" if stream else ""
    safe_id = quote(str(skill_id), safe="")
    if thread_id:
        safe_tid = quote(str(thread_id), safe="")
        return f"/api/v1/skills/{safe_id}/conversations/{safe_tid}/chat{suffix}"
    return f"/api/v1/skills/{safe_id}/chat{suffix}"


def _init_session_state() -> None:
    defaults: dict[str, Any] = {
        "stream_messages": [],
        "buffered_messages": [],
        "stream_thread_id": None,
        "buffered_thread_id": None,
        "selected_skill_id": None,
        "selected_model": DEFAULT_MODEL,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _clear_conversations() -> None:
    st.session_state.stream_messages = []
    st.session_state.buffered_messages = []
    st.session_state.stream_thread_id = None
    st.session_state.buffered_thread_id = None


@st.cache_resource
def get_list_client() -> modus.Modus:
    """Read-only client for skill listing."""
    return modus.Modus()


@st.cache_resource
def get_stream_client() -> modus.Modus:
    """Dedicated client for SSE chat/stream — do not share across threads."""
    return modus.Modus()


@st.cache_resource
def get_buffered_client() -> modus.Modus:
    """Dedicated client for buffered JSON chat — safe for background threads."""
    return modus.Modus()


@st.cache_data(ttl=120, show_spinner=False)
def load_active_skills() -> list[dict[str, Any]]:
    client = get_list_client()
    skills = []
    for skill in client.skills.list().auto_paging_iter():
        if skill.is_active:
            skills.append(
                {
                    "id": skill.id,
                    "name": skill.name,
                    "label": f"{skill.name} (id={skill.id})",
                }
            )
    return sorted(skills, key=lambda s: s["name"].lower())


def _render_messages(messages: list[dict[str, str]]) -> None:
    for msg in messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])


def _run_buffered_chat(
    skill_id: int,
    message: str,
    model: str,
    thread_id: str | None,
) -> ChatResult | BaseException:
    try:
        return get_buffered_client().skills.chat(
            skill_id,
            message,
            model=model,
            thread_id=thread_id,
        )
    except BaseException as exc:
        return exc


def _format_error(exc: BaseException) -> str:
    if isinstance(exc, modus.ModusError):
        return exc.message if hasattr(exc, "message") else str(exc)
    return str(exc)


def _render_buffered_result(col_buffered: Any, buffered_future: Future[Any]) -> bool:
    """Render buffered assistant message when the future is done. Returns True if rendered."""
    if not buffered_future.done():
        return False

    result = buffered_future.result()
    with col_buffered:
        with st.chat_message("assistant"):
            if isinstance(result, BaseException):
                msg = _format_error(result)
                st.error(msg)
                st.session_state.buffered_messages.append(
                    {"role": "assistant", "content": f"**Error:** {msg}"}
                )
            else:
                st.markdown(result.text)
                st.session_state.buffered_thread_id = result.thread_id
                st.session_state.buffered_messages.append(
                    {"role": "assistant", "content": result.text}
                )
    return True


def _handle_parallel_send(
    skill_id: int,
    prompt: str,
    model: str,
    col_stream: Any,
    col_buffered: Any,
) -> None:
    st.session_state.stream_messages.append({"role": "user", "content": prompt})
    st.session_state.buffered_messages.append({"role": "user", "content": prompt})

    with col_stream:
        with st.chat_message("user"):
            st.markdown(prompt)

    with col_buffered:
        with st.chat_message("user"):
            st.markdown(prompt)

    buffered_rendered = False

    with ThreadPoolExecutor(max_workers=1) as executor:
        buffered_future: Future[Any] = executor.submit(
            _run_buffered_chat,
            skill_id,
            prompt,
            model,
            st.session_state.buffered_thread_id,
        )

        with col_stream:
            with st.chat_message("assistant"):
                stream_placeholder = st.empty()
                accumulated = ""
                try:
                    with get_stream_client().skills.chat_stream(
                        skill_id,
                        prompt,
                        model=model,
                        thread_id=st.session_state.stream_thread_id,
                    ) as stream:
                        for chunk in stream.text_stream:
                            accumulated += chunk
                            stream_placeholder.markdown(accumulated or "…")

                            if not buffered_rendered and buffered_future.done():
                                buffered_rendered = _render_buffered_result(
                                    col_buffered, buffered_future
                                )

                        final = stream.get_final_result()
                        st.session_state.stream_thread_id = final.thread_id
                        st.session_state.stream_messages.append(
                            {"role": "assistant", "content": final.text}
                        )
                except BaseException as exc:
                    msg = _format_error(exc)
                    stream_placeholder.error(msg)
                    st.session_state.stream_messages.append(
                        {"role": "assistant", "content": f"**Error:** {msg}"}
                    )

        if not buffered_rendered:
            if buffered_future.done():
                _render_buffered_result(col_buffered, buffered_future)
            else:
                with col_buffered:
                    with st.chat_message("assistant"):
                        with st.spinner("Waiting for buffered response…"):
                            result = buffered_future.result()
                        if isinstance(result, BaseException):
                            msg = _format_error(result)
                            st.error(msg)
                            st.session_state.buffered_messages.append(
                                {"role": "assistant", "content": f"**Error:** {msg}"}
                            )
                        else:
                            st.markdown(result.text)
                            st.session_state.buffered_thread_id = result.thread_id
                            st.session_state.buffered_messages.append(
                                {"role": "assistant", "content": result.text}
                            )


def main() -> None:
    st.set_page_config(page_title="Modus Skill Chat", layout="wide")
    _init_session_state()

    st.title("Modus Skill Chat")
    st.caption("Compare streaming (`/chat/stream`) vs buffered (`/chat`) side by side.")

    if not os.environ.get("MODUS_API_KEY"):
        st.error("MODUS_API_KEY is not set. Export your token before starting Streamlit:")
        st.code(_SETUP_HINT, language="bash")
        st.stop()

    try:
        client = get_list_client()
        base_url = client._config.base_url
    except modus.AuthenticationError as exc:
        st.error(str(exc))
        st.stop()

    skill_id: int | None = None
    model = st.session_state.selected_model

    with st.sidebar:
        st.subheader("Settings")
        st.markdown(f"**API origin:** `{base_url}`")
        st.markdown("**API key:** set")

        if st.button("Refresh skills"):
            load_active_skills.clear()

        try:
            skills = load_active_skills()
        except modus.ModusError as exc:
            st.error(_format_error(exc))
            st.stop()

        if not skills:
            st.warning("No active skills found. Deploy a skill in Modus first.")
        else:
            labels = [s["label"] for s in skills]
            id_by_label = {s["label"]: s["id"] for s in skills}
            default_idx = 0
            if st.session_state.selected_skill_id is not None:
                for i, s in enumerate(skills):
                    if s["id"] == st.session_state.selected_skill_id:
                        default_idx = i
                        break

            chosen_label = st.selectbox("Skill", labels, index=default_idx)
            skill_id = id_by_label[chosen_label]

            if st.session_state.selected_skill_id != skill_id:
                st.session_state.selected_skill_id = skill_id
                _clear_conversations()

        model = st.selectbox(
            "Model",
            CHAT_MODELS,
            index=CHAT_MODELS.index(st.session_state.selected_model)
            if st.session_state.selected_model in CHAT_MODELS
            else CHAT_MODELS.index(DEFAULT_MODEL),
        )
        st.session_state.selected_model = model

        if st.button("Clear conversations"):
            _clear_conversations()
            st.rerun()

        if skill_id is not None:
            with st.expander("Thread IDs"):
                st.text(f"Stream:   {st.session_state.stream_thread_id or '(new)'}")
                st.text(f"Buffered: {st.session_state.buffered_thread_id or '(new)'}")

    col_stream, col_buffered = st.columns(2)

    with col_stream:
        st.subheader("Streaming")
        if skill_id is not None:
            st.caption(
                f"`POST {chat_path(skill_id, st.session_state.stream_thread_id, stream=True)}`"
            )

    with col_buffered:
        st.subheader("Buffered")
        if skill_id is not None:
            st.caption(
                f"`POST {chat_path(skill_id, st.session_state.buffered_thread_id, stream=False)}`"
            )

    prompt = st.chat_input("Message")

    if prompt and skill_id is not None:
        with col_stream:
            _render_messages(st.session_state.stream_messages[:-1])
        with col_buffered:
            _render_messages(st.session_state.buffered_messages[:-1])
        _handle_parallel_send(skill_id, prompt, model, col_stream, col_buffered)
    else:
        if prompt and skill_id is None:
            st.error("Select an active skill before chatting.")
        with col_stream:
            _render_messages(st.session_state.stream_messages)
        with col_buffered:
            _render_messages(st.session_state.buffered_messages)


if __name__ == "__main__":
    main()
