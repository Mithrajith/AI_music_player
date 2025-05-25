import os
import tkinter as tk
from tkinter import messagebox, ttk
import random
from PIL import Image, ImageTk
from pygame import mixer

# Assuming extract_album_art is provided
try:
    from utils.album_art import extract_album_art
except ImportError:
    def extract_album_art(song_path, default_path):
        return Image.open(default_path)  # Mock implementation

mixer.init()

def launch_player(folder_path, mood_tags):
    window = tk.Tk()
    window.title("Mood Music Player")
    window.geometry("600x650")
    window.configure(bg="#f0f0f0")

    # Store current image and song list
    current_image = None
    current_index = [0]
    original_songs = list(mood_tags.keys())  # Preserve original song list
    filtered_songs = original_songs.copy()

    def show_album_art(song_path):
        nonlocal current_image
        try:
            if song_path is None:
                album_art_label.configure(image="")
                album_art_label.image = None
                return

            img = extract_album_art(song_path, os.path.join("assets", "default_cover.jpg"))
            if img is None:
                img = Image.open(os.path.join("assets", "default_cover.jpg"))

            img = img.resize((300, 300), Image.Resampling.LANCZOS)
            current_image = ImageTk.PhotoImage(img)
            album_art_label.configure(image=current_image)
            album_art_label.image = current_image
        except Exception as e:
            print(f"Error loading album art for {song_path}: {e}")
            album_art_label.configure(image="")
            album_art_label.image = None
            messagebox.showwarning("Album Art", f"Using default art for {os.path.basename(song_path)}.")

    def load_song(index):
        if not filtered_songs:
            messagebox.showwarning("No Songs", "No songs available to play.")
            label.config(text="No song loaded")
            show_album_art(None)
            return

        if index >= len(filtered_songs):
            current_index[0] = 0
            index = 0

        try:
            song = filtered_songs[index]
            full_path = os.path.join(folder_path, song)
            mixer.music.load(full_path)
            mixer.music.play()
            label.config(text=f"Now Playing: {os.path.splitext(song)[0]} (Mood: {mood_tags[song]})")
            show_album_art(full_path)
            current_index[0] = index
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load song: {e}")
            label.config(text="Error loading song")
            show_album_art(None)

    def next_song():
        if not filtered_songs:
            messagebox.showwarning("No Songs", "No songs available.")
            return
        current_index[0] = (current_index[0] + 1) % len(filtered_songs)
        load_song(current_index[0])

    def prev_song():
        if not filtered_songs:
            messagebox.showwarning("No Songs", "No songs available.")
            return
        current_index[0] = (current_index[0] - 1) % len(filtered_songs)
        load_song(current_index[0])

    def shuffle_song():
        if not filtered_songs:
            messagebox.showwarning("No Songs", "No songs to shuffle.")
            return
        random.shuffle(filtered_songs)
        current_index[0] = 0
        load_song(current_index[0])
        messagebox.showinfo("Shuffle", "Playlist shuffled.")

    def toggle_play_pause():
        if mixer.music.get_busy():
            mixer.music.pause()
            play_pause_btn.config(text="▶️")
        else:
            mixer.music.unpause()
            play_pause_btn.config(text="⏸")

    def stop_song():
        mixer.music.stop()
        label.config(text="Stopped")
        play_pause_btn.config(text="▶️")
        show_album_art(None)

    def filter_by_mood(*args):
        nonlocal filtered_songs
        mood = mood_var.get().lower()
        if mood == "all":
            filtered_songs = original_songs.copy()
        else:
            filtered_songs = [s for s in original_songs if mood_tags[s].lower() == mood]
            if not filtered_songs:
                messagebox.showinfo("No Songs", f"No songs found for mood: {mood}. Showing all songs.")
                filtered_songs = original_songs.copy()
        current_index[0] = 0
        load_song(current_index[0])

    def set_volume(val):
        volume = float(val) / 100
        mixer.music.set_volume(volume)
        volume_label.config(text=f"Volume: {int(float(val))}%")

    # UI Elements with enhanced styling
    main_frame = tk.Frame(window, bg="#f0f0f0")
    main_frame.pack(padx=20, pady=20, fill="both", expand=True)

    label = tk.Label(
        main_frame,
        text="No song loaded",
        font=("Helvetica", 14, "bold"),
        bg="#f0f0f0",
        fg="#333333",
        wraplength=500
    )
    label.pack(pady=10)

    album_art_label = tk.Label(main_frame, bg="#f0f0f0")
    album_art_label.pack(pady=10)

    # Mood selection dropdown
    mood_frame = tk.Frame(main_frame, bg="#f0f0f0")
    mood_frame.pack(fill="x", pady=10)

    moods = ["All"] + sorted(set(mood.lower() for mood in mood_tags.values()))
    mood_var = tk.StringVar(window)
    mood_var.set("All")
    mood_var.trace("w", filter_by_mood)

    mood_dropdown = ttk.Combobox(
        mood_frame,
        textvariable=mood_var,
        values=moods,
        state="readonly",
        font=("Helvetica", 12),
        width=20
    )
    mood_dropdown.pack(side="left", padx=5)

    # Control buttons frame
    controls = tk.Frame(main_frame, bg="#f0f0f0")
    controls.pack(pady=15)

    button_style = {
        "font": ("Helvetica", 12),
        "width": 8,
        "bg": "#2196F3",
        "fg": "white",
        "relief": "flat",
        "activebackground": "#1976D2"
    }

    tk.Button(controls, text="⏮", command=prev_song, **button_style).grid(row=0, column=0, padx=5)
    play_pause_btn = tk.Button(controls, text="▶️", command=toggle_play_pause, **button_style)
    play_pause_btn.grid(row=0, column=1, padx=5)
    tk.Button(controls, text="⏭", command=next_song, **button_style).grid(row=0, column=2, padx=5)
    tk.Button(controls, text="🔀", command=shuffle_song, **button_style).grid(row=0, column=3, padx=5)
    tk.Button(controls, text="⏹", command=stop_song, **button_style).grid(row=0, column=4, padx=5)

    # Volume control
    volume_frame = tk.Frame(main_frame, bg="#f0f0f0")
    volume_frame.pack(pady=10)
    volume_label = tk.Label(volume_frame, text="Volume: 50%", bg="#f0f0f0", font=("Helvetica", 10))
    volume_label.pack(side="left")
    volume_scale = tk.Scale(
        volume_frame,
        from_=0,
        to=100,
        orient="horizontal",
        length=200,
        command=set_volume,
        bg="#f0f0f0",
        highlightthickness=0
    )
    volume_scale.set(50)
    volume_scale.pack(side="left", padx=10)

    # Autoload first song
    if filtered_songs:
        window.after(0, lambda: load_song(current_index[0]))

    window.mainloop()
    mixer.quit()
