# Game Mechanics

## Core loop

1. Everyone playing today gets the same secret word (`GET /api/game/today`
   never reveals it).
2. Player types a word, presses Enter.
3. Backend scores semantic closeness 0–100 and returns feedback text.
4. Player keeps guessing — no guess limit — until they hit the exact word
   (always scores 100).

## Scoring rules

- Semantic similarity only. Spelling, letter overlap, and sound are never
  factors — see `app/scoring.py`'s system prompt, which explicitly
  instructs the scoring backend to ignore them.
- The exact secret word always scores 100, checked via string normalization
  *before* any model call — this can never be affected by model drift.
- No other guess may display 100 (`scoring.calculate_score` clamps any
  non-exact 100 down to 99).
- Scores are clamped to [0, 100] regardless of what the backend returns.

## Feedback thresholds (configurable, `Settings.feedback_thresholds`)

| Score | Feedback |
|-------|----------|
| 0–19  | ❄️ Very cold |
| 20–39 | 🧊 Cold |
| 40–59 | 🌱 Getting warmer |
| 60–79 | 🔥 Warm |
| 80–89 | 🔥🔥 Hot |
| 90–94 | 🔥🔥 Very hot |
| 95–99 | 🚨 Extremely close |
| 100   | 🎉 Correct |

## Calibration anchors

The scoring backend is anchored with these examples (from the original
spec) so its 0–100 scale stays consistent across secret words:

```
ocean, computer  -> 4
ocean, mountain  -> 17
ocean, fish      -> 62
ocean, beach     -> 82
ocean, water     -> 93
ocean, sea       -> 97
football, soccer -> 91
football, stadium-> 68
football, banana -> 3
doctor, hospital -> 71
doctor, telescope-> 5
```

If real playtesting shows scores feel off, adjust `_CALIBRATION_EXAMPLES`
in `app/scoring.py` — that's the single place calibration lives.

## Word selection rules

- ~935 curated words across 23 categories (Animals, Nature, Food, ... see
  `data/candidate_words.csv`), deduplicated so no word appears twice even
  across categories.
- Category is stored for admin/organizational purposes only — never shown
  to players.
- A word won't repeat as the daily secret within 60 days of its last use.
