import os
import glob
import json

def clear_data_folder():
    if not os.path.exists("data"):
        os.makedirs("data")
    else:
        files = glob.glob("data/*.json")
        for f in files:
            os.remove(f)

def save_comments(video_id, comments):
    file_path = f"data/comments_{video_id}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(comments, f, ensure_ascii=False, indent=4)
