#!/usr/bin/env python3
import sys
import random
import argparse
import os
import json
from PIL import Image

def rgb_to_ansi_fg(r, g, b, a):
    if a == 0:
        return "\033[39m", " "
    return f"\033[38;2;{r};{g};{b}m", "▀"

def rgb_to_ansi_bg(r, g, b, a):
    if a == 0:
        return "\033[49m"
    return f"\033[48;2;{r};{g};{b}m"

def reset_ansi():
    return "\033[0m"

def crop_transparent_borders(image):
    image = image.convert("RGBA")
    width, height = image.size
    pix = image.load()
    
    top, bottom = 0, height - 1
    left, right = 0, width - 1

    for y in range(height):
        if any(pix[x, y][3] != 0 for x in range(width)):
            top = y
            break

    for y in range(height - 1, -1, -1):
        if any(pix[x, y][3] != 0 for x in range(width)):
            bottom = y
            break

    for x in range(width):
        if any(pix[x, y][3] != 0 for y in range(top, bottom + 1)):
            left = x
            break

    for x in range(width - 1, -1, -1):
        if any(pix[x, y][3] != 0 for y in range(top, bottom + 1)):
            right = x
            break

    return image.crop((left, top, right + 1, bottom + 1))

def image_to_ansi(image):
    """
    Convert the image to ANSI art while minimizing repeated escape codes.
    If the foreground or background is identical to the previous pixel in the line,
    the code won't be re-emitted.
    """
    image = image.convert("RGBA")
    image = crop_transparent_borders(image)
    width, height = image.size
    ansi_str = ""

    # Process two rows at a time (using one character per two rows)
    for y in range(0, height, 2):
        line = ""
        last_fg = ""
        last_bg = ""
        for x in range(width):
            top_pixel = image.getpixel((x, y))
            bottom_pixel = image.getpixel((x, y+1)) if y+1 < height else (0, 0, 0, 0)
            fg, char = rgb_to_ansi_fg(*top_pixel)
            bg = rgb_to_ansi_bg(*bottom_pixel)
            pixel_str = ""
            if bg != last_bg:
                pixel_str += bg
                last_bg = bg
            if fg != last_fg:
                pixel_str += fg
                last_fg = fg
            pixel_str += char
            line += pixel_str
        line += reset_ansi()
        ansi_str += line + "\n"
    return ansi_str

def classify_image(ansi_art, small_threshold, medium_threshold, large_threshold):
    # Count the number of output lines
    lines = ansi_art.strip('\n').split("\n")
    num_lines = len(lines)
    if num_lines < small_threshold:
        category = "small"
    elif num_lines < medium_threshold:
        category = "medium"
    elif num_lines < large_threshold:
        category = "large"
    else:
        category = "extra-large"
    return category, num_lines

def load_cache(cache_file):
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading cache: {e}")
            return {}
    return {}

def save_cache(cache, cache_file):
    try:
        with open(cache_file, "w") as f:
            json.dump(cache, f)
    except Exception as e:
        print(f"Error saving cache: {e}")

def process_image(file_path, small_threshold, medium_threshold, large_threshold):
    # Open and process the image, then classify its ANSI output.
    try:
        img = Image.open(file_path)
    except Exception as e:
        print(f"Error opening image {file_path}: {e}")
        return None

    # For animated GIFs, choose a random frame.
    if getattr(img, "is_animated", False):
        random_frame = random.randint(0, img.n_frames - 1)
        img.seek(random_frame)

    ansi_art = image_to_ansi(img)
    category, num_lines = classify_image(ansi_art, small_threshold, medium_threshold, large_threshold)
    return {"ansi_art": ansi_art, "category": category, "num_lines": num_lines}

def get_cache_info(cache_file, cache):
    """ Prints statistics about the cache file """
    try:
        file_size = os.path.getsize(cache_file) / 1024  # KB
    except FileNotFoundError:
        file_size = 0

    total_entries = len(cache)
    category_counts = {}
    for data in cache.values():
        category = data["category"]
        category_counts[category] = category_counts.get(category, 0) + 1

    print("\n=== Cache Info ===")
    print(f"Cache file: {cache_file}")
    print(f"File size: {file_size:.2f} KB")
    print(f"Total cached entries: {total_entries}")
    print("Entries per category:")
    for category, count in category_counts.items():
        print(f"  - {category}: {count}")
    print("==================\n")

def main():
    
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Use the script directory to build the default paths
    default_rsc_dir = os.path.join(script_dir, "rsc")
    default_cache = os.path.join(script_dir, "cache.json")

    parser = argparse.ArgumentParser(description="Convert images to ANSI art with caching and categorization")
    
    parser.add_argument("--rsc-dir", default=default_rsc_dir, help=f"Directory containing image files (default: {default_rsc_dir})")
    parser.add_argument("--cache", default=default_cache, help=f"Path to JSON cache file (default: {default_cache})")
    
    parser.add_argument("file", nargs="?", help="Image file to process. If omitted, all .gif files in rsc/ directory are processed.")
    parser.add_argument("--refresh", action="store_true", help="Force reprocessing images even if cached")
    parser.add_argument("--random", action="store_true", help="Display a random cached image")
    parser.add_argument("--cache-info", action="store_true", help="Display cache statistics")
    parser.add_argument("--small-threshold", type=int, default=20, help="Threshold for small images (default: 20)")
    parser.add_argument("--medium-threshold", type=int, default=40, help="Threshold for medium images (default: 40)")
    parser.add_argument("--large-threshold", type=int, default=60, help="Threshold for large images (default: 60)")
    parser.add_argument("--small", action="store_true", help="Enable processing of small images")
    parser.add_argument("--medium", action="store_true", help="Enable processing of medium images")
    parser.add_argument("--large", action="store_true", help="Enable processing of large images")
    parser.add_argument("--extra-large", action="store_true", help="Enable processing of extra-large images")
    parser.add_argument("--silent", action="store_true", help="Disables log output when running the --random flag")

    args = parser.parse_args()
    cache = load_cache(args.cache)

    if args.cache_info:
        get_cache_info(args.cache, cache)
        sys.exit(0)

    # Determine selected categories.
    selected_categories = set()
    if args.small:
        selected_categories.add("small")
    if args.medium:
        selected_categories.add("medium")
    if args.large:
        selected_categories.add("large")
    if args.extra_large:
        selected_categories.add("extra-large")
    filter_categories = len(selected_categories) > 0

    # Handle random image selection.
    if args.random:
        valid_entries = [key for key, data in cache.items() if not filter_categories or data["category"] in selected_categories]
        if not valid_entries:
            print("No images in cache match the selected categories.")
            sys.exit(1)

        random_key = random.choice(valid_entries)
        data = cache[random_key]
        if not args.silent:
            print(f"Random Image: {random_key}")
            print(f"Category: {data['category']} ({data['num_lines']} lines)")
        print(data["ansi_art"])
        sys.exit(0)

    # Determine which files to process.
    files_to_process = []
    if args.file:
        files_to_process = [args.file]
    else:
        if not os.path.isdir(args.rsc_dir):
            print(f"Directory {args.rsc_dir} does not exist.")
            sys.exit(1)
        for entry in os.listdir(args.rsc_dir):
            if entry.lower().endswith(".gif"):
                files_to_process.append(os.path.join(args.rsc_dir, entry))

    # Process each image file.
    for file_path in files_to_process:
        key = os.path.abspath(file_path)
        if not args.refresh and key in cache:
            data = cache[key]
        else:
            data = process_image(file_path, args.small_threshold, args.medium_threshold, args.large_threshold)
            if data is None:
                continue
            cache[key] = data
        
        if filter_categories and data["category"] not in selected_categories:
            continue

        print(f"File: {file_path}")
        print(f"Category: {data['category']} ({data['num_lines']} lines)")
        print(data["ansi_art"])

    save_cache(cache, args.cache)

if __name__ == "__main__":
    main()
