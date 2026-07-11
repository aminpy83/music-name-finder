import os
import re
import time
import hashlib
from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
from mutagen.mp3 import MP3
from mutagen.id3 import ID3
from pprint import pprint


directory = r'ABS PATH'
names = os.listdir(directory)

duplicates_directory = os.path.join(directory, "duplicates")
conflicts_directory = os.path.join(directory, "conflicts")

os.makedirs(duplicates_directory, exist_ok=True)
os.makedirs(conflicts_directory, exist_ok=True)

os.environ["FPCALC"] = r"A:\fpcalc.exe"
import acoustid
api_key = 'API KEY'

errors = {}
supported_formats = ['.mp3', '.m4a', '.flac'] 


def get_hash(path):
    sha = hashlib.sha256()

    with open(path, "rb") as f:
        while chunk := f.read(8192):
            sha.update(chunk)

    return sha.hexdigest()


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


def new_filename(full_name, name):
    """
    making title via full_name.
    error handling if directory or not mp3 passed.
    checking if music name is already correct (full_name == new_name).  
    """

    if not os.path.isfile(full_name): 
        return 'directory'
    
    
    ext = os.path.splitext(full_name)[1].lower()
    if ext not in supported_formats:
        return 'not supported'
    
    try:
        if ext == ".mp3":
            music = EasyID3(full_name)
            title = music["title"][0]

            audio = MP3(full_name, ID3=ID3)
            apic = audio.tags.getall("APIC")
            # if not apic:
            #     print(name)


        elif ext == ".flac":
            music = FLAC(full_name)
            title = music["title"][0]

            # if not music.pictures:
            #     print(name)

        elif ext == ".m4a":
            music = MP4(full_name)
            title = music["©nam"][0]

            # if not "covr" in music:
            #     print(name)


        title = re.sub(r'[<>:"/\\|?*]', '_', title)
        title = title.strip()
        new_name = os.path.join(
                                os.path.dirname(full_name),
                                title + ext)
    

        if os.path.normcase(full_name) == os.path.normcase(new_name):
            return 'already correct'
        return new_name

    except Exception as e:
        errors[name] = f' {type(e).__name__}: {e}'
        print('\n', e, '\n')
        return None


def rename_music(name, full_name):
    try:
        new_name = new_filename(full_name, name)
        if new_name in ['not supported', 'directory', 'already correct']:
            return 'nothing to do'
        
        if not new_name:
            return 'online'
        
        #title still  -> collision
        if os.path.exists(new_name):
            name_collision(full_name, new_name )
            return 'collision'

        os.rename(full_name, new_name)
        return 'renamed'
    except Exception as e:
        errors[name] = f' {type(e).__name__}: {e}'


def online_title(full_name):

    # print(full_name)
    # print(os.path.exists(full_name))


    result = acoustid.match(
                            api_key,
                            full_name) 
    
    for score, recording_id, title, artist in result:

        if title and score >= 0.9:
            title = re.sub(r'[<>:"/\\|?*]', '_', title)
            title = title.strip()
            ext = os.path.splitext(full_name)[1].lower()
            online_name = os.path.join(directory, (title + ext))
            
            # checking online-offline collision
            if os.path.exists(online_name):
                name_collision(full_name, online_name)
                return

            os.rename(full_name, online_name)
            break


def cover_finder(name):
    ...


rate_limit = 0
for name in names:
    full_name = os.path.join(directory, name)

    if 'online' == rename_music(name, full_name):

        if rate_limit >= 3:
            time.sleep(0.5)
            rate_limit = 0

        online_title(os.path.join(directory, name))
        rate_limit += 1

print(errors)
