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

The app looks into the user profile to learn the user's type of music, then categorizes the attributes and sorts the list of songs that are similar to the user's preferences. At the same time, it calculates a score for the songs that seem to fit the user and returns an explanation along with the score (the higher the score, the better the match). The system evaluates each song based on four attributes - mood (string), genre (string), energy (numeric), and acoustic (numeric) - on a scale of 0 to 100, weighted 30% each on mood and energy, and 20% each on genre and acoustic. From my perspective, keeping genre and acoustic lower encourages greater creativity, allowing the user to experience a new type of music at the same energy and mood level. Finally, it returns a ranking based on the score, with the highest-scoring song on top and the lowest at the bottom. Ties are broken first by the closer energy match, then by song id.

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

1. Sunset Road - Country Riders  (Score: 75.2/100)
     - mood match (+30.0)
     - energy closeness (+27.6)
     - This is not the genre you found but it can surprise you with the matched energy.
     - acoustic closeness (+17.6)

2. Soul Fire - Soul Singers  (Score: 73.7/100)
     - mood match (+30.0)
     - energy closeness (+26.7)
     - This is not the genre you found but it can surprise you with the matched energy.
     - acoustic closeness (+17.0)

3. Rooftop Lights - Indigo Parade  (Score: 70.2/100)
     - mood match (+30.0)
     - energy closeness (+25.2)
     - This is not the genre you found but it can surprise you with the matched energy.
     - acoustic closeness (+15.0)

4. Sunrise City - Neon Echo  (Score: 65.0/100)
     - mood match (+30.0)
     - energy closeness (+23.4)
     - This is not the genre you found but it can surprise you with the matched energy.
     - acoustic closeness (+11.6)

5. Symphony in D - Classical Ensemble  (Score: 52.5/100)
     - energy closeness (+19.5)
     - genre match (+20.0)
     - acoustic closeness (+13.0)
```

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or demo video link here -->

---

## Experiments You Tried

Use this section to document the experiments you ran. For example:

- What happened when you changed the weight on genre from 2.0 to 0.5
- What happened when you added tempo or valence to the score
- How did your system behave for different types of users

---

## Limitations and Risks

A brief note on where this algorithm can be biased or fall short:

- **Weighting bias** — mood and energy carry 60% of the score, so the system leans hard toward matching *feel* to leverage the creativity of system and can push a genuinely good genre or acoustic match down the list.
- **Depends on good tags** — the score is only as accurate as the mood/genre/energy/acoustic values in the data; missing or mislabeled attributes lead to bad matches.
- **Shallow understanding** — it scores four attributes only and does not understand lyrics, language, or cultural meaning.
- **No social learning** — it ignores what similar users enjoy (the strength of collaborative filtering).
- **Small catalog** — with fewer than ~100 songs, good options run out quickly.

You will go deeper on this in your model card.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Write 1 to 2 paragraphs here about what you learned:

- about how recommenders turn data into predictions
- about where bias or unfairness could show up in systems like this



