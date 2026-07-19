# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agentic Workflow (SF8)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**What task did you give the agent?**

<!-- Describe the goal you asked the agent to accomplish -->
- I choose challenge 2-3-4 and will go for it one-by-one.

**Prompts used:**

**Challenge 2 Prompts**
1. @Claude+Track.md Now I want to have a multiple scoring modes, which are four more named "Genre-First", "Mood-First", "Energy-Focused", and "Acoustic-Focused" with a 50% weight for each concentration factor and the rest 50% divide equally so that user can switch between modes. But before that I need you to build a skeleton first of what you will do and what you need to build these addition features. 

**Challenge 3 Prompts**
1. @Claude+Track.md I want to add a "Diversity Penalty" that prevents the recommender from suggesting too many songs from the same artist or genre in the top results. As the recommendation only show 5 best songs, I need the protection makes sure that no more than 3 songs came from the same artist or genre. Execute it.

**Challenge 4 Prompts**
1. @Claude+Track.md I want you to help me improve the readability of the terminal output by providing a formatted table and the summary. Think about a way to use library like tabulate to display the top recommendation. Each row should include in this order: rank, name, score and explanations. If the genre is not matched, keep the suprise comment at last.

**What did the agent generate or change?**

**Challenge 2**
- First produced a skeleton/plan (no code) covering the mode registry design, weight tables, and how switching would work, then asked clarifying questions before writing any code: where the mode should live (plain parameter vs. a field on `UserProfile` vs. Strategy classes), whether the existing weights should stay as a default "balanced" mode, and how the CLI should let the user switch modes.
- `src/recommender.py`: added a `SCORING_MODES` registry (`balanced` = original 30/30/20/20, plus `genre_first`/`mood_first`/`energy_focused`/`acoustic_focused`, each giving its named attribute 50 pts and splitting the remaining 50 evenly across the other three, 50/3 ≈ 16.67 each). Added a `mode` parameter to `score_song`, `recommend_songs`, `Recommender.recommend`, and `Recommender.explain_recommendation`; an unrecognized mode name raises `ValueError`.
- `src/main.py`: added `prompt_scoring_mode()`, which asks the user to pick a mode before scoring each of the 4 sample profiles; recommendation output now prints the active mode.
- `tests/test_recommender.py`: added 6 new tests — one isolating each new mode's weight, one confirming non-focus attributes still split 50/3, one for the `ValueError` on an invalid mode, and one confirming `recommend_songs` ranking actually changes under a mode.
- `src/Skeleton.md`: added a "Scoring Modes" section documenting the weight tables, mirroring the style of the existing "Scoring Rule" section.

**Challenge 3**
- `src/recommender.py` (`recommend_songs`): added a `max_per_group: int = 3` parameter. After the existing score/energy/id sort, it greedily fills the k slots while skipping any song whose artist or genre has already hit 3 picks in the result so far; if the cap leaves too few candidates to reach k, it backfills the remaining slots from the skipped songs in score order so a full k-length list is still returned instead of coming up short.
- `src/recommender.py` (`Recommender.recommend`): added the same `max_per_group=3` parameter and forwarded it through to `recommend_songs`.
- `tests/test_recommender.py`: added 3 tests — one confirming the artist cap (4 same-artist songs would fill 4 of 5 top slots on score alone, but only 3 make it), one confirming the genre cap (same shape, keyed on genre), and one confirming the backfill path when all 5 candidate songs share a single artist and the cap can't be satisfied without under-filling the list.
- Implemented as a hard cap/filter rather than a soft score penalty, since the request said "makes sure that no more than 3" — a guarantee, not a nudge.

**Challenge 4**
- `requirements.txt`: added `tabulate` as a new dependency.
- `src/main.py`: replaced the per-song `print` loop in `print_recommendations` with a `tabulate` table (columns: Rank, Name, Score, Explanation) followed by a one-line summary. Added a `_format_explanation` helper that bullets each reason string and, when the genre-mismatch "surprise" comment (`"This is not the genre you found..."`) is present, moves it to the end of that row's explanation instead of leaving it in its original position between the energy and acoustic reasons.

**What did you verify or fix manually?**

**Challenge 2**
- Ran the full `pytest` suite (25 tests) after the change; all passed, confirming the pre-existing balanced-mode tests were untouched.
- Manually ran `src/main.py`, piping mode choices (1/2/3/4) for the four sample profiles, and confirmed the printed "Scoring mode" line matched what was selected and that scores differed by mode.
- The agent's first edit had `main.py` importing a private module symbol (`recommender._SCORING_MODES`), which the IDE flagged as a lint error; fixed by renaming the registry to the public `SCORING_MODES`.

**Challenge 3**
- Ran the full `pytest` suite after the change; all 28 tests passed (25 pre-existing + 3 new diversity-cap tests), confirming existing scoring/mode behavior was untouched.
- Manually ran `src/main.py` against the real 35-song catalog to sanity-check the change end-to-end; the cap wasn't visibly triggered there because every song in that catalog happens to have a distinct artist, so the dedicated unit tests are what actually exercise the cap and backfill paths.

**Challenge 4**
- Ran the full `pytest` suite; all 28 tests passed, confirming the output-formatting change didn't touch scoring/ranking logic.
- Manually ran `src/main.py` for all 4 sample profiles and inspected the printed tables; caught a `UnicodeEncodeError` from the first attempt (`tablefmt="fancy_grid"`), since its Unicode box-drawing characters can't be encoded by Windows' default `cp1252` console — fixed by switching to `tablefmt="grid"` (ASCII borders), then re-ran to confirm clean output and that the surprise comment appeared last only on rows where the genre didn't match.

---

## Design Pattern (SF10)

> Document how AI helped you choose or implement a design pattern.

**Which design pattern did you use?**

I use Strategy pattern.

**How did AI help you brainstorm or implement it?**

It is actually quite straightforward as I did the brainstorm then ask the AI to implement under my control.

**How does the pattern appear in your final code?**

The pattern appears as the SCORING_MODES dict in recommender.py (each entry is an interchangeable weight-table "strategy") and the mode parameter on score_song/recommend_songs/Recommender.recommend, which lets the caller pick which strategy runs without changing any of the scoring logic itself.
