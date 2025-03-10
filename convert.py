#!/usr/bin/env python3
import sys
import random
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
    image = image.convert("RGBA")
    image = crop_transparent_borders(image)
    width, height = image.size
    ansi_str = ""

    for y in range(0, height, 2):
        line = ""
        for x in range(width):
            top_pixel = image.getpixel((x, y))
            bottom_pixel = image.getpixel((x, y + 1)) if y + 1 < height else (0, 0, 0, 0)

            fg, char = rgb_to_ansi_fg(*top_pixel)
            bg = rgb_to_ansi_bg(*bottom_pixel)
            line += f"{bg}{fg}{char}"
        line += reset_ansi()
        ansi_str += line + "\n"
    return ansi_str

def main():
    # if len(sys.argv) < 2:
    #     print("Usage: python script.py <image_file>")
    #     sys.exit(1)
    # file_path = sys.argv[1]

    file_path = f'rsc/{random.randint(1, 1506)}.gif'

    
    try:
        img = Image.open(file_path)
    except Exception as e:
        print("Error opening image:", e)
        sys.exit(1)

    # If the image is an animated GIF, select a random frame
    if getattr(img, "is_animated", False):
        random_frame = random.randint(0, img.n_frames - 1)
        img.seek(random_frame)

    ansi_art = image_to_ansi(img)
    print(ansi_art)

if __name__ == "__main__":
    main()
