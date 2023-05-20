#!/usr/bin/env python3

import os
import sys
import argparse

from PIL import Image, ImageDraw, ImageFont
import stransi

# Workaround for unwanted color rounding
# RGB.__post_init__ rounds the color components, in decimal, causing 128 to become 127.
from ochre.spaces import RGB
RGB.__post_init__ = lambda self: None

# log_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ansi-thumbnailer.log')
# sys.stdout = open(log_file, 'w')
# sys.stderr = sys.stdout

class AnsiArtDocument:
    """A document representing terminal output (a grid of characters and colors), i.e. ANSI art.
    
    Class extracted from Textual Paint (https://github.com/1j01/textual-paint)
    """

    def __init__(self, width: int, height: int, default_bg: str = "#000000", default_fg: str = "#ffffff") -> None:
        """Initialize the document."""
        self.width: int = width
        self.height: int = height
        self.ch = [[" " for _ in range(width)] for _ in range(height)]
        self.bg = [[default_bg for _ in range(width)] for _ in range(height)]
        self.fg = [[default_fg for _ in range(width)] for _ in range(height)]

    @staticmethod
    def from_ansi(text: str, default_bg: str = "#000000", default_fg: str = "#ffffff") -> 'AnsiArtDocument':
        """Creates a document from the given ANSI text."""
        ansi = stransi.Ansi(text)

        document = AnsiArtDocument(0, 0, default_bg, default_fg)
        # Minimum size of 1x1, so that the document is never empty.
        width = 1
        height = 1

        x = 0
        y = 0
        bg_color = default_bg
        fg_color = default_fg
        for instruction in ansi.instructions():
            if isinstance(instruction, str):
                # Text and control characters other than escape sequences
                for char in instruction:
                    if char == '\r':
                        x = 0
                    elif char == '\n':
                        x = 0
                        y += 1
                        # Don't increase height until there's a character to put in the new row.
                        # This avoids an extra row if the file ends with a newline.
                    elif char == '\t':
                        x += 8 - (x % 8)
                    elif char == '\b':
                        x -= 1
                        if x < 0:
                            x = 0
                            # on some terminals, backspace at the start of a line moves the cursor up,
                            # but we're not defining a width for the document up front, so we can't do that
                    elif char == '\x07':
                        # ignore bell
                        # TODO: ignore other unhandled control characters
                        pass
                    else:
                        while len(document.ch) <= y:
                            document.ch.append([])
                            document.bg.append([])
                            document.fg.append([])
                        while len(document.ch[y]) <= x:
                            document.ch[y].append(' ')
                            document.bg[y].append(default_bg)
                            document.fg[y].append(default_fg)
                        document.ch[y][x] = char
                        document.bg[y][x] = bg_color
                        document.fg[y][x] = fg_color
                        width = max(x + 1, width)
                        height = max(y + 1, height)
                        x += 1
            elif isinstance(instruction, stransi.SetColor) and instruction.color is not None:
                # Color (I'm not sure why instruction.color would be None, but it's typed as Optional[Color])
                # (maybe just for initial state?)
                if instruction.role == stransi.color.ColorRole.FOREGROUND:
                    rgb = instruction.color.rgb
                    fg_color = "rgb(" + str(int(rgb.red * 255)) + "," + str(int(rgb.green * 255)) + "," + str(int(rgb.blue * 255)) + ")"
                elif instruction.role == stransi.color.ColorRole.BACKGROUND:
                    rgb = instruction.color.rgb
                    bg_color = "rgb(" + str(int(rgb.red * 255)) + "," + str(int(rgb.green * 255)) + "," + str(int(rgb.blue * 255)) + ")"
            elif isinstance(instruction, stransi.SetCursor):
                # Cursor position is encoded as y;x, so stransi understandably gets this backwards.
                # TODO: fix stransi to interpret ESC[<y>;<x>H correctly
                # (or update it if it gets fixed)
                # Note that stransi gives 0-based coordinates; the underlying ANSI is 1-based.
                if instruction.move.relative:
                    x += instruction.move.y
                    y += instruction.move.x
                else:
                    x = instruction.move.y
                    y = instruction.move.x
                x = max(0, x)
                y = max(0, y)
                width = max(x + 1, width)
                height = max(y + 1, height)
                while len(document.ch) <= y:
                    document.ch.append([])
                    document.bg.append([])
                    document.fg.append([])
            elif isinstance(instruction, stransi.SetClear):
                def clear_line(row_to_clear: int, before: bool, after: bool):
                    cols_to_clear: list[int] = []
                    if before:
                        cols_to_clear += range(0, len(document.ch[row_to_clear]))
                    if after:
                        cols_to_clear += range(x, len(document.ch[row_to_clear]))
                    for col_to_clear in cols_to_clear:
                        document.ch[row_to_clear][col_to_clear] = ' '
                        document.bg[row_to_clear][col_to_clear] = default_bg
                        document.fg[row_to_clear][col_to_clear] = default_fg
                match instruction.region:
                    case stransi.clear.Clear.LINE:
                        # Clear the current line
                        clear_line(y, True, True)
                    case stransi.clear.Clear.LINE_AFTER:
                        # Clear the current line after the cursor
                        clear_line(y, False, True)
                    case stransi.clear.Clear.LINE_BEFORE:
                        # Clear the current line before the cursor
                        clear_line(y, True, False)
                    case stransi.clear.Clear.SCREEN:
                        # Clear the entire screen
                        for row_to_clear in range(len(document.ch)):
                            clear_line(row_to_clear, True, True)
                        # and reset the cursor to home
                        x, y = 0, 0
                    case stransi.clear.Clear.SCREEN_AFTER:
                        # Clear the screen after the cursor
                        for row_to_clear in range(y, len(document.ch)):
                            clear_line(row_to_clear, row_to_clear > y, True)
                    case stransi.clear.Clear.SCREEN_BEFORE:
                        # Clear the screen before the cursor
                        for row_to_clear in range(y):
                            clear_line(row_to_clear, True, row_to_clear < y)
            elif isinstance(instruction, stransi.SetAttribute):
                # Attribute
                pass
            elif isinstance(instruction, stransi.Unsupported):
                raise ValueError("Unknown instruction " + repr(instruction.token))
            else:
                raise ValueError("Unknown instruction type " + str(type(instruction)))
        document.width = width
        document.height = height
        # Handle minimum height.
        while len(document.ch) <= document.height:
            document.ch.append([])
            document.bg.append([])
            document.fg.append([])
        # Pad rows to a consistent width.
        for y in range(document.height):
            for x in range(len(document.ch[y]), document.width):
                document.ch[y].append(' ')
                document.bg[y].append(default_bg)
                document.fg[y].append(default_fg)
        return document
    

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
    with open(arguments.input, 'r') as f:
        doc = AnsiArtDocument.from_ansi(f.read())

    # make PIL image
    img = Image.new('RGB', (arguments.size, arguments.size), color='black')
    draw = ImageDraw.Draw(img)

    # load font
    # font = ImageFont.truetype('fonts/ansi.ttf', 16)
    font = ImageFont.load_default()
    ch_width, ch_height = font.getsize('A')

    # draw cell backgrounds
    for y in range(doc.height):
        for x in range(doc.width):
            bg_color = doc.bg[y][x]
            draw.rectangle((x * ch_width, y * ch_height, (x + 1) * ch_width, (y + 1) * ch_height), fill=bg_color)

    # draw text
    for y in range(doc.height):
        for x in range(doc.width):
            char = doc.ch[y][x]
            bg_color = doc.bg[y][x]
            fg_color = doc.fg[y][x]
            try:
                draw.text((x * ch_width, y * ch_height), char, font=font, fill=fg_color)
            except UnicodeEncodeError:
                pass

    # save image
    img.save(arguments.output, 'PNG', optimize=True)

    sys.exit(0)
