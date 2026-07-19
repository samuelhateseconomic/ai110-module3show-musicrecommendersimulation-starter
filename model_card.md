# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name  

**RYLAB 1.0** — *Read You Like A Book*

---

## 2. Intended Use  

RYLAB is a classroom exploration project, not a system built for real listeners. It exists to make the mechanics of a content-based recommender — and the ways it can quietly go wrong — visible and easy to inspect, rather than to serve real users.

- **What kind of recommendations it generates**: a ranked list of songs from a small, fixed 35-song catalog, each scored 0–100 against a listener's stated `favorite_genre`, `favorite_mood`, `target_energy`, and `target_acousticness`, with a plain-language explanation attached to every score.
- **What assumptions it makes about the user**: that a listener's taste can be fully captured by four values — one exact genre, one exact mood, and two 0–1 numeric dials — and that those four things are what the listener wants *right now*. That's a real simplification of how musical taste actually works.
- **Real users or classroom exploration**: classroom exploration. It's meant to be read, tested, and picked apart to understand how a content-based recommender turns a few stated preferences into a score, and where that approach breaks down.

---

## 3. How the Model Works  

Think of every song as a short profile: a mood, a genre, and two dials set somewhere between 0 and 1 - how energetic it feels, and how acoustic versus electronic it sounds. The listener has the same kind of profile: a favorite mood, a favorite genre, and where they'd like those two dials set.

To score a song, the system asks four questions: 
Does the genre match? 
How close is the song's energy dial to what the listener wants? 
Does the mood match? 
How close is the acoustic dial? 
Each question is worth points out of 100 — genre and energy count for 30 points each, because genre is the listener's clearest, most stable signal of what they want (get that right first), and energy is a simple, objective dial to measure, unlike mood, which is a fuzzier, more subjective read on "how someone feels right now." Mood and acoustic count for 20 points each: once genre and energy are satisfied, the system can still surprise the listener with a different mood or acoustic level at that same genre/energy. 
Add the four pieces together and you get a 0–100 match score, plus a plain-language reason for every point awarded.

**The main change I made from the starter logic** was in how the system handles a listener profile that isn't perfectly filled in. The starter version assumed every preference would always arrive clean — a real number for energy, real text for mood and genre. But real data is messy: a form field can arrive empty, a preference can come in as the wrong type, or a number can come in as "not a number" at all. My first instinct was that the system should either reject bad input outright or just ignore it — but I realized both of those are bad options: rejecting it crashes the whole recommendation, and silently ignoring it produces a score nobody can make sense of, because it looks like a normal 100-point score even though a quarter of the pool was never actually evaluated.

So instead, I changed the scoring logic to *adapt*: when one piece of the listener's profile turns out to be unusable, the system pulls that piece's points out of the 100-point pool and spreads them evenly across whichever pieces are still trustworthy — and it says so in plain language right in the explanation (for example: *"energy preference ignored (value is NaN); Pool adjustment: 30 pts from energy redistributed evenly across mood, genre, acoustic"*). That way the system never crashes on messy input, never produces a misleadingly "normal-looking" score, and always tells you exactly what it did and why.

---

## 4. Data  

The catalog now has **35 songs** (`data/songs.csv`), built up in three stages:

- The starter scaffold shipped with **10 songs**.
- I added **20 more songs** early on to broaden genre and mood variety before running any real experiments.
- While adversarially testing the scoring logic in this project, I noticed the catalog had **zero songs tagged with a "sad" mood** — so I added **5 more songs** (mood=sad, spanning the indie, acoustic, folk, piano, and indie rock genres) to close that gap.

**Genres represented** (27 total): pop, lofi, rock, ambient, jazz, synthwave, indie pop, electronic, hip-hop, r&b, country, folk, classical, metal, reggae, indie, edm, soul, trap, acoustic, funk, indie rock, house, blues, k-pop, alternative, piano.

**Moods represented** (17 total): happy, chill, intense, relaxed, moody, focused, energetic, aggressive, smooth, peaceful, serene, angry, upbeat, melancholic, euphoric, dark, sad.

**What's still missing**: even at 35 songs, this is a tiny, hand-curated slice of real musical taste. There's no real world/global music beyond a single reggae and a single k-pop entry, no moods like "nostalgic," "anxious," or "hopeful," and most genres only have one or two songs representing them - so the system can't yet tell the difference between "this song happens to be tagged pop" and "this is genuinely what pop sounds like." The catalog is also entirely English-language in its artist/title naming, so it doesn't say anything about how the system would handle non-English metadata.

---

## 5. Strengths  

**Genre-first behavior now matches the actual design intent.** Before reweighting, a song with the wrong genre but the right mood+energy (Rooftop Lights, 75.8) could outrank a song with the right genre but the wrong mood (Gym Hero, 63.1). After moving to genre 30 / energy 30 / mood 20 / acoustic 20, that flipped - Gym Hero (73.1) now correctly beats Rooftop Lights (65.8). That's exactly the intuition the reweighting was meant to capture: genre should be satisfied first, and I confirmed the formula actually does that instead of just assuming it.

**Mood is pulling real, independent weight - not just decoration.** I tested this directly by temporarily disabling the mood check: every score's ceiling dropped to 80/100, and songs that only ranked highly because they matched the user's mood (e.g. Sunset Road, Soul Fire, Rooftop Lights for a classical/happy user) fell out of the top 5 entirely, replaced by songs that were merely strongest on genre/energy/acoustic. This confirms mood and energy genuinely capture different things - a high-energy song can be angry or euphoric, a calm one can be sad or peaceful - so keeping them as separate checks produces a more discriminating ranking than energy alone would.

**It never crashes or silently produces a misleading score on messy input.** A missing key, a NaN, a boolean where a number was expected, or a non-string mood/genre all get disqualified with a plain-language reason instead of raising an exception - verified with 13 dedicated adversarial tests (`tests/test_recommender.py`). Every one of those cases still returns a usable, ranked recommendation list.

**Bad data doesn't just get ignored - its weight goes somewhere sensible.** When an attribute is disqualified, its points are redistributed evenly across whatever's left instead of being lost, so the system always spends the full 100 point pool on real signal. This was verified for a single disqualified attribute, two disqualified at once, and the all-four-disqualified edge case (which correctly falls back to a score of 0.0 with an explanation, rather than dividing by zero).

**Matching is resilient to how preferences are typed in.** `"POP"`, `" pop "`, and even full-width Unicode `"ｐｏｐ"` all correctly match `"pop"` - case, whitespace, and Unicode look-alikes no longer cause a silent, unexplained mismatch the way they used to.

**Every recommendation explains itself.** Each song's explanation lists exactly which attributes matched, how close the numeric ones were, and - when something was ignored or redistributed — a warning saying exactly what and why. Nothing about the score is a black box.

**Ranking is deterministic and reproducible.** Ties are broken consistently (closer energy match, then song id), so the same profile against the same catalog always produces the same ordering - verified with a dedicated tie-break test using two songs that score identically on every other attribute.

---

## 6. Limitations and Bias 

**Genres and moods that are underrepresented.** Of the 27 genres in the catalog, most (reggae, k-pop, blues, funk, classical, etc.) have only 1–2 songs representing them, so a user whose favorite genre is "reggae" gets recommendations built from a single data point, while a "pop" fan draws from a much richer pool. The 5 "sad"-mood songs I added late in this project are also thin compared to well-covered moods like "happy" or "chill," and there's still no "nostalgic," "anxious," or "hopeful" mood in the catalog at all - a listener whose actual mood doesn't map cleanly onto one of the 17 available labels has no way to express it.

**Cases where the system overfits to one preference.** Since the reweighting, genre and energy carry 60% of the score, so a song that nails those two but misses mood/acoustic entirely can still outrank a song that's a great mood/acoustic match but slightly off on genre - the Gym Hero vs. Rooftop Lights experiment showed this concretely (73.1 vs 65.8, a reversal from the old weights). The redistribution logic can make this worse in degraded cases: if two of the four attributes are disqualified (bad data), the remaining two absorb the full 100-point pool between them (e.g. energy+acoustic each become worth 55/45 instead of 30/20), so whichever single attribute survives ends up dominating the ranking far more than the original per-attribute weights ever intended.

**Ways the scoring might unintentionally favor some users.** Because the catalog is so unevenly distributed across genres and moods, users whose taste lines up with over-represented tags (pop, happy, chill, energetic) see a longer, more varied, more confident-looking list of good matches than users whose taste lines up with under-represented tags (reggae, blues, sad, serene) - not because their taste is any less valid, but purely because the data behind it is thinner. The system also can't distinguish "this preference is exactly right" from "this preference is close enough": genre and mood matching is now case/whitespace/Unicode-normalized, but a user who types a semantically close, not identical value (e.g. "hip-hop" vs "hip hop", or "chill" vs "relaxed") still gets silently scored as a total mismatch, with no indication that this was a near-miss rather than a real disagreement in taste. And because bad/missing data is disqualified silently rather than rejected outright, a systemic upstream bug affecting one group of users (e.g. a client that always submits `target_energy` as a string) could quietly degrade their recommendations for a long time without anyone noticing, since the only signal is a warning buried in the explanation text.

---

## 7. Evaluation  

**Which user profiles I tested.** Beyond the four "normal" profiles in `main.py` (classical/happy, high-energy pop, chill lofi, deep intense rock), most of my evaluation work was adversarial rather than typical-user testing - I deliberately built profiles designed to break or trick the scoring logic: out-of-range numeric targets (`target_energy=1.5`, `target_acousticness=-0.5`), wrong types (`target_energy="abc"`, `target_energy=True`, `favorite_mood=42`, `favorite_genre=None`), missing keys, `NaN` values, and case/whitespace/Unicode variants of the same genre/mood (`"POP"`, `" pop "`, `"ｐｏｐ"`). I also ran two structural experiments on the model itself: reweighting the four attributes (genre 30 / energy 30 / mood 20 / acoustic 20 vs. the original mood 30 / energy 30 / genre 20 / acoustic 20) and temporarily disabling the mood check entirely to see how rankings change without it.

**What I looked for.** For the adversarial profiles, I wasn't checking "is this a good recommendation" - I was checking whether the system crashed, silently produced a misleading score, or degraded gracefully with a clear explanation. For the two structural experiments, I was checking whether the ranking actually moved in the direction the change implied, using the same fixed worked example (Sunrise City / Rooftop Lights / Gym Hero) as a before/after control.

**What surprised me.**
- `min(1.0, float('nan'))` doesn't raise or stay `NaN` — it silently returns `1.0`, because of how Python's `min`/`max` compare against `NaN`. Left unguarded, that would have quietly turned "we don't know the energy" into "max energy," with no error and no warning. That's the one that worried me most, because it fails *silently* rather than loudly.
- Disabling mood didn't just lower every score by a flat amount — it reshuffled the *rankings* for some users, because mood was acting as the tiebreaker that let otherwise-average songs leapfrog into the top spots. I expected scores to drop; I didn't expect the top 5 to become a nearly different set of songs.
- Reweighting genre/energy above mood/acoustic flipped a ranking I'd already written into `Skeleton.md` as a worked example (Rooftop Lights beating Gym Hero). Good reminder that a worked example is only valid for one specific weighting, not a general truth about the system.

**Simple tests and comparisons I ran.** Every adversarial profile and both structural experiments were eventually turned into permanent, automated checks rather than one-off manual runs: `tests/test_recommender.py` now has 18 tests covering clamping, type coercion vs. disqualification, NaN/bool/missing-key handling, case/whitespace/Unicode matching, and all three redistribution shapes (one attribute disqualified, two, and all four). I also kept `demo_edge_cases.py` as a standalone script to regenerate real `recommend_songs()` output for all 15 adversarial profiles on demand, and used direct before/after diffs of `python src/main.py`'s output for the two structural experiments (reweighting and mood-ablation) rather than eyeballing scores by hand.

No numeric metrics beyond the 0–100 match score itself — with a 35-song catalog and no ground-truth "correct" recommendations, precision/recall-style metrics wouldn't mean much here.

---

## 8. Future Work  

Ideas for how you would improve the model next.  

- Add AI to fix the input (i.e. hip-hop | hip hop | hiphop)
- Add an API to a music library for bigger dataset and more reality
- Add visualize interactions and control user-profile
---

## 9. Personal Reflection  

The best thing I learned from this project was the system evaluation part - the part where I had to continuously stress-test and, honestly, fail my own belief in the system I'd just built. Working through this with an AI agent brought both positive and negative feedback, and I had to sit with the negative feedback instead of brushing it off. Looking back, a lot of the calls it made when pointing out the system's limits - the NaN bug, the silent case-sensitivity failures, the crash on a missing key - were genuinely good catches I wouldn't have found on my own. It made me realize how many more errors and edge cases are lurking in a system like this, especially once you let go of control and let a user type their own preferences in instead of picking from a fixed list.

This project also changed how I think about music recommendation apps for real, and it made me think a lot about Spotify. Even though mine is the basic version, it made me appreciate how much Spotify is tracking every single interaction I make in the app, not just four static preferences: how long I listen to a song, what artist I search for, what time of day I'm listening, what my "song of the day" ends up being, whether I skip a track after 2 seconds versus 10 seconds- and that those two numbers mean completely different things about how I actually felt about the song. That's mindblowing to me in a way it wasn't before this project, and it's made me want to eventually build something that complex myself.
