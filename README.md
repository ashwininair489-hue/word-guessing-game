# 🚀 Word Guessing Game

A small full stack word guessing game: a landing page, a dark single-page game,
and a Flask server that owns the secret word.

The answer never reaches the browser while a round is in play. The page only
receives the masked word (`_ _ _ _ o _ k`), which letters are revealed, how many
attempts are left and the score. The word is shown when you win or lose.

- **Landing page** — `/` explains the game and links into it.
- **Game** — `/play` is the game itself, one letter at a time.
- **API** — `/api/*` is a small JSON API the page talks to.

Built with **Flask 3 on Python 3.12**, with no database and no build step, so it
deploys to [Vercel](https://vercel.com) as a single serverless function.

## Screens

| Landing | Game |
| --- | --- |
| Hero, rules, score values and a call to action | Word slots, letter input, hearts and score |

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open <http://localhost:5000>. Environment variables:

| Name         | Default                     | Meaning                                      |
| ------------ | --------------------------- | -------------------------------------------- |
| `PORT`       | `5000`                      | Port to listen on (binds `0.0.0.0`).          |
| `DEBUG`      | `0`                         | Set to `1` for the Flask reloader.            |
| `SECRET_KEY` | built-in development secret | Signs session cookies — set this in production. |

## How to play

- A word is picked from a category (animals, food, nature, technology, places,
  music) and shown as one dash per letter.
- Guess one letter at a time. A correct letter reveals every occurrence and
  scores **10 points**.
- A wrong guess costs one of your **12 hearts**.
- Solve the word to earn **5 bonus points per remaining heart**.
- Run out of hearts and the word is revealed.

Typing a letter fills the box and `Enter` submits, so the whole game is playable
from the keyboard.

## API

Every endpoint returns the same public game state (`letters`, `masked`,
`attempts_left`, `score`, `status`, `message`, `word` once the round is over).

| Method | Path            | Body               | Purpose                 |
| ------ | --------------- | ------------------ | ----------------------- |
| `GET`  | `/`             | –                  | Landing page.           |
| `GET`  | `/play`         | –                  | Game page.              |
| `GET`  | `/api/state`    | –                  | Current state as JSON.  |
| `POST` | `/api/guess`    | `{"letter": "o"}`  | Submit one letter.      |
| `POST` | `/api/new-game` | –                  | Start a fresh word.     |
| `GET`  | `/healthz`      | –                  | Health probe.           |

### How state survives serverless

Vercel runs requests in stateless functions, so nothing is held in memory. The
signed session cookie stores only a round **seed** plus your progress (guessed
letters, hearts, score). The server maps the seed to a word with
`HMAC-SHA256(SECRET_KEY, seed)`, which means:

- the same cookie always resumes the same word, on any instance;
- the word itself is never stored in the cookie, so it cannot be read out of it;
- sessions are signed, so attempts and score cannot be tampered with.

Because the mapping depends on `SECRET_KEY`, set a stable value in production or
in-progress rounds will reset when the key changes.

## Deploy to Vercel

The repository is already shaped for Vercel's Flask preset:

- `app.py` exposes the top-level `app` object Vercel looks for;
- `public/` holds CSS and JS, which Vercel serves from its CDN;
- `templates/` is rendered by Flask;
- `requirements.txt` pins Flask, `.python-version` pins Python 3.12.

### Option A — Vercel CLI

```bash
npm i -g vercel      # once
vercel login
vercel                # preview deployment
vercel --prod         # production deployment
```

### Option B — Git integration

1. Import the repository at <https://vercel.com/new>.
2. Vercel detects Flask automatically — leave the build and output settings alone.
3. Under **Settings → Environment Variables**, add `SECRET_KEY` with a long
   random string (for example `python -c "import secrets; print(secrets.token_hex(32))"`).
4. Deploy.

Once the deployment is live, the landing page is at `/` and the game at `/play`.
Every push to `main` redeploys automatically.

## Project layout

```
app.py                 Flask app: rules, state, routes
words.py               word bank grouped by category
templates/index.html   landing page
templates/play.html    game page
public/styles.css      dark theme for both pages
public/game.js         game rendering + API calls
requirements.txt       pinned Python 3 dependency
vercel.json            function settings for Vercel
.python-version        Python runtime version for Vercel
```

## Notes

- `SECRET_KEY` falls back to a development value so `python app.py` works out of
  the box; always set a real one in production.
- Word list ordering is part of the seed → word mapping. Reordering `words.py`
  changes which word an existing cookie resolves to (it stays valid, just
  different), so rounds in progress can change after a word list edit.
