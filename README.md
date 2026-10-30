# lift-planner

`src/plan_lift.py` plans today's lift from your past sessions and last night's sleep.
It writes today's note and prints a table of what changed.

## Run

```
python3 -m src.plan_lift [--day NAME] [--sleep HOURS] [--input-dir DIR] [--output-dir DIR] [--force]
```

| Arg | What it does |
| --- | --- |
| `--day` | Plan from the newest note with this `# heading`, e.g. `--day Lower`. Default: the newest note. |
| `--sleep` | Hours slept last night. Skips Google Health and the `sleep:` property. |
| `--input-dir` | Folder of past sessions, as `YYYY-MM/YYYY-MM-DD.md`. |
| `--output-dir` | Folder for today's note. It goes in `YYYY-MM/` inside it. |
| `--force` | Replace today's note if it already has a plan. |

Run it from the repo folder. Both folders default to `LIFTING_DIR` in `.env`. Without it, both flags are
required.

Try it on the sample notes:

```
python3 -m src.plan_lift --input-dir examples/notes --output-dir /tmp/lift-demo
```

## Your config

Your settings live in two gitignored files. Each has a committed example to copy.

| File | Holds | Start from |
| --- | --- | --- |
| `config.toml` | Lift names, rep targets, weight steps, sleep cutoffs | `config.example.toml` |
| `.env` | Google Health credentials, `LIFTING_DIR` | `.env.example` |

1. Copy `config.example.toml` to `config.toml` and edit it. Every setting has a
   comment. Lift names must match your notes. Without `config.toml`, the
   script uses the example.
2. Optional: copy `.env.example` to `.env`. Set `LIFTING_DIR` to your notes
   folder. For sleep from Google Health, fill in your OAuth client ID and secret.
   The script reuses the refresh token that the google-health MCP saved at
   `GOOGLE_HEALTH_TOKEN_PATH`. Git ignores `.env`.

Python 3.11 or newer. No packages to install.

## Sleep

The script finds last night's sleep in this order:

1. The `--sleep` flag, if given.
2. The Google Health API, if `.env` works and sleep has synced.
3. The `sleep:` property in today's note, in hours (for example `sleep: 6.5`).
   No Fitbit? Create today's note with just that property, then run the script.
4. None of these? The script skips the sleep rules and plans from weight and reps.

It writes the hours it used into the `sleep:` property of today's note.

## Notes

Each note is a markdown table with the columns Exercise, Set, Weight, Reps, and
RIR. Properties are `start:`, `end:`, and `sleep:`. The `# heading` names the
day (`# Fullbody`, `# Upper`, `# Push`).

All notes go in one folder, one subfolder per month:

```
lifting/
  2026-09/
    2026-09-29.md
  2026-10/
    2026-10-01.md
    2026-10-03.md
```

Other layouts, like one folder per split day, aren't read.

- **Exercise order** comes from your newest note, or with `--day` the newest
  note with that heading. To add, drop, or reorder a lift, edit that note.
  There is no split list.
- **Sets**: the rules run on each lift's first set. Later sets copy its
  weight and aim (straight sets), and the chat table shows one row per lift.
- **Splits** work by heading. Run `--day Lower` on lower days. A lift's
  history comes only from notes that have it, so an Upper lift's stall check
  skips the Lower days in between.
- **The note column** is yours. The script reads only weight and reps, and writes
  `aim N` in that column.
- **A new exercise** with no logged weight shows `?` and the rule "no history".
  Pick a starting weight yourself.

## Rules

`plan_exercise` in `src/transform/plan.py` calls the rules top to bottom. The first
one that returns a plan wins.

| Rule | Fires when | Does |
| --- | --- | --- |
| short sleep | Sleep under the cutoff | Holds last weight and reps |
| too few reps | Reps at or below half the go-up reps | Drops 5% |
| stall | 3 sessions at one weight with no rep gain | Drops 5% |
| step up | Reps hit the go-up reps | Adds one step: 5 lb for `compound_lifts`, else 2.5 |
| +1 rep | Anything else | Aims for one more rep |

Short sleep also skips accessories, in `drop_order`. All the numbers live in
`config.toml`. Each rule's source is in `docs/references.bib`, cited by key in its
docstring.

## Layout

| Path | Job |
| --- | --- |
| `src/extract/` | Reads sleep (`google_health.py`) and past notes (`lift_notes.py`). |
| `src/transform/` | The rules (`rules.py`) and the plan (`plan.py`). |
| `src/write/` | Writes today's note and prints the table. |
| `src/settings.py` | Loads `config.toml` and `.env`. Don't edit it. |
| `examples/notes/` | Made-up notes for trying the script. |
| `test/` | Rule, note-reading, and end-to-end tests. Run `python3 -m unittest`. They always use `config.example.toml`. |
| `test_files/` | Notes for each split (fullbody, upper/lower, push/pull/legs) that the end-to-end tests plan from. |
