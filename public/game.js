(function () {
  "use strict";

  var ICONS = {
    success: "✅",
    error: "❌",
    info: "💡",
    win: "🎉",
    lose: "💔"
  };

  var boot = document.getElementById("initial-state");
  var state = JSON.parse(boot.textContent || "{}");

  var panel = document.querySelector(".word-panel");
  var wordEl = document.getElementById("word");
  var form = document.getElementById("guess-form");
  var input = document.getElementById("guess-input");
  var button = document.getElementById("guess-button");
  var feedback = document.getElementById("feedback");
  var feedbackIcon = document.getElementById("feedback-icon");
  var feedbackText = document.getElementById("feedback-text");
  var attemptsEl = document.getElementById("attempts-left");
  var scoreEl = document.getElementById("score");
  var categoryChip = document.getElementById("category-chip");
  var lettersChip = document.getElementById("letters-chip");
  var wrongChip = document.getElementById("wrong-chip");
  var wrongLetters = document.getElementById("wrong-letters");
  var newGameButton = document.getElementById("new-game");

  var busy = false;
  var previousGuessed = (state.guessed || []).slice();

  function isPlaying() {
    return state.status === "playing";
  }

  /* -- painting ---------------------------------------------------------- */

  function paintWord(animate) {
    var previous = previousGuessed;
    wordEl.innerHTML = "";

    (state.letters || []).forEach(function (slot) {
      var span = document.createElement("span");
      span.className = "slot";
      span.textContent = slot.revealed ? slot.char : "_";

      if (slot.revealed) {
        span.className += " is-revealed";
        var isNew = animate && previous.indexOf(slot.char) === -1;
        if (!isNew) {
          /* only letters uncovered by this guess should pop in */
          span.style.animation = "none";
        }
      }
      wordEl.appendChild(span);
    });
  }

  function paint() {
    paintWord(true);

    wordEl.setAttribute("data-length", state.word_length);
    attemptsEl.textContent = state.attempts_left;
    scoreEl.textContent = state.score;
    categoryChip.textContent = state.category;
    lettersChip.textContent = state.word_length + " letters";

    if (state.wrong && state.wrong.length) {
      wrongLetters.textContent = state.wrong.join(" ").toUpperCase();
      wrongChip.hidden = false;
    } else {
      wrongChip.hidden = true;
    }

    feedback.className = "feedback is-" + state.message_type;
    feedbackIcon.textContent = ICONS[state.message_type] || "💡";
    feedbackText.textContent = state.message;

    panel.classList.toggle("is-solved", state.status === "won");
    panel.classList.toggle("is-lost", state.status === "lost");

    input.disabled = !isPlaying();
    input.hidden = !isPlaying();
    button.disabled = false;
    button.textContent = isPlaying() ? "Guess Letter" : "Play Again";

    if (isPlaying()) {
      input.value = "";
      input.focus();
    } else {
      input.value = "";
    }
  }

  function shake() {
    panel.classList.remove("is-shaking");
    /* force a reflow so the animation can be retriggered */
    void panel.offsetWidth;
    panel.classList.add("is-shaking");
  }

  /* -- server calls ------------------------------------------------------ */

  function post(url, body) {
    return fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
      body: JSON.stringify(body || {})
    }).then(function (response) {
      if (!response.ok) {
        throw new Error("Request failed with " + response.status);
      }
      return response.json();
    });
  }

  function apply(next, previous) {
    previousGuessed = (previous.guessed || []).slice();
    state = next;
    paint();
    if (next.status === "lost") {
      shake();
    }
  }

  function submitGuess() {
    if (busy || !isPlaying()) {
      return;
    }

    var letter = (input.value || "").replace(/[^a-zA-Z]/g, "");
    if (letter.length !== 1) {
      state.message = "Enter a single letter from A to Z.";
      state.message_type = "error";
      feedback.className = "feedback is-error";
      feedbackIcon.textContent = ICONS.error;
      feedbackText.textContent = state.message;
      input.value = "";
      input.focus();
      return;
    }

    busy = true;
    input.disabled = true;

    var before = state;
    post("/api/guess", { letter: letter })
      .then(function (next) {
        var wasWrong = next.outcome === "wrong";
        apply(next, before);
        if (wasWrong) {
          shake();
        }
      })
      .catch(function () {
        state.message = "Could not reach the server. Try again.";
        state.message_type = "error";
        feedback.className = "feedback is-error";
        feedbackIcon.textContent = ICONS.error;
        feedbackText.textContent = state.message;
        input.disabled = false;
        input.focus();
      })
      .then(function () {
        busy = false;
      });
  }

  function startNewGame() {
    if (busy) {
      return;
    }
    busy = true;
    var before = state;

    post("/api/new-game", {})
      .then(function (next) {
        apply(next, before);
        state.message = "New word picked. Good luck!";
        state.message_type = "info";
        feedback.className = "feedback is-info";
        feedbackIcon.textContent = ICONS.info;
        feedbackText.textContent = state.message;
      })
      .catch(function () {
        state.message = "Could not start a new game. Try again.";
        state.message_type = "error";
        feedback.className = "feedback is-error";
        feedbackIcon.textContent = ICONS.error;
        feedbackText.textContent = state.message;
      })
      .then(function () {
        busy = false;
      });
  }

  /* -- events ------------------------------------------------------------ */

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    if (isPlaying()) {
      submitGuess();
    } else {
      startNewGame();
    }
  });

  newGameButton.addEventListener("click", startNewGame);

  input.addEventListener("input", function () {
    var cleaned = (input.value || "").replace(/[^a-zA-Z]/g, "").toLowerCase();
    input.value = cleaned.slice(-1).toUpperCase();
  });

  document.addEventListener("keydown", function (event) {
    if (event.metaKey || event.ctrlKey || event.altKey) {
      return;
    }
    if (/^[a-zA-Z]$/.test(event.key) && document.activeElement !== input) {
      if (!isPlaying()) {
        return;
      }
      input.value = event.key.toUpperCase();
      input.focus();
      event.preventDefault();
    }
  });

  paint();
})();
