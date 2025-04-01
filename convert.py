#!/usr/bin/env python3
import sys
import random
import argparse
import os
import json
import subprocess # Still needed for fallback commands
import shutil
import math
import re
import platform
import getpass
import socket
import time
import datetime
from pathlib import Path
from PIL import Image
from itertools import zip_longest

# --- Try importing psutil (Recommended Dependency) ---
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None # Assign None if not available
    PSUTIL_AVAILABLE = False
    # Optionally print a warning only once
    # print("Warning: 'psutil' library not found. Some system info (CPU%, Memory, Uptime) will be limited or unavailable.", file=sys.stderr)
    # print("Install it via: pip install psutil", file=sys.stderr)

# Import configuration variables
try:
    import config
except ImportError:
    print("Error: config.py not found. Please ensure it exists in the same directory.")
    sys.exit(1)

# --- ANSI Color Functions ---
# (Keep these functions as they were)
def rgb_to_ansi_fg(r, g, b, a):
    if a < 128: return config.RESET_COLOR, " "
    return f"\033[38;2;{r};{g};{b}m", "▀"

def rgb_to_ansi_bg(r, g, b, a):
    if a < 128: return "\033[49m"
    return f"\033[48;2;{r};{g};{b}m"

def reset_ansi(): return config.RESET_COLOR

# --- Image Processing Functions ---
# (Keep crop_transparent_borders and image_to_ansi as they were)
def crop_transparent_borders(image):
    image = image.convert("RGBA")
    try: bbox = image.getbbox()
    except Exception: bbox = None
    if bbox: return image.crop(bbox)
    else: return Image.new('RGBA', (1, 1), (0, 0, 0, 0))

def image_to_ansi(image):
    image = image.convert("RGBA")
    image = crop_transparent_borders(image)
    width, height = image.size
    ansi_lines = []
    if height % 2 != 0:
        img_copy = Image.new('RGBA', (width, height + 1), (0, 0, 0, 0))
        img_copy.paste(image, (0, 0))
        image = img_copy
        height += 1
    for y in range(0, height, 2):
        line = ""
        last_fg_ansi, last_bg_ansi = None, None
        for x in range(width):
            r_fg, g_fg, b_fg, a_fg = image.getpixel((x, y))
            r_bg, g_bg, b_bg, a_bg = image.getpixel((x, y + 1))
            fg_ansi, char = rgb_to_ansi_fg(r_fg, g_fg, b_fg, a_fg)
            bg_ansi = rgb_to_ansi_bg(r_bg, g_bg, b_bg, a_bg)
            current_line = ""
            if bg_ansi != last_bg_ansi: current_line += bg_ansi; last_bg_ansi = bg_ansi
            if char != " " and fg_ansi != last_fg_ansi: current_line += fg_ansi; last_fg_ansi = fg_ansi
            elif char == " " and last_fg_ansi != "\033[39m": current_line += "\033[39m"; last_fg_ansi = "\033[39m"
            current_line += char
            line += current_line
        line += reset_ansi()
        ansi_lines.append(line)
    if not ansi_lines and (width > 0 or height > 0): return config.RESET_COLOR
    elif not ansi_lines: return ""
    return "\n".join(ansi_lines)

# --- Classification and Caching ---
# (Keep classify_image, load_cache, save_cache, process_image as they were,
#  but consider adding orjson for load/save if desired)
# --- Add orjson attempt ---
try:
    import orjson as json_lib
    # print("Using orjson for faster JSON handling.", file=sys.stderr)
except ImportError:
    import json as json_lib # Fallback to standard json
    # print("orjson not found, using standard json library.", file=sys.stderr)

def load_cache(cache_file):
    if os.path.exists(cache_file):
        mode = "rb" if json_lib.__name__ == 'orjson' else "r"
        try:
            with open(cache_file, mode) as f:
                content = f.read()
                if not content: return {}
                return json_lib.loads(content)
        except (json_lib.JSONDecodeError, IOError, ValueError) as e:
            print(f"Warning: Error loading cache file {cache_file}: {e}", file=sys.stderr)
            return {}
    return {}

def save_cache(cache, cache_file):
    try:
        cache_dir = os.path.dirname(cache_file)
        if cache_dir and not os.path.exists(cache_dir): os.makedirs(cache_dir, exist_ok=True)
        mode = "wb" if json_lib.__name__ == 'orjson' else "w"
        with open(cache_file, mode) as f:
            if json_lib.__name__ == 'orjson':
                # Use OPT_INDENT_2 for pretty printing with orjson
                f.write(json_lib.dumps(cache, option=json_lib.OPT_INDENT_2))
            else:
                # Standard json uses indent argument
                json_lib.dump(cache, f, indent=2)
    except IOError as e: print(f"Error: Could not save cache file {cache_file}: {e}", file=sys.stderr)
    except Exception as e: print(f"An unexpected error occurred while saving cache: {e}", file=sys.stderr)

def classify_image(ansi_art):
    lines = ansi_art.strip('\n').split("\n")
    num_lines = len(lines)
    if num_lines < config.SMALL_THRESHOLD: category = "small"
    elif num_lines < config.MEDIUM_THRESHOLD: category = "medium"
    elif num_lines < config.LARGE_THRESHOLD: category = "large"
    else: category = "extra-large"
    return category, num_lines

def process_image(file_path):
    try: img = Image.open(file_path)
    except FileNotFoundError: print(f"Error: Image file not found: {file_path}", file=sys.stderr); return None
    except Exception as e: print(f"Error opening image {file_path}: {e}", file=sys.stderr); return None
    try:
        if getattr(img, "is_animated", False) and img.n_frames > 1:
            random_frame = random.randint(0, img.n_frames - 1)
            img.seek(random_frame); img.load()
        ansi_art = image_to_ansi(img)
        if not ansi_art or ansi_art.isspace(): category, num_lines = "empty", 0
        else: category, num_lines = classify_image(ansi_art)
        return {"ansi_art": ansi_art, "category": category, "num_lines": num_lines}
    except Exception as e:
        frame_info = ""
        try: frame_info = f" (frame {img.tell()})" if getattr(img, "is_animated", False) else ""
        except Exception: pass
        print(f"Error processing image {file_path}{frame_info}: {e}", file=sys.stderr); return None
    finally: img.close()

# --- System Information Fetching (Python API Methods) ---

def format_error(msg): return f"{config.SYS_INFO_ERROR_COLOR}{msg}{config.RESET_COLOR}"
def format_warn(msg): return f"{config.SYS_INFO_WARN_COLOR}{msg}{config.RESET_COLOR}"

# --- Still needed for specific fallback commands ---
def fetch_shell_command(command):
    """Executes a single shell command using subprocess."""
    if not command: return format_error("No command provided")
    try:
        result = subprocess.run(
            command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, check=True, timeout=10
        )
        return result.stdout.strip()
    except FileNotFoundError: return format_error(f"Cmd not found: {command.split()[0]}")
    except subprocess.CalledProcessError as e:
        err = e.stderr.strip() or f"Exit {e.returncode}"; return format_error(f"Cmd Err: {err[:50]}")
    except subprocess.TimeoutExpired: return format_error("Timeout")
    except Exception as e: return format_error(f"Subprocess Error: {e}")

# --- Python API Fetchers ---
def get_user_host():
    try: user = getpass.getuser()
    except Exception: user = "N/A"
    try: host = socket.gethostname()
    except Exception: host = "N/A"
    return f"{user}@{host}"

def get_os():
    if sys.platform == "darwin":
        try:
            name = platform.mac_ver()[0] or "macOS"
            ver = platform.mac_ver()[1] or ""
            return f"{name} {ver}".strip()
        except Exception: pass # Fallthrough
    elif sys.platform.startswith("linux"):
        try: # Try reading /etc/os-release first (common and detailed)
            with open("/etc/os-release") as f:
                data = dict(line.strip().split('=', 1) for line in f if '=' in line)
                return data.get('PRETTY_NAME', 'Linux').strip('"')
        except FileNotFoundError: pass # Fallthrough
        except Exception as e: print(f"Error reading /etc/os-release: {e}", file=sys.stderr) # Log error but continue
        try: # Fallback using platform module
            dist = platform.freedesktop_os_release()
            if dist.get('PRETTY_NAME'): return dist['PRETTY_NAME']
            # platform.linux_distribution() is deprecated, use release files if possible
        except Exception: pass # Fallthrough
    # Generic platform info as last resort
    try: return platform.system() + " " + platform.release()
    except Exception: return format_error("OS Unknown")

def get_kernel():
    try: return platform.release()
    except Exception: return format_error("Kernel Unknown")

def get_uptime():
    if PSUTIL_AVAILABLE:
        try:
            boot_time_timestamp = psutil.boot_time()
            elapsed_seconds = time.time() - boot_time_timestamp
            # Format timedelta nicely
            td = datetime.timedelta(seconds=elapsed_seconds)
            days, remainder = divmod(td.seconds, 86400)
            hours, remainder = divmod(remainder, 3600)
            minutes, seconds = divmod(remainder, 60)
            parts = []
            if td.days > 0: parts.append(f"{td.days} days")
            if hours > 0: parts.append(f"{hours} hours")
            if minutes > 0: parts.append(f"{minutes} minutes")
            if not parts and seconds > 0: parts.append(f"{seconds} seconds") # Show seconds if uptime is very short
            return ", ".join(parts) if parts else "Just booted"
        except Exception as e: return format_error(f"psutil Uptime Error: {e}")
    else: # Fallback using uptime command (less precise formatting)
        return fetch_shell_command("uptime -p | sed 's/^up //'") # Keep simple fallback

def get_shell():
    try:
        shell_path = os.environ.get('SHELL', '')
        if shell_path: return Path(shell_path).name
        else: return "N/A"
    except Exception: return "N/A"

def get_terminal():
    term_program = os.environ.get('TERM_PROGRAM', '')
    if term_program:
        return term_program.removesuffix('.app') # For macOS .app suffix
    else:
        return os.environ.get('TERM', 'N/A')

def get_cpu():
    cpu_name = "N/A"
    # Try getting detailed name first
    if sys.platform.startswith("linux"):
        try: # Read /proc/cpuinfo directly
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if line.strip().startswith("model name"):
                        cpu_name = line.split(':', 1)[1].strip()
                        break
        except Exception: pass # Fallthrough
    elif sys.platform == "darwin":
        # Use the shell command fallback for macOS brand string as it's reliable
        cpu_name = fetch_shell_command("sysctl -n machdep.cpu.brand_string")

    # Use psutil for counts and frequency (more reliable cross-platform)
    cores_logical = "N/A"
    freq_current = "N/A"
    if PSUTIL_AVAILABLE:
        try: cores_logical = psutil.cpu_count(logical=True)
        except Exception: pass
        try:
            freq = psutil.cpu_freq()
            if freq and freq.current > 0: # Check if freq info is available
                freq_current = f"{freq.current:.0f}MHz" # Format without decimals
        except NotImplementedError: freq_current = format_warn("Freq N/A") # Some OS/VMs don't support
        except Exception: pass

    # Combine Name, Cores, Freq
    display_parts = [cpu_name]
    if cores_logical != "N/A": display_parts.append(f"({cores_logical} Cores)")
    if freq_current != "N/A": display_parts.append(f"@ {freq_current}")

    return " ".join(p for p in display_parts if p != "N/A")

def get_memory():
    if PSUTIL_AVAILABLE:
        try:
            mem = psutil.virtual_memory()
            # Format bytes nicely using powers of 1024
            def format_bytes(b):
                if b < 1024: return f"{b} B"
                elif b < 1024**2: return f"{b/1024:.1f} KiB"
                elif b < 1024**3: return f"{b/1024**2:.1f} MiB"
                else: return f"{b/1024**3:.1f} GiB"

            used = format_bytes(mem.used)
            total = format_bytes(mem.total)
            percent = mem.percent
            return f"{used} / {total} ({percent:.0f}%)" # Show percentage too
        except Exception as e: return format_error(f"psutil Memory Error: {e}")
    else: # Basic fallback (less informative)
        return format_warn("N/A (psutil req.)")

def get_color_palette():
    lines = []
    line1 = " " + "".join(f"\033[4{i}m  " for i in range(8)) + "\033[0m"
    line2 = " " + "".join(f"\033[10{i}m  " for i in range(8)) + "\033[0m"
    return f"{line1}\n{line2}" # Return as single string with newline

# --- System Info Orchestrator ---
# Map labels from config to Python functions or fallback keys
INFO_FETCHER_MAP = {
    "User@Host": get_user_host,
    "OS": get_os,
    "Kernel": get_kernel,
    "Uptime": get_uptime,
    "Shell": get_shell,
    "Terminal": get_terminal,
    "CPU": get_cpu,
    "Memory": get_memory,
    "Color Palette": get_color_palette,
    # --- Labels using fallback commands ---
    "Packages": "Packages",
    "Resolution": "Resolution",
    "WM": "WM",
    "Theme": "Theme",
    "Icons": "Icons",
    "Terminal Font": "Terminal Font",
    "GPU": "GPU",
}

# Fetch and format using Python APIs where possible
def get_formatted_system_info():
    """Fetches and formats system information using Python APIs and fallbacks."""
    info_lines = []
    max_label_len = 0
    labels_in_order = []

    # Pre-calculate max label length
    for item in config.SYSTEM_INFO_ORDER:
        if isinstance(item, dict) and "label" in item:
            label = item["label"]
            if label != "Color Palette": # Don't pad for color palette
                labels_in_order.append(label)
                max_label_len = max(max_label_len, len(label))

    # Fetch data and format lines
    for item in config.SYSTEM_INFO_ORDER:
        if not isinstance(item, dict): continue

        if "separator" in item:
            separator_text = item["separator"]
            line_width = max_label_len + len(config.SYS_INFO_KV_SEPARATOR) + 15
            if isinstance(separator_text, str) and separator_text:
                padding = max(0, (line_width - len(separator_text)) // 2)
                info_lines.append(f"{' ' * padding}{config.SYS_INFO_LABEL_COLOR}{separator_text}{config.RESET_COLOR}")
            else:
                info_lines.append(f"{config.SYS_INFO_LABEL_COLOR}{config.SYS_INFO_SEPARATOR_CHAR * line_width}{config.RESET_COLOR}")
            continue

        if "label" in item:
            label = item["label"]
            value = format_error("Fetcher N/A") # Default error
            fetcher = INFO_FETCHER_MAP.get(label)

            if callable(fetcher): # Is it a Python function?
                try: value = fetcher()
                except Exception as e: value = format_error(f"Func Error: {e}")
            elif isinstance(fetcher, str): # Is it a key for fallback command?
                command = config.FALLBACK_COMMANDS.get(fetcher)
                if command: value = fetch_shell_command(command)
                else: value = format_error(f"No cmd for {fetcher}")
            else: # No fetcher found
                 value = format_error(f"No fetcher for {label}")


            # Handle multi-line values (like color palette)
            value_lines = str(value).split('\n') # Ensure value is string
            value = value_lines[0]
            extra_lines = value_lines[1:]

            if label == "Color Palette":
                info_lines.append(value) # Palette line 1
                indent = max_label_len + len(config.SYS_INFO_KV_SEPARATOR) + 1
                for extra in extra_lines: info_lines.append((" " * indent) + extra) # Palette line 2
            else:
                padded_label = label.ljust(max_label_len)
                info_lines.append(
                    f"{config.SYS_INFO_LABEL_COLOR}{padded_label}{config.RESET_COLOR}"
                    f"{config.SYS_INFO_KV_SEPARATOR} "
                    f"{config.SYS_INFO_VALUE_COLOR}{value}{config.RESET_COLOR}"
                )
                indent = max_label_len + len(config.SYS_INFO_KV_SEPARATOR) + 1
                for extra in extra_lines: info_lines.append((" " * indent) + extra)

    # Add psutil warning at the end if needed
    if not PSUTIL_AVAILABLE:
        info_lines.append("") # Add a blank line
        info_lines.append(format_warn("Install 'psutil' (`pip install psutil`) for more detailed system info (CPU%, Uptime, Memory)."))

    return info_lines


# --- Display Functions ---
# (Keep display_art_and_info as it was, ensuring it uses config.IMAGE_INFO_SEPARATOR)
def display_art_and_info(ansi_art, sys_info_lines):
    art_lines = ansi_art.strip('\n').split('\n')
    max_art_width = 0
    if art_lines:
        plain_lines = [re.sub(r'\x1b\[[0-9;]*[mK]', '', line) for line in art_lines]
        max_art_width = max(len(line) for line in plain_lines if line) if any(plain_lines) else 0

    for art_line, info_line in zip_longest(art_lines, sys_info_lines, fillvalue=""):
        plain_art_line = re.sub(r'\x1b\[[0-9;]*[mK]', '', art_line)
        padding_needed = max(0, max_art_width - len(plain_art_line))
        padded_art_line = art_line + (" " * padding_needed)

        if info_line:
            print(f"{padded_art_line}{config.IMAGE_INFO_SEPARATOR}{info_line}")
        else:
            print(padded_art_line) # Print only padded art line if no corresponding info line


# (Keep get_cache_info as it was)
def get_cache_info(cache_file, cache):
    print("\n=== Cache Info ===")
    print(f"Cache file: {os.path.abspath(cache_file)}")
    try: file_size = os.path.getsize(cache_file) / 1024; print(f"File size: {file_size:.2f} KB")
    except FileNotFoundError: print("File size: N/A (Cache file not found or empty)"); file_size = 0
    except Exception as e: print(f"File size: Error calculating ({e})")
    total_entries = len(cache)
    category_counts = {}
    if total_entries > 0:
        for key, data in cache.items():
            if isinstance(data, dict) and "category" in data:
                 category = data.get("category", "unknown")
                 category_counts[category] = category_counts.get(category, 0) + 1
            else: category_counts["invalid"] = category_counts.get("invalid", 0) + 1
    print(f"Total cached entries: {total_entries}")
    if category_counts:
        print("Entries per category:"); [print(f"  - {cat}: {cnt}") for cat, cnt in sorted(category_counts.items())]
    else: print("No valid entries found to categorize.")
    print("==================\n")

# --- Main Execution ---
# (Keep main function largely the same - it orchestrates calls to other functions)
def main():
    parser = argparse.ArgumentParser(
        description="Convert images to ANSI art with caching, categorization, and optional system info (Python API backend).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    # (Arguments remain the same as before)
    parser.add_argument("--rsc-dir", default=config.DEFAULT_RSC_DIR, help="Directory containing image files.")
    parser.add_argument("--cache", default=config.DEFAULT_CACHE_FILE, help="Path to JSON cache file.")
    parser.add_argument("file", nargs="?", help="Specific image file to process. If omitted, processes compatible files in --rsc-dir.")
    parser.add_argument("--refresh", action="store_true", help="Force reprocessing images even if cached.")
    parser.add_argument("--random", action="store_true", help="Display a random cached image, honoring category filters.")
    parser.add_argument("--fetch-system", "--sysinfo", action="store_true", help="Display system information alongside the image.")
    parser.add_argument("--cache-info", action="store_true", help="Display cache statistics and exit.")
    parser.add_argument("--silent", action="store_true", help="Suppress log output (like file/category info) when displaying.")
    parser.add_argument("--small", dest="filter_small", action="store_true", help="Filter for small images.")
    parser.add_argument("--medium", dest="filter_medium", action="store_true", help="Filter for medium images.")
    parser.add_argument("--large", dest="filter_large", action="store_true", help="Filter for large images.")
    parser.add_argument("--extra-large", dest="filter_xl", action="store_true", help="Filter for extra-large images.")

    args = parser.parse_args()
    cache = load_cache(args.cache)

    if args.cache_info: get_cache_info(args.cache, cache); sys.exit(0)

    selected_categories = set()
    if args.filter_small: selected_categories.add("small")
    if args.filter_medium: selected_categories.add("medium")
    if args.filter_large: selected_categories.add("large")
    if args.filter_xl: selected_categories.add("extra-large")
    filter_categories = len(selected_categories) > 0

    # Handle --random first (no need to scan dir if random)
    if args.random:
        if not cache: print("Cache is empty.", file=sys.stderr); sys.exit(1)
        valid_keys = [ k for k, d in cache.items() if isinstance(d, dict) and "category" in d and \
                       (not filter_categories or d["category"] in selected_categories) ]
        if not valid_keys: print("No cached images match criteria.", file=sys.stderr); sys.exit(1)
        random_key = random.choice(valid_keys)
        data = cache[random_key]
        if not isinstance(data, dict) or "ansi_art" not in data:
             print(f"Error: Invalid data in cache for {random_key}", file=sys.stderr); sys.exit(1)
        if not args.silent: print(f"Random: {random_key}\nCategory: {data.get('category', 'N/A')} ({data.get('num_lines', '?')} lines)")
        if args.fetch_system: sys_info = get_formatted_system_info(); display_art_and_info(data["ansi_art"], sys_info)
        else: print(data["ansi_art"])
        sys.exit(0)

    # Process specific file or directory
    files_to_process = []
    if args.file:
        if os.path.isfile(args.file): files_to_process.append(args.file)
        else: print(f"Error: File not found: {args.file}", file=sys.stderr); sys.exit(1)
    else: # Scan directory
        if not os.path.isdir(args.rsc_dir): print(f"Error: Dir not found: {args.rsc_dir}", file=sys.stderr); sys.exit(1)
        try:
            supported = ('.gif', '.png', '.jpg', '.jpeg', '.bmp', '.webp')
            for entry in os.listdir(args.rsc_dir):
                if entry.lower().endswith(supported):
                     full_path = os.path.join(args.rsc_dir, entry)
                     if os.path.isfile(full_path): files_to_process.append(full_path)
            if not files_to_process and not args.silent: print(f"No supported images found in {args.rsc_dir}")
        except OSError as e: print(f"Error reading dir {args.rsc_dir}: {e}", file=sys.stderr); sys.exit(1)

    if not files_to_process and not args.silent: print("No images to process.")

    processed_count = 0
    cache_updated = False
    # Pre-fetch sys info once if needed (now faster due to Python APIs)
    sys_info = get_formatted_system_info() if args.fetch_system else None

    for file_path in files_to_process:
        key = os.path.abspath(file_path)
        data = None
        if not args.refresh and key in cache:
             cached_data = cache[key]
             if isinstance(cached_data, dict) and "ansi_art" in cached_data and "category" in cached_data:
                 data = cached_data
                 if not args.silent: print(f"Cached: {os.path.basename(file_path)}")
             elif not args.silent: print(f"Invalid cache for {os.path.basename(file_path)}. Reprocessing.", file=sys.stderr)

        if data is None:
            if not args.silent: print(f"Processing: {os.path.basename(file_path)}")
            processed_data = process_image(file_path)
            if processed_data:
                data = processed_data; cache[key] = data; cache_updated = True
            else:
                if not args.silent: print(f"Skipping failed process: {os.path.basename(file_path)}", file=sys.stderr)
                continue

        current_category = data.get("category")
        if filter_categories and current_category not in selected_categories:
            if not args.silent: print(f"Skipping (filter): {os.path.basename(file_path)} ({current_category})")
            continue
        if current_category == "empty" and not data.get("ansi_art"):
            if not args.silent: print(f"Skipping (empty result): {os.path.basename(file_path)}")
            continue

        processed_count += 1
        if not args.silent:
            print(f"\n--- File: {os.path.basename(file_path)} ---")
            print(f"Category: {current_category} ({data.get('num_lines', '?')} lines)")

        if args.fetch_system: display_art_and_info(data["ansi_art"], sys_info)
        else: print(data["ansi_art"])

    if processed_count == 0 and not args.silent and (files_to_process or args.file):
         print("No images were displayed (check filters/errors).")

    if cache_updated:
        if not args.silent: print("\nSaving updated cache...")
        save_cache(cache, args.cache)
    elif not args.silent and (files_to_process or args.file): print("\nCache up to date.")


if __name__ == "__main__":
    main()