"""Draw the 21 November 2026 world-news image, version 2.

Standard library only. No network, no files read, no randomness:
the same run always writes the same PNG bytes.
Text is rendered with a small bitmap font defined below, so the
image needs no font files. Every story below was checked against
news reported on 21 November 2026; items marked * happened on
20 November and were reported on 21 November.
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
GREEN = (110, 150, 90)

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
    "*": ("00100", "10101", "01110", "10101", "00100", "00000", "00000"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
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


def draw_text_right(rx, y, text, scale, color):
    draw_text(rx - text_width(text, scale), y, text, scale, color)


def card(x, y, w, h):
    rect(x, y, w, h, WHITE)
    rect(x, y, w, 3, NAVY)
    rect(x, y, 3, h, NAVY)
    rect(x + w - 3, y, 3, h, NAVY)
    rect(x, y + h - 3, w, 3, NAVY)


def hero(x, y, w, h, kicker, head1, head2, details, accent, art):
    card(x, y, w, h)
    rect(x, y, w, 6, accent)
    draw_text(x + 14, y + 14, kicker, 2, accent)
    draw_text(x + 14, y + 36, head1, 4, NAVY)
    draw_text(x + 14, y + 68, head2, 4, NAVY)
    yy = y + 100
    for d in details:
        draw_text(x + 14, yy, d, 2, INK)
        yy += 17
    art(x, y, w, h)


def art_sun(x, y, w, h):
    cx, cy = x + w - 40, y + 50
    circle(cx, cy, 13, GOLD)
    for dx, dy in ((-22, -12), (0, -22), (22, -12)):
        line(cx, cy, cx + dx, cy + dy, GOLD, 3)


def art_missile(x, y, w, h):
    for i, (sx, sy) in enumerate(((0, 18), (20, 8), (40, 18))):
        line(x + w - 88 + sx, y + h - 6, x + w - 88 + sx + 14, y + h - 6 - sy, RED, 3)
        circle(x + w - 88 + sx + 14, y + h - 6 - sy, 3, RED)


def art_waves(x, y, w, h):
    for row in range(2):
        yy = y + h - 12 + row * 6
        for xx in range(x + 16, x + w - 40, 26):
            line(xx, yy, xx + 13, yy, TEAL, 3)


def medium(x, y, w, h, title, detail, region, accent):
    card(x, y, w, h)
    rect(x, y, 6, h, accent)
    draw_text(x + 16, y + 5, title, 3, NAVY)
    draw_text_right(x + w - 12, y + 7, region, 2, GREY)
    draw_text(x + 16, y + 28, detail, 2, INK)


def main():
    rect(0, 0, W, H, PAPER)

    # Top strip + date masthead.
    rect(0, 0, W, 30, NAVY)
    draw_text_centered(W // 2, 8, "THE WORLD IN ONE DAY", 2, WHITE)
    draw_text_centered(W // 2, 42, "SATURDAY 21 NOVEMBER 2026", 6, NAVY)
    draw_text_centered(
        W // 2, 96,
        "COP31 OVERTIME - MISSILES OVER RIYADH - QUAKE IN PERU", 2, INK,
    )
    rect(0, 118, W, 4, RED)

    # Number strip: six verified figures.
    numbers = [
        ("200", "AT COP31"),
        ("3", "OVER RIYADH"),
        ("6.7", "PERU QUAKE"),
        ("146", "DAVAO SAFE"),
        ("-3.7%", "S&P 500"),
        ("M6.8", "BANDA SEA"),
    ]
    for i, (num, label) in enumerate(numbers):
        bx = 32 + i * 160
        card(bx, 124, 152, 54)
        draw_text_centered(bx + 76, 131, num, 4, RED)
        draw_text_centered(bx + 76, 161, label, 2, NAVY)

    # Three hero stories.
    hero(32, 186, 304, 168, "GLOBAL - CLIMATE", "COP31 IN", "OVERTIME",
         ["DRAFT OMITS FOSSIL FUELS", "NEARLY 200 NATIONS", "ANTALYA, TURKIYE"],
         TEAL, art_sun)
    hero(360, 186, 304, 168, "MIDDLE EAST", "3 MISSILES", "DOWNED",
         ["OVER RIYADH", "EARLY SATURDAY", "ALERT AT 01:53"],
         RED, art_missile)
    hero(688, 186, 304, 168, "EUROPE - WAR", "UKRAINE", "NIGHT RAID",
         ["KRYVYI RIH: 2 KILLED", "83 INJURED IN UKRAINE", "POLAND: MISSILES *"],
         RED, art_waves)

    # Ten medium stories, two columns.
    rows = [
        ("PERU QUAKE", "M6.7 - NO DEATHS - 00:09 GMT", "AMERICAS", TEAL),
        ("BANDA SEA QUAKE", "226 KM NE OF DILI - FELT IN DARWIN", "OCEANIA", TEAL),
        ("BASRA FIRE", "AT LEAST 4 KILLED, 30-35 HURT", "MIDDLE EAST", RED),
        ("WALL STREET FALLS", "S&P -3.7% - NASDAQ -5.3%", "AMERICAS", RED),
        ("BITCOIN SLIDES", "BELOW $59,000 - LOWEST SINCE JULY", "GLOBAL", GOLD),
        ("NVIDIA SLIDES", "-14% - SEC PROBE REPORTED", "AMERICAS", RED),
        ("GENEVA: ROBOT ARMS", "RULES BY 2028 - NO BINDING DEAL", "EUROPE", NAVY),
        ("HORMUZ TANKERS", "IRAN CLAIMS DRONE DOWNED", "MIDDLE EAST", ORANGE),
        ("DAVAO LANDING", "146 ABOARD ALL SAFE", "ASIA", TEAL),
        ("SEJONG DERAILMENT", "5 CARS OFF - NO INJURIES", "ASIA", GREY),
    ]
    for i, (title, detail, region, accent) in enumerate(rows):
        col = i % 2
        row_i = i // 2
        mx = 32 + col * 488
        my = 362 + row_i * 46
        medium(mx, my, 472, 44, title, detail, region, accent)

    # Bottom left: region counts + schematic map note.
    card(32, 592, 288, 354)
    draw_text(48, 606, "WHERE IT HAPPENED", 2, RED)
    rect(48, 628, 256, 110, SKY)
    rect(64, 656, 52, 34, GREEN)
    rect(132, 646, 70, 44, GREEN)
    rect(214, 664, 40, 30, GREEN)
    rect(96, 696, 36, 26, GREEN)
    circle(176, 668, 5, RED)
    circle(88, 672, 5, RED)
    circle(232, 678, 5, RED)
    draw_text(48, 746, "SCHEMATIC MAP", 2, GREY)
    counts = [
        ("EUROPE", "7"), ("ASIA", "5"), ("MIDDLE EAST", "5"),
        ("AFRICA", "3"), ("AMERICAS", "6"), ("OCEANIA", "2"),
        ("GLOBAL", "2"), ("TOTAL", "30"),
    ]
    yy = 772
    for name, num in counts:
        draw_text(48, yy, name, 2, INK)
        draw_text_right(304, yy, num, 2, NAVY)
        yy += 19

    # Bottom right: 17 more stories reported on 21 November.
    card(336, 592, 656, 354)
    draw_text(352, 606, "ALSO REPORTED 21 NOVEMBER 2026", 3, NAVY)
    rect(352, 632, 624, 3, RED)
    more = [
        "POLAND: MISSILES REPORTED, NO INJURIES *",
        "KYIV BRIDGES DAMAGED IN STRIKES *",
        "SPAIN TO EXTEND BANK TAX TO 2027",
        "ITALY CLEARS TESLA DRIVER ASSIST",
        "PARIS PROTEST PLANNED, 70,000 POLICE",
        "ASIA SHARES FALL: NIKKEI -5.1%",
        "ANTHROPIC SHARES -8.5% AFTER IPO",
        "TRUMP THREATENS DATA-CENTRE TAX",
        "F1: VERSTAPPEN ON POLE IN VEGAS *",
        "U17: MOROCCO 6-0, MALI 3-0 *",
        "AFLW: NORTH MELBOURNE REACH FINAL",
        "SOMALIA EXPELS UAE ENVOY, 72 HOURS *",
        "NIGERIA BOAT: POLICE SAY 4 DEAD *",
        "GAZA STRIKE KILLS 3, WAFA SAYS",
        "IRAN OPEN TO FAIR URANIUM DEAL",
        "AUSTRALIA, CHINA AGREE AI TALKS *",
        "CHINA PRESSES JAPAN OVER TAIWAN *",
    ]
    yy = 644
    for item in more:
        draw_text(352, yy, item, 2, INK)
        yy += 17

    # Footer: date check.
    rect(0, 954, W, 70, NAVY)
    draw_text_centered(W // 2, 968, "DATE CHECK: ALL STORIES REPORTED 21 NOV 2026", 2, WHITE)
    draw_text_centered(
        W // 2, 992,
        "* = EVENT ON 20 NOV, REPORTED 21 NOV - SOURCES: REUTERS, AP, AFP, AL JAZEERA",
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
