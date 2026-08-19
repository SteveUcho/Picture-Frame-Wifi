import os
import random
from PIL import Image

from .constants import exts
from .models import OrientationType

def get_decimal_from_dms(dms, ref):
    degrees = dms[0]
    minutes = dms[1] / 60.0
    seconds = dms[2] / 3600.0
    if ref in ['S', 'W']:
        return -(degrees + minutes + seconds)
    return degrees + minutes + seconds


def parse_sleep_time(sleep_time: str):
    hours, minutes, seconds = sleep_time.split(":")
    return [int(hours), int(minutes), int(seconds)]


def traverse_directory(path):
    results = []
    for root, test, files in os.walk(path):
        for file_name in files:
            if file_name.lower().endswith(exts):
                full_file_path = os.path.join(root, file_name)
                results.append(full_file_path)
    return results


def find_files_with_exts(photo_dir: str):
    """Recursively finds all JPG, JPEG, PNG, and HEIC files using the glob module."""
    image_candidates = traverse_directory(photo_dir)

    if not len(image_candidates):
        raise FileNotFoundError(
            "No .jpeg, .jpg, .png, or .heic files found in the directory."
        )

    return image_candidates


# returns absolute image path
def get_random_image_orientation(orientation: OrientationType, photo_dir: str):
    image_candidates = find_files_with_exts(photo_dir)
    if not len(image_candidates):
        return None
    correct_orientation = False
    while not correct_orientation:
        chosen_image = random.choice(image_candidates)
        with Image.open(chosen_image) as image:
            correct_orientation = check_orientation(image, orientation)
            if correct_orientation:
                return chosen_image
    return None


def check_orientation(image, orientation: OrientationType):
    width, height = image.size
    if orientation == "horizontal":
        return width > height
    elif orientation == "vertical":
        return height > width
