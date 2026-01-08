#!/usr/bin/env python3
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

# Try importing pygame
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("Warning: pygame not installed. Audio will be disabled.")
    time.sleep(1)

# --- Configuration & Data ---
SOUNDS = {}

# Determine paths
APP_NAME = "hypertyper"

# 1. Data Directory (Read-only assets: words, sounds)
# Check local first (dev mode), then system install path
local_data = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
if os.path.exists(local_data):
    DATA_DIR = local_data
else:
    # Standard Linux install path
    DATA_DIR = os.path.join("/usr/share", APP_NAME, "data")

# 2. Config Directory (Writable: settings, highscores)
# Use XDG_CONFIG_HOME or default to ~/.config
xdg_config = os.environ.get("XDG_CONFIG_HOME", os.path.join(os.path.expanduser("~"), ".config"))
CONFIG_DIR = os.path.join(xdg_config, APP_NAME)

# Ensure config directory exists
os.makedirs(CONFIG_DIR, exist_ok=True)

HIGHSCORE_FILE = os.path.join(CONFIG_DIR, "highscores.json")
SETTINGS_FILE = os.path.join(CONFIG_DIR, "settings.json")

# Backwards compatibility: Migration from local dir if user was running locally before
# (Optional: You could add logic here to move local json files to CONFIG_DIR if they exist)

WORD_FILE = "words.txt"
BACKUP_WORDS = ["apple", "banana", "cherry", "date", "elderberry", "fig", "grape", "lemon", "lime", "mango"]

DEFAULT_SETTINGS = {
    "sound": True,
    "time_limit": 30,
    "show_timer": True
}
SETTINGS = {}

# --- Helper Functions ---

def load_settings():
    """Loads settings from data/settings.json, creating it with defaults if missing."""
    global SETTINGS
    
    # Path is global constant now
    file_path = SETTINGS_FILE
    
    if not os.path.exists(file_path):
        SETTINGS = DEFAULT_SETTINGS.copy()
        save_settings(SETTINGS)
        return

    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            # Merge with defaults to ensure all keys exist
            SETTINGS = DEFAULT_SETTINGS.copy()
            SETTINGS.update(data)
    except (json.JSONDecodeError, IOError):
        SETTINGS = DEFAULT_SETTINGS.copy()
        save_settings(SETTINGS)

def save_settings(new_settings):
    """Saves the settings dict to data/settings.json."""
    global SETTINGS
    SETTINGS = new_settings
    
    file_path = SETTINGS_FILE
    try:
        with open(file_path, 'w') as f:
            json.dump(SETTINGS, f, indent=4)
    except IOError:
        print(f"\n{Fore.RED}Warning: Could not save settings.{Style.RESET_ALL}")

def load_words(filename, exact_match=False):
    """Loads words from data/filename. Falls back to BACKUP_WORDS if needed.
    If exact_match is True, preserves case and allows punctuation/spaces.
    """
    words = []
    # Look for filename inside the DATA_DIR folder
    file_path = os.path.join(DATA_DIR, filename)
    
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    if exact_match:
                        # Just strip newlines, keep content as is
                        w = line.strip()
                        if w:
                            words.append(w)
                    else:
                        # Standard mode logic
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


def organize_sound_files():
    """Checks for a root 'sounds' folder and moves it to data/sounds (Dev mode only)."""
    # Only run if we are in local dev mode
    if DATA_DIR != os.path.join(os.path.dirname(os.path.abspath(__file__)), "data"):
        return

    root_sounds = "sounds"
    dest_sounds = os.path.join(DATA_DIR, "sounds")
    
    if os.path.exists(root_sounds) and os.path.isdir(root_sounds):
        if not os.path.exists(dest_sounds):
            print(f"{Fore.YELLOW}Organizing: Moving '{root_sounds}' to '{dest_sounds}'...{Style.RESET_ALL}")
            try:
                shutil.move(root_sounds, dest_sounds)
                time.sleep(1)
            except Exception as e:
                print(f"{Fore.RED}Error moving sounds folder: {e}{Style.RESET_ALL}")
                time.sleep(2)
        else:
            # Destination already exists, maybe merge? For now just warn
            print(f"{Fore.YELLOW}Note: '{root_sounds}' exists but '{dest_sounds}' also exists. Manual cleanup may be needed.{Style.RESET_ALL}")
            time.sleep(2)

def init_audio():
    """Initializes pygame mixer and loads sounds."""
    global SOUNDS
    if not PYGAME_AVAILABLE:
        return

    try:
        pygame.mixer.init()
    except Exception as e:
        print(f"{Fore.RED}Audio Init Failed: {e}{Style.RESET_ALL}")
        return

    sound_files = {
        "splash": "splash.wav",
        "countdown": "countdown.wav",
        "correct": "correct.wav",
        "levelup": "levelup.wav",
        "gameover": "gameover.wav",
        "victory": "victory.wav"
    }
    
    base_path = os.path.join(DATA_DIR, "sounds")
    
    print(f"{Fore.CYAN}Loading sounds...{Style.RESET_ALL}")
    for name, filename in sound_files.items():
        path = os.path.join(base_path, filename)
        if os.path.exists(path):
            try:
                SOUNDS[name] = pygame.mixer.Sound(path)
            except Exception as e:
                print(f"{Fore.RED}Failed to load {filename}: {e}{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}Warning: Sound file '{filename}' not found.{Style.RESET_ALL}")
    
    # Small delay to let user see load status if any issues
    # time.sleep(0.5)

def play_sound(name):
    """Plays a sound by name if available."""
    # Check settings first
    if not SETTINGS.get("sound", True):
        return

    if name in SOUNDS:
        try:
            SOUNDS[name].play()
        except:
            pass



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
    
    play_sound("splash")
    draw_centered(logo, input_prompt=f"{Fore.YELLOW}Press Enter to Start...{Style.RESET_ALL}")

def countdown():
    """Runs a 3-2-1-GO countdown."""
    play_sound("countdown")
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
    """Loads high scores, migrating old format {'Mode': 100} to {'Mode': {'score': 100, 'name': 'CPU'}}."""
    defaults = {"Streak": {"score": 0, "name": "---"}}
    
    if not os.path.exists(HIGHSCORE_FILE):
        return defaults
    
    try:
        with open(HIGHSCORE_FILE, 'r') as f:
            data = json.load(f)
            if not isinstance(data, dict):
                return defaults
            
            # Check for migration needs
            migrated = False
            new_data = {}
            
            for k, v in data.items():
                if isinstance(v, int):
                    # Old format detected
                    new_data[k] = {"score": v, "name": "CPU"}
                    migrated = True
                elif isinstance(v, dict) and "score" in v:
                    # New format (basic check)
                    new_data[k] = v
                else:
                     new_data[k] = {"score": 0, "name": "---"}
            
            if migrated:
                print(f"{Fore.YELLOW}Migrated high scores to new format...{Style.RESET_ALL}")
                save_high_scores(new_data)
                return new_data
            
            return data
    except (json.JSONDecodeError, IOError):
        return defaults

def save_high_scores(scores):
    """Saves the high score dict to JSON."""
    try:
        with open(HIGHSCORE_FILE, 'w') as f:
            json.dump(scores, f, indent=4)
    except IOError:
        print("\nWarning: Could not save high scores.")

def get_high_score_data(mode_name):
    """Returns the high score dict {'score': X, 'name': 'Y'} for a mode."""
    scores = load_high_scores()
    return scores.get(mode_name, {"score": 0, "name": "---"})

def show_high_scores():
    """Displays high scores in a formatted Hall of Fame table."""
    scores = load_high_scores()
    
    lines = [
        f"{Fore.CYAN}{Style.BRIGHT}=== HALL OF FAME ==={Style.RESET_ALL}",
        ""
    ]
    
    # Table Header
    # MODE (15) | SCORE (8) | HELD BY
    header = f"{Fore.WHITE}{Style.BRIGHT}{'MODE':<15} {'SCORE':<8} {'HELD BY'}{Style.RESET_ALL}"
    lines.append(header)
    lines.append("-" * 35)
    
    if not scores:
        lines.append("No scores recorded yet.")
    else:
        for mode in sorted(scores.keys()):
            entry = scores[mode]
            s_val = entry.get('score', 0)
            s_name = entry.get('name', '---')
            
            # Format row
            # Use yellow for score to make it pop
            row = f"{Fore.CYAN}{mode:<15}{Style.RESET_ALL} {Fore.YELLOW}{s_val:<8}{Style.RESET_ALL} {Fore.MAGENTA}{s_name}{Style.RESET_ALL}"
            lines.append(row)
    
    lines.append("")
    lines.append("-" * 35)
    
    draw_centered(lines, input_prompt=f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")

# --- Game Modes ---

def streak_mode(mode_name, word_filename, exact_match=False):
    """Runs the Streak Mode game loop with a 30s global timer and game feel."""
    
    # Load words for this mode
    current_words = load_words(word_filename, exact_match=exact_match)
    
    while True:
        # Countdown
        countdown()
        
        score = 0
        total_chars_typed = 0
        correct_words = 0
        combo = 0
        start_time = time.time()
        
        # Use settings for time limit
        time_limit = float(SETTINGS.get("time_limit", 30))
        
        while True:
            # 1. Check time BEFORE showing word
            elapsed = time.time() - start_time
            if elapsed >= time_limit:
                play_sound("victory")
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
            # Logic for timer display
            if SETTINGS.get("show_timer", True):
                timer_display = f"{Fore.YELLOW}~{remaining}s{Style.RESET_ALL}"
            else:
                timer_display = f"{Fore.YELLOW}--{Style.RESET_ALL}"
                
            lines = [
                f"{Fore.CYAN}--- {mode_name.upper()} MODE ---{Style.RESET_ALL}",
                f"SCORE: {Fore.YELLOW}{score}{Style.RESET_ALL}  |  TIME: {timer_display}  |  COMBO: {Fore.GREEN}{combo}{Style.RESET_ALL}{combo_text}",
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
                play_sound("victory")
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
                play_sound("correct")
                
                # Check for combo tier up (simple check: if combo hits a threshold exactly)
                # Tiers: 3, 5, 7, 10, 12
                if combo in [3, 5, 7, 10, 12]:
                    play_sound("levelup")
                
                msg = f"{Fore.GREEN}{target_word} OK! (+{points}){Style.RESET_ALL}"
                cols, _ = shutil.get_terminal_size()
                vis_len = get_visible_length(msg)
                padding = max(0, (cols - vis_len) // 2)
                print(" " * padding + msg)
                time.sleep(0.2)
            else:
                combo = 0 # Reset combo on mistake (though game ends here anyway)
                
                play_sound("gameover")
                
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
        

        # Check High Score
        hs_data = get_high_score_data(mode_name)
        current_best = hs_data.get('score', 0)
        is_new_record = score > current_best
        
        if is_new_record:
            play_sound("levelup")
            lines.insert(2, f"{Fore.GREEN}🚨 NEW HIGH SCORE! 🚨{Style.RESET_ALL}")
            
            # Prompt for name
            prompt_line = f"Enter initials (3 chars): "
            
            while True:
                name_input = draw_centered(lines, input_prompt=prompt_line).strip().upper()
                if len(name_input) > 3:
                     name_input = name_input[:3]
                
                if name_input:
                    # Save it
                    all_scores = load_high_scores()
                    all_scores[mode_name] = {'score': score, 'name': name_input}
                    save_high_scores(all_scores)
                    
                    lines.append(f"{Fore.GREEN}Score Saved! {name_input} - {score}{Style.RESET_ALL}")
                    break
                else:
                    # Force default
                    name_input = 'UNK'
                    all_scores = load_high_scores()
                    all_scores[mode_name] = {'score': score, 'name': name_input}
                    save_high_scores(all_scores)
                    lines.append(f"{Fore.GREEN}Score Saved! {name_input} - {score}{Style.RESET_ALL}")
                    break

            lines.append("")
            lines.append(f"[{Fore.CYAN}Press ENTER for Menu{Style.RESET_ALL}] or [{Fore.CYAN}Press 'R' to Retry{Style.RESET_ALL}]")
             
            cmd = draw_centered(lines, input_prompt="").strip().lower()
            if cmd == 'r':
                continue
            else:
                break
            
        else:
            # Not a high score
            hs_msg = f"{Fore.CYAN}High Score: {current_best} ({hs_data.get('name', '---')}){Style.RESET_ALL}"
            lines.insert(7, hs_msg)
            
            lines.append(f"[{Fore.CYAN}Press ENTER for Menu{Style.RESET_ALL}] or [{Fore.CYAN}Press 'R' to Retry{Style.RESET_ALL}]")
            
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
            f"{Fore.CYAN}1. Streak{Style.RESET_ALL}",
            f"{Fore.CYAN}2. Cities{Style.RESET_ALL}",
            f"{Fore.CYAN}3. Food{Style.RESET_ALL}",
            f"{Fore.CYAN}4. Animals{Style.RESET_ALL}",
            f"{Fore.CYAN}5. Lorem Ipsum{Style.RESET_ALL}",
            f"{Fore.CYAN}6. Code Snippets{Style.RESET_ALL}",
            f"{Fore.CYAN}7. Terminal Commands{Style.RESET_ALL}",
            f"{Fore.CYAN}8. Brainrot{Style.RESET_ALL}",
            f"{Fore.CYAN}9. UwU{Style.RESET_ALL}",
            f"{Fore.CYAN}10. LinkedIn Jargon{Style.RESET_ALL}",
            f"{Fore.CYAN}11. Spanish{Style.RESET_ALL}",
            f"{Fore.CYAN}12. Pokemon{Style.RESET_ALL}",
            f"{Fore.CYAN}13. Back to Main Menu{Style.RESET_ALL}"
        ]
        
        try:
            choice = draw_centered(lines, input_prompt="Select an option (1-13): ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if choice == '1':
            streak_mode("Streak", "words.txt")
        elif choice == '2':
            streak_mode("Cities", "capitals.txt", exact_match=True)
        elif choice == '3':
            streak_mode("Food", "foods.txt")
        elif choice == '4':
            streak_mode("Animals", "animals.txt")
        elif choice == '5':
            streak_mode("Lorem", "lorem.txt")
        elif choice == '6':
            streak_mode("Code Snippets", "code.txt", exact_match=True)
        elif choice == '7':
            streak_mode("Terminal Commands", "terminal.txt", exact_match=True)
        elif choice == '8':
            streak_mode("Brainrot", "brainrot.txt", exact_match=True)
        elif choice == '9':
            streak_mode("UwU", "uwu.txt", exact_match=True)
        elif choice == '10':
            streak_mode("LinkedIn Jargon", "linkedin.txt", exact_match=True)
        elif choice == '11':
            streak_mode("Spanish", "spanish.txt")
        elif choice == '12':
            streak_mode("Pokemon", "pokemon.txt")
        elif choice == '13':
            break
        else:
            pass

def settings_menu():
    """Menu for changing game settings."""
    while True:
        # Load current values from global SETTINGS
        s_sound = "ON" if SETTINGS.get("sound", True) else "OFF"
        s_time = SETTINGS.get("time_limit", 30)
        s_display = "SHOW" if SETTINGS.get("show_timer", True) else "HIDE"
        
        # Colors for status
        c_sound = Fore.GREEN if s_sound == "ON" else Fore.RED
        c_display = Fore.GREEN if s_display == "SHOW" else Fore.RED
        
        lines = [
            f"{Fore.CYAN}{Style.BRIGHT}=== SETTINGS ==={Style.RESET_ALL}",
            f"1. Sound: [{c_sound}{s_sound}{Style.RESET_ALL}]",
            f"2. Timer Length: [{Fore.YELLOW}{s_time}s{Style.RESET_ALL}]",
            f"3. Timer Display: [{c_display}{s_display}{Style.RESET_ALL}]",
            f"4. {Fore.RED}Reset All High Scores{Style.RESET_ALL}",
            f"5. Back to Main Menu"
        ]
        
        try:
            choice = draw_centered(lines, input_prompt="Select an option (1-5): ").strip()
        except (EOFError, KeyboardInterrupt):
            break
            
        if choice == '1':
            # Toggle Sound
            SETTINGS["sound"] = not SETTINGS.get("sound", True)
            save_settings(SETTINGS)
            
        elif choice == '2':
            # Cycle Timer: 15 -> 30 -> 60 -> 120 -> 15
            options = [15, 30, 60, 120]
            current = SETTINGS.get("time_limit", 30)
            try:
                idx = options.index(current)
                next_idx = (idx + 1) % len(options)
                SETTINGS["time_limit"] = options[next_idx]
            except ValueError:
                SETTINGS["time_limit"] = 30 # Default if unknown value
            save_settings(SETTINGS)
            
        elif choice == '3':
            # Toggle Timer Display
            SETTINGS["show_timer"] = not SETTINGS.get("show_timer", True)
            save_settings(SETTINGS)
            
        elif choice == '4':
            # Reset High Scores (Danger Zone)
            # Clear screen and show warning
            warning_lines = [
                f"{Fore.RED}{Style.BRIGHT}ARE YOU SURE? THIS CANNOT BE UNDONE.{Style.RESET_ALL}",
                "Type 'Y' or 'y' to confirm, anything else to cancel."
            ]
            confirm = draw_centered(warning_lines, input_prompt="Confirm Reset: ").strip().lower()
            
            if confirm == 'y':
                defaults = {"Streak": {"score": 0, "name": "---"}}
                save_high_scores(defaults)
                # Show success
                msg_lines = [
                    f"{Fore.GREEN}Scores Reset!{Style.RESET_ALL}",
                ]
                draw_centered(msg_lines, input_prompt="Press Enter to continue...")
            else:
                # Cancelled
                pass
                
        elif choice == '5':
            break
        else:
            pass

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
            settings_menu()
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
    
    # Load settings
    load_settings()

    # Clear screen immediately on launch
    organize_sound_files()
    init_audio()
    splash_screen()
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\nGame Interrupted. Bye!")
        sys.exit(0)
