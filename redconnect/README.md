# RedConnect — Community Blood Donation Platform

## Run locally
- Create a virtualenv (optional) and install deps:
```
pip install -r requirements.txt
```
- Start the server:
```
python app.py
```
- Open http://localhost:5000

On first run, SQLite DB `redconnect.db` is created with seed data.

## Tech
- Flask, SQLAlchemy (SQLite)
- Bootstrap 5 + custom CSS (white/deep red theme)
- Flask-Mail placeholders (configure env vars to enable)

## Env variables (optional)
- `SECRET_KEY` — Flask secret
- `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USE_TLS`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_DEFAULT_SENDER`

## Deploy notes
- Render/PythonAnywhere: build by installing `requirements.txt`, run `python app.py` (or use WSGI/gunicorn).
- Persist `redconnect.db` or switch to managed DB.
