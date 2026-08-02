"""Central configuration — everything comes from environment variables / .env."""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Claude
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-5")

# Business identity
COMPANY_NAME = os.getenv("COMPANY_NAME", "Your Training Company")
COMPANY_EMAIL = os.getenv("COMPANY_EMAIL", "sales@example.com")
COMPANY_PHONE = os.getenv("COMPANY_PHONE", "")
COMPANY_ADDRESS = os.getenv("COMPANY_ADDRESS", "")
COMPANY_WEBSITE = os.getenv("COMPANY_WEBSITE", "")
CURRENCY = os.getenv("CURRENCY", "SGD")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000").rstrip("/")

# Autonomy: "draft" = human approves before send, "auto" = bot sends directly
EMAIL_MODE = os.getenv("EMAIL_MODE", "draft").lower()
INVOICE_MODE = os.getenv("INVOICE_MODE", "draft").lower()

# WhatsApp Cloud API
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "change-me")

# Email
IMAP_HOST = os.getenv("IMAP_HOST", "imap.gmail.com")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EMAIL_POLL_SECONDS = int(os.getenv("EMAIL_POLL_SECONDS", "120"))

# Storage
DATA_DIR = BASE_DIR / "data"
DOCUMENTS_DIR = DATA_DIR / "documents"      # generated PDFs
OUTBOX_DIR = DATA_DIR / "outbox"            # drafts awaiting human approval
CONVERSATIONS_DIR = DATA_DIR / "conversations"
LEADS_FILE = DATA_DIR / "leads.csv"
KNOWLEDGE_DIR = BASE_DIR / "app" / "knowledge"

for _d in (DATA_DIR, DOCUMENTS_DIR, OUTBOX_DIR, CONVERSATIONS_DIR):
    _d.mkdir(parents=True, exist_ok=True)
