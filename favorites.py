import os
import re

STORAGE_DIR = os.path.join(os.getcwd(), 'favorites.txt')
REGEX_HEX_PATTERN = r"(#[A-f0-9]{6})\n"

def store_favorite(hex):
    data =  f"#{hex}\n"

    if not re.match(REGEX_HEX_PATTERN, data):
        return

    with open(STORAGE_DIR, "a") as f:
        f.write(data)

def read_favorites():
    favs = []
    with open(STORAGE_DIR, "r") as f:
        for l in f:
            if re.match(REGEX_HEX_PATTERN, l):
                favs.append(l)

    return favs
