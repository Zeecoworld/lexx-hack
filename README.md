# RightsDesk (Django)

Plain-language legal help for Nigeria - a rights chatbot and a contract clause
risk-checker in one app. Built for **LexHack 2026** (Access to Justice & Civic
Tech / Legal Automation).

## What it does

- **Ask a question** - a chat that explains tenant, consumer, and labour
  rights in plain English and suggests concrete next steps.
- **Check a document** - paste a lease, offer letter, or contract and get
  clause-by-clause risk flags (low / medium / high) with plain-language
  reasons.

Both features run on a **local, rule-based NLP engine** (`core/nlp_engine.py`)
 - keyword classification for the chatbot, regex-based clause pattern
matching for the document checker. No external AI API, no API key, no
network dependency, nothing that can fail or run out of quota during a demo.

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

python manage.py runserver
```

Open http://127.0.0.1:8000/. That's it - no environment variables, no API
keys, no database migrations (the app has no models).

## Deploying to Render

This zip is Render-ready: `whitenoise` serves static files and `gunicorn`
runs the app, both already in `requirements.txt`.

**Option A - Blueprint (fastest):** push this repo to GitHub, then in Render
click **New > Blueprint** and point it at the repo. `render.yaml` sets
everything up automatically (build command, start command, a generated
`DJANGO_SECRET_KEY`).

**Option B - manual Web Service:**
1. Push this repo to GitHub.
2. Render dashboard → **New > Web Service** → connect the repo.
3. Build command: `./build.sh`
4. Start command: `gunicorn rightsdesk.wsgi`
5. Add an environment variable `DJANGO_DEBUG` = `0`.
6. Deploy. Render sets `RENDER_EXTERNAL_HOSTNAME` automatically, which the
   app already reads for `ALLOWED_HOSTS`/CSRF - no extra config needed.

Either way, no database and no API key are required - deploy should just work.

## Tech stack

Django, vanilla JS (fetch), a local rule-based NLP engine (Python `re` +
keyword scoring - no external ML library), Google Fonts (Fraunces + Inter).

## How the NLP engine works

- **Chatbot:** `classify_question()` scores the user's message against
  keyword lists for tenancy, consumer, and labour sub-categories, and
  returns a templated, plain-language answer with concrete next steps for
  the best-scoring category (or a fallback prompt if nothing matches well).
- **Document checker:** `analyze_document()` splits the pasted text into
  clause-sized chunks and matches each against a small library of regex
  patterns for common risk signals (auto-renewal, waived rights, unlimited
  liability, non-compete, penalties, indefinite terms, etc.), each tagged
  with a risk level and a plain-language reason.

Both are easy to extend - add an entry to `CATEGORIES` or `CLAUSE_PATTERNS`
in `core/nlp_engine.py` and it's picked up automatically.

## Notes for judges

This is general information, not legal advice - the app says so on-screen.
It's scoped to Nigerian tenant/consumer/labour principles as a starting
jurisdiction; the keyword lists and templates can be swapped for another
country's law with no architecture changes.
