"""FastAPI server: website chat widget API + WhatsApp webhook + PDF downloads.

Run with:  uvicorn app.main:app --host 0.0.0.0 --port 8000
"""

import secrets
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel, Field

from . import agent, config, whatsapp

app = FastAPI(title="Sales Chatbot", docs_url=None, redoc_url=None)

# The widget is embedded on your website, so allow cross-origin calls to /chat.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to your website's domain in production
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

WIDGET_DIR = Path(__file__).resolve().parent.parent / "widget"


# ── Website chat ─────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_id: str | None = None


@app.post("/chat")
def chat(req: ChatRequest):
    session_id = req.session_id or secrets.token_urlsafe(12)
    answer = agent.reply("web", session_id, req.message)
    return {"reply": answer, "session_id": session_id}


@app.get("/widget/chat.js")
def widget_js():
    return FileResponse(WIDGET_DIR / "chat.js", media_type="application/javascript")


@app.get("/widget/demo")
def widget_demo():
    return FileResponse(WIDGET_DIR / "demo.html", media_type="text/html")


# ── Generated documents (proposals / approved invoices) ──────────────────────

@app.get("/documents/{filename}")
def get_document(filename: str):
    # basename() guard against path traversal
    safe = Path(filename).name
    path = config.DOCUMENTS_DIR / safe
    if not safe.endswith(".pdf") or not path.exists():
        raise HTTPException(404, "Document not found")
    return FileResponse(path, media_type="application/pdf", filename=safe)


# ── WhatsApp webhook (Meta Cloud API) ────────────────────────────────────────

@app.get("/webhooks/whatsapp")
def whatsapp_verify(
    hub_mode: str = Query("", alias="hub.mode"),
    hub_token: str = Query("", alias="hub.verify_token"),
    hub_challenge: str = Query("", alias="hub.challenge"),
):
    """Meta calls this once when you register the webhook."""
    if hub_mode == "subscribe" and hub_token == config.WHATSAPP_VERIFY_TOKEN:
        return PlainTextResponse(hub_challenge)
    raise HTTPException(403, "Verification failed")


def _handle_whatsapp_message(sender: str, text: str) -> None:
    try:
        answer = agent.reply("whatsapp", sender, text)
        if answer:
            whatsapp.send_text(sender, answer)
    except Exception as exc:  # noqa: BLE001 — webhook worker must not crash
        print(f"[whatsapp] Error replying to {sender}: {exc}")


@app.post("/webhooks/whatsapp")
async def whatsapp_webhook(request: Request, background: BackgroundTasks):
    payload = await request.json()
    for msg in whatsapp.parse_incoming(payload):
        # Reply in the background so Meta gets a fast 200 (they retry slow webhooks)
        background.add_task(_handle_whatsapp_message, msg["from"], msg["text"])
    return {"status": "ok"}


@app.get("/health")
def health():
    return {"status": "ok", "model": config.CLAUDE_MODEL}
