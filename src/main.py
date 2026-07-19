"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from typing import List, Tuple, Dict

from tabulate import tabulate

from recommender import load_songs, recommend_songs, SCORING_MODES

_SURPRISE_PREFIX = "This is not the genre you found"

_MODE_NAMES = list(SCORING_MODES)


def prompt_scoring_mode(profile_label: str) -> str:
    print(f"\nChoose a scoring mode for {profile_label}:")
    for i, name in enumerate(_MODE_NAMES, start=1):
        print(f"  {i}. {name}")
    choice = input(f"Enter 1-{len(_MODE_NAMES)} [default 1: {_MODE_NAMES[0]}]: ").strip()
    if not choice:
        return _MODE_NAMES[0]
    if choice.isdigit() and 1 <= int(choice) <= len(_MODE_NAMES):
        return _MODE_NAMES[int(choice) - 1]
    print(f"Invalid choice, defaulting to {_MODE_NAMES[0]}.")
    return _MODE_NAMES[0]


def _format_explanation(explanation: str) -> str:
    """Bullets each reason, moving the genre-mismatch surprise comment to the end."""
    reasons = explanation.split("; ")
    surprise = [r for r in reasons if r.startswith(_SURPRISE_PREFIX)]
    others = [r for r in reasons if not r.startswith(_SURPRISE_PREFIX)]
    return "\n".join(f"- {reason}" for reason in others + surprise)


def print_recommendations(label: str, user_prefs: Dict, recommendations: List[Tuple[Dict, float, str]], mode: str) -> None:
    print(f"\n{label}")
    print("=" * len(label))
    print(f"Scoring mode: {mode}")
    print(f"User Profile: favorite_genre={user_prefs['favorite_genre']}, favorite_mood={user_prefs['favorite_mood']}, "
          f"target_energy={user_prefs['target_energy']}, target_acousticness={user_prefs['target_acousticness']}")

    rows = [
        [rank, f"{song['title']} - {song['artist']}", f"{score:.1f}/100", _format_explanation(explanation)]
        for rank, (song, score, explanation) in enumerate(recommendations, start=1)
    ]
    print()
    print(tabulate(rows, headers=["Rank", "Name", "Score", "Explanation"], tablefmt="grid"))
    print(f"Summary: {len(recommendations)} recommendations for {label} (mode: {mode}).")


def main() -> None:
    songs = load_songs("data/songs.csv")

    # Starter example profile
    user_prefs_1 = {"favorite_genre": "classical", "favorite_mood": "happy", "target_energy": 0.6, "target_acousticness": 0.6}
    High_Energy_Pop = {"favorite_genre": "pop", "favorite_mood": "energetic", "target_energy": 0.9, "target_acousticness": 0.1}
    Chill_Lofi = {"favorite_genre": "lofi", "favorite_mood": "chill", "target_energy": 0.35, "target_acousticness": 0.8}
    Deep_Intense_Rock = {"favorite_genre": "rock", "favorite_mood": "intense", "target_energy": 0.9, "target_acousticness": 0.1}

    mode_1 = prompt_scoring_mode("User 1")
    mode_2 = prompt_scoring_mode("User 2 (High Energy Pop)")
    mode_3 = prompt_scoring_mode("User 3 (Chill Lofi)")
    mode_4 = prompt_scoring_mode("User 4 (Deep Intense Rock)")

    recommendations_1 = recommend_songs(user_prefs_1, songs, k=5, mode=mode_1)
    recommendations_2 = recommend_songs(High_Energy_Pop, songs, k=5, mode=mode_2)
    recommendations_3 = recommend_songs(Chill_Lofi, songs, k=5, mode=mode_3)
    recommendations_4 = recommend_songs(Deep_Intense_Rock, songs, k=5, mode=mode_4)

    print_recommendations("Top recommendations for User 1", user_prefs_1, recommendations_1, mode_1)
    print_recommendations("Top recommendations for User 2 (High Energy Pop)", High_Energy_Pop, recommendations_2, mode_2)
    print_recommendations("Top recommendations for User 3 (Chill Lofi)", Chill_Lofi, recommendations_3, mode_3)
    print_recommendations("Top recommendations for User 4 (Deep Intense Rock)", Deep_Intense_Rock, recommendations_4, mode_4)


if __name__ == "__main__":
    main()
