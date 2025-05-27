import os
import tkinter as tk
from tkinter import messagebox, ttk
import random
from PIL import Image, ImageTk, ImageFilter
from pygame import mixer
import threading
import time
import mutagen
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4

# Assuming extract_album_art is provided
try:
    from utils.album_art import extract_album_art
except ImportError:
    def extract_album_art(song_path, default_path):
        try:
            return Image.open(default_path)
        except:
            return Image.new('RGB', (300, 300), color='#2d2d2d')

mixer.init()

def get_song_duration(file_path):
    """Get the duration of an audio file in seconds"""
    try:
        audio_file = mutagen.File(file_path)
        if audio_file is not None:
            return int(audio_file.info.length)
        return 180  # Default 3 minutes if can't determine
    except:
        return 180

def launch_player(folder_path, mood_tags):
    window = tk.Tk()
    window.title("Smart Music Player")
    window.geometry("900x800")
    window.configure(bg="#0a0a0a")
    window.resizable(True, True)
    
    # Apply blur effect to window (Windows only)
    try:
        window.wm_attributes("-alpha", 0.97)
    except:
        pass

    # Store current image and song list
    current_image = None
    current_index = [0]
    original_songs = list(mood_tags.keys())
    filtered_songs = original_songs.copy()
    is_playing = [False]
    is_paused = [False]
    song_length = [0]
    current_position = [0]
    repeat_mode = [0]  # 0: no repeat, 1: repeat all, 2: repeat one
    is_shuffled = [False]
    update_thread = [None]

    # Enhanced color scheme with blur theme
    colors = {
        'bg': '#121212',  # deeper black
        'card_bg': '#1e1e1e',
        'CATEGARY': 'white', # semi-transparent dark gray
        'primary': '#1ed760',          # Spotify green
        'primary_hover': '#1fdf64',
        'secondary': '#3e3e3e',
        'text': '#ffffff',
        'text_secondary': '#aaaaaa',
        'accent': '#ff6b35',
        'accent_secondary': '#ff8c42',
        'glass_opacity': 0.15
    }


    def create_glass_frame(parent, **kwargs):
        """Create a glass morphism frame"""
        frame = tk.Frame(parent, bg=colors['card_bg'], relief="flat", bd=0, **kwargs)
        # Add subtle border effect
        frame.configure(highlightbackground=colors['secondary'], highlightthickness=1)
        return frame

    def create_rounded_button(parent, text, command, width=10, height=2, bg_color=None, 
                            text_color='white', font_size=10, is_circular=False):
        """Create a modern rounded button with hover effects"""
        bg = bg_color or colors['primary']
        
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            font=("Segoe UI", font_size, "bold"),
            width=width if not is_circular else 3,
            height=height,
            bg=bg,
            fg=text_color,
            relief="flat",
            bd=0,
            cursor="hand2",
            activebackground=colors['primary_hover'] if bg == colors['primary'] else bg,
            activeforeground=text_color,
            padx=10,
            pady=5
        )
        
        # Add hover effects
        def on_enter(event):
            if bg == colors['primary']:
                btn.configure(bg=colors['primary_hover'])
            else:
                btn.configure(bg=colors['secondary'])
        
        def on_leave(event):
            btn.configure(bg=bg)
        
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        
        return btn

    def create_circular_button(parent, text, command, size=50, bg_color=None, text_color='white'):
        """Create a circular button"""
        bg = bg_color or colors['primary']
        
        canvas = tk.Canvas(parent, width=size, height=size, bg=colors['card_bg'], 
                          highlightthickness=0, bd=0)
        
        # Draw circle
        circle = canvas.create_oval(2, 2, size-2, size-2, fill=bg, outline=colors['secondary'], width=1)
        text_item = canvas.create_text(size//2, size//2, text=text, fill=text_color, 
                                     font=("Segoe UI", 12, "bold"))
        
        def on_click(event):
            command()
        
        def on_enter(event):
            canvas.itemconfig(circle, fill=colors['primary_hover'] if bg == colors['primary'] else colors['secondary'])
        
        def on_leave(event):
            canvas.itemconfig(circle, fill=bg)
        
        canvas.bind("<Button-1>", on_click)
        canvas.bind("<Enter>", on_enter)
        canvas.bind("<Leave>", on_leave)
        canvas.configure(cursor="hand2")
        
        return canvas

    def show_album_art(song_path):
        nonlocal current_image
        try:
            if song_path is None:
                # Create default album art with blur effect
                img = Image.new('RGB', (320, 320), color='#2d2d2d')
                # Add gradient effect
                for y in range(320):
                    for x in range(320):
                        distance = ((x - 160) ** 2 + (y - 160) ** 2) ** 0.5
                        brightness = max(0, 1 - distance / 160)
                        color = int(45 + brightness * 20)
                        img.putpixel((x, y), (color, color, color))
                
                current_image = ImageTk.PhotoImage(img)
                album_art_label.configure(image=current_image, bg=colors['card_bg'])
                album_art_label.image = current_image
                return

            img = extract_album_art(song_path, os.path.join("assets", "default_cover.jpg"))
            if img is None:
                try:
                    img = Image.open(os.path.join("assets", "default_cover.jpg"))
                except:
                    img = Image.new('RGB', (320, 320), color='#2d2d2d')

            # Resize and apply subtle blur effect
            img = img.resize((320, 320), Image.Resampling.LANCZOS)
            
            # Create a blurred background version
            blurred = img.filter(ImageFilter.GaussianBlur(radius=20))
            
            # Blend original with blurred for glass effect
            img = Image.blend(blurred, img, 0.8)
            
            current_image = ImageTk.PhotoImage(img)
            album_art_label.configure(image=current_image, bg=colors['card_bg'])
            album_art_label.image = current_image
        except Exception as e:
            print(f"Error loading album art for {song_path}: {e}")
            img = Image.new('RGB', (320, 320), color='#2d2d2d')
            current_image = ImageTk.PhotoImage(img)
            album_art_label.configure(image=current_image, bg=colors['card_bg'])
            album_art_label.image = current_image

    def update_progress_bar():
        """Update progress bar continuously while playing"""
        while is_playing[0] and not is_paused[0]:
            try:
                current_position[0] += 1
                if song_length[0] > 0:
                    progress = min((current_position[0] / song_length[0]) * 100, 100)
                    progress_var.set(progress)
                    
                    # Update time labels
                    current_time = min(current_position[0], song_length[0])
                    time_current_label.config(text=format_time(current_time))
                    
                    # Check if song ended
                    if current_position[0] >= song_length[0]:
                        window.after(100, handle_song_end)
                        break
                        
                time.sleep(1)
            except:
                break

    def handle_song_end():
        """Handle what happens when a song ends"""
        if repeat_mode[0] == 2:  # Repeat one
            load_song(current_index[0])
        elif repeat_mode[0] == 1:  # Repeat all
            next_song()
        else:
            # Just move to next song
            next_song()

    def format_time(seconds):
        """Format seconds to MM:SS"""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"

    def load_song(index):
        nonlocal update_thread
        if not filtered_songs:
            messagebox.showwarning("No Songs", "No songs available to play.")
            song_title_label.config(text="No song loaded")
            artist_label.config(text="")
            show_album_art(None)
            return

        if index >= len(filtered_songs):
            current_index[0] = 0
            index = 0

        try:
            song = filtered_songs[index]
            full_path = os.path.join(folder_path, song)
            
            # Stop current update thread
            is_playing[0] = False
            if update_thread[0] and update_thread[0].is_alive():
                update_thread[0].join(timeout=1)
            
            # Get dynamic song duration
            song_length[0] = get_song_duration(full_path)
            
            mixer.music.load(full_path)
            mixer.music.play()
            
            is_playing[0] = True
            is_paused[0] = False
            current_position[0] = 0
            
            # Update UI
            song_name = os.path.splitext(song)[0]
            # Truncate long song names
            if len(song_name) > 40:
                song_name = song_name[:37] + "..."
            
            song_title_label.config(text=song_name)
            artist_label.config(text=f"Mood: {mood_tags[song]}")
            time_total_label.config(text=format_time(song_length[0]))
            
            show_album_art(full_path)
            current_index[0] = index
            play_pause_btn_canvas.itemconfig(play_pause_text, text="⏸️")
            
            # Reset progress bar
            progress_var.set(0)
            time_current_label.config(text="00:00")
            
            # Start progress update thread
            update_thread[0] = threading.Thread(target=update_progress_bar, daemon=True)
            update_thread[0].start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load song: {e}")
            song_title_label.config(text="Error loading song")
            artist_label.config(text="")
            show_album_art(None)

    def next_song():
        if not filtered_songs:
            messagebox.showwarning("No Songs", "No songs available.")
            return
        
        if repeat_mode[0] == 2:  # Repeat one
            load_song(current_index[0])
        else:
            current_index[0] = (current_index[0] + 1) % len(filtered_songs)
            load_song(current_index[0])

    def prev_song():
        if not filtered_songs:
            messagebox.showwarning("No Songs", "No songs available.")
            return
        current_index[0] = (current_index[0] - 1) % len(filtered_songs)
        load_song(current_index[0])

    def toggle_shuffle():
        nonlocal filtered_songs
        if is_shuffled[0]:
            # Un-shuffle: restore original order
            mood = mood_var.get().lower()
            if mood == "all":
                filtered_songs = original_songs.copy()
            else:
                filtered_songs = [s for s in original_songs if mood_tags[s].lower() == mood]
            is_shuffled[0] = False
            shuffle_btn.itemconfig(shuffle_circle, fill=colors['secondary'])
        else:
            # Shuffle
            current_song = filtered_songs[current_index[0]] if filtered_songs else None
            random.shuffle(filtered_songs)
            if current_song and current_song in filtered_songs:
                # Keep current song at current position
                filtered_songs.remove(current_song)
                filtered_songs.insert(current_index[0], current_song)
            is_shuffled[0] = True
            shuffle_btn.itemconfig(shuffle_circle, fill=colors['primary'])

    def toggle_repeat():
        repeat_mode[0] = (repeat_mode[0] + 1) % 3
        repeat_texts = ["🔁", "🔂", "🔁"]
        repeat_colors = [colors['secondary'], colors['primary'], colors['accent']]
        repeat_btn.itemconfig(repeat_circle, fill=repeat_colors[repeat_mode[0]])
        repeat_btn.itemconfig(repeat_text, text=repeat_texts[repeat_mode[0]])

    def toggle_play_pause():
        if mixer.music.get_busy() and not is_paused[0]:
            mixer.music.pause()
            is_paused[0] = True
            play_pause_btn_canvas.itemconfig(play_pause_text, text="▶️")
        else:
            mixer.music.unpause()
            is_paused[0] = False
            play_pause_btn_canvas.itemconfig(play_pause_text, text="⏸️")
            # Restart progress thread if needed
            if is_playing[0] and (not update_thread[0] or not update_thread[0].is_alive()):
                update_thread[0] = threading.Thread(target=update_progress_bar, daemon=True)
                update_thread[0].start()

    def stop_song():
        is_playing[0] = False
        is_paused[0] = False
        mixer.music.stop()
        song_title_label.config(text="Stopped")
        artist_label.config(text="")
        play_pause_btn_canvas.itemconfig(play_pause_text, text="▶️")
        progress_var.set(0)
        time_current_label.config(text="00:00")
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
        
        # Reset shuffle state when changing mood
        is_shuffled[0] = False
        shuffle_btn.itemconfig(shuffle_circle, fill=colors['secondary'])
        
        current_index[0] = 0
        if filtered_songs:
            load_song(current_index[0])

    def set_volume(val):
        volume = float(val) / 100
        mixer.music.set_volume(volume)
        volume_label.config(text=f"{int(float(val))}%")

    def on_progress_click(event):
        """Handle progress bar clicks for seeking"""
        try:
            # Calculate position based on click
            click_pos = event.x / progress_bar.winfo_width()
            new_position = click_pos * song_length[0]
            current_position[0] = new_position
            progress_var.set(click_pos * 100)
            time_current_label.config(text=format_time(new_position))
            # Note: Actual seeking would require different audio library
        except:
            pass

    # Main container with padding and blur effect
    # Scrollable Canvas Wrapper
    canvas = tk.Canvas(window, bg=colors['bg'], highlightthickness=0)
    scrollbar = tk.Scrollbar(window, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)

    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    # Create a frame inside the canvas
    scrollable_frame = tk.Frame(canvas, bg=colors['bg'])
    scrollable_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

    # Configure scroll region on resize
    def update_scroll_region(event):
        canvas.configure(scrollregion=canvas.bbox("all"))

    scrollable_frame.bind("<Configure>", update_scroll_region)
    canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(-1*(e.delta//120), "units"))

    # Use scrollable_frame instead of window/main_container
    main_container = create_glass_frame(scrollable_frame)
    main_container.pack(fill="both", expand=True, padx=25, pady=25)

    # Header section
    header_section = create_glass_frame(main_container)
    header_section.pack(fill="x", pady=(0, 20))
    
    header_label = tk.Label(
        header_section,
        text="🎵 Smart Music Player",
        font=("Segoe UI", 24, "bold"),
        bg=colors['card_bg'],
        fg=colors['text'],
        pady=20
    )
    header_label.pack()

    # Album art and song info section
    top_section = tk.Frame(main_container, bg=colors['bg'])
    top_section.pack(fill="x", pady=(0, 25))

    # Album art card with enhanced styling
    art_frame = create_glass_frame(top_section)
    art_frame.pack(side="left", padx=(0, 25))

    album_art_label = tk.Label(art_frame, bg=colors['card_bg'])
    album_art_label.pack(padx=20, pady=20)

    # Song info card with better layout
    info_frame = create_glass_frame(top_section)
    info_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

    song_title_label = tk.Label(
        info_frame,
        text="No song loaded",
        font=("Segoe UI", 20, "bold"),
        bg=colors['card_bg'],
        fg=colors['text'],
        anchor="w",
        wraplength=400
    )
    song_title_label.pack(fill="x", padx=25, pady=(25, 8))

    artist_label = tk.Label(
        info_frame,
        text="",
        font=("Segoe UI", 14),
        bg=colors['card_bg'],
        fg=colors['text_secondary'],
        anchor="w"
    )
    artist_label.pack(fill="x", padx=25, pady=(0, 25))

    # Mood selector in info card
    mood_frame = tk.Frame(info_frame, bg=colors['card_bg'])
    mood_frame.pack(fill="x", padx=25, pady=15)

    tk.Label(mood_frame, text="SELECT", bg=colors['card_bg'], fg=colors['text'], 
             font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 8))

    moods = ["All"] + sorted(set(mood.lower() for mood in mood_tags.values()))
    mood_var = tk.StringVar(window)
    mood_var.set("All")
    mood_var.trace("w", filter_by_mood)

    style = ttk.Style()
    style.theme_use('clam')
    style.configure('Custom.TCombobox', 
                   fieldbackground=colors['bg'],
                   background=colors['card_bg'],
                   foreground=colors['text'],
                   selectbackground=colors['card_bg'])

    mood_dropdown = ttk.Combobox(
        mood_frame,
        textvariable=mood_var,
        values=moods,
        state="readonly",
        font=("Segoe UI", 11),
        width=30,
        style='Custom.TCombobox'
    )
    mood_dropdown.pack(anchor="w", pady=5)

    # Progress section with enhanced styling
    progress_section = create_glass_frame(main_container)
    progress_section.pack(fill="x", pady=(0, 20), padx=5)

    # Time labels and progress bar
    time_frame = tk.Frame(progress_section, bg=colors['card_bg'])
    time_frame.pack(fill="x", padx=25, pady=20)

    time_current_label = tk.Label(time_frame, text="00:00", bg=colors['card_bg'], 
                                 fg=colors['text'], font=("Segoe UI", 11, "bold"))
    time_current_label.pack(side="left")

    time_total_label = tk.Label(time_frame, text="00:00", bg=colors['card_bg'], 
                               fg=colors['text'], font=("Segoe UI", 11, "bold"))
    time_total_label.pack(side="right")

    # Enhanced progress bar
    progress_var = tk.DoubleVar()
    progress_bar = tk.Scale(
        time_frame,
        from_=0,
        to=100,
        orient="horizontal",
        variable=progress_var,
        length=400,
        bg=colors['card_bg'],
        fg=colors['primary'],
        highlightthickness=0,
        bd=0,
        troughcolor=colors['bg'],
        activebackground=colors['primary_hover'],
        sliderrelief="flat"
    )
    progress_bar.pack(fill="x", padx=25)
    progress_bar.bind("<Button-1>", on_progress_click)

    # Control buttons section with circular buttons
    controls_section = create_glass_frame(main_container)
    controls_section.pack(fill="x", pady=(0, 20), padx=5)

    controls_frame = tk.Frame(controls_section, bg=colors['card_bg'])
    controls_frame.pack(pady=25)

    # Main playback controls with circular buttons
    main_controls = tk.Frame(controls_frame, bg=colors['card_bg'])
    main_controls.pack(pady=15)

    # Shuffle button (circular)
    shuffle_btn = tk.Canvas(main_controls, width=50, height=50, bg=colors['card_bg'], 
                           highlightthickness=0, bd=0)
    shuffle_circle = shuffle_btn.create_oval(2, 2, 48, 48, fill=colors['secondary'], 
                                           outline=colors['text_secondary'], width=1)
    shuffle_text = shuffle_btn.create_text(25, 25, text="🔀", fill=colors['text'], 
                                         font=("Segoe UI", 14, "bold"))
    shuffle_btn.grid(row=0, column=0, padx=12)
    shuffle_btn.bind("<Button-1>", lambda e: toggle_shuffle())
    shuffle_btn.configure(cursor="hand2")

    # Previous button
    prev_btn = create_circular_button(main_controls, "⏮️", prev_song, 50, colors['secondary'])
    prev_btn.grid(row=0, column=1, padx=12)

    # Play/Pause button (larger)
    play_pause_btn_canvas = tk.Canvas(main_controls, width=70, height=70, bg=colors['card_bg'], 
                                     highlightthickness=0, bd=0)
    play_pause_circle = play_pause_btn_canvas.create_oval(2, 2, 68, 68, fill=colors['primary'], 
                                                         outline=colors['primary_hover'], width=2)
    play_pause_text = play_pause_btn_canvas.create_text(35, 35, text="▶️", fill=colors['text'], 
                                                       font=("Segoe UI", 16, "bold"))
    play_pause_btn_canvas.grid(row=0, column=2, padx=15)
    play_pause_btn_canvas.bind("<Button-1>", lambda e: toggle_play_pause())
    play_pause_btn_canvas.configure(cursor="hand2")

    # Next button
    next_btn = create_circular_button(main_controls, "⏭️", next_song, 50, colors['secondary'])
    next_btn.grid(row=0, column=3, padx=12)

    # Repeat button (circular)
    repeat_btn = tk.Canvas(main_controls, width=50, height=50, bg=colors['card_bg'], 
                          highlightthickness=0, bd=0)
    repeat_circle = repeat_btn.create_oval(2, 2, 48, 48, fill=colors['secondary'], 
                                         outline=colors['text_secondary'], width=1)
    repeat_text = repeat_btn.create_text(25, 25, text="🔁", fill=colors['text'], 
                                       font=("Segoe UI", 14, "bold"))
    repeat_btn.grid(row=0, column=4, padx=12)
    repeat_btn.bind("<Button-1>", lambda e: toggle_repeat())
    repeat_btn.configure(cursor="hand2")

    # Secondary controls
# Unified bottom controls (stop + volume in one line)
    bottom_controls = create_glass_frame(main_container)
    bottom_controls.pack(fill="x", padx=5, pady=(10, 30))

    bottom_frame = tk.Frame(bottom_controls, bg=colors['card_bg'])
    bottom_frame.pack(pady=15)

    # STOP button
    stop_btn = create_rounded_button(bottom_frame, "⏹️ STOP", stop_song, width=10, height=2,
                                    bg_color=colors['accent'], font_size=11)
    stop_btn.pack(side="left", padx=10)

    # Volume label
    volume_title = tk.Label(bottom_frame, text="🔊 Volume:", font=("Segoe UI", 12, "bold"),
                            bg=colors['card_bg'], fg=colors['text'])
    volume_title.pack(side="left", padx=10)

    # Volume scale
    volume_scale = tk.Scale(
        bottom_frame,
        from_=0,
        to=100,
        orient="horizontal",
        length=200,
        command=set_volume,
        bg=colors['card_bg'],
        fg=colors['primary'],
        highlightthickness=0,
        bd=0,
        troughcolor=colors['bg'],
        activebackground=colors['primary_hover'],
        sliderrelief="flat"
    )
    volume_scale.set(50)
    volume_scale.pack(side="left", padx=10)

    # Volume percentage
    volume_label = tk.Label(bottom_frame, text="50%", bg=colors['card_bg'],
                            fg=colors['text'], font=("Segoe UI", 12, "bold"))
    volume_label.pack(side="left", padx=10)

    # Initialize with first song
    show_album_art(None)
    if filtered_songs:
        window.after(100, lambda: load_song(current_index[0]))

    # Handle window closing
    def on_closing():
        is_playing[0] = False
        mixer.quit()
        window.destroy()

    window.protocol("WM_DELETE_WINDOW", on_closing)
    window.mainloop()