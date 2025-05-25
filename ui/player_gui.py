import os
import tkinter as tk
from tkinter import messagebox
import random
from PIL import ImageTk
from pygame import mixer
from utils.album_art import extract_album_art

mixer.init()

def launch_player(folder_path, mood_tags):
    window = tk.Tk()
    window.title("Mood Music Player")
    window.geometry("500x450")
    
    current_index = [0]
    filtered_songs = list(mood_tags.keys())

    def load_song(index):
        song = filtered_songs[index]
        full_path = os.path.join(folder_path, song)
        mixer.music.load(full_path)
        mixer.music.play()
        label.config(text=f"Now Playing: {song}")
        show_album_art(full_path)

    def next_song():
        current_index[0] = (current_index[0] + 1) % len(filtered_songs)
        load_song(current_index[0])

    def prev_song():
        current_index[0] = (current_index[0] - 1) % len(filtered_songs)
        load_song(current_index[0])

    def shuffle_song():
        current_index[0] = random.randint(0, len(filtered_songs)-1)
        load_song(current_index[0])

    def filter_by_mood():
        mood = mood_entry.get().strip().lower()
        if mood == "":
            messagebox.showerror("Empty", "Type a mood to search!")
            return
        new_list = [s for s in mood_tags if mood_tags[s] == mood]
        if not new_list:
            messagebox.showinfo("No Songs", f"No songs found for mood: {mood}")
            return
        nonlocal filtered_songs
        filtered_songs = new_list
        current_index[0] = 0
        load_song(current_index[0])

    def show_album_art(song_path):
        img = extract_album_art(song_path, os.path.join("assets", "default_cover.jpg"))
        img = img.resize((200, 200))
        img_tk = ImageTk.PhotoImage(img)
        album_art_label.config(image=img_tk)
        album_art_label.image = img_tk

    # UI Elements
    label = tk.Label(window, text="No song loaded", font=("Helvetica", 14))
    label.pack(pady=10)

    album_art_label = tk.Label(window)
    album_art_label.pack(pady=10)

    mood_entry = tk.Entry(window, font=("Helvetica", 12))
    mood_entry.pack()

    mood_btn = tk.Button(window, text="Search Mood", command=filter_by_mood)
    mood_btn.pack(pady=5)

    controls = tk.Frame(window)
    tk.Button(controls, text="⏮", command=prev_song, width=8).grid(row=0, column=0)
    tk.Button(controls, text="▶️", command=lambda: load_song(current_index[0]), width=8).grid(row=0, column=1)
    tk.Button(controls, text="⏭", command=next_song, width=8).grid(row=0, column=2)
    tk.Button(controls, text="🔀", command=shuffle_song, width=8).grid(row=0, column=3)
    controls.pack(pady=15)

    window.mainloop()
