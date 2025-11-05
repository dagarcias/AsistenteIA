# Personal Assistant

An all-in-one personal assistant for quick capture, reminders, daily briefings, and vault-aware question answering.

## Features

- **Quick capture**: Save notes and tasks from the CLI or HTTP endpoints.
- **Task reminders**: One-shot or recurring reminders with local notifications via APScheduler.
- **Daily briefing**: Summaries of today's agenda, overdue items, priorities, and recent notes.
- **Vault RAG**: Ask questions about documents stored in the local `vault/` folder (PDF, Markdown, or text).
- **API + mini-UI ready**: Exposes a FastAPI backend; can be paired with any frontend.

## Getting Started

1. **Install dependencies**

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure environment**

   Copy `.env.example` to `.env` and fill in the values. At minimum set `OPENAI_API_KEY`.

3. **Prepare the database**

   Tables are created automatically on startup. The default database lives at `assistant.db`.

4. **Run the API**

   ```bash
   uvicorn assistant.app.main:app --reload
   ```

   The API exposes the following main routes:

   - `POST /notes/` – create notes.
   - `POST /tasks/` – create tasks with optional reminders.
   - `GET /briefing/today` – daily summary.
   - `POST /ask/` – ask questions against your vault.

5. **Quick capture CLI**

   ```bash
   python -m assistant.app.cli note "Idea" "Follow up with marketing"
   python -m assistant.app.cli task "Submit report" --due "2024-05-30T09:00" --priority 1 --reminder 30
   ```

6. **Populate the vault**

   Drop `.pdf`, `.md`, or `.txt` files into the `vault/` folder. They are indexed on first query.

## Scheduling & Notifications

Reminders print notifications to stdout and log them; adjust `_notify` in `assistant/app/services/scheduler.py` to integrate with desktop notifications.

Recurring tasks support presets (`daily`, `weekly`, `weekdays`) or standard cron expressions.

## Notes

- The RAG pipeline uses ChromaDB for local embeddings; ensure the `CHROMA_DB_PATH` directory is writable.
- The default OpenAI model can be overridden via `OPENAI_MODEL`.
