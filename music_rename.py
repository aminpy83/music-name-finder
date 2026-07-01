import os
import re
import hashlib
from pprint import pprint
from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4

directory = r'A:\New folder\Music\samples'
names = os.listdir(directory)

duplicates_directory = os.path.join(directory, "duplicates")
conflicts_directory = os.path.join(directory, "conflicts")

os.makedirs(duplicates_directory, exist_ok=True)
os.makedirs(conflicts_directory, exist_ok=True)

os.environ["FPCALC"] = r"A:\fpcalc.exe"
import acoustid
api_key = '4o8cPCTwS5'
errors = {}


def get_hash(path):
    sha = hashlib.sha256()

    with open(path, "rb") as f:
        while chunk := f.read(8192):
            sha.update(chunk)

    return sha.hexdigest()


def new_filename(full_name, name):
    """
    making title via full_name.
    error handling if directory or not mp3 passed.
    checking if music name is already correct (full_name == new_name).  
    """
    global online

    if not os.path.isfile(full_name): 
        return None
    
    
    ext = os.path.splitext(full_name)[1].lower()
    supported_formats = ['.mp3', '.m4a', '.flac'] 
    if ext not in supported_formats:
        return None
    
    try:
        if ext == ".mp3":
            music = EasyID3(full_name)
            title = music["title"][0]

        elif ext == ".flac":
            music = FLAC(full_name)
            title = music["title"][0]

        elif ext == ".m4a":
            music = MP4(full_name)
            title = music["©nam"][0]


        title = re.sub(r'[<>:"/\\|?*]', '_', title)
        title = title.strip()
        new_name = os.path.join(
                                os.path.dirname(full_name),
                                title + ext)
    
        if os.path.normcase(full_name) == os.path.normcase(new_name):
            return None
        return new_name

    except Exception as e:
        errors[name] = f' {type(e).__name__}: {e}'
        print('\n', e, '\n')
        online = True
        return None


def name_collision(full_name, new_name):
    """ handling duplications and conflicts"""

    # duplication
    if os.path.getsize(full_name) == os.path.getsize(new_name):

        old_hash = get_hash(full_name)
        new_hash = get_hash(new_name)

        if old_hash == new_hash:
            duplicate_path = os.path.join(duplicates_directory, os.path.basename(full_name))

            print(f"Duplicate -> {duplicate_path}")
            os.rename(full_name, duplicate_path)
            return
        
    # conflicts: same songs same names (remix or sth)
    conflict_path = os.path.join(conflicts_directory, os.path.basename(full_name) )
    print(f"Conflict -> {conflict_path}")

    os.rename(full_name, conflict_path)
    return True


def rename_music(name, full_name, directory):
    try:
        new_name = new_filename(full_name, name)
        if not new_name:
            return
        
        #title still exists
        if os.path.exists(new_name):
            name_collision(full_name, new_name, )
            return

        os.rename(full_name, new_name)
    
    except Exception as e:
        errors[name] = f' {type(e).__name__}: {e}'


def online_title(full_name):
    result = acoustid.match(
                            api_key,
                            full_name) 
    
    for score, recording_id, title, artist in result:
        # print(score)
        # print(title)
        # print(artist)
        if title and score >= 0.9:
            online_name = os.path.join(directory, (title + ext))
            os.rename(full_name, online_name)
            break

        
for name in names:
    # print(name)
    full_name = os.path.join(directory, name)
    ext = os.path.splitext(name)[1].lower()

    online = False
    rename_music(name, full_name, directory)

    if online:
        # print(name)
        online_title(os.path.join(directory, name))
        # print(40*'---')
print(errors)
