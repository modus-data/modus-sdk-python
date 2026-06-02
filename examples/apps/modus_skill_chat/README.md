# Modus Skill Chat (Streamlit)

Side-by-side comparison of **streaming** (`/chat/stream`) vs **buffered** (`/chat`) skill chat using the Modus Python SDK.

## Setup

Create a token at **app.modus.com → Settings → API Tokens**, then export it in your shell (the app does **not** read `.env` files):

```bash
export MODUS_API_KEY=modus_xxx
```

The client uses `https://api.modus.com` by default. For staging or another host, pass `base_url` when constructing `modus.Modus()` in `app.py`.

## Run

From this directory:

```bash
pip install modus-sdk streamlit   # or: uv sync && uv run ...
streamlit run app.py
```

From the monorepo root (local SDK development):

```bash
export MODUS_API_KEY=modus_xxx
bash scripts/sdk-python/ensure-uv.sh run \
  --with streamlit \
  streamlit run examples/apps/modus_skill_chat/app.py
```

(`ensure-uv.sh` already runs from `sdk/python/modus-sdk` — do not pass `--directory`.)

Open the URL Streamlit prints (default `http://localhost:8501`).

## Usage

- Pick an **active** skill and model in the sidebar.
- Type a message at the bottom — it is sent to **both** panels in parallel.
- Left: tokens from `/chat/stream`. Right: full reply from `/chat`.
- Endpoint paths and `thread_id` values are shown per panel for debugging.
