"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from typing import List, Tuple, Dict

from recommender import load_songs, recommend_songs


def print_recommendations(label: str, user_prefs: Dict, recommendations: List[Tuple[Dict, float, str]]) -> None:
    print(f"\n{label}")
    print("=" * len(label))
    print(f"User Profile: favorite_genre={user_prefs['favorite_genre']}, favorite_mood={user_prefs['favorite_mood']}, "
          f"target_energy={user_prefs['target_energy']}, target_acousticness={user_prefs['target_acousticness']}")
    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        print(f"\n{rank}. {song['title']} - {song['artist']}  (Score: {score:.1f}/100)")
        for reason in explanation.split("; "):
            print(f"     - {reason}")


def main() -> None:
    songs = load_songs("data/songs.csv") 

    # Starter example profile
    user_prefs_1 = {"favorite_genre": "classical", "favorite_mood": "happy", "target_energy": 0.6, "target_acousticness": 0.6}
    user_prefs_2 = {"favorite_genre": "blues", "favorite_mood": "relaxed", "target_energy": 0.15, "target_acousticness": 0.9}
    user_prefs_3 = {"favorite_genre": "rock", "favorite_mood": "angry", "target_energy": 0.9, "target_acousticness": 0.1}

    recommendations_1 = recommend_songs(user_prefs_1, songs, k=5)
    recommendations_2 = recommend_songs(user_prefs_2, songs, k=5)
    recommendations_3 = recommend_songs(user_prefs_3, songs, k=5)

    print_recommendations("Top recommendations for User 1", user_prefs_1, recommendations_1)
    print_recommendations("Top recommendations for User 2", user_prefs_2, recommendations_2)
    print_recommendations("Top recommendations for User 3", user_prefs_3, recommendations_3)


if __name__ == "__main__":
    main()
