import os
import tkinter as tk
from tkinter import filedialog, messagebox
from utils.tag_manager import load_tags, save_tags
from utils.mood_detector import process_folder
from ui.player_gui import launch_player

def main():
    root = tk.Tk()
    root.withdraw()

    folder_path = filedialog.askdirectory(title="Select your music folder")
    if not folder_path:
        messagebox.showinfo("Exit", "No folder selected.")
        return

    tag_file = os.path.join(folder_path, "mood_tags.json")

    if not os.path.exists(tag_file):
        print("[INFO] No mood_tags.json found. Processing songs...")
        mood_tags = process_folder(folder_path)
        save_tags(tag_file, mood_tags)
        print("[DONE] Mood tagging complete.")
    else:
        mood_tags = load_tags(tag_file)
        print("[INFO] Loaded existing mood tags.")

    launch_player(folder_path, mood_tags)

if __name__ == "__main__":
    main()
