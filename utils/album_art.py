# Extract image from MP3
# ...to be implemented...
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC
from PIL import Image
import io

def extract_album_art(mp3_path, default_img_path):
    try:
        audio = MP3(mp3_path, ID3=ID3)
        for tag in audio.tags.values():
            if isinstance(tag, APIC):
                image = Image.open(io.BytesIO(tag.data))
                return image
    except Exception:
        pass
    return Image.open(default_img_path)
