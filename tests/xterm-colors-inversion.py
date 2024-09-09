#!/usr/bin/python3
import re

# Define the ANSI color mappings for foreground and background inversion
color_map = {
    '30': '37',  # Black to White
    '31': '36',  # Red to Cyan
    '32': '35',  # Green to Magenta
    '33': '34',  # Yellow to Blue
    '34': '33',  # Blue to Yellow
    '35': '32',  # Magenta to Green
    '36': '31',  # Cyan to Red
    '37': '30',  # White to Black
    '40': '47',  # Black background to White background
    '41': '46',  # Red background to Cyan background
    '42': '45',  # Green background to Magenta background
    '43': '44',  # Yellow background to Blue background
    '44': '43',  # Blue background to Yellow background
    '45': '42',  # Magenta background to Green background
    '46': '41',  # Cyan background to Red background
    '47': '40'   # White background to Black background
}

# Regular expression to match ANSI escape sequences for colors
ansi_color_pattern = re.compile(r'(\033\[(3[0-7]|4[0-7])m)')

def invert_ansi_colors(text):
    def replace_color(match):
        ansi_code = match.group(2)
        return f"\033[{color_map.get(ansi_code, ansi_code)}m"
    
    # Substitute all the matched ANSI sequences with their inverted counterparts
    return ansi_color_pattern.sub(replace_color, text)

# Example input text with ANSI colors
input_text = (
    "\033[31mRed text\033[0m, \033[42mGreen background\033[0m, "
    "\033[33mYellow text\033[0m, \033[47mWhite background\033[0m"
)

# Apply the color inversion
inverted_text = invert_ansi_colors(input_text)

# Print the original and the inverted versions
print("Original text with ANSI colors:")
print(input_text)
print("\nInverted text with ANSI colors:")
print(inverted_text)

