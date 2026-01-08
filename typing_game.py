
import os
import random
import sys
import time
import json
import shutil
import re
from colorama import Fore, Back, Style, init

# Initialize colorama
init(autoreset=True)

# --- Configuration & Data ---

HIGHSCORE_FILE = "highscores.json"
WORD_FILE = "words.txt"
BACKUP_WORDS = ["apple", "banana", "cherry", "date", "elderberry", "fig", "grape", "lemon", "lime", "mango"]

# --- Helper Functions ---

def load_words(filename):
    """Loads words from data/filename, filtering invalid ones. Falls back to BACKUP_WORDS if needed."""
    words = []
    # Look for filename inside the 'data' folder
    file_path = os.path.join("data", filename)
    
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    w = line.strip().lower()
                    if len(w) >= 3 and w.isalpha():
                        words.append(w)
        except IOError:
            pass # Keep list empty to trigger backup

    if not words:
        print(f"Warning: {file_path} not found or empty, using backup list.")
        time.sleep(2) # Give user a chance to see the warning
        return BACKUP_WORDS
    
    return words


def get_visible_length(s):
    """Returns the length of the string without ANSI color codes."""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return len(ansi_escape.sub('', s))

def get_combo_tier(combo):
    """
    Returns (tier_name, multiplier, color_code) based on combo count.
    Tiers:
      0-2:   None
      3-4:   Flow State (1.5x) - Cyan
      5-6:   Overclocked (2x) - Green
      7-9:   Surge (3x) - Yellow
      10-11: Unstoppable (5x) - Red
      12+:   God Mode (8x) - Magenta
    """
    if combo >= 12:
        return "GOD MODE", 8.0, Fore.MAGENTA + Style.BRIGHT
    elif combo >= 10:
        return "UNSTOPPABLE", 5.0, Fore.RED + Style.BRIGHT
    elif combo >= 7:
        return "SURGE", 3.0, Fore.YELLOW + Style.BRIGHT
    elif combo >= 5:
        return "OVERCLOCKED", 2.0, Fore.GREEN + Style.BRIGHT
    elif combo >= 3:
        return "FLOW STATE", 1.5, Fore.CYAN + Style.BRIGHT
    else:
        return "", 1.0, ""

def draw_centered(lines, input_prompt=None):
    """
    Clears screen and draws the list of 'lines' centered vertically and horizontally.
    If input_prompt is provided, it is printed centered below the lines,
    and the function returns the user input.
    """
    clear_screen()
    
    # Get terminal size
    cols, rows = shutil.get_terminal_size()
    
    # Calculate total height of content
    content_height = len(lines)
    if input_prompt is not None:
        content_height += 2 # Add spacing + prompt line
        
    # Vertical padding (top)
    # Ensure at least 0
    top_padding = max(0, (rows - content_height) // 2)
    
    # Print top newlines
    print("\n" * top_padding)
    
    # Print each line centered
    for line in lines:
        vis_len = get_visible_length(line)
        left_padding = max(0, (cols - vis_len) // 2)
        print(" " * left_padding + line)
        
    if input_prompt is not None:
        # Print a blank spacer line
        print()
        # Calculate padding for prompt
        vis_len = get_visible_length(input_prompt)
        left_padding = max(0, (cols - vis_len) // 2)
        
        # Print prompt with padding, no newline at end so cursor stays there
        print(" " * left_padding + input_prompt, end='')
        return input("")



def clear_screen():
    """Clears the terminal screen."""
    # os.name is 'nt' for Windows, 'posix' for Linux/Mac
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')

def splash_screen():
    """Displays a cool ASCII art logo on startup."""
    logo = [
        f"{Fore.MAGENTA}{Style.BRIGHT}",
        r"  _   _  __   __  ____   _____   ____  ",
        r" | | | | \ \ / / |  _ \ | ____| |  _ \ ",
        r" | |_| |  \ V /  | |_) ||  _|   | |_) |",
        r" |  _  |   | |   |  __/ | |___  |  _ < ",
        " |_| |_|   |_|   |_|    |_____| |_| \\_\\",
        f"{Fore.CYAN}",
        r"   _____  __   __  ____   _____   ____  ",
        r"  |_   _| \ \ / / |  _ \ | ____| |  _ \ ",
        r"    | |    \ V /  | |_) ||  _|   | |_) |",
        r"    | |     | |   |  __/ | |___  |  _ < ",
        "   |_|     |_|   |_|    |_____| |_| \\_\\",
        f"{Style.RESET_ALL}"
    ]
    
    draw_centered(logo, input_prompt=f"{Fore.YELLOW}Press Enter to Start...{Style.RESET_ALL}")

def countdown():
    """Runs a 3-2-1-GO countdown."""
    for i in [3, 2, 1]:
        draw_centered([f"{Fore.CYAN}{Style.BRIGHT}{i}"])
        time.sleep(1)
    
    draw_centered([f"{Fore.GREEN}{Style.BRIGHT}GO!"])
    time.sleep(0.5)

def pause():
    """Waits for user input to continue."""
    # We can't really center this effectively without clearing the screen,
    # but usually pause follows some output. 
    # If we want to center the "Press Enter" message, we'd need to know what was on screen.
    # For now, let's keep it simple or we can just print it centered relative to the last known size? 
    # Actually, the user wants "Action: Clear the screen...". 
    # So if pause is a standalone screen (like after high scores), we can use draw_centered.
    input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")

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

def check_high_score(mode_name, score):
    """Updates the high score for a given mode if the new score is higher. Returns a message string."""
    scores = load_high_scores()
    current_best = scores.get(mode_name, 0)
    
    if score > current_best:
        scores[mode_name] = score
        save_high_scores(scores)
        return f"{Fore.GREEN}{Style.BRIGHT}NEW HIGH SCORE for {mode_name}: {score}!{Style.RESET_ALL}"
    else:
        return f"{Fore.CYAN}High Score for {mode_name}: {current_best}{Style.RESET_ALL}"

def show_high_scores():
    """Displays all high scores."""
    lines = [f"{Fore.CYAN}{Style.BRIGHT}--- HIGH SCORES ---{Style.RESET_ALL}"]
    scores = load_high_scores()
    
    if not scores:
        lines.append("No scores recording yet.")
    else:
        for mode, score in scores.items():
            lines.append(f"{mode}: {Fore.YELLOW}{score}{Style.RESET_ALL}")
    
    lines.append("-" * 20)
    
    draw_centered(lines, input_prompt=f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")

# --- Game Modes ---

def streak_mode(mode_name, word_filename):
    """Runs the Streak Mode game loop with a 30s global timer and game feel."""
    
    # Load words for this mode
    current_words = load_words(word_filename)
    
    while True:
        # Countdown
        countdown()
        
        score = 0
        total_chars_typed = 0
        correct_words = 0
        combo = 0
        start_time = time.time()
        time_limit = 30.0
        
        while True:
            # 1. Check time BEFORE showing word
            elapsed = time.time() - start_time
            if elapsed >= time_limit:
                break # Go to Game Over logic

            remaining = max(0, int(time_limit - elapsed))
            
            # Determine multiplier and combo text
            tier_name, multiplier, color_code = get_combo_tier(combo)
            
            combo_text = ""
            if tier_name:
                # Format: " TIER_NAME (Nx)"
                # e.g. " GOD MODE (8x)"
                # We interpret "x" as multiplier symbol. User asked for "NAME (Nx)"
                if multiplier.is_integer():
                    mult_str = f"{int(multiplier)}x"
                else:
                    mult_str = f"{multiplier}x"
                
                combo_text = f" {color_code}{tier_name} ({mult_str}){Style.RESET_ALL}"
            
            target_word = random.choice(current_words)
            
            # Construct Game Loop UI
            lines = [
                f"{Fore.CYAN}--- {mode_name.upper()} MODE ---{Style.RESET_ALL}",
                f"SCORE: {Fore.YELLOW}{score}{Style.RESET_ALL}  |  TIME: {Fore.YELLOW}~{remaining}s{Style.RESET_ALL}  |  COMBO: {Fore.GREEN}{combo}{Style.RESET_ALL}{combo_text}",
                "-" * 60,
                "",
                f"Word:  {Style.BRIGHT}{Fore.WHITE}{target_word}{Style.RESET_ALL}",
                ""
            ]
            
            try:
                user_input = draw_centered(lines, input_prompt="Type it: ").strip()
            except (EOFError, KeyboardInterrupt):
                return

            # 2. Check time AFTER input
            elapsed = time.time() - start_time
            if elapsed >= time_limit:
                break # Go to Game Over logic

            # 3. Sudden Death Check
            if user_input == target_word:
                combo += 1
                word_len = len(target_word)
                points = int(word_len * multiplier)
                score += points
                
                total_chars_typed += word_len
                correct_words += 1
                
                # Success Flash - Centered manually since we don't want to clear screen
                msg = f"{Fore.GREEN}{target_word} OK! (+{points}){Style.RESET_ALL}"
                cols, _ = shutil.get_terminal_size()
                vis_len = get_visible_length(msg)
                padding = max(0, (cols - vis_len) // 2)
                print(" " * padding + msg)
                time.sleep(0.2)
            else:
                combo = 0 # Reset combo on mistake (though game ends here anyway)
                
                # Fail Message - Centered manually
                msg = f"{Fore.RED}Wrong! You typed '{user_input}', expected '{target_word}'.{Style.RESET_ALL}"
                cols, _ = shutil.get_terminal_size()
                vis_len = get_visible_length(msg)
                padding = max(0, (cols - vis_len) // 2)
                print()
                print(" " * padding + msg)
                break # Go to Game Over logic

        # --- GAME OVER SCREEN ---
        final_elapsed = time.time() - start_time
        
        if final_elapsed < 1.0: 
            final_elapsed = 1.0 # Avoid div by zero
        
        minutes = final_elapsed / 60.0
        wpm = (total_chars_typed / 5.0) / minutes if minutes > 0 else 0
        
        lines = [
            "",
            f"{Fore.RED}{Style.BRIGHT}GAME OVER{Style.RESET_ALL}",
            f"Final Score: {Fore.YELLOW}{score}{Style.RESET_ALL}",
            "-" * 30,
            f"Total Words Typed: {correct_words}",
            f"WPM: {Fore.CYAN}{wpm:.1f}{Style.RESET_ALL}",
            "-" * 30,
            "",
            f"[{Fore.CYAN}Press ENTER for Menu{Style.RESET_ALL}] or [{Fore.CYAN}Press 'R' to Retry{Style.RESET_ALL}]"
        ]
        

        hs_message = check_high_score(mode_name, score) # Renamed or new helper?
        if hs_message:
            lines.insert(2, hs_message) # Insert after GAME OVER?
            
        cmd = draw_centered(lines, input_prompt="").strip().lower()
        if cmd == 'r':
            continue # Restart loop
        else:
            break # Return to menu

def play_menu():
    """Submenu for selecting a game mode."""
    while True:
        lines = [
            f"{Fore.CYAN}{Style.BRIGHT}--- SELECT CATEGORY ---{Style.RESET_ALL}",
            f"{Fore.CYAN}1. Standard Streak{Style.RESET_ALL}",
            f"{Fore.CYAN}2. Capital Cities{Style.RESET_ALL}",
            f"{Fore.CYAN}3. Foods{Style.RESET_ALL}",
            f"{Fore.CYAN}4. Animals{Style.RESET_ALL}",
            f"{Fore.CYAN}5. Lorem Ipsum{Style.RESET_ALL}",
            f"{Fore.CYAN}6. Back to Main Menu{Style.RESET_ALL}"
        ]
        
        try:
            choice = draw_centered(lines, input_prompt="Select an option (1-6): ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if choice == '1':
            streak_mode("Streak", "words.txt")
        elif choice == '2':
            streak_mode("Capitals", "capitals.txt")
        elif choice == '3':
            streak_mode("Foods", "foods.txt")
        elif choice == '4':
            streak_mode("Animals", "animals.txt")
        elif choice == '5':
            streak_mode("Lorem", "lorem.txt")
        elif choice == '6':
            break
        else:
            pass

def show_placeholder(feature_name):
    """Displays a 'Coming Soon' message."""
    lines = [
        f"--- {feature_name} ---",
        "\nComing Soon!\n"
    ]
    draw_centered(lines, input_prompt=f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")

# --- Main Menu ---

def main_menu():
    """Runs the main menu loop."""
    while True:
        lines = [
            f"{Fore.CYAN}{Style.BRIGHT}=== CLI TYPING GAME ==={Style.RESET_ALL}",
            f"{Fore.CYAN}1. Play Game{Style.RESET_ALL}",
            f"{Fore.CYAN}2. High Scores{Style.RESET_ALL}",
            f"{Fore.CYAN}3. Settings{Style.RESET_ALL}",
            f"{Fore.CYAN}4. Quit{Style.RESET_ALL}"
        ]
        
        try:
            choice = draw_centered(lines, input_prompt="Select an option (1-4): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if choice == '1':
            play_menu()
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
    splash_screen()
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\nGame Interrupted. Bye!")
        sys.exit(0)
