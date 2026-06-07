# Modus Skill Chat (Streamlit)

Optional interactive demo: compare **streaming** (`client.skills.chat_stream()`) vs **buffered** (`client.skills.chat()`) skill chat side by side.

## Setup

Create an API token in the Modus app (**Settings → API Tokens** on your Modus home page), then export it in your shell (the app does **not** read `.env` files):

```bash
export MODUS_API_KEY=modus_xxx
```

## Run

From this directory:

```bash
pip install modus-sdk streamlit
streamlit run app.py
```

Open the URL Streamlit prints (default `http://localhost:8501`).

## Usage

- Pick an **active** skill and model in the sidebar.
- Type a message at the bottom — it is sent to **both** panels in parallel.
- Left: tokens arrive as they stream. Right: the full reply appears when complete.
