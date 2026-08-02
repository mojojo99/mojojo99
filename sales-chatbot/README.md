# Sales Chatbot — Leadership Training & Teambuilding

An AI sales assistant (powered by Claude) that answers client enquiries on your
**website**, **WhatsApp**, and **email** — so your sales team can focus on
closing deals instead of answering the same questions all day.

## What it does

| Capability | How |
|---|---|
| Answers programme & pricing questions | From an editable knowledge base (`app/knowledge/offerings.md`) — it never invents prices |
| Website live chat | One `<script>` tag embeds a chat bubble on your site |
| WhatsApp auto-reply | Meta WhatsApp Business Cloud API webhook |
| Email auto-reply | Polls your inbox, drafts replies (draft or auto mode) |
| Captures leads | Name/company/email/phone saved to `data/leads.csv` |
| Creates proposals | Branded PDF quotation with a download link |
| Creates invoices | Branded PDF invoice — **held for your approval by default** |
| Escalates to humans | Complaints, custom discounts, contracts → flagged for the team |

Safety first: `EMAIL_MODE=draft` and `INVOICE_MODE=draft` are the defaults —
the bot **prepares** replies and invoices, and a human approves them with
`python approve.py` before anything reaches a client. Switch either to `auto`
once you trust it.

---

## What you need (accounts & keys)

1. **A Claude API key** (required) — sign up at
   [platform.claude.com](https://platform.claude.com), add billing, create an
   API key. Typical cost: a few cents per conversation.
2. **A server to run this on** (required) — any small VPS or PaaS works:
   Railway, Render, Fly.io, DigitalOcean (~USD 5–10/month). It must have a
   public HTTPS URL for the widget and the WhatsApp webhook.
3. **WhatsApp Business Cloud API** (only for WhatsApp) — free from Meta:
   - Create an app at [developers.facebook.com](https://developers.facebook.com)
     → type "Business" → add the **WhatsApp** product.
   - You get a test number instantly; to use **your own business number** you
     must verify your business and register the number (it can't be
     simultaneously used in the normal WhatsApp/WA Business app).
   - You need: a permanent **access token** (create a System User in Meta
     Business Settings) and your **Phone Number ID**.
4. **An email account with IMAP/SMTP** (only for email) — e.g. Gmail or
   Google Workspace: enable 2-factor auth, then create an **App Password** at
   myaccount.google.com/apppasswords. Best practice: use a dedicated address
   like `sales@yourcompany.com`, not your personal inbox — the bot replies to
   **every unseen email** in the inbox it watches.

---

## Setup (15 minutes)

```bash
cd sales-chatbot
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env: at minimum set ANTHROPIC_API_KEY and your company details
```

**Edit your knowledge base** — open `app/knowledge/offerings.md` and replace
the placeholder programmes, prices, and FAQs with your real ones. This is the
single source of truth for everything the bot tells clients. You can add more
`.md` files to that folder (e.g. `about-us.md`, `trainers.md`) — all are
loaded automatically.

**Start the server:**

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open <http://localhost:8000/widget/demo> and chat with the bot. 🎉

---

## Channel 1: Website widget

Once deployed with a public URL (set `PUBLIC_BASE_URL` in `.env`), add this
single line to your website, before `</body>`:

```html
<script src="https://YOUR-BOT-SERVER/widget/chat.js" defer></script>
```

Optional customisation:

```html
<script src="https://YOUR-BOT-SERVER/widget/chat.js" defer
        data-title="Ask us about training!"
        data-color="#0d7a3f"
        data-greeting="Hi! How can we help your team grow?"></script>
```

Works on Wix, WordPress, Squarespace, Shopify — anywhere you can paste an HTML
snippet.

## Channel 2: WhatsApp

1. Fill in `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, and pick any
   random `WHATSAPP_VERIFY_TOKEN` in `.env`.
2. In the Meta app dashboard → WhatsApp → **Configuration** → Webhook:
   - Callback URL: `https://YOUR-BOT-SERVER/webhooks/whatsapp`
   - Verify token: the same `WHATSAPP_VERIFY_TOKEN` value
   - Subscribe to the **messages** field.
3. Message your WhatsApp business number — the bot replies.

Note: WhatsApp's 24-hour rule means the bot can freely reply to clients who
messaged you within the last 24 h. Messaging clients *first* (outside 24 h)
requires pre-approved templates — that's a Meta rule, not a bot limitation.

## Channel 3: Email

1. Fill in the `IMAP_*` / `SMTP_*` / `EMAIL_*` values in `.env`.
2. Run the email worker (as a second process, alongside the web server):

```bash
python -m app.email_bot
```

- `EMAIL_MODE=draft` (default): replies are saved to `data/outbox/` as `.eml`
  files. Review and send them with `python approve.py`.
- `EMAIL_MODE=auto`: the bot replies to clients directly.

## The approval console

```bash
python approve.py
```

Shows every drafted email reply and every generated invoice waiting for
approval, plus conversations the bot escalated to the team. Approve, discard,
or keep each item.

## Leads

Every captured lead lands in `data/leads.csv` — open it in Excel/Sheets, or
import it into your CRM.

---

## Deploying (example: any Linux VPS)

```bash
# Web server (widget + WhatsApp + PDFs)
uvicorn app.main:app --host 0.0.0.0 --port 8000
# Email worker
python -m app.email_bot
```

Run both under a process manager (systemd, pm2, Docker, or your PaaS's
worker feature) and put HTTPS in front (Caddy/nginx/your PaaS does this
automatically). Set `PUBLIC_BASE_URL` to the final https URL.

## Customising the bot's behaviour

- **What it knows** → edit `app/knowledge/*.md`
- **How it behaves/sounds** → edit the system prompt in `app/agent.py`
- **PDF branding** → colours & layout in `app/documents.py`
- **Widget look** → `widget/chat.js` (or pass `data-color` / `data-title`)
- **Model** → `CLAUDE_MODEL` in `.env` (default `claude-opus-5`; use
  `claude-sonnet-5` for lower cost, `claude-haiku-4-5` for high volume)

## Costs (rough)

| Item | Cost |
|---|---|
| Claude API | ~USD 0.01–0.05 per conversation on Opus 5 (prompt caching enabled) |
| Hosting | ~USD 5–10/month |
| WhatsApp Cloud API | Free for user-initiated conversations (Meta's service conversations) |
| Email | Free (your existing account) |

## Limitations & honest notes

- The bot only knows what's in the knowledge base — keep it updated.
- WhatsApp requires Meta business verification to use your real number.
- Email replies handle plain-text enquiries; attachments are ignored.
- Invoices/proposals are simple branded PDFs — for accounting-grade invoices
  (GST reporting, numbering sequences), connect your accounting tool (e.g.
  Xero/QuickBooks) or keep `INVOICE_MODE=draft` and issue the final invoice
  from your accounting system, using the bot's draft as the source.
- Always keep `draft` mode on for at least the first couple of weeks and
  review what the bot is saying via `data/conversations/`.
