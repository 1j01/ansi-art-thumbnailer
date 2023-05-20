#!/usr/bin/env python3

import os
import sys
import argparse
from PIL import Image, ImageDraw, ImageFont

# log_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ansi-thumbnailer.log')
# sys.stdout = open(log_file, 'w')
# sys.stderr = sys.stdout

if __name__ == '__main__':

    # parse arguments
    parser = argparse.ArgumentParser(description='Generate thumbnails for .ans and .nfo files')
    parser.add_argument('input',    type=str,   help='Path to input file')
    parser.add_argument('output',   type=str,   help='Path to output png thumbnail')
    parser.add_argument('size',     type=int,   help='Thumbnail image size')
    arguments = parser.parse_args()

    # check file extension
    file_extension = os.path.splitext(arguments.input)[1].lower()
    if file_extension not in [".ans", ".nfo"]:
        sys.exit(1)

    # load file
    with open(arguments.input, 'rb') as f:
        data = f.read()

    # make PIL image
    img = Image.new('RGB', (arguments.size, arguments.size), color='black')
    draw = ImageDraw.Draw(img)

    # load font
    # font = ImageFont.truetype('fonts/ansi.ttf', 16)
    font = ImageFont.load_default()

    # draw text
    x = 0
    y = 0
    for byte in data:
        if byte == 10:
            x = 0
            y += 16
        else:
            draw.text((x, y), chr(byte), fill='white', font=font)
            x += 8

    # save image
    img.save(arguments.output, 'PNG', optimize=True)

    sys.exit(0)
