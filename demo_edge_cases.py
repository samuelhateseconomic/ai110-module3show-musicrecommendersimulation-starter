"""Prints real recommend_songs() output for the adversarial profiles covered
by tests/test_recommender.py, so the output can be copied into docs/README
as evidence of how each edge case is handled.

Run with: python demo_edge_cases.py
"""

import sys

from src.recommender import load_songs, recommend_songs

sys.stdout.reconfigure(encoding="utf-8")

PROFILES = [
    ("Baseline (valid profile)", dict(favorite_genre="pop", favorite_mood="happy", target_energy=0.8, target_acousticness=0.2)),
    ("Clamped target_energy above 1 (1.5 -> 1.0)", dict(favorite_genre="pop", favorite_mood="happy", target_energy=1.5, target_acousticness=0.2)),
    ("Clamped target_acousticness below 0 (-0.5 -> 0.0)", dict(favorite_genre="pop", favorite_mood="happy", target_energy=0.8, target_acousticness=-0.5)),
    ("Numeric string target_energy (\"0.8\")", dict(favorite_genre="pop", favorite_mood="happy", target_energy="0.8", target_acousticness=0.2)),
    ("Non-numeric string target_energy (\"abc\")", dict(favorite_genre="pop", favorite_mood="happy", target_energy="abc", target_acousticness=0.2)),
    ("NaN target_energy", dict(favorite_genre="pop", favorite_mood="happy", target_energy=float("nan"), target_acousticness=0.2)),
    ("Boolean target_energy (True)", dict(favorite_genre="pop", favorite_mood="happy", target_energy=True, target_acousticness=0.2)),
    ("Missing target_acousticness key", dict(favorite_genre="pop", favorite_mood="happy", target_energy=0.8)),
    ("Case-insensitive genre/mood (\"POP\"/\"HAPPY\")", dict(favorite_genre="POP", favorite_mood="HAPPY", target_energy=0.8, target_acousticness=0.2)),
    ("Whitespace genre/mood (\" pop \"/\" happy \")", dict(favorite_genre=" pop ", favorite_mood=" happy ", target_energy=0.8, target_acousticness=0.2)),
    ("Full-width Unicode genre (\"ｐｏｐ\")", dict(favorite_genre="ｐｏｐ", favorite_mood="happy", target_energy=0.8, target_acousticness=0.2)),
    ("Non-string favorite_mood (42)", dict(favorite_genre="pop", favorite_mood=42, target_energy=0.8, target_acousticness=0.2)),
    ("Genre disqualified alone (redistributes to mood/energy/acoustic)", dict(favorite_genre=42, favorite_mood="happy", target_energy=0.8, target_acousticness=0.2)),
    ("Genre + mood disqualified (redistributes to energy/acoustic)", dict(favorite_genre=42, favorite_mood=None, target_energy=0.8, target_acousticness=0.2)),
    ("All four attributes disqualified", dict(favorite_genre=42, favorite_mood=None, target_energy="abc", target_acousticness=float("nan"))),
]


def main():
    songs = load_songs("data/songs.csv")

    for name, prefs in PROFILES:
        print(f"=== {name} ===")
        print(f"Profile: {prefs}")
        results = recommend_songs(prefs, songs, k=3)
        for song, score, explanation in results:
            print(f"  {song['title']:20s} score={score:6.2f}  {explanation}")
        print()


if __name__ == "__main__":
    main()
