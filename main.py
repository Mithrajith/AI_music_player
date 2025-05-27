import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from utils.tag_manager import load_tags, save_tags
from utils.mood_detector import process_folder
from ui.player_gui import launch_player
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("music_player.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def create_default_cover():
    """Create a default cover image if it doesn't exist."""
    default_cover_path = os.path.join("assets", "default_cover.jpg")
    if not os.path.exists(default_cover_path):
        try:
            from PIL import Image, ImageDraw, ImageFont
            img = Image.new('RGB', (300, 300), color='#808080')
            draw = ImageDraw.Draw(img)
            try:
                font = ImageFont.truetype("arial.ttf", 20)
            except:
                font = ImageFont.load_default()
            draw.text((50, 140), "No Cover Available", fill='white', font=font)
            os.makedirs("assets", exist_ok=True)
            img.save(default_cover_path)
            logger.info("Created default cover image at %s", default_cover_path)
        except Exception as e:
            logger.error("Failed to create default cover image: %s", e)
    return default_cover_path

def validate_folder(folder_path, audio_extensions=(".mp3", ".wav")):
    """Validate the selected folder contains audio files."""
    if not os.path.isdir(folder_path):
        logger.error("Selected path is not a directory: %s", folder_path)
        return False
    for file in os.listdir(folder_path):
        if file.lower().endswith(audio_extensions):
            return True
    logger.warning("No audio files found in %s", folder_path)
    return False

def process_mood_tags(folder_path, force_reprocess=False):
    """Load or generate mood tags for the selected folder."""
    tag_file = os.path.join(folder_path, "mood_tags.json")
    if force_reprocess or not os.path.exists(tag_file):
        logger.info("No mood_tags.json found or reprocessing requested. Processing songs in %s", folder_path)
        try:
            mood_tags = process_folder(folder_path)
            save_tags(tag_file, mood_tags)
            logger.info("Mood tagging complete. Saved to %s", tag_file)
        except Exception as e:
            logger.error("Failed to process mood tags: %s", e)
            return None
    else:
        try:
            mood_tags = load_tags(tag_file)
            logger.info("Loaded existing mood tags from %s", tag_file)
        except Exception as e:
            logger.error("Failed to load mood tags: %s", e)
            return None
    return mood_tags

def main():
    """Main function to initialize and run the music player."""
    root = tk.Tk()
    root.title("Smart Music Player - Setup")
    root.geometry("400x300")
    root.configure(bg="#f0f0f0")
    root.resizable(False, False)

    def select_folder():
        """Handle folder selection and launch player."""
        folder_path = filedialog.askdirectory(title="Select your music folder")
        if not folder_path:
            messagebox.showinfo("Exit", "No folder selected.")
            return

        # Validate folder
        if not validate_folder(folder_path):
            messagebox.showerror("Error", "Selected folder contains no audio files (MP3/WAV).")
            return

        # Create default cover image if needed
        create_default_cover()

        # Update UI to show processing
        status_label.config(text="Processing mood tags, please wait...")
        select_btn.config(state="disabled")
        reprocess_var.set(0)  # Reset reprocess checkbox
        root.update()

        # Process mood tags
        mood_tags = process_mood_tags(folder_path, reprocess_var.get())
        if mood_tags is None:
            messagebox.showerror("Error", "Failed to load or process mood tags. Check log for details.")
            select_btn.config(state="normal")
            status_label.config(text="")
            return

        # Launch player
        logger.info("Launching player with folder: %s, mood_tags: %s", folder_path, list(mood_tags.keys()))
        root.destroy()  # Close setup window
        launch_player(folder_path, mood_tags)

    def on_closing():
        """Handle window close event."""
        logger.info("Application closed by user.")
        root.destroy()

    # UI Elements
    main_frame = tk.Frame(root, bg="#f0f0f0")
    main_frame.pack(padx=20, pady=20, fill="both", expand=True)

    tk.Label(
        main_frame,
        text="Welcome to Smart Music Player",
        font=("Helvetica", 16, "bold"),
        bg="#f0f0f0",
        fg="#333333"
    ).pack(pady=10)

    tk.Label(
        main_frame,
        text="Select a folder containing your music files (MP3/WAV):",
        font=("Helvetica", 12),
        bg="#f0f0f0",
        fg="#333333",
        wraplength=350
    ).pack(pady=10)

    select_btn = tk.Button(
        main_frame,
        text="Select Music Folder",
        command=select_folder,
        font=("Helvetica", 12),
        bg="#4CAF50",
        fg="white",
        relief="flat",
        activebackground="#45a049"
    )
    select_btn.pack(pady=10)

    reprocess_var = tk.BooleanVar()
    tk.Checkbutton(
        main_frame,
        text="Force reprocess mood tags",
        variable=reprocess_var,
        font=("Helvetica", 10),
        bg="#f0f0f0",
        activebackground="#f0f0f0"
    ).pack(pady=5)

    status_label = tk.Label(
        main_frame,
        text="",
        font=("Helvetica", 10),
        bg="#f0f0f0",
        fg="#333333"
    )
    status_label.pack(pady=10)

    # Bind window close event
    root.protocol("WM_DELETE_WINDOW", on_closing)

    root.mainloop()

if __name__ == "__main__":
    main()