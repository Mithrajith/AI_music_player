# Save/load mood_tags.json
# ...to be implemented...
import json

def save_tags(filepath, tags_dict):
    with open(filepath, 'w') as f:
        json.dump(tags_dict, f, indent=4)

def load_tags(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)
