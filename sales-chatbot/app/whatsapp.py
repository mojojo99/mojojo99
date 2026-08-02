"""Sending replies via the Meta WhatsApp Business Cloud API."""

import httpx

from . import config

GRAPH_URL = "https://graph.facebook.com/v21.0"


def send_text(to: str, text: str) -> None:
    """Send a plain text WhatsApp message. `to` is the client's phone number."""
    if not (config.WHATSAPP_ACCESS_TOKEN and config.WHATSAPP_PHONE_NUMBER_ID):
        raise RuntimeError("WhatsApp is not configured (see .env)")
    # WhatsApp caps a text body at 4096 chars
    for chunk in _chunks(text, 4000):
        resp = httpx.post(
            f"{GRAPH_URL}/{config.WHATSAPP_PHONE_NUMBER_ID}/messages",
            headers={"Authorization": f"Bearer {config.WHATSAPP_ACCESS_TOKEN}"},
            json={
                "messaging_product": "whatsapp",
                "to": to,
                "type": "text",
                "text": {"body": chunk, "preview_url": True},
            },
            timeout=30,
        )
        resp.raise_for_status()


def _chunks(text: str, size: int):
    for i in range(0, len(text), size):
        yield text[i:i + size]


def parse_incoming(payload: dict) -> list[dict]:
    """Extract text messages from a webhook payload.

    Returns a list of {"from": phone, "text": body, "name": profile_name}.
    Ignores statuses (delivered/read receipts) and non-text messages.
    """
    out = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            contacts = {c.get("wa_id"): c.get("profile", {}).get("name", "")
                        for c in value.get("contacts", [])}
            for msg in value.get("messages", []):
                if msg.get("type") == "text":
                    out.append({
                        "from": msg.get("from", ""),
                        "text": msg.get("text", {}).get("body", ""),
                        "name": contacts.get(msg.get("from", ""), ""),
                    })
    return out
