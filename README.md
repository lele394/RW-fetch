# <div align="center"><img src="https://raw.githubusercontent.com/lele394/lele394/main/rsc/77.gif"   style="width: calc(43 / 41 * 100%);;  height: 100%;"  /> RW-fetch <img src="https://raw.githubusercontent.com/lele394/lele394/main/rsc/74.gif"   style="width: calc(43 / 41 * 100%);;  height: 100%;"  />
</div>  

Welcome to **RW-fetch** – your terminal’s nostalgic gateway to the pixel art of *Revived Witch*! This project converts GIFs and other images (with a focus on those from the gacha game *Revived Witch*, which has sadly reached its end of service) into vibrant ANSI art for your terminal. Enjoy a blast from the past, optionally displayed alongside your system information, every time you open your shell!

_Distributed under the [CC BY-NC-SA](https://creativecommons.org/licenses/by-nc-sa/4.0/) license._

## Table of Contents 📚

- [Overview 🌟](#overview-)
- [Features ✨](#features-)
- [Installation 🛠️](#installation-)
- [Get Started 🚀](#get-started-)
  - [Adding New Images/GIFs 📁](#adding-new-imagesgifs-)
  - [Generating the Cache ⚡](#generating-the-cache-)
  - [Basic Display Commands 💻](#basic-display-commands-)
- [Usage Details ⚙️](#usage-details-)
  - [Cache Management 💾](#cache-management-)
  - [Image Categorization & Thresholds 📏](#image-categorization--thresholds-)
  - [Displaying Random Images 🎲](#displaying-random-images-)
  - [System Information Display 📊](#system-information-display-)
- [Examples 🔍](#examples-)
- [Parameters Explained 🎛️](#parameters-explained-%EF%B8%8F)
- [Terminal Startup Integration ⏰](#terminal-startup-integration-)
- [Contributing 🤝](#contributing-)
- [License 📄](#license-)

## Overview 🌟

RW-fetch is a Python script designed to:

1.  **Convert Images:** Transform static images and animated GIFs (like those from *Revived Witch*) into ANSI escape sequences suitable for display in modern terminals. It uses the half-block character (`▀`) technique for higher vertical resolution and attempts to preserve transparency.
2.  **Display Art:** Render the generated ANSI art directly in your terminal.
3.  **Show System Info:** Optionally fetch and display key system statistics alongside the artwork, using Python APIs where possible for speed and portability, and falling back to shell commands for harder-to-get information.
4.  **Cache Results:** Store the generated ANSI art and image metadata in a JSON cache file (`cache.json` by default) to significantly speed up subsequent displays, especially for random selections.
5.  **Categorize & Filter:** Classify images based on the height of their ANSI art ("small", "medium", "large", "extra-large") and allow filtering based on these categories.

It aims to be a fun, visually appealing, and informative addition to your terminal environment, powered by Python, Pillow, and optionally `psutil` and `orjson` for enhanced performance and features.

## Features ✨

*   **Image to ANSI Conversion:** Renders images (PNG, GIF, JPG, WEBP, BMP) as ANSI art using 24-bit color escape codes.
*   **Animated GIF Support:** Selects a random frame from animated GIFs for conversion.
*   **Transparency & Cropping:** Handles transparent backgrounds and automatically crops transparent borders before conversion.
*   **Efficient Caching:** Stores generated ANSI art and metadata (category, line count) in a JSON file (`cache.json`) for fast subsequent access. Uses `orjson` if available for faster JSON processing.
*   **Image Categorization:** Automatically categorizes images into `small`, `medium`, `large`, or `extra-large` based on the generated ANSI art height (configurable thresholds in `config.py`).
*   **System Information:** Fetches and displays system info (OS, Kernel, Uptime, CPU, Memory, etc.).
    *   Prioritizes Python APIs (`platform`, `psutil`, `socket`, etc.) for speed and reliability.
    *   Uses `psutil` (optional dependency) for detailed CPU usage, Memory usage, and accurate Uptime.
    *   Provides configurable shell command fallbacks (in `config.py`) for information not easily accessible via Python (e.g., Packages, WM, GPU, Theme).
    *   System info layout and content are configurable via `config.py`.
*   **Filtering:** Allows displaying images based on specific categories (`--small`, `--medium`, etc.), useful with `--random` or when processing a directory.
*   **Random Display:** Selects and displays a random image from the cache (`--random`), respecting category filters if applied.
*   **Configurable:** Key settings like paths, category thresholds, system info order/commands, and colors are managed in `config.py`.
*   **Cross-Platform:** Primarily Python-based, aiming for compatibility across Linux, macOS, and potentially WSL. Note that some fallback shell commands for system info might be OS-specific.
*   **Silent Mode:** Suppresses informational messages (`--silent`) for cleaner output, ideal for terminal startup scripts.

## Installation 🛠️

1.  **Prerequisites:**
    *   Python 3.6 or later.
    *   `pip` (Python package installer).

2.  **Clone the Repository:**
    ```bash
    git clone https://github.com/your-username/rw-fetch.git # Replace with the actual repo URL
    cd rw-fetch
    ```

3.  **Install Required Python Dependencies:**
    *   **Pillow (PIL Fork):** For image processing.
    ```bash
    pip install Pillow
    ```

4.  **Install Recommended Python Dependencies (Optional but highly suggested):**
    *   **psutil:** Provides more accurate and detailed system information (CPU Usage, Memory, Uptime) reliably across platforms.
    *   **orjson:** Offers significantly faster JSON parsing and serialization, speeding up cache loading/saving.
    ```bash
    pip install psutil orjson
    ```
    If `psutil` is not installed, the script will show warnings and some system info fields (like Memory, detailed Uptime) will display "N/A" or rely on less reliable methods. If `orjson` is not found, it falls back to Python's built-in `json` module.

5.  **System Dependencies (for Fallback Commands):**
    *   Some system information items rely on external commands (defined in `config.py`). You might need to install tools like `lspci`, `xrandr`, `wmctrl`, `gsettings` (for GNOME/GTK), `kreadconfig5` (for KDE Plasma), `jq`, `system_profiler` (macOS), `dpkg-query` (Debian/Ubuntu), `rpm` (Fedora/CentOS), `snap`, `flatpak` depending on your OS and what information you want displayed accurately via the fallbacks. The script attempts to handle their absence gracefully but might show "N/A" or errors for those specific fields if the commands fail or are missing.

6.  **Make the Script Executable (Optional):**
    ```bash
    chmod +x rw_fetch.py
    ```
    This allows you to run it directly using `./rw_fetch.py` instead of `python rw_fetch.py`.

## Get Started 🚀

This section provides the quickest way to get RW-fetch running.

### Adding New Images/GIFs 📁

*   By default, the script looks for images in a directory named `rsc` located in the same directory as the script.
*   Simply **place your `.gif`, `.png`, `.jpg`, `.webp`, or `.bmp` files inside the `rsc/` directory.**
*   You can change the source directory using the `--rsc-dir <path>` argument.

### Generating the Cache ⚡

*   The cache stores the pre-converted ANSI art, making future runs (especially `--random`) much faster.
*   To generate or update the cache for all supported images found in the `rsc/` directory (or the one specified by `--rsc-dir`), simply run the script without the `--random` or specific file arguments:
    ```bash
    # If you made it executable:
    ./rw_fetch.py

    # Or using python:
    python rw_fetch.py
    ```
*   The script will process each image, display it (unless `--silent` is used), and save the results to `cache.json` (or the file specified by `--cache`). You only need to do this once initially, or whenever you add/remove images, or if you want to refresh existing entries (using `--refresh`).

### Basic Display Commands 💻

*   **Display a specific image:**
    ```bash
    ./rw_fetch.py rsc/your_favorite.gif
    ```

*   **Display a random image from the cache:**
    ```bash
    ./rw_fetch.py --random
    ```

*   **Display a random image with system info:**
    ```bash
    ./rw_fetch.py --random --sysinfo
    ```

*   **Display a random *small* image, with system info, silently (ideal for startup):**
    ```bash
    ./rw_fetch.py --random --small --sysinfo --silent
    ```

## Usage Details ⚙️

### Cache Management 💾

*   **Cache File:** By default, `cache.json` in the script's directory. Use `--cache <path>` to specify a different location.
*   **Automatic Caching:** When processing a directory or a specific file (without `--refresh`), the script checks the cache first. If a valid entry exists, it's used. Otherwise, the image is processed, and the result is added to the cache.
*   **Forcing Refresh:** Use `--refresh` to ignore existing cache entries and force reprocessing of images. The cache will be updated with the new results.
    ```bash
    ./rw_fetch.py --refresh # Reprocess all images in rsc/
    ./rw_fetch.py rsc/image.png --refresh # Reprocess only image.png
    ```
*   **Viewing Cache Info:** Use `--cache-info` to display statistics about the current cache file (path, size, number of entries, category breakdown).
    ```bash
    ./rw_fetch.py --cache-info
    ```

### Image Categorization & Thresholds 📏

*   Images are categorized based on the number of lines in their generated ANSI art:
    *   `small`: Fewer lines than `SMALL_THRESHOLD`
    *   `medium`: Fewer lines than `MEDIUM_THRESHOLD`
    *   `large`: Fewer lines than `LARGE_THRESHOLD`
    *   `extra-large`: Equal to or more lines than `LARGE_THRESHOLD`
*   These thresholds (`SMALL_THRESHOLD`, `MEDIUM_THRESHOLD`, `LARGE_THRESHOLD`) can be adjusted in the `config.py` file.

### Displaying Random Images 🎲

*   The `--random` flag selects a random entry from the cache.
*   You can combine `--random` with category filters:
    ```bash
    ./rw_fetch.py --random --medium # Show a random medium-sized image
    ./rw_fetch.py --random --large --extra-large # Show a random large OR extra-large image
    ```
*   If no cached images match the filter criteria, an error message is shown.

### System Information Display 📊

*   Use `--fetch-system` or its alias `--sysinfo` to display system information alongside the image.
*   The information displayed, its order, labels, colors, and any fallback commands used are defined in `config.py` within the `SYSTEM_INFO_ORDER` list and `FALLBACK_COMMANDS` dictionary.
*   If `psutil` is not installed, fields like Memory, detailed Uptime, and CPU frequency/usage might show "N/A" or limited information, and a warning message will be appended.
*   Fallback commands are executed via `subprocess` if a direct Python method isn't available or specified for a label in `SYSTEM_INFO_ORDER`. Errors during command execution (e.g., command not found, timeout) are displayed inline.

## Examples 🔍

1.  **Process and display a specific image:**
    ```bash
    ./rw_fetch.py rsc/witch_stand.gif
    ```

2.  **Process/display a specific image and show system info:**
    ```bash
    ./rw_fetch.py rsc/another.png --sysinfo
    ```

3.  **Build/update the cache for all images in `rsc/` (shows processing output):**
    ```bash
    ./rw_fetch.py
    ```

4.  **Show a random image from the cache:**
    ```bash
    ./rw_fetch.py --random
    ```

5.  **Show a random LARGE or EXTRA-LARGE image with system info:**
    ```bash
    ./rw_fetch.py --random --large --extra-large --sysinfo
    ```

6.  **Show statistics about the cache:**
    ```bash
    ./rw_fetch.py --cache-info
    ```

7.  **Show a random SMALL image with system info, without any log messages (good for startup):**
    ```bash
    ./rw_fetch.py --random --small --sysinfo --silent
    ```

8.  **Force reprocessing of all images in a custom directory:**
    ```bash
    ./rw_fetch.py --rsc-dir /path/to/my/images --refresh
    ```

## Parameters Explained 🎛️

*   `--rsc-dir <path>`: Specifies the directory containing image files. (Default: `./rsc`)
*   `--cache <path>`: Specifies the path to the JSON cache file. (Default: `./cache.json`)
*   `file`: (Positional argument) Path to a specific image file to process. If omitted, the script processes compatible files in `--rsc-dir`.
*   `--refresh`: Ignores existing cache entries and forces reprocessing of the specified image(s). Updates the cache with the new result.
*   `--random`: Displays a random image from the cache, honoring category filters if set.
*   `--fetch-system`, `--sysinfo`: Displays system information alongside the image art.
*   `--cache-info`: Displays statistics about the cache file (size, entry count, categories) and exits.
*   `--silent`: Suppresses non-essential output (like "Processing:", "Cached:", category info). Useful for clean output in scripts or terminal startup.
*   `--small`: Filters for images categorized as "small". Used with `--random` or when processing a directory.
*   `--medium`: Filters for images categorized as "medium".
*   `--large`: Filters for images categorized as "large".
*   `--extra-large`: Filters for images categorized as "extra-large".

## Terminal Startup Integration ⏰

You can add RW-fetch to your shell's startup file (like `.bashrc`, `.zshrc`, `.config/fish/config.fish`) to see a random artwork every time you open a new terminal. Remember to use the full path to the script unless it's in your system's PATH. Using `--silent` is recommended here.

Example for `.bashrc` or `.zshrc`:

```bash
# Add this line at the end of your ~/.bashrc or ~/.zshrc
/path/to/rw-fetch/rw_fetch.py --random --small --sysinfo --silent
```

Example for Fish shell (`~/.config/fish/config.fish`):

```fish
# Add this line to your config.fish
/path/to/rw-fetch/rw_fetch.py --random --small --sysinfo --silent
```

*Replace `/path/to/rw-fetch/` with the actual path to where you cloned the repository.* Make sure the cache has been generated at least once before adding it to your startup file.

### Using Rust version

I made a small compiled version to avoid having to initialize conda in my terminal everytime. (not gonna lie, chugged it to Gemini 2.5).

Please make sure to first process a cache using python. Compile the rust version using `compile_rust.sh`, which will copy back the executable in your directory. Now you can `chmod +x rw_fetch_rs.o` and use it directly.

Use this method if you would rather not use python on each shell spawn.

## Contributing 🤝

Open an issue with your request and potential fixes. I'll see what I can do!

## License 📄

This project is distributed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License. See the [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) page for more details.

Essentially, you are free to share and adapt the work for non-commercial purposes, provided you give appropriate credit, indicate if changes were made, and share any derivative works under the same license.
