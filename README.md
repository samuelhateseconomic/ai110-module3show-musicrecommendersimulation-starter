# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

Replace this paragraph with your own summary of what your version does.

---

## How The System Works

The app looks into the user profile to learn the user's type of music, then categorizes the attributes and sorts the list of songs that are similar to the user's preferences. At the same time, it calculates a score for the songs that seem to fit the user and returns an explanation along with the score (the higher the score, the better the match). The system evaluates each song based on four attributes - mood (string), genre (string), energy (numeric), and acoustic (numeric) - on a scale of 0 to 100, weighted 30% each on genre and energy, and 20% each on mood and acoustic. From my perspective, genre is the listener's clearest and most stable signal of what they want, so it should be the top priority; energy comes right behind it because it's a simple, objective dial to measure (calm vs. intense), unlike mood, which is a fuzzier, more subjective read on how someone feels right now. Once genre and energy are satisfied, the system can still surprise the listener with a different mood or acoustic level at that same genre/energy level. Finally, it returns a ranking based on the score, with the highest-scoring song on top and the lowest at the bottom. Ties are broken first by the closer energy match, then by song id.

### Features Used

Each `Song` is described by four attributes that the system scores, plus two used only for display:

- **mood** (string) — the feeling of the track, e.g. happy, chill, intense
- **genre** (string) — the style of the track, e.g. pop, lofi, rock
- **energy** (numeric, 0.0–1.0) — how intense or active the track is
- **acousticness** (numeric, 0.0–1.0) — how acoustic versus electronic the track is
- **title** and **artist** (strings) — shown in the results so the user can see what was recommended, but not used in scoring

The `UserProfile` stores the matching preference for each scored attribute:

- **favorite_mood** (string) — matched against the song's mood
- **favorite_genre** (string) — matched against the song's genre
- **target_energy** (numeric, 0.0–1.0) — the energy level the user wants
- **target_acousticness** (numeric, 0.0–1.0) — how acoustic the user wants (0.0 = electronic, 1.0 = acoustic, ~0.5 = neutral)

Every `UserProfile` field maps directly to one `Song` attribute, and that pairing is what the score is built on:

| UserProfile | Song |
|-------------|------|
| favorite_mood | mood |
| favorite_genre | genre |
| target_energy | energy |
| target_acousticness | acousticness |

The songs also include `tempo_bpm`, `valence`, and `danceability`, but this system intentionally does not use them — the four attributes above are enough to demonstrate the scoring idea.


---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Sample Recommendation Output

```
Top recommendations for User 1
==============================
User Profile: favorite_genre=classical, favorite_mood=happy, target_energy=0.6, target_acousticness=0.6

1. Sunset Road - Country Riders  (Score: 65.2/100)
     - mood match (+20.0)
     - energy closeness (+27.6)
     - This is not the genre you found but it can surprise you with the matched energy.
     - acoustic closeness (+17.6)

2. Soul Fire - Soul Singers  (Score: 63.7/100)
     - mood match (+20.0)
     - energy closeness (+26.7)
     - This is not the genre you found but it can surprise you with the matched energy.
     - acoustic closeness (+17.0)

3. Symphony in D - Classical Ensemble  (Score: 62.5/100)
     - energy closeness (+19.5)
     - genre match (+30.0)
     - acoustic closeness (+13.0)

4. Rooftop Lights - Indigo Parade  (Score: 60.2/100)
     - mood match (+20.0)
     - energy closeness (+25.2)
     - This is not the genre you found but it can surprise you with the matched energy.
     - acoustic closeness (+15.0)

5. Sunrise City - Neon Echo  (Score: 55.0/100)
     - mood match (+20.0)
     - energy closeness (+23.4)
     - This is not the genre you found but it can surprise you with the matched energy.
     - acoustic closeness (+11.6)
```

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or demo video link here -->

---

## Experiments You Tried

**0. Reweighted from mood 30 / energy 30 / genre 20 / acoustic 20 to genre 30 / energy 30 / mood 20 / acoustic 20.** Reasoning: genre is the listener's clearest, most stable signal, so it should be satisfied first; energy is a simple, objective dial (calm vs. intense) that pairs naturally with genre as the two leading factors, while mood is a fuzzier, more subjective read that now takes a supporting role alongside acoustic. This flips real rankings — using the Skeleton.md worked example (`favorite_genre=pop, favorite_mood=happy, target_energy=0.8, target_acousticness=0.2`):

```
Old weights (mood 30 / energy 30 / genre 20 / acoustic 20):
  Rooftop Lights (wrong genre, right mood+energy)  -> 75.8   <- used to win
  Gym Hero       (right genre, wrong mood)         -> 63.1

New weights (genre 30 / energy 30 / mood 20 / acoustic 20):
  Gym Hero       (right genre, wrong mood)         -> 73.1   <- wins now
  Rooftop Lights (wrong genre, right mood+energy)  -> 65.8
```

Getting genre right now outranks getting mood right, matching the intent: satisfy genre + energy first, then let mood/acoustic add variety on top.

I also stress-tested the scoring logic with malformed and adversarial user profiles to see how it degrades — not just whether it produces good recommendations for a normal profile. The full set of 15 profiles can be reproduced with `python demo_edge_cases.py`; a few representative results (recomputed under the new weights):

**1. Out-of-range numeric targets get clamped, not corrupted.** `target_energy=1.5` (invalid — above the 0–1 scale) clamps to 1.0 instead of producing a score above 100:

```
=== Clamped target_energy above 1 (1.5 -> 1.0) ===
Profile: {'favorite_genre': 'pop', 'favorite_mood': 'happy', 'target_energy': 1.5, 'target_acousticness': 0.2}
  Sunrise City         score= 94.20  mood match (+20.0); energy closeness (+24.6); genre match (+30.0); acoustic closeness (+19.6)
```

**2. Bad data doesn't crash the system — it "adapts" by redistributing that attribute's weight.** When `target_energy` is unusable (NaN, a non-numeric string, or a boolean), the system disqualifies just that attribute, explains why, and spreads its 30 points evenly across mood/genre/acoustic instead of losing them:

```
=== Non-numeric string target_energy ("abc") ===
Profile: {'favorite_genre': 'pop', 'favorite_mood': 'happy', 'target_energy': 'abc', 'target_acousticness': 0.2}
  Sunrise City         score= 99.40  mood match (+30.0); genre match (+40.0); acoustic closeness (+29.4); Warning: energy preference ignored (expected a number, got str); Pool adjustment: 30.00 pts from energy redistributed evenly across mood +10.00, genre +10.00, acoustic +10.00.
```

**3. Case, whitespace, and Unicode look-alikes no longer silently break matching.** `"POP"`/`"HAPPY"`, `" pop "`/`" happy "`, and even full-width Unicode `"ｐｏｐ"` all match `"pop"`/`"happy"` correctly — previously any of these would have silently dropped that match to 0 with no explanation:

```
=== Case-insensitive genre/mood ("POP"/"HAPPY") ===
Profile: {'favorite_genre': 'POP', 'favorite_mood': 'HAPPY', 'target_energy': 0.8, 'target_acousticness': 0.2}
  Sunrise City         score= 99.00  mood match (+20.0); energy closeness (+29.4); genre match (+30.0); acoustic closeness (+19.6)
```

**4. Multiple attributes disqualified at once still concentrates the pool sensibly.** If genre AND mood are both unusable, their combined 50 points split evenly between energy and acoustic instead of being lost:

```
=== Genre + mood disqualified (redistributes to energy/acoustic) ===
Profile: {'favorite_genre': 42, 'favorite_mood': None, 'target_energy': 0.8, 'target_acousticness': 0.2}
  Sunrise City         score= 98.00  energy closeness (+53.9); acoustic closeness (+44.1); Warning: mood preference ignored (expected text, got NoneType); Warning: genre preference ignored (expected text, got int); Pool adjustment: 50.00 pts from mood, genre redistributed evenly across energy +25.00, acoustic +25.00.
```

**5. If every attribute is bad, the system gives up cleanly instead of crashing:**

```
=== All four attributes disqualified ===
Profile: {'favorite_genre': 42, 'favorite_mood': None, 'target_energy': 'abc', 'target_acousticness': nan}
  Sunrise City         score=  0.00  Warning: mood preference ignored (expected text, got NoneType); Warning: energy preference ignored (expected a number, got str); Warning: genre preference ignored (expected text, got int); Warning: acousticness preference ignored (value is NaN); Unable to score: no valid preference attributes remained after disqualification.
```

**Takeaway:** none of these produce a crash or a silently wrong recommendation — every degraded profile still returns a ranked list, and the explanation text always says exactly what was ignored and how the 100-point scoring pool was rebalanced. These 15 profiles are also locked in as permanent regression tests in `tests/test_recommender.py` (run with `pytest -v`).

---

## Limitations and Risks

A brief note on where this algorithm can be biased or fall short:

- **Weighting bias** — genre and energy now carry 60% of the score, so the system leans hard toward "get the genre and intensity right first" and can push a genuinely good mood or acoustic match down the list, even when that mood match is what the listener actually cares about most in the moment.
- **Redistribution can over-concentrate weight** — when an attribute is disqualified (missing, wrong type, NaN), its points are spread evenly across whatever remains. If several attributes fail at once, the one or two that survive can end up carrying most or all of the 100-point pool, so a single match dominates the ranking far more than the original 30/30/20/20 design intended.
- **Depends on good tags, but only catches structural errors, not wrong ones** — a missing, mistyped, or NaN preference is now disqualified with a clear explanation instead of crashing, but a value that is technically valid yet just plain wrong (e.g. a genre typo the user meant differently) still silently scores as a mismatch with no warning at all.
- **Silent degradation risk** — because bad data no longer raises an error, a systemic upstream bug (e.g. a form that always submits `target_energy` as a string) could go unnoticed for a long time, since the only signal is a warning inside the explanation text, which isn't guaranteed to be read.
- **Case/whitespace/Unicode normalization only fixes exact-content differences** — `"POP"` and `"ｐｏｐ"` now match `"pop"`, but semantically related values (e.g. `"hip-hop"` vs `"hip hop"`, or `"chill"` vs `"relaxed"`) still don't, since the system compares exact normalized strings, not meaning.
- **Shallow understanding** — it scores four attributes only and does not understand lyrics, language, or cultural meaning.
- **No social learning** — it ignores what similar users enjoy (the strength of collaborative filtering).
- **Small catalog** — with fewer than ~100 songs, good options run out quickly.

You will go deeper on this in your model card.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Building this system changed how I think about how recommenders turn data into predictions. My version only works off four things a user tells it directly - favorite genre, favorite mood, and two number dials - and turns that into a single 0–100 score. Going through this project made me think hard about how much more data an app like Spotify actually uses to make the same kind of prediction: not just what you say you like, but how long you listen to a song, whether you skip it after 2 seconds or 10 seconds (which mean very different things), what time of day you're listening, and what you search for. A prediction is only as good as what it's allowed to see, and my system sees very little compared to that - which is exactly what made me want to eventually build something that complex myself.

The bias and unfairness side became real to me during the evaluation phase, working through adversarial testing with an AI agent. It pointed out real limits in my system - cases where bad or missing input could quietly produce a misleading score instead of an honest error, and cases where the catalog's uneven genre/mood coverage would make some users' recommendations look much richer than others through no fault of their own. Some of that feedback was hard to hear, but it was right, and I'd rather find those problems now than pretend the system doesn't have them. It also made me realize that the more freedom you give a user to type their own input, the more of these cases you have to plan for - that trade-off between flexibility and reliability is exactly where a lot of real-world bias and fragility sneaks in.



