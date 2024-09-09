#!/usr/bin/python3
import re

# Regular expression to match ANSI escape sequences for normal colors (3X)
ansi_normal_color_pattern = re.compile(r'(\033\[3[0-7]m)')

# Function to convert ANSI escape sequences from normal to bold
def convert_to_bold(text):
    # Convert all ANSI color sequences from \033[3Xm to \033[1;3Xm (which makes them bold)
    return ansi_normal_color_pattern.sub(lambda match: f'\033[1;{match.group(0)[2:]}', text)

# Example input text with ANSI normal colors
input_text = (
    "\033[30mBlack text\033[0m, \033[31mRed text\033[0m, "
    "\033[32mGreen text\033[0m, \033[33mYellow text\033[0m"
)

# Apply the bold conversion
bold_text = convert_to_bold(input_text)

# Print the original and the bold version
print("Original text with normal ANSI colors:")
print(input_text)
print("\nText with bold ANSI colors:")
print(bold_text)

