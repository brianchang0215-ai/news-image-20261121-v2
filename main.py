"""Draw the 21 November 2026 world-news image.

Standard library only. No network, no files read, no randomness:
the same run always writes the same PNG bytes.
Text is rendered with a small bitmap font defined below, so the
image needs no font files and stays legible when scaled down.
"""

import os
import struct
import zlib
from pathlib import Path

W = 1024
H = 1024

PAPER = (247, 243, 232)
WHITE = (255, 255, 255)
NAVY = (18, 35, 63)
INK = (28, 32, 40)
RED = (178, 34, 34)
ORANGE = (224, 110, 30)
GOLD = (214, 164, 48)
TEAL = (0, 105, 95)
GREY = (96, 102, 112)
LIGHT = (228, 224, 212)
SKY = (205, 224, 236)
WATER = (120, 160, 190)

# 5x7 bitmap font. Each glyph is 7 rows of 5 cells, "#" = on.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "01010", "00100", "00100", "00100", "01010", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "00110", "00110"),
    ",": ("00000", "00000", "00000", "00000", "00110", "00100", "01000"),
    ":": ("00000", "00110", "00110", "00000", "00110", "00110", "00000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "|": ("00100", "00100", "00100", "00100", "00100", "00100", "00100"),
}

pix = bytearray(W * H * 3)


def set_px(x, y, color):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        pix[i], pix[i + 1], pix[i + 2] = color


def rect(x, y, w, h, color):
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            set_px(xx, yy, color)


def line(x0, y0, x1, y1, color, thick=1):
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    x, y = x0, y0
    while True:
        for t in range(thick):
            set_px(x + t, y + t, color)
        if x == x1 and y == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x += sx
        if e2 <= dx:
            err += dx
            y += sy


def circle(cx, cy, r, color):
    for yy in range(cy - r, cy + r + 1):
        for xx in range(cx - r, cx + r + 1):
            if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                set_px(xx, yy, color)


def ring(cx, cy, r, color, thick=3):
    for yy in range(cy - r, cy + r + 1):
        for xx in range(cx - r, cx + r + 1):
            d2 = (xx - cx) ** 2 + (yy - cy) ** 2
            if (r - thick) ** 2 <= d2 <= r * r:
                set_px(xx, yy, color)


def text_width(text, scale, spacing=None):
    if spacing is None:
        spacing = scale
    if not text:
        return 0
    return len(text) * (5 * scale + spacing) - spacing


def draw_text(x, y, text, scale, color):
    spacing = scale
    cx = x
    for ch in text:
        glyph = FONT.get(ch, FONT[" "])
        for row_i, row in enumerate(glyph):
            for col_i, cell in enumerate(row):
                if cell == "1":
                    rect(cx + col_i * scale, y + row_i * scale, scale, scale, color)
        cx += 5 * scale + spacing
    return cx


def draw_text_centered(cx, y, text, scale, color):
    draw_text(cx - text_width(text, scale) // 2, y, text, scale, color)


def card(x, y, w, h):
    rect(x, y, w, h, WHITE)
    rect(x, y, w, 3, NAVY)
    rect(x, y, 3, h, NAVY)
    rect(x + w - 3, y, 3, h, NAVY)
    rect(x, y + h - 3, w, 3, NAVY)


def kicker(x, y, text, color):
    draw_text(x, y, text, 3, color)


def main():
    rect(0, 0, W, H, PAPER)

    # Masthead.
    rect(0, 0, W, 112, NAVY)
    draw_text_centered(W // 2, 24, "WORLD NEWS", 7, WHITE)
    rect(0, 112, W, 46, GOLD)
    draw_text_centered(W // 2, 126, "SATURDAY 21 NOVEMBER 2026", 3, NAVY)

    # Hero: Ukraine / Poland. Text on the left, picture on the right:
    # the bridge must never sit under the text.
    card(32, 172, 960, 320)
    rect(540, 188, 424, 288, SKY)
    # Bridge: deck, towers, cables, water, inside the right column only.
    rect(556, 372, 392, 14, NAVY)
    rect(624, 268, 18, 118, NAVY)
    rect(864, 268, 18, 118, NAVY)
    line(633, 268, 556, 372, NAVY, 3)
    line(633, 268, 756, 372, NAVY, 3)
    line(873, 268, 756, 372, NAVY, 3)
    line(873, 268, 948, 372, NAVY, 3)
    for wx in range(556, 948, 28):
        line(wx, 420, wx + 14, 420, WATER, 3)
        line(wx + 6, 444, wx + 20, 444, WATER, 3)
    circle(908, 246, 26, GREY)
    circle(932, 226, 18, GREY)
    circle(908, 246, 10, RED)
    kicker(52, 196, "UKRAINE - POLAND", RED)
    draw_text(52, 228, "KYIV BRIDGES", 5, NAVY)
    draw_text(52, 268, "HIT", 5, NAVY)
    draw_text(52, 326, "OVERNIGHT STRIKES", 3, INK)
    draw_text(52, 352, "KRYVYI RIH: 2 KILLED,", 3, INK)
    draw_text(52, 378, "83 INJURED", 3, INK)
    draw_text(52, 404, "MISSILES REPORTED", 3, INK)
    draw_text(52, 430, "IN POLAND", 3, INK)

    # Middle left: markets.
    card(32, 508, 472, 236)
    kicker(52, 524, "MARKETS", RED)
    draw_text(52, 550, "WALL STREET", 4, NAVY)
    draw_text(52, 578, "FALLS", 4, NAVY)
    draw_text(52, 618, "S&P 500 -3.7%", 3, INK)
    draw_text(52, 644, "NASDAQ -5.3%", 3, INK)
    draw_text(52, 670, "INTO CORRECTION", 3, INK)
    # Falling chart.
    line(330, 620, 372, 640, RED, 4)
    line(372, 640, 414, 668, RED, 4)
    line(414, 668, 458, 706, RED, 4)
    line(330, 706, 458, 706, GREY, 2)

    # Middle right: climate.
    card(520, 508, 472, 236)
    kicker(540, 524, "CLIMATE", TEAL)
    draw_text(540, 550, "COP31 IN", 4, NAVY)
    draw_text(540, 578, "OVERTIME", 4, NAVY)
    draw_text(540, 618, "DRAFT DROPS", 3, INK)
    draw_text(540, 644, "FOSSIL FUELS", 3, INK)
    draw_text(540, 670, "ANTALYA, TURKIYE", 3, INK)
    circle(916, 650, 30, GOLD)
    for dx, dy in ((-44, -30), (0, -48), (44, -30), (-52, 6), (52, 6)):
        line(916, 650, 916 + dx, 650 + dy, GOLD, 4)

    # Bottom left: quake.
    card(32, 760, 472, 176)
    kicker(52, 774, "EARTHQUAKE", TEAL)
    draw_text(52, 800, "M6.8 QUAKE", 4, NAVY)
    draw_text(52, 840, "BANDA SEA", 3, INK)
    draw_text(52, 866, "NEAR TIMOR-LESTE", 3, INK)
    ring(432, 848, 52, RED, 4)
    ring(432, 848, 36, RED, 4)
    ring(432, 848, 20, RED, 4)
    circle(432, 848, 7, RED)

    # Bottom right: Iraq fire.
    card(520, 760, 472, 176)
    kicker(540, 774, "IRAQ", RED)
    draw_text(540, 800, "BASRA FIRE", 4, NAVY)
    draw_text(540, 840, "4 KILLED, 30 HURT", 3, INK)
    draw_text(540, 866, "POWER STATION", 3, INK)
    # Flame: outer and inner triangles made of stacked bars.
    for i, half in enumerate((6, 12, 18, 22, 24, 22, 18, 12)):
        rect(916 - half, 806 + i * 9, half * 2, 9, ORANGE)
    for i, half in enumerate((3, 6, 9, 10, 9, 6)):
        rect(916 - half, 830 + i * 9, half * 2, 9, RED)

    # Footer ticker.
    rect(0, 952, W, 72, NAVY)
    draw_text_centered(
        W // 2, 978,
        "IRAN SEEKS TALKS - US: TERMS UNACCEPTABLE  |  SPAIN EXTENDS BANK TAX",
        2, WHITE,
    )

    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "entry.png"
    write_png(out_path)


def chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(path):
    raw = bytearray()
    for y in range(H):
        raw.append(0)
        raw.extend(pix[y * W * 3:(y + 1) * W * 3])
    compressed = zlib.compress(bytes(raw), 9)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", compressed)
    png += chunk(b"IEND", b"")
    Path(path).write_bytes(png)


if __name__ == "__main__":
    main()
