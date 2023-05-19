#!/usr/bin/env python3

import os
import sys
import argparse
from PIL import Image

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
    # with open(arguments.input, 'rb') as f:
    #     data = f.read()

    # convert to PIL
    # img = Image.fromarray(data)

    # make PIL image
    img = Image.new('RGB', (arguments.size, arguments.size), color='black')

    # resize to thumbnail
    # img.thumbnail((arguments.size, arguments.size))

    # save image
    img.save(arguments.output, 'PNG')

    sys.exit(0)
