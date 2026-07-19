from typing import Any, Dict

import pytest

from src.recommender import Song, UserProfile, Recommender, score_song, recommend_songs

def make_small_recommender() -> Recommender:
    songs = [
        Song(
            id=1,
            title="Test Pop Track",
            artist="Test Artist",
            genre="pop",
            mood="happy",
            energy=0.8,
            tempo_bpm=120,
            valence=0.9,
            danceability=0.8,
            acousticness=0.2,
        ),
        Song(
            id=2,
            title="Chill Lofi Loop",
            artist="Test Artist",
            genre="lofi",
            mood="chill",
            energy=0.4,
            tempo_bpm=80,
            valence=0.6,
            danceability=0.5,
            acousticness=0.9,
        ),
    ]
    return Recommender(songs)


def test_recommend_returns_songs_sorted_by_score():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        target_acousticness=0.2,
    )
    rec = make_small_recommender()
    results = rec.recommend(user, k=2)

    assert len(results) == 2
    # Starter expectation: the pop, happy, high energy song should score higher
    assert results[0].genre == "pop"
    assert results[0].mood == "happy"


def test_explain_recommendation_returns_non_empty_string():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        target_acousticness=0.2,
    )
    rec = make_small_recommender()
    song = rec.songs[0]

    explanation = rec.explain_recommendation(user, song)
    assert isinstance(explanation, str)
    assert explanation.strip() != ""


def make_dict_songs():
    return [
        {
            "id": 2, "title": "B", "artist": "X", "genre": "jazz", "mood": "calm",
            "energy": 0.5, "tempo_bpm": 100, "valence": 0.5, "danceability": 0.5, "acousticness": 0.5,
        },
        {
            "id": 1, "title": "A", "artist": "X", "genre": "rock", "mood": "angry",
            "energy": 0.5, "tempo_bpm": 100, "valence": 0.5, "danceability": 0.5, "acousticness": 0.5,
        },
    ]


def test_recommend_songs_tie_break_uses_id_when_score_and_energy_match():
    # Neither song's genre/mood exists in the user's preferences, and both songs
    # have identical energy/acousticness, so they tie on score. The tie-break
    # rule (lowest id first) must decide the order.
    prefs = dict(
        favorite_genre="unknown-genre",
        favorite_mood="unknown-mood",
        target_energy=0.5,
        target_acousticness=0.5,
    )
    songs = make_dict_songs()

    results = recommend_songs(prefs, songs, k=2)

    assert [song["id"] for song, _, _ in results] == [1, 2]
    assert results[0][1] == results[1][1] == 50.0


def test_score_song_handles_empty_string_preferences():
    # Empty-string favorite_genre/favorite_mood should never match a real song
    # and must not raise, degrading gracefully to energy/acoustic-only scoring.
    prefs = dict(
        favorite_genre="",
        favorite_mood="",
        target_energy=0.6,
        target_acousticness=0.4,
    )
    song = {
        "id": 3, "title": "C", "artist": "X", "genre": "pop", "mood": "happy",
        "energy": 0.6, "tempo_bpm": 100, "valence": 0.5, "danceability": 0.5, "acousticness": 0.4,
    }

    score, reasons = score_song(prefs, song)

    assert score == 50.0
    assert not any("mood match" in reason for reason in reasons)
    assert not any("genre match" in reason for reason in reasons)


def make_baseline_song() -> Dict[str, Any]:
    return {
        "id": 1, "title": "Baseline", "artist": "X", "genre": "pop", "mood": "happy",
        "energy": 0.8, "tempo_bpm": 120, "valence": 0.8, "danceability": 0.8, "acousticness": 0.2,
    }


def test_score_song_clamps_target_energy_above_one():
    # target_energy=1.5 is out of the valid 0..1 range and must clamp to 1.0
    # rather than producing an energy_closeness > 1 (i.e. a score > 100).
    prefs = dict(favorite_genre="pop", favorite_mood="happy", target_energy=1.5, target_acousticness=0.2)

    score, reasons = score_song(prefs, make_baseline_song())

    assert score == 94.0
    assert "energy closeness (+24.0)" in reasons


def test_score_song_clamps_target_acousticness_below_zero():
    # target_acousticness=-0.5 is out of the valid 0..1 range and must clamp
    # to 0.0 rather than producing a negative acoustic_score.
    prefs = dict(favorite_genre="pop", favorite_mood="happy", target_energy=0.8, target_acousticness=-0.5)

    score, reasons = score_song(prefs, make_baseline_song())

    assert score == 96.0
    assert "acoustic closeness (+16.0)" in reasons


def test_score_song_coerces_numeric_string_target_energy():
    # A numeric string (e.g. from a form field) should coerce to float and
    # score normally instead of crashing or being disqualified.
    prefs = dict(favorite_genre="pop", favorite_mood="happy", target_energy="0.8", target_acousticness=0.2)

    score, reasons = score_song(prefs, make_baseline_song())

    assert score == 100.0
    assert not any(reason.startswith("Warning:") for reason in reasons)


def test_score_song_disqualifies_non_numeric_target_energy():
    # A non-numeric string can't be coerced, so target_energy is disqualified
    # and its 30 pts are redistributed evenly across mood/genre/acoustic.
    prefs = dict(favorite_genre="pop", favorite_mood="happy", target_energy="abc", target_acousticness=0.2)

    score, reasons = score_song(prefs, make_baseline_song())

    assert score == 100.0
    assert "Warning: energy preference ignored (expected a number, got str)" in reasons
    assert "Pool adjustment: 30.00 pts from energy redistributed evenly across mood +10.00, genre +10.00, acoustic +10.00." in reasons


def test_score_song_disqualifies_nan_target_energy():
    # NaN must not silently clamp to a real number (a prior bug where
    # min(1.0, nan) resolved to 1.0) -- it should be disqualified instead.
    prefs = dict(favorite_genre="pop", favorite_mood="happy", target_energy=float("nan"), target_acousticness=0.2)

    score, reasons = score_song(prefs, make_baseline_song())

    assert score == 100.0
    assert "Warning: energy preference ignored (value is NaN)" in reasons


def test_score_song_disqualifies_boolean_target_energy():
    # bool is a subclass of int in Python, so True/False would silently pass
    # as 1.0/0.0 without an explicit type check -- it must be disqualified.
    prefs = dict(favorite_genre="pop", favorite_mood="happy", target_energy=True, target_acousticness=0.2)

    score, reasons = score_song(prefs, make_baseline_song())

    assert score == 100.0
    assert "Warning: energy preference ignored (expected a number, got bool)" in reasons


def test_score_song_disqualifies_missing_target_acousticness():
    # A partially-filled profile (missing key entirely) must not raise
    # KeyError -- it should be disqualified and redistributed like any
    # other invalid value.
    prefs = dict(favorite_genre="pop", favorite_mood="happy", target_energy=0.8)

    score, reasons = score_song(prefs, make_baseline_song())

    assert score == 100.0
    assert "Warning: acousticness preference ignored (not provided)" in reasons


def test_score_song_matches_genre_and_mood_case_insensitively():
    # "POP"/"HAPPY" should match "pop"/"happy" -- comparisons must not be
    # case-sensitive.
    prefs = dict(favorite_genre="POP", favorite_mood="HAPPY", target_energy=0.8, target_acousticness=0.2)

    score, reasons = score_song(prefs, make_baseline_song())

    assert score == 100.0
    assert "mood match (+20.0)" in reasons
    assert "genre match (+30.0)" in reasons


def test_score_song_matches_genre_and_mood_with_whitespace():
    # Leading/trailing whitespace (e.g. from a copy-pasted form value) must
    # not cause an otherwise-exact match to fail.
    prefs = dict(favorite_genre=" pop ", favorite_mood=" happy ", target_energy=0.8, target_acousticness=0.2)

    score, reasons = score_song(prefs, make_baseline_song())

    assert score == 100.0
    assert "mood match (+20.0)" in reasons
    assert "genre match (+30.0)" in reasons


def test_score_song_matches_fullwidth_unicode_genre():
    # Full-width Unicode "ｐｏｐ" looks identical to "pop" but is made of
    # different codepoints -- NFKC normalization must still match it.
    prefs = dict(favorite_genre="ｐｏｐ", favorite_mood="happy", target_energy=0.8, target_acousticness=0.2)

    score, reasons = score_song(prefs, make_baseline_song())

    assert score == 100.0
    assert "genre match (+30.0)" in reasons


def test_score_song_disqualifies_non_string_favorite_mood():
    # A non-string favorite_mood (e.g. an int from a malformed request) must
    # not raise AttributeError from .strip() -- it should be disqualified.
    prefs = dict(favorite_genre="pop", favorite_mood=42, target_energy=0.8, target_acousticness=0.2)

    score, reasons = score_song(prefs, make_baseline_song())

    assert score == 100.0
    assert "Warning: mood preference ignored (expected text, got int)" in reasons


def test_score_song_redistributes_weight_when_genre_disqualified():
    # A single disqualified attribute (genre, now the highest-weighted at 30
    # pts) spreads its weight evenly across the 3 remaining attributes: +10 each.
    prefs = dict(favorite_genre=42, favorite_mood="happy", target_energy=0.8, target_acousticness=0.2)

    score, reasons = score_song(prefs, make_baseline_song())

    assert score == 100.0
    assert "mood match (+30.0)" in reasons
    assert "energy closeness (+40.0)" in reasons
    assert "acoustic closeness (+30.0)" in reasons
    assert "Pool adjustment: 30.00 pts from genre redistributed evenly across mood +10.00, energy +10.00, acoustic +10.00." in reasons


def test_score_song_redistributes_weight_when_genre_and_mood_disqualified():
    # Two disqualified attributes (genre=20, mood=30 -> 50 pts total) spread
    # evenly across the 2 remaining attributes: +25 each.
    prefs = dict(favorite_genre=42, favorite_mood=None, target_energy=0.8, target_acousticness=0.2)

    score, reasons = score_song(prefs, make_baseline_song())

    assert score == 100.0
    assert "energy closeness (+55.0)" in reasons
    assert "acoustic closeness (+45.0)" in reasons
    assert "Pool adjustment: 50.00 pts from mood, genre redistributed evenly across energy +25.00, acoustic +25.00." in reasons


def test_score_song_returns_zero_when_all_attributes_disqualified():
    # When every attribute is disqualified there's nowhere to redistribute
    # weight to -- score must fall back to 0.0 with an explanatory reason
    # instead of raising a ZeroDivisionError.
    prefs = dict(favorite_genre=42, favorite_mood=None, target_energy="abc", target_acousticness=float("nan"))

    score, reasons = score_song(prefs, make_baseline_song())

    assert score == 0.0
    assert "Unable to score: no valid preference attributes remained after disqualification." in reasons


# --- Scoring modes ---
# Each test isolates a single matching attribute (everything else mismatched/zero
# closeness) so the resulting score equals that mode's weight for the named
# attribute directly -- 50.0 for the mode's own focus, 50.0/3 otherwise.

def test_score_song_genre_first_mode_weights_genre_at_50():
    song = {
        "id": 10, "title": "T", "artist": "A", "genre": "pop", "mood": "happy",
        "energy": 1.0, "tempo_bpm": 100, "valence": 0.5, "danceability": 0.5, "acousticness": 1.0,
    }
    prefs = dict(favorite_genre="pop", favorite_mood="sad", target_energy=0.0, target_acousticness=0.0)

    score, _ = score_song(prefs, song, mode="genre_first")

    assert score == 50.0


def test_score_song_mood_first_mode_weights_mood_at_50():
    song = {
        "id": 11, "title": "T", "artist": "A", "genre": "pop", "mood": "happy",
        "energy": 1.0, "tempo_bpm": 100, "valence": 0.5, "danceability": 0.5, "acousticness": 1.0,
    }
    prefs = dict(favorite_genre="rock", favorite_mood="happy", target_energy=0.0, target_acousticness=0.0)

    score, _ = score_song(prefs, song, mode="mood_first")

    assert score == 50.0


def test_score_song_energy_focused_mode_weights_energy_at_50():
    song = {
        "id": 12, "title": "T", "artist": "A", "genre": "pop", "mood": "happy",
        "energy": 0.8, "tempo_bpm": 100, "valence": 0.5, "danceability": 0.5, "acousticness": 1.0,
    }
    prefs = dict(favorite_genre="rock", favorite_mood="sad", target_energy=0.8, target_acousticness=0.0)

    score, _ = score_song(prefs, song, mode="energy_focused")

    assert score == 50.0


def test_score_song_acoustic_focused_mode_weights_acoustic_at_50():
    song = {
        "id": 13, "title": "T", "artist": "A", "genre": "pop", "mood": "happy",
        "energy": 1.0, "tempo_bpm": 100, "valence": 0.5, "danceability": 0.5, "acousticness": 0.2,
    }
    prefs = dict(favorite_genre="rock", favorite_mood="sad", target_energy=0.0, target_acousticness=0.2)

    score, _ = score_song(prefs, song, mode="acoustic_focused")

    assert score == 50.0


def test_score_song_non_focus_modes_split_genre_evenly_at_50_thirds():
    # Under any mode other than genre_first, an isolated genre match should
    # only be worth 50/3 (the "other 3 attributes" share), not 50.
    song = {
        "id": 10, "title": "T", "artist": "A", "genre": "pop", "mood": "happy",
        "energy": 1.0, "tempo_bpm": 100, "valence": 0.5, "danceability": 0.5, "acousticness": 1.0,
    }
    prefs = dict(favorite_genre="pop", favorite_mood="sad", target_energy=0.0, target_acousticness=0.0)

    for mode in ("mood_first", "energy_focused", "acoustic_focused"):
        score, _ = score_song(prefs, song, mode=mode)
        assert score == 50.0 / 3


def test_score_song_raises_on_unknown_mode():
    prefs = dict(favorite_genre="pop", favorite_mood="happy", target_energy=0.8, target_acousticness=0.2)

    with pytest.raises(ValueError):
        score_song(prefs, make_baseline_song(), mode="not_a_real_mode")


def test_recommend_songs_forwards_mode_to_score_song():
    songs = make_dict_songs()  # jazz/calm (id2) and rock/angry (id1), identical energy/acoustic
    prefs = dict(favorite_genre="rock", favorite_mood="unknown-mood", target_energy=0.5, target_acousticness=0.5)

    results = recommend_songs(prefs, songs, k=2, mode="genre_first")

    # Under genre_first, the rock match (id 1) should score well above the
    # non-matching jazz song (id 2) and be ranked first.
    assert results[0][0]["id"] == 1
    assert results[0][1] > results[1][1]


# --- Diversity cap ---
# Neither favorite_genre="unmatched-genre" nor favorite_mood="unmatched-mood"
# matches any song below, so score is driven entirely by energy/acoustic
# closeness (target_energy=0.5, target_acousticness=0.5), giving each song a
# distinct, easy-to-predict score that decreases as "energy" moves away from 0.5.

def make_diversity_prefs() -> Dict[str, Any]:
    return dict(
        favorite_genre="unmatched-genre",
        favorite_mood="unmatched-mood",
        target_energy=0.5,
        target_acousticness=0.5,
    )


def test_recommend_songs_caps_songs_per_artist_at_max_per_group():
    # 4 songs from artist "A" (ids 1-4, strictly decreasing score) would fill
    # 4 of the top 5 slots on score alone, but the default max_per_group=3
    # must cap artist "A" at 3 -- the 4th-place "A" song (id 4) is skipped in
    # favor of the two artist "B" songs, and since B fills the remaining 2
    # slots, no backfill is needed.
    songs = [
        {"id": 1, "title": "A1", "artist": "A", "genre": "g1", "mood": "m", "energy": 0.50, "tempo_bpm": 100, "valence": 0.5, "danceability": 0.5, "acousticness": 0.50},
        {"id": 2, "title": "A2", "artist": "A", "genre": "g2", "mood": "m", "energy": 0.55, "tempo_bpm": 100, "valence": 0.5, "danceability": 0.5, "acousticness": 0.50},
        {"id": 3, "title": "A3", "artist": "A", "genre": "g3", "mood": "m", "energy": 0.60, "tempo_bpm": 100, "valence": 0.5, "danceability": 0.5, "acousticness": 0.50},
        {"id": 4, "title": "A4", "artist": "A", "genre": "g4", "mood": "m", "energy": 0.65, "tempo_bpm": 100, "valence": 0.5, "danceability": 0.5, "acousticness": 0.50},
        {"id": 5, "title": "B1", "artist": "B", "genre": "g5", "mood": "m", "energy": 0.70, "tempo_bpm": 100, "valence": 0.5, "danceability": 0.5, "acousticness": 0.50},
        {"id": 6, "title": "B2", "artist": "B", "genre": "g6", "mood": "m", "energy": 0.75, "tempo_bpm": 100, "valence": 0.5, "danceability": 0.5, "acousticness": 0.50},
    ]

    results = recommend_songs(make_diversity_prefs(), songs, k=5)

    assert [song["id"] for song, _, _ in results] == [1, 2, 3, 5, 6]
    artist_counts = {}
    for song, _, _ in results:
        artist_counts[song["artist"]] = artist_counts.get(song["artist"], 0) + 1
    assert all(count <= 3 for count in artist_counts.values())


def test_recommend_songs_caps_songs_per_genre_at_max_per_group():
    # Same idea as the artist cap test, but with 4 songs sharing genre "g"
    # (each a different artist) and 2 songs on a different genre. The 4th "g"
    # song (id 4) is skipped in favor of the 2 differently-genred songs.
    songs = [
        {"id": 1, "title": "T1", "artist": "artist1", "genre": "g", "mood": "m", "energy": 0.50, "tempo_bpm": 100, "valence": 0.5, "danceability": 0.5, "acousticness": 0.50},
        {"id": 2, "title": "T2", "artist": "artist2", "genre": "g", "mood": "m", "energy": 0.55, "tempo_bpm": 100, "valence": 0.5, "danceability": 0.5, "acousticness": 0.50},
        {"id": 3, "title": "T3", "artist": "artist3", "genre": "g", "mood": "m", "energy": 0.60, "tempo_bpm": 100, "valence": 0.5, "danceability": 0.5, "acousticness": 0.50},
        {"id": 4, "title": "T4", "artist": "artist4", "genre": "g", "mood": "m", "energy": 0.65, "tempo_bpm": 100, "valence": 0.5, "danceability": 0.5, "acousticness": 0.50},
        {"id": 5, "title": "T5", "artist": "artist5", "genre": "other", "mood": "m", "energy": 0.70, "tempo_bpm": 100, "valence": 0.5, "danceability": 0.5, "acousticness": 0.50},
        {"id": 6, "title": "T6", "artist": "artist6", "genre": "other", "mood": "m", "energy": 0.75, "tempo_bpm": 100, "valence": 0.5, "danceability": 0.5, "acousticness": 0.50},
    ]

    results = recommend_songs(make_diversity_prefs(), songs, k=5)

    assert [song["id"] for song, _, _ in results] == [1, 2, 3, 5, 6]
    genre_counts = {}
    for song, _, _ in results:
        genre_counts[song["genre"]] = genre_counts.get(song["genre"], 0) + 1
    assert all(count <= 3 for count in genre_counts.values())


def test_recommend_songs_backfills_when_diversity_cap_cannot_fill_k():
    # All 5 songs share the same artist, so the cap (max 3) can't be satisfied
    # for a k=5 list without leaving slots empty. The remaining 2 slots must
    # be backfilled from the capped-out songs (best score first) so the
    # function still returns k results instead of only 3.
    songs = [
        {"id": i, "title": f"S{i}", "artist": "only-artist", "genre": f"g{i}", "mood": "m",
         "energy": 0.50 + (i - 1) * 0.05, "tempo_bpm": 100, "valence": 0.5, "danceability": 0.5, "acousticness": 0.50}
        for i in range(1, 6)
    ]

    results = recommend_songs(make_diversity_prefs(), songs, k=5)

    assert len(results) == 5
    assert [song["id"] for song, _, _ in results] == [1, 2, 3, 4, 5]
