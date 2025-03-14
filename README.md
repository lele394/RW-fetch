# <div align="center"><img src="https://raw.githubusercontent.com/lele394/lele394/main/rsc/77.gif"   style="width: calc(43 / 41 * 100%);;  height: 100%;"  /> RW-fetch <img src="https://raw.githubusercontent.com/lele394/lele394/main/rsc/74.gif"   style="width: calc(43 / 41 * 100%);;  height: 100%;"  />
</div>  

Welcome to **RW-fetch** – your terminal’s nostalgic gateway to the pixel art of *Revived Witch*! This project converts GIFs from the once-popular gacha game *Revived Witch* (which has sadly reached its end of service) into vibrant ANSI art for your terminal. Enjoy a blast from the past every time you open your terminal!

_Distributed under the [CC BY-NC-SA](https://creativecommons.org/licenses/by-nc-sa/4.0/) license._

---

## Table of Contents 📚

- [Overview 🌟](#overview-)
- [Features ✨](#features-)
- [Installation 🛠️](#installation-)
- [Usage 🚀](#usage-)
  - [Adding New GIFs 📁](#adding-new-gifs-)
  - [Cache Management 💾](#cache-management-)
  - [Category Thresholds 📏](#category-thresholds-)
  - [Displaying Random Images 🎲](#displaying-random-images-)
- [Examples 🔍](#examples-)
- [Parameters Explained ⚙️](#parameters-explained-)
- [Terminal Startup Integration ⏰](#terminal-startup-integration-)
- [Contributing 🤝](#contributing-)
- [License 📄](#license-)

---

## Presentation Video

Check out our presentation below:

<video src="./vid/presentation.webm" controls style="max-width: 100%; height: auto;">
  Your browser does not support the video tag.
</video>

---

## Overview 🌟

**RW-fetch** is a specialized tool for converting GIFs extracted from *Revived Witch* – a pixel art gacha game that captured many hearts before its unfortunate end-of-service. This script transforms these GIFs into ANSI art with minimal redundancy in escape codes, categorizes each image by size, and caches the output for faster re-displays. Perfect for reliving those retro gaming moments every time you fire up your terminal!

Note : This program, though developped for RW is compatible with ay kind of GIFs.

---

## Features ✨

- **GIF to ANSI Art Conversion:** Efficiently converts static and animated GIFs from *Revived Witch* into colorful ANSI static art.
- **Caching:** Automatically saves processed images into a JSON cache to speed up future runs.
- **Cache Information:** Quickly view details like cache file size and entry count per category.
- **Category Filtering:** Filter images by size (small, medium, large, extra-large) based on customizable line-count thresholds.
- **Random Image Display:** Fetch a random image from the cache, with options for silent output and category restrictions.
- **Optimized ANSI Output:** Reduces redundant ANSI escape codes for a cleaner terminal display.
- **Terminal Startup Ready:** Designed to run on terminal startup, giving you a nostalgic pixel art greeting every time you open your terminal.

---

## Installation 🛠️

1. **Clone the repository** or download the project files:
    ```bash
    git clone https://github.com/yourusername/rw-fetch.git
    cd rw-fetch
    ```

2. **Install the required dependency:**
    ```bash
    pip install Pillow
    ```

3. **Prepare your GIFs:**  
   Place your *Revived Witch* GIFs into the default `rsc/` directory or specify a custom directory using the `--rsc-dir` parameter.

---

## Usage 🚀

### Adding New GIFs 📁

Simply add any new GIFs from *Revived Witch* to the `rsc/` directory (or your chosen directory). The script will automatically detect and process all `.gif` files unless you specify a particular file as an argument.

### Cache Management 💾

- **Creating/Loading Cache:**  
  On the first run, the script generates a cache file (`cache.json` by default). Future executions load this cache, avoiding the need to reprocess unchanged GIFs.
  
- **Refreshing Cache:**  
  To reprocess all images (for example, after updating GIFs), use the `--refresh` flag. This will update the cache with the latest ANSI art conversions.

### Category Thresholds 📏

The ANSI art output is classified by the number of lines it generates. Customize these thresholds to best suit the pixel art style of *Revived Witch*:

- `--small-threshold`: Images with fewer than this number of lines are classified as **small** (default: 20).
- `--medium-threshold`: Images with line counts between the small threshold and this value are **medium** (default: 40).
- `--large-threshold`: Images with line counts between the medium threshold and this value are **large** (default: 60).  
  Images with line counts equal to or above this threshold are classified as **extra-large**.

### Displaying Random Images 🎲

Craving a surprise from the past? Use the `--random` flag to display a random cached image. Combine it with:
- `--silent` to suppress extra log output (only the ANSI art is shown).
- Category flags (like `--small`, `--medium`) to restrict the selection to specific sizes.

---

## Examples 🔍

1. **Process all GIFs in the `rsc/` directory and update the cache:**
    ```bash
    ./script.py
    ```

2. **Refresh the cache (force reprocessing) for all GIFs:**
    ```bash
    ./script.py --refresh
    ```

3. **Process a specific GIF file:**
    ```bash
    ./script.py path/to/your/image.gif
    ```

4. **Set custom category thresholds:**
    ```bash
    ./script.py --small-threshold 25 --medium-threshold 45 --large-threshold 70
    ```

5. **Display cache information:**
    ```bash
    ./script.py --cache-info
    ```

6. **Display a random image (from small and medium categories) silently:**
    ```bash
    ./script.py --random --silent --small --medium
    ```

---

## Parameters Explained ⚙️

- **Positional Argument:**
  - `file`: (Optional) Specific image file to process. If omitted, all `.gif` files in the designated directory are processed.

- **Optional Arguments:**
  - `--rsc-dir`: Directory containing *Revived Witch* GIF images (default: `rsc`).
  - `--cache`: Path to the JSON cache file (default: `cache.json`).
  - `--refresh`: Forces reprocessing of images even if they are already cached.
  - `--random`: Displays a random cached image.
  - `--cache-info`: Outputs statistics about the cache (e.g., file size, total entries, entries per category).
  - `--small-threshold`: Maximum number of lines for an image to be considered **small** (default: 20).
  - `--medium-threshold`: Upper limit for **medium** images (default: 40).
  - `--large-threshold`: Upper limit for **large** images (default: 60). Images with line counts equal to or above this are **extra-large**.
  - `--small`, `--medium`, `--large`, `--extra-large`: Flags to filter images by their size category.
  - `--silent`: When used with `--random`, minimizes extra log output (only the ANSI art is displayed).

---

## Terminal Startup Integration ⏰

For a daily blast of pixel art nostalgia, you can configure your terminal to run **RW-fetch** on startup. Add the following line to your shell’s startup file (like `~/.bashrc` or `~/.zshrc`):

```bash
# Display a random Revived Witch ANSI art image on terminal startup
/path/to/rw-fetch/script.py --random --silent
```

Or, to limit the random selection to smaller images:
```bash
/path/to/rw-fetch/script.py --random --silent --small --medium
```

---


## License 📄

This project is distributed under the [CC BY-NC-SA](https://creativecommons.org/licenses/by-nc-sa/4.0/) license. You are free to use, share, and modify the project for non-commercial purposes as long as you attribute the original work and share your modifications under the same license.

---

Enjoy reviving the pixel art memories of *Revived Witch* in your terminal every day. Happy coding and keep the retro vibes alive! 😄

# Long Live The Witch!