#!/usr/bin/env python3
import argparse
import os
import sys
import shutil # For backup

# --- Try importing orjson ---
try:
    import orjson as json_lib
    JSON_LIB_NAME = 'orjson'
except ImportError:
    import json as json_lib # Fallback to standard json
    JSON_LIB_NAME = 'json'
    # print("orjson not found, using standard json library.", file=sys.stderr)


# --- Cache Loading/Saving Functions (adapted from rw_fetch.py) ---

def load_cache(cache_file):
    """Loads the cache file, handling potential errors."""
    if not os.path.exists(cache_file):
        # Allow purging from a non-existent file (results in empty cache)
        print(f"Warning: Cache file '{cache_file}' not found. Starting with empty cache.", file=sys.stderr)
        return {}
    if os.path.getsize(cache_file) == 0:
        print(f"Warning: Cache file '{cache_file}' is empty.", file=sys.stderr)
        return {}

    mode = "rb" if JSON_LIB_NAME == 'orjson' else "r"
    try:
        with open(cache_file, mode) as f:
            content = f.read()
            if not content:
                return {}
            return json_lib.loads(content)
    except (json_lib.JSONDecodeError, IOError, ValueError) as e:
        print(f"Error: Failed to load or decode cache file '{cache_file}': {e}", file=sys.stderr)
        return None # Signal error
    except Exception as e:
        print(f"Error: An unexpected error occurred while loading cache: {e}", file=sys.stderr)
        return None # Signal error

def save_cache(cache, cache_file):
    """Saves the cache file, handling potential errors."""
    try:
        cache_dir = os.path.dirname(cache_file)
        if cache_dir and not os.path.exists(cache_dir):
            os.makedirs(cache_dir, exist_ok=True)

        mode = "wb" if JSON_LIB_NAME == 'orjson' else "w"
        with open(cache_file, mode) as f:
            if JSON_LIB_NAME == 'orjson':
                # Use OPT_INDENT_2 for pretty printing with orjson
                options = json_lib.OPT_INDENT_2 | json_lib.OPT_SORT_KEYS
                f.write(json_lib.dumps(cache, option=options))
            else:
                # Standard json uses indent argument
                json_lib.dump(cache, f, indent=2, sort_keys=True)
        return True # Signal success
    except IOError as e:
        print(f"Error: Could not save cache file '{cache_file}': {e}", file=sys.stderr)
        return False # Signal error
    except Exception as e:
        print(f"Error: An unexpected error occurred while saving cache: {e}", file=sys.stderr)
        return False # Signal error

def main():
    parser = argparse.ArgumentParser(
        description="Purge all entries of a specific category from the cache file.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "category",
        help="The category to purge (e.g., small, medium, large, extra-large)."
    )
    parser.add_argument(
        "--cache",
        default="cache.json",
        help="Path to the JSON cache file."
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Do not create a backup of the original cache file."
    )

    args = parser.parse_args()

    cache_file = args.cache
    category_to_purge = args.category.lower() # Make comparison case-insensitive

    # --- Load Cache ---
    print(f"Loading cache from '{cache_file}'...")
    cache = load_cache(cache_file)

    if cache is None:
        # Loading failed, error already printed by load_cache
        sys.exit(1)

    original_count = len(cache)
    if original_count == 0:
        print("Cache is empty. Nothing to purge.")
        sys.exit(0)

    # --- Filter Cache ---
    print(f"Filtering out entries with category '{category_to_purge}'...")
    new_cache = {}
    purged_count = 0

    for key, data in cache.items():
        # Check if data is a dict and has the 'category' key before accessing
        if isinstance(data, dict):
            entry_category = data.get("category", "").lower() # Safely get category, default to "", lowercase
            if entry_category == category_to_purge:
                purged_count += 1
                # print(f"  - Removing: {key}") # Uncomment for verbose output
            else:
                new_cache[key] = data # Keep this entry
        else:
            # Keep invalid/unexpected entries? Or discard? Let's keep them for now.
            print(f"Warning: Skipping invalid cache entry for key '{key}' (not a dictionary).", file=sys.stderr)
            new_cache[key] = data


    if purged_count == 0:
        print(f"\nNo entries found matching category '{category_to_purge}'. Cache remains unchanged.")
        sys.exit(0)

    # --- Backup Cache (Optional) ---
    backup_file = f"{cache_file}.bak"
    if not args.no_backup:
        try:
            print(f"Creating backup: '{backup_file}'...")
            shutil.copy2(cache_file, backup_file) # copy2 preserves metadata
        except FileNotFoundError:
             print(f"Warning: Original cache file '{cache_file}' not found for backup (might have been empty initially).")
        except Exception as e:
            print(f"Error: Failed to create backup file '{backup_file}': {e}", file=sys.stderr)
            print("Aborting save to prevent data loss.")
            sys.exit(1)

    # --- Save New Cache ---
    remaining_count = len(new_cache)
    print(f"Saving updated cache with {remaining_count} entries back to '{cache_file}'...")

    if save_cache(new_cache, cache_file):
        print("\n--- Purge Summary ---")
        print(f"Original entries: {original_count}")
        print(f"Entries purged ({category_to_purge}): {purged_count}")
        print(f"Remaining entries: {remaining_count}")
        if not args.no_backup and os.path.exists(backup_file):
             print(f"Backup created at: {backup_file}")
        print("---------------------")
        sys.exit(0)
    else:
        # Saving failed, error already printed
        print("\nError occurred during saving. The original cache might be lost if backup failed.")
        if not args.no_backup and os.path.exists(backup_file):
             print(f"A backup *might* exist at '{backup_file}'.")
        sys.exit(1)


if __name__ == "__main__":
    main()