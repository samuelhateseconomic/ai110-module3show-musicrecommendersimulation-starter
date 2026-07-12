import csv
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

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

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        # TODO: Implement recommendation logic
        return self.songs[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        # TODO: Implement explanation logic
        return "Explanation placeholder"

def load_songs(csv_path: str) -> List[Dict]:
    """Loads songs from a CSV file, converting id to int and numeric fields to float."""
    numeric_fields = ["energy", "tempo_bpm", "valence", "danceability", "acousticness"]

    songs = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["id"] = int(row["id"])
            for field in numeric_fields:
                row[field] = float(row[field])
            songs.append(row)
    print(f"Loaded {len(songs)} songs from {csv_path}")
    return songs

def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """Scores a song against user preferences and returns (score, reasons)."""
    mood_match = song["mood"] == user_prefs["favorite_mood"]
    genre_match = song["genre"] == user_prefs["favorite_genre"]
    energy_closeness = 1 - abs(user_prefs["target_energy"] - song["energy"])
    acoustic_closeness = 1 - abs(user_prefs["target_acousticness"] - song["acousticness"])

    mood_score = 30 * (1 if mood_match else 0)
    energy_score = 30 * energy_closeness
    genre_score = 20 * (1 if genre_match else 0)
    acoustic_score = 20 * acoustic_closeness

    score = mood_score + energy_score + genre_score + acoustic_score

    reasons = []
    if mood_match:
        reasons.append(f"mood match (+{mood_score:.1f})")
    reasons.append(f"energy closeness (+{energy_score:.1f})")
    if genre_match:
        reasons.append(f"genre match (+{genre_score:.1f})")
    elif score >= 40:
        reasons.append("This is not the genre you found but it can surprise you with the matched energy.")
    reasons.append(f"acoustic closeness (+{acoustic_score:.1f})")

    return score, reasons

def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """Scores, ranks, and returns the top-k songs for a user profile."""
    scored = []
    for song in songs:
        score, reasons = score_song(user_prefs, song)
        # score_song folds this into `score` and doesn't expose it, but ties need
        # the raw value to break by "higher energy match" per the ranking rule.
        energy_closeness = 1 - abs(user_prefs["target_energy"] - song["energy"])
        explanation = "; ".join(reasons)
        scored.append((song, score, explanation, energy_closeness))

    # Sort by score desc, then energy closeness desc, then id asc (stable tie-break).
    scored.sort(key=lambda entry: (-entry[1], -entry[3], entry[0]["id"]))

    # Drop the scratch energy_closeness now that ordering is settled.
    return [(song, score, explanation) for song, score, explanation, _ in scored[:k]]
