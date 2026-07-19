import csv
import math
import unicodedata
from typing import Any, List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    target_acousticness: float

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5, mode: str = "balanced", max_per_group: int = 3) -> List[Song]:
        song_by_id = {song.id: song for song in self.songs}
        song_dicts = [asdict(song) for song in self.songs]
        results = recommend_songs(asdict(user), song_dicts, k=k, mode=mode, max_per_group=max_per_group)
        return [song_by_id[song_dict["id"]] for song_dict, _, _ in results]

    def explain_recommendation(self, user: UserProfile, song: Song, mode: str = "balanced") -> str:
        _, reasons = score_song(asdict(user), asdict(song), mode=mode)
        return "; ".join(reasons)

def load_songs(csv_path: str) -> List[Dict[str, Any]]:
    """Loads songs from a CSV file, converting id to int and numeric fields to float."""
    numeric_fields = ["energy", "tempo_bpm", "valence", "danceability", "acousticness"]

    songs: List[Dict[str, Any]] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["id"] = int(row["id"])
            for field in numeric_fields:
                row[field] = float(row[field])
            songs.append(row)
    print(f"Loaded {len(songs)} songs from {csv_path}")
    return songs

def _match_categorical(song_value: str, user_prefs: Dict[str, Any], field_name: str, display_name: str) -> Tuple[bool, Optional[str]]:
    """Matches a categorical preference (mood/genre) against a song value.

    Returns (matched, warning). Instead of raising when the preference is
    missing or isn't text, disqualifies the match (matched=False) and reports
    why via warning so the rest of the score can still be computed.
    """
    if field_name not in user_prefs:
        return False, f"{display_name} preference ignored (not provided)"
    user_value = user_prefs[field_name]
    if not isinstance(user_value, str):
        return False, f"{display_name} preference ignored (expected text, got {type(user_value).__name__})"
    normalized_song = unicodedata.normalize("NFKC", song_value).strip().lower()
    normalized_user = unicodedata.normalize("NFKC", user_value).strip().lower()
    return normalized_song == normalized_user, None

def _closeness_to_target(song_value: float, user_prefs: Dict[str, Any], field_name: str, display_name: str) -> Tuple[float, Optional[str]]:
    """Computes 1 - |target - song_value| for a numeric preference (energy/acousticness).

    Returns (closeness, warning). Disqualifies (closeness=0.0) instead of
    raising or silently corrupting the score when the preference is missing,
    not a real number, NaN, or a bool masquerading as a number.
    """
    if field_name not in user_prefs:
        return 0.0, f"{display_name} preference ignored (not provided)"
    value = user_prefs[field_name]
    if isinstance(value, bool):
        return 0.0, f"{display_name} preference ignored (expected a number, got bool)"
    try:
        value = float(value)
    except (TypeError, ValueError):
        return 0.0, f"{display_name} preference ignored (expected a number, got {type(value).__name__})"
    if math.isnan(value):
        return 0.0, f"{display_name} preference ignored (value is NaN)"
    bounded = max(0.0, min(1.0, value))
    return 1 - abs(bounded - song_value), None

_BASE_WEIGHTS: Dict[str, float] = {"mood": 20.0, "energy": 30.0, "genre": 30.0, "acoustic": 20.0}

# Each scoring mode is a weight table over the same 4 attributes (always summing to 100).
# "balanced" is the original default; the other 4 give one attribute 50 pts and split
# the remaining 50 evenly across the other 3 (50/3 each).
_OTHER_SHARE = 50.0 / 3
SCORING_MODES: Dict[str, Dict[str, float]] = {
    "balanced": _BASE_WEIGHTS,
    "genre_first": {"genre": 50.0, "mood": _OTHER_SHARE, "energy": _OTHER_SHARE, "acoustic": _OTHER_SHARE},
    "mood_first": {"mood": 50.0, "genre": _OTHER_SHARE, "energy": _OTHER_SHARE, "acoustic": _OTHER_SHARE},
    "energy_focused": {"energy": 50.0, "genre": _OTHER_SHARE, "mood": _OTHER_SHARE, "acoustic": _OTHER_SHARE},
    "acoustic_focused": {"acoustic": 50.0, "genre": _OTHER_SHARE, "mood": _OTHER_SHARE, "energy": _OTHER_SHARE},
}

def score_song(user_prefs: Dict[str, Any], song: Dict[str, Any], mode: str = "balanced") -> Tuple[float, List[str]]:
    """Scores a song against user preferences and returns (score, reasons).

    `mode` selects which weight table from SCORING_MODES to use. If an
    attribute is disqualified (missing/wrong type/NaN), its weight is split
    evenly across the remaining qualified attributes instead of being lost,
    so the 100-point pool is always fully spent on real signal.
    """
    if mode not in SCORING_MODES:
        raise ValueError(f"Unknown scoring mode {mode!r}; valid modes: {', '.join(SCORING_MODES)}")
    base_weights = SCORING_MODES[mode]
    # Mood must stay its own check, separate from energy: the two don't always move
    # together (e.g. high energy can be angry or euphoric; low energy can be sad or
    # peaceful), so collapsing them would lose a real, independent signal. An
    # experiment that force-disabled this check confirmed rankings collapse toward
    # whichever songs are strongest on genre/energy/acoustic alone.
    mood_match, mood_warning = _match_categorical(song["mood"], user_prefs, "favorite_mood", "mood")
    genre_match, genre_warning = _match_categorical(song["genre"], user_prefs, "favorite_genre", "genre")
    energy_closeness, energy_warning = _closeness_to_target(song["energy"], user_prefs, "target_energy", "energy")
    acoustic_closeness, acoustic_warning = _closeness_to_target(song["acousticness"], user_prefs, "target_acousticness", "acousticness")

    warnings: Dict[str, Optional[str]] = {
        "mood": mood_warning, "energy": energy_warning, "genre": genre_warning, "acoustic": acoustic_warning,
    }
    match_values: Dict[str, float] = {
        "mood": 1.0 if mood_match else 0.0,
        "energy": energy_closeness,
        "genre": 1.0 if genre_match else 0.0,
        "acoustic": acoustic_closeness,
    }
    disqualified = [attr for attr in base_weights if warnings[attr]]
    qualified = [attr for attr in base_weights if attr not in disqualified]

    reasons: List[str] = []

    if not qualified:
        for attr in disqualified:
            reasons.append(f"Warning: {warnings[attr]}")
        reasons.append("Unable to score: no valid preference attributes remained after disqualification.")
        return 0.0, reasons

    redistributed_total = sum(base_weights[attr] for attr in disqualified)
    bonus_per_attr = redistributed_total / len(qualified)
    weights = {attr: base_weights[attr] + bonus_per_attr if attr in qualified else 0.0 for attr in base_weights}

    mood_score = weights["mood"] * match_values["mood"]
    energy_score = weights["energy"] * match_values["energy"]
    genre_score = weights["genre"] * match_values["genre"]
    acoustic_score = weights["acoustic"] * match_values["acoustic"]

    score = mood_score + energy_score + genre_score + acoustic_score

    if "mood" in qualified and mood_match:
        reasons.append(f"mood match (+{mood_score:.1f})")
    if "energy" in qualified:
        reasons.append(f"energy closeness (+{energy_score:.1f})")
    if "genre" in qualified:
        if genre_match:
            reasons.append(f"genre match (+{genre_score:.1f})")
        elif score >= 40:
            reasons.append("This is not the genre you found but it can surprise you with the matched energy.")
    if "acoustic" in qualified:
        reasons.append(f"acoustic closeness (+{acoustic_score:.1f})")

    for attr in disqualified:
        reasons.append(f"Warning: {warnings[attr]}")

    if disqualified:
        redistribution = ", ".join(f"{attr} +{bonus_per_attr:.2f}" for attr in qualified)
        reasons.append(
            f"Pool adjustment: {redistributed_total:.2f} pts from {', '.join(disqualified)} "
            f"redistributed evenly across {redistribution}."
        )

    return score, reasons

def recommend_songs(user_prefs: Dict[str, Any], songs: List[Dict[str, Any]], k: int = 5, mode: str = "balanced", max_per_group: int = 3) -> List[Tuple[Dict[str, Any], float, str]]:
    """Scores, ranks, and returns the top-k songs for a user profile.

    Diversity cap: while filling the k slots, a song is skipped if its artist
    or genre has already reached `max_per_group` picks, so the list can't be
    dominated by one artist or genre. If too few diverse candidates exist to
    fill all k slots this way, the remaining slots are backfilled from the
    skipped songs (best score first) so a full list is still returned.
    """
    scored: List[Tuple[Dict[str, Any], float, str, float]] = []
    for song in songs:
        score, reasons = score_song(user_prefs, song, mode=mode)
        # score_song folds this into `score` and doesn't expose it, but ties need
        # the raw value to break by "higher energy match" per the ranking rule.
        energy_closeness, _ = _closeness_to_target(song["energy"], user_prefs, "target_energy", "energy")
        explanation = "; ".join(reasons)
        scored.append((song, score, explanation, energy_closeness))

    # Sort by score desc, then energy closeness desc, then id asc (stable tie-break).
    scored.sort(key=lambda entry: (-entry[1], -entry[3], entry[0]["id"]))

    selected: List[Tuple[Dict[str, Any], float, str, float]] = []
    skipped: List[Tuple[Dict[str, Any], float, str, float]] = []
    artist_counts: Dict[str, int] = {}
    genre_counts: Dict[str, int] = {}

    for entry in scored:
        if len(selected) == k:
            break
        song = entry[0]
        artist, genre = song["artist"], song["genre"]
        if artist_counts.get(artist, 0) >= max_per_group or genre_counts.get(genre, 0) >= max_per_group:
            skipped.append(entry)
            continue
        selected.append(entry)
        artist_counts[artist] = artist_counts.get(artist, 0) + 1
        genre_counts[genre] = genre_counts.get(genre, 0) + 1

    # Not enough diverse candidates to fill k slots -- backfill from the
    # skipped (over-the-cap) songs, still in score order, rather than
    # returning fewer than k results.
    for entry in skipped:
        if len(selected) == k:
            break
        selected.append(entry)

    return [(song, score, explanation) for song, score, explanation, _ in selected]
