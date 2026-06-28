import os, re, mutagen
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from pprint import pprint
import hashlib

directory = r'A:\New folder\Music\samples'
names = os.listdir(directory)
errors = {}

duplicates_directory = os.path.join(directory, "duplicates")
conflicts_directory = os.path.join(directory, "conflicts")

os.makedirs(duplicates_directory, exist_ok=True)
os.makedirs(conflicts_directory, exist_ok=True)

def get_hash(path):
    sha = hashlib.sha256()

    with open(path, "rb") as f:
        while chunk := f.read(8192):
            sha.update(chunk)

    return sha.hexdigest()


for name in names:
    try:
        full_name =os.path.join(directory, name)
        
        # skipping if dir or not mp3
        if not os.path.isfile(full_name) or not name.lower().endswith('.mp3'):
            continue
        music = EasyID3(full_name)


        title = music["title"][0]
        title = re.sub(r'[<>:"/\\|?*]', '_', title)
        title = title.strip()
        new_name = os.path.join(directory, f"{title}.mp3")
        
        # skipping when name is already correct (full_name == new_name)
        if os.path.normcase(full_name) == os.path.normcase(new_name):
            continue

        # pprint(full_name)
        # print(new_name)

        if os.path.exists(new_name):
            if os.path.getsize(full_name) == os.path.getsize(new_name):

                old_hash = get_hash(full_name)
                new_hash = get_hash(new_name)

                if old_hash == new_hash:
                    duplicate_path = os.path.join(duplicates_directory, os.path.basename(full_name) )

                    print(f"Duplicate -> {duplicate_path}")

                    os.rename(full_name, duplicate_path)
                    continue

            # different songs same names (remix or sth)
            conflict_path = os.path.join(conflicts_directory, os.path.basename(full_name) )

            print(f"Conflict -> {conflict_path}")

            os.rename(full_name, conflict_path)
            continue

        os.rename(full_name, new_name)

        pprint(name)
        # print(len(names))
    except Exception as e:
        errors[name] = type(e).__name__

pprint(errors, depth=3) 
