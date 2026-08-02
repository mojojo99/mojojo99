"""Email channel: polls the inbox over IMAP, drafts replies with the agent.

EMAIL_MODE=draft (default): replies are saved to data/outbox/ as .eml files
for a human to review and send (drag into your mail client, or flip to auto).
EMAIL_MODE=auto: replies are sent directly via SMTP.
"""

import email
import imaplib
import json
import re
import smtplib
import time
from datetime import datetime, timezone
from email.header import decode_header, make_header
from email.mime.text import MIMEText
from email.utils import parseaddr

from . import agent, config


def _decode(value: str) -> str:
    try:
        return str(make_header(decode_header(value or "")))
    except Exception:  # noqa: BLE001
        return value or ""


def _body_text(msg: email.message.Message) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain" and not part.get_filename():
                payload = part.get_payload(decode=True)
                if payload:
                    return payload.decode(part.get_content_charset() or "utf-8", "replace")
        return ""
    payload = msg.get_payload(decode=True)
    if payload:
        return payload.decode(msg.get_content_charset() or "utf-8", "replace")
    return ""


def _strip_quoted(text: str) -> str:
    """Drop quoted history so the agent sees only the new message."""
    lines = []
    for line in text.splitlines():
        if line.startswith(">") or re.match(r"^On .+ wrote:$", line.strip()):
            break
        lines.append(line)
    return "\n".join(lines).strip() or text.strip()


def _build_reply(original: email.message.Message, to_addr: str, body: str) -> MIMEText:
    reply = MIMEText(body, "plain", "utf-8")
    subject = _decode(original.get("Subject", ""))
    reply["Subject"] = subject if subject.lower().startswith("re:") else f"Re: {subject}"
    reply["From"] = config.EMAIL_ADDRESS
    reply["To"] = to_addr
    if original.get("Message-ID"):
        reply["In-Reply-To"] = original["Message-ID"]
        reply["References"] = original["Message-ID"]
    return reply


def _send(reply: MIMEText) -> None:
    with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(config.EMAIL_ADDRESS, config.EMAIL_PASSWORD)
        smtp.send_message(reply)


def _save_draft(reply: MIMEText, sender: str) -> None:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    safe = re.sub(r"[^A-Za-z0-9@._-]", "_", sender)
    path = config.OUTBOX_DIR / f"email-{stamp}-{safe}.eml"
    path.write_text(reply.as_string(), encoding="utf-8")
    meta = config.OUTBOX_DIR / f"email-{stamp}-{safe}.json"
    meta.write_text(json.dumps({
        "type": "email_reply", "to": sender, "status": "awaiting_approval",
        "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }, indent=2), encoding="utf-8")
    print(f"[email] Draft saved for approval: {path.name}")


def process_inbox_once() -> int:
    """Fetch unseen emails, run the agent, reply or save drafts. Returns count."""
    handled = 0
    with imaplib.IMAP4_SSL(config.IMAP_HOST) as imap:
        imap.login(config.EMAIL_ADDRESS, config.EMAIL_PASSWORD)
        imap.select("INBOX")
        _, data = imap.search(None, "UNSEEN")
        for num in data[0].split():
            _, msg_data = imap.fetch(num, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])
            sender = parseaddr(msg.get("From", ""))[1]
            if not sender or sender.lower() == config.EMAIL_ADDRESS.lower():
                continue
            # Skip obvious automated mail
            if msg.get("Auto-Submitted", "no").lower() != "no" or "noreply" in sender.lower():
                continue

            subject = _decode(msg.get("Subject", ""))
            body = _strip_quoted(_body_text(msg))
            if not body:
                continue

            print(f"[email] New enquiry from {sender}: {subject!r}")
            answer = agent.reply("email", sender, f"Subject: {subject}\n\n{body}")
            reply = _build_reply(msg, sender, answer)

            if config.EMAIL_MODE == "auto":
                _send(reply)
                print(f"[email] Auto-replied to {sender}")
            else:
                _save_draft(reply, sender)
            handled += 1
    return handled


def run_forever() -> None:
    print(f"[email] Polling {config.EMAIL_ADDRESS} every {config.EMAIL_POLL_SECONDS}s "
          f"(mode: {config.EMAIL_MODE})")
    while True:
        try:
            process_inbox_once()
        except Exception as exc:  # noqa: BLE001 — keep the poller alive
            print(f"[email] Error: {exc}")
        time.sleep(config.EMAIL_POLL_SECONDS)


if __name__ == "__main__":
    run_forever()
