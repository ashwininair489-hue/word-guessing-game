"""Word Guessing Game - a small full stack Flask app.

Python 3.12 compatible and ready for Vercel: the module exposes a top level
``app`` WSGI object, static files live in ``public/`` and every request is
stateless, so it runs on serverless functions.

The secret word is never stored in the session cookie. The cookie only holds a
random seed which the server maps to a word with an HMAC, so the answer cannot
be read out of the cookie even though the rest of the round is client-side.
"""

import hashlib
import hmac
import os
import secrets

from flask import Flask, jsonify, render_template, request, session

import words

# ---------------------------------------------------------------------------
# Game rules
# ---------------------------------------------------------------------------

MAX_ATTEMPTS = 12          # hearts you start each round with
POINTS_PER_LETTER = 10     # score for a letter that is in the word
WIN_BONUS_PER_ATTEMPT = 5  # extra points for every unused attempt on a win

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    # On Vercel this folder is served by the CDN at /<file>; locally Flask does it.
    static_folder=os.path.join(BASE_DIR, "public"),
    static_url_path="",
)

app.config.update(
    # Set SECRET_KEY in the Vercel project settings for production.
    SECRET_KEY=os.environ.get("SECRET_KEY") or "word-guessing-game-dev-secret",
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("VERCEL_ENV") == "production",
    SEND_FILE_MAX_AGE_DEFAULT=0,
)

FEEDBACK_ICONS = {
    "success": "\u2705",
    "error": "\u274c",
    "info": "\U0001f4a1",
    "win": "\U0001f389",
    "lose": "\U0001f494",
}

FEEDBACK_ICONS_DEFAULT = "\U0001f4a1"


def asset_version():
    """Newest mtime in public/, used to bust browser caches on deploy."""
    folder = os.path.join(BASE_DIR, "public")
    latest = 0
    try:
        for name in os.listdir(folder):
            path = os.path.join(folder, name)
            if os.path.isfile(path):
                latest = max(latest, int(os.path.getmtime(path)))
    except OSError:
        pass
    return latest


app.jinja_env.globals["feedback_icon"] = lambda kind: FEEDBACK_ICONS.get(
    kind, FEEDBACK_ICONS_DEFAULT
)
app.jinja_env.globals["asset_version"] = asset_version


# ---------------------------------------------------------------------------
# Word selection: seed in the cookie, word on the server
# ---------------------------------------------------------------------------


def word_for_seed(seed):
    """Map a random seed to a (word, category) pair, deterministically."""
    pairs = words.all_words()
    key = str(app.config["SECRET_KEY"]).encode("utf-8")
    digest = hmac.new(key, seed.encode("utf-8"), hashlib.sha256).digest()
    index = int.from_bytes(digest[:8], "big") % len(pairs)
    return pairs[index]


# ---------------------------------------------------------------------------
# Game state
# ---------------------------------------------------------------------------


class Game(object):
    """One player's round: the secret word plus what they have guessed."""

    def __init__(self, seed, guessed=None, wrong=None, attempts_left=MAX_ATTEMPTS,
                 score=0, status="playing", message="Guess a letter to start.",
                 message_type="info"):
        self.seed = seed
        self.word, self.category = word_for_seed(seed)
        self.guessed = set(guessed or [])
        self.wrong = list(wrong or [])
        self.attempts_left = attempts_left
        self.score = score
        self.status = status
        self.message = message
        self.message_type = message_type

    # -- persistence ------------------------------------------------------

    @classmethod
    def from_session(cls):
        seed = session.get("seed")
        if not seed:
            game = cls.new()
            game.save()
            return game
        return cls(
            seed=seed,
            guessed=session.get("guessed"),
            wrong=session.get("wrong"),
            attempts_left=session.get("attempts_left", MAX_ATTEMPTS),
            score=session.get("score", 0),
            status=session.get("status", "playing"),
            message=session.get("message", "Guess a letter to start."),
            message_type=session.get("message_type", "info"),
        )

    @classmethod
    def new(cls):
        return cls(seed=secrets.token_hex(16))

    def save(self):
        session["seed"] = self.seed
        session["guessed"] = sorted(self.guessed)
        session["wrong"] = self.wrong
        session["attempts_left"] = self.attempts_left
        session["score"] = self.score
        session["status"] = self.status
        session["message"] = self.message
        session["message_type"] = self.message_type

    # -- rules ------------------------------------------------------------

    def is_solved(self):
        return all(letter in self.guessed for letter in self.word)

    def _finish(self, status, message, message_type):
        self.status = status
        self.message = message
        self.message_type = message_type

    def guess(self, letter):
        """Apply one single-letter guess and return a short outcome."""
        if self.status != "playing":
            return "over"

        if letter in self.guessed or letter in self.wrong:
            self.message = "%s is already guessed." % letter.upper()
            self.message_type = "info"
            return "repeat"

        if letter in self.word:
            self.guessed.add(letter)
            self.score += POINTS_PER_LETTER
            if self.is_solved():
                self.score += self.attempts_left * WIN_BONUS_PER_ATTEMPT
                self._finish("won", "You got it! The word was %s." % self.word.upper(), "win")
            else:
                self.message = "Correct Guess!"
                self.message_type = "success"
            return "correct"

        self.wrong.append(letter)
        self.attempts_left -= 1
        if self.attempts_left <= 0:
            self.attempts_left = 0
            self._finish("lost", "Out of attempts! The word was %s." % self.word.upper(), "lose")
        else:
            self.message = "Wrong Guess!"
            self.message_type = "error"
        return "wrong"

    def public_state(self):
        """Everything the browser is allowed to know."""
        # Show the whole word once the round is over.
        revealed = self.status != "playing"
        is_open = lambda c: revealed or c in self.guessed
        return {
            "letters": [{"char": c, "revealed": is_open(c)} for c in self.word],
            "masked": "".join(c if is_open(c) else "_" for c in self.word),
            "word_length": len(self.word),
            "category": self.category,
            "guessed": sorted(self.guessed),
            "wrong": sorted(self.wrong),
            "attempts_left": self.attempts_left,
            "attempts_max": MAX_ATTEMPTS,
            "score": self.score,
            "status": self.status,
            "message": self.message,
            "message_type": self.message_type,
            "word": self.word if self.status != "playing" else None,
        }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.route("/")
def landing():
    return render_template("index.html")


@app.route("/play")
def play():
    game = Game.from_session()
    game.save()
    return render_template("play.html", initial_state=game.public_state())


@app.route("/api/state")
def api_state():
    game = Game.from_session()
    game.save()
    return jsonify(game.public_state())


@app.route("/api/new-game", methods=["POST"])
def api_new_game():
    game = Game.new()
    game.save()
    return jsonify(game.public_state())


@app.route("/api/guess", methods=["POST"])
def api_guess():
    payload = request.get_json(silent=True) or {}
    raw = payload.get("letter", "")
    letter = raw.strip().lower() if isinstance(raw, str) else ""

    game = Game.from_session()

    if len(letter) != 1 or not letter.isalpha():
        state = game.public_state()
        state["message"] = "Enter a single letter from A to Z."
        state["message_type"] = "error"
        return jsonify(state)

    outcome = game.guess(letter)
    game.save()
    state = game.public_state()
    state["outcome"] = outcome
    return jsonify(state)


@app.route("/healthz")
def healthz():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("DEBUG", "0") == "1"
    print("Word Guessing Game on http://0.0.0.0:%d" % port)
    app.run(host="0.0.0.0", port=port, debug=debug, threaded=True)
