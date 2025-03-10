#!/usr/bin/env python3
import sys
from PIL import Image

def rgb_to_ansi_fg(r, g, b, a):
    """
    Return ANSI escape code for setting the foreground color to the specified RGB value.
    If a is 0, reset to the terminal default foreground color.
    """
    if a == 0:
        return "\033[39m", " "  # Reset to default foreground.
    return f"\033[38;2;{r};{g};{b}m", "▀"

def rgb_to_ansi_bg(r, g, b, a):
    """
    Return ANSI escape code for setting the background color to the specified RGB value.
    If a is 0, reset to the terminal default background color.
    """
    if a == 0:
        return "\033[49m"  # Reset to default background.
    return f"\033[48;2;{r};{g};{b}m"

def reset_ansi():
    """
    Return ANSI escape code for resetting colors.
    """
    return "\033[0m"

def crop_transparent_borders(image):
    """
    Crop off any contiguous transparent rows from the top and bottom, 
    and transparent columns from the left and right.
    A row or column is considered transparent if all its pixels have an alpha value of 0.
    """
    image = image.convert("RGBA")
    width, height = image.size
    pix = image.load()
    
    # Find top boundary (first row with at least one non-transparent pixel)
    top = 0
    for y in range(height):
        if any(pix[x, y][3] != 0 for x in range(width)):
            top = y
            break

    # Find bottom boundary (last row with at least one non-transparent pixel)
    bottom = height - 1
    for y in range(height - 1, -1, -1):
        if any(pix[x, y][3] != 0 for x in range(width)):
            bottom = y
            break

    # Find left boundary (first column with at least one non-transparent pixel)
    left = 0
    for x in range(width):
        if any(pix[x, y][3] != 0 for y in range(top, bottom + 1)):
            left = x
            break

    # Find right boundary (last column with at least one non-transparent pixel)
    right = width - 1
    for x in range(width - 1, -1, -1):
        if any(pix[x, y][3] != 0 for y in range(top, bottom + 1)):
            right = x
            break

    return image.crop((left, top, right + 1, bottom + 1))

    # Crop the image vertically; the full width remains unchanged.
    return image.crop((0, top, width, bottom + 1))

def image_to_ansi(image):
    """
    Convert an RGB image to a string of ANSI-colored text using half blocks.
    
    Each printed character encodes two vertical pixels:
    - The top pixel color is used as the foreground.
    - The bottom pixel color is used as the background.
    """
    image = image.convert("RGBA")
    image = crop_transparent_borders(image)
    width, height = image.size
    ansi_str = ""

    # Process two rows at a time.
    for y in range(0, height, 2):
        line = ""
        for x in range(width):
            # Get the top pixel
            top_pixel = image.getpixel((x, y))
            # For the bottom pixel, if available; otherwise default to black.
            if y + 1 < height:
                bottom_pixel = image.getpixel((x, y + 1))
            else:
                bottom_pixel = (0, 0, 0, 0)

            # Set foreground for top pixel and background for bottom pixel
            fg, char = rgb_to_ansi_fg(*top_pixel)
            bg = rgb_to_ansi_bg(*bottom_pixel)
            # Use the upper half block (▀) to combine both colors in one character.
            line += f"{bg}{fg}{char}"
        line += reset_ansi()  # Reset at the end of the line.
        ansi_str += line + "\n"
    return ansi_str

def main():
    if len(sys.argv) < 2:
        print("Usage: python script.py <image_file>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    try:
        img = Image.open(file_path)
    except Exception as e:
        print("Error opening image:", e)
        sys.exit(1)

    # If the image is an animated GIF, load the first frame.
    try:
        img.seek(0)
    except Exception:
        # Not a multi-frame image.
        pass

    # Convert image to ANSI art and print.
    ansi_art = image_to_ansi(img)
    print(ansi_art)

if __name__ == "__main__":
    main()
