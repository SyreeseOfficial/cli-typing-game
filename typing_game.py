
import os
import random
import sys
import time
import json

# --- Configuration & Data ---

HIGHSCORE_FILE = "highscores.json"
WORDS = [
    "apple", "banana", "cherry", "date", "elderberry",
    "fig", "grape", "honeydew", "kiwi", "lemon",
    "mango", "nectarine", "orange", "papaya", "quince",
    "raspberry", "strawberry", "tangerine", "ugli", "vanilla",
    "watermelon", "xigua", "yam", "zucchini", "avocado",
    "blueberry", "cantaloupe", "durian", "eggplant", "fennel",
    "guava", "huckleberry", "jackfruit", "kumquat", "lime",
    "mulberry", "nutmeg", "olive", "peach", "quinoa",
    "radish", "spinach", "tomato", "umbrella", "violet",
    "waffle", "xylophone", "yogurt", "zebra", "asteroid",
    "galaxy", "nebula", "planet", "comet", "meteor",
    "satellite", "telescope", "universe", "astronaut", "spaceship",
    "adventure", "bicycle", "camera", "diamond", "elephant",
    "festival", "garden", "history", "island", "jungle",
    "kangaroo", "lantern", "mountain", "notebook", "ocean",
    "penguin", "question", "rainbow", "sunflower", "treasure",
    "unicorn", "volcano", "waterfall", "xenon", "yellow",
    "zeppelin", "architect", "biologist", "chemist", "dentist",
    "engineer", "farmer", "geologist", "historian", "inventor",
    "journalist", "librarian", "musician", "nurse", "optician"
]

# --- Helper Functions ---

def clear_screen():
    """Clears the terminal screen."""
    # os.name is 'nt' for Windows, 'posix' for Linux/Mac
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')

def pause():
    """Waits for user input to continue."""
    input("\nPress Enter to continue...")

def load_high_scores():
    """Loads high scores from JSON, returning a dict."""
    if not os.path.exists(HIGHSCORE_FILE):
        return {"Streak": 0}
    
    try:
        with open(HIGHSCORE_FILE, 'r') as f:
            data = json.load(f)
            if not isinstance(data, dict):
                return {"Streak": 0}
            return data
    except (json.JSONDecodeError, IOError):
        return {"Streak": 0}

def save_high_scores(scores):
    """Saves the high score dict to JSON."""
    try:
        with open(HIGHSCORE_FILE, 'w') as f:
            json.dump(scores, f, indent=4)
    except IOError:
        print("\nWarning: Could not save high scores.")

def update_high_score(mode_name, score):
    """Updates the high score for a given mode if the new score is higher."""
    scores = load_high_scores()
    current_best = scores.get(mode_name, 0)
    
    if score > current_best:
        scores[mode_name] = score
        save_high_scores(scores)
        print(f"\nNEW HIGH SCORE for {mode_name}: {score}!")
    else:
        print(f"\nHigh Score for {mode_name}: {current_best}")

def show_high_scores():
    """Displays all high scores."""
    clear_screen()
    print("--- HIGH SCORES ---")
    scores = load_high_scores()
    
    if not scores:
        print("No scores recording yet.")
    else:
        for mode, score in scores.items():
            print(f"{mode}: {score}")
    
    print("-" * 20)
    print()
    pause()

# --- Game Modes ---

def streak_mode():
    """Runs the Streak Mode game loop with a 30s global timer."""
    score = 0
    start_time = time.time()
    time_limit = 30.0
    
    while True:
        # 1. Check time BEFORE showing word
        elapsed = time.time() - start_time
        if elapsed >= time_limit:
            print("\nTime's Up! Game Over.")
            print(f"Final Score: {score}")
            update_high_score("Streak", score)
            print()
            pause()
            break

        remaining = max(0, int(time_limit - elapsed))
        
        clear_screen()
        print("--- STREAK MODE ---")
        print(f"CURRENT SCORE: {score}   |   TIME LEFT: ~{remaining}s")
        print("-" * 40)
        print()
        
        target_word = random.choice(WORDS)
        print(f"Word:  {target_word}")
        print()
        
        try:
            user_input = input("Type it: ").strip()
        except (EOFError, KeyboardInterrupt):
            return

        # 2. Check time AFTER input
        elapsed = time.time() - start_time
        if elapsed >= time_limit:
            print("\nTime's Up! (You ran out of time while typing)")
            print(f"Final Score: {score}")
            update_high_score("Streak", score)
            print()
            pause()
            break

        # 3. Sudden Death Check
        if user_input == target_word:
            score += len(target_word)
        else:
            print()
            print(f"Wrong! You typed '{user_input}', expected '{target_word}'.")
            print(f"Final Score: {score}")
            update_high_score("Streak", score)
            print()
            pause()
            break

def show_placeholder(feature_name):
    """Displays a 'Coming Soon' message."""
    clear_screen()
    print(f"--- {feature_name} ---")
    print("\nComing Soon!\n")
    pause()

# --- Main Menu ---

def main_menu():
    """Runs the main menu loop."""
    while True:
        clear_screen()
        print("=== CLI TYPING GAME ===")
        print("1. Play Game")
        print("2. High Scores")
        print("3. Settings")
        print("4. Quit")
        print()
        
        try:
            choice = input("Select an option (1-4): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if choice == '1':
            streak_mode()
        elif choice == '2':
            show_high_scores()
        elif choice == '3':
            show_placeholder("Settings")
        elif choice == '4':
            print("\nThanks for playing! Goodbye.")
            break
        else:
            # Invalid input, just loop again (or could print error)
            pass

if __name__ == "__main__":
    # Ensure highscore file exists
    if not os.path.exists(HIGHSCORE_FILE):
        save_high_scores({"Streak": 0})

    # Clear screen immediately on launch
    clear_screen()
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\nGame Interrupted. Bye!")
        sys.exit(0)
