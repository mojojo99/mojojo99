"""Tiny approval console for draft mode.

Run:  python approve.py

Lists everything the bot has parked for human review (email drafts, invoices)
and lets you send/approve or discard each one.
"""

import email
import json
import smtplib
import sys

from app import config


def _send_eml(path) -> None:
    msg = email.message_from_string(path.read_text(encoding="utf-8"))
    with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(config.EMAIL_ADDRESS, config.EMAIL_PASSWORD)
        smtp.send_message(msg)


def main() -> None:
    items = sorted(config.OUTBOX_DIR.glob("*.json"))
    items = [p for p in items if p.name != "escalations.jsonl"]
    if not items:
        print("Outbox is empty — nothing awaiting approval. ✅")
        return

    for meta_path in items:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if meta.get("status") != "awaiting_approval":
            continue
        print("\n" + "─" * 60)
        print(f"Type:    {meta.get('type')}")
        print(f"Created: {meta.get('created')}")

        if meta["type"] == "email_reply":
            eml = meta_path.with_suffix(".eml")
            print(f"To:      {meta.get('to')}")
            print("\n" + eml.read_text(encoding="utf-8")[:2000])
            choice = input("\n[s]end / [d]iscard / [k]eep for later? ").strip().lower()
            if choice == "s":
                _send_eml(eml)
                meta["status"] = "sent"
                meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
                print("Sent. ✉️")
            elif choice == "d":
                eml.unlink(missing_ok=True)
                meta_path.unlink()
                print("Discarded.")

        elif meta["type"] == "invoice":
            pdf = config.DOCUMENTS_DIR / meta["file"]
            url = f"{config.PUBLIC_BASE_URL}/documents/{meta['file']}"
            print(f"Invoice: {pdf}")
            print(f"Link:    {url}")
            choice = input("\n[a]pprove (client can be sent the link) / [d]iscard / [k]eep? ").strip().lower()
            if choice == "a":
                meta["status"] = "approved"
                meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
                print(f"Approved — share this link with the client: {url}")
            elif choice == "d":
                pdf.unlink(missing_ok=True)
                meta_path.unlink()
                print("Discarded.")

    esc = config.OUTBOX_DIR / "escalations.jsonl"
    if esc.exists():
        lines = esc.read_text(encoding="utf-8").strip().splitlines()
        if lines:
            print("\n" + "─" * 60)
            print(f"⚠️  {len(lines)} conversation(s) flagged for human follow-up:")
            for line in lines[-10:]:
                e = json.loads(line)
                print(f"  [{e['urgency']}] {e['channel']}:{e['contact_id']} — {e['reason']}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
