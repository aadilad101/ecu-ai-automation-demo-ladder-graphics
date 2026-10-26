"""Draw a league ladder onto a 1080x1080 social media template."""

from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).parent
DEFAULT_CSV = BASE_DIR / "data" / "div1_ladder.csv"
DEFAULT_TEMPLATE = BASE_DIR / "assets" / "template_div1.png"

# Poppins is bundled so the graphic looks the same on every machine
FONTS_DIR = BASE_DIR / "assets" / "fonts"
REGULAR_FONT = FONTS_DIR / "Poppins-Medium.ttf"
BOLD_FONT = FONTS_DIR / "Poppins-ExtraBold.ttf"

WHITE = (255, 255, 255, 255)
ROW_STRIPE = (255, 255, 255, 28)
HEADER_BG = (255, 255, 255, 55)
PTS_BG = (255, 255, 255, 40)

# Table area sits below the template title (which ends at y=100)
CANVAS_SIZE = 1080
TABLE_LEFT, TABLE_RIGHT = 60, 1020
TABLE_TOP = 150
TABLE_MAX_BOTTOM = 1060
HEADER_HEIGHT = 70
ROW_HEIGHT = 80

# (label, csv column, x centre or left edge, alignment)
COLUMNS = [
    ("#", "index", 105, "center"),
    ("TEAM", "teamname", 160, "left"),
    ("P", "p", 590, "center"),
    ("W", "w", 660, "center"),
    ("D", "d", 730, "center"),
    ("L", "l", 800, "center"),
    ("GD", "gd", 875, "center"),
    ("PTS", "pts", 965, "center"),
]
COLUMN_NAMES = [column for _, column, _, _ in COLUMNS]
NUMERIC_COLUMNS = [c for c in COLUMN_NAMES if c != "teamname"]
PTS_COL_LEFT = 915


def load_font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size)


def clean_ladder(ladder: pd.DataFrame) -> pd.DataFrame:
    """Drop rows with no team and make every stat a whole number (blanks become 0)."""
    ladder = ladder[COLUMN_NAMES].dropna(subset=["teamname"]).reset_index(drop=True)
    for column in NUMERIC_COLUMNS:
        ladder[column] = pd.to_numeric(ladder[column], errors="coerce").fillna(0).astype(int)
    return ladder


def sort_ladder(ladder: pd.DataFrame) -> pd.DataFrame:
    """Order by points, then goal difference, and renumber the positions."""
    ladder = ladder.sort_values(["pts", "gd"], ascending=False).reset_index(drop=True)
    ladder["index"] = range(1, len(ladder) + 1)
    return ladder


def format_value(column: str, value) -> str:
    if column == "gd" and value > 0:
        return f"+{value}"
    return str(value)


def render_ladder(ladder: pd.DataFrame, template: Image.Image, bold_points: bool = True) -> Image.Image:
    """Return the template with the ladder table drawn over it."""
    base = template.convert("RGBA").resize((CANVAS_SIZE, CANVAS_SIZE))
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Rows shrink to fit if there are more than 10 teams
    row_height = min(ROW_HEIGHT, (TABLE_MAX_BOTTOM - TABLE_TOP - HEADER_HEIGHT) // max(len(ladder), 1))
    scale = row_height / ROW_HEIGHT
    header_font = load_font(BOLD_FONT, 30)
    body_font = load_font(REGULAR_FONT, int(34 * scale))
    points_font = load_font(BOLD_FONT if bold_points else REGULAR_FONT, int((38 if bold_points else 34) * scale))

    header_bottom = TABLE_TOP + HEADER_HEIGHT
    table_bottom = header_bottom + row_height * len(ladder)

    draw.rounded_rectangle((TABLE_LEFT, TABLE_TOP, TABLE_RIGHT, header_bottom), radius=14, fill=HEADER_BG)
    draw.rectangle((PTS_COL_LEFT, header_bottom, TABLE_RIGHT, table_bottom), fill=PTS_BG)

    for label, _, x, align in COLUMNS:
        anchor = "mm" if align == "center" else "lm"
        draw.text((x, TABLE_TOP + HEADER_HEIGHT / 2), label, font=header_font, fill=WHITE, anchor=anchor)

    for i, row in enumerate(ladder.itertuples(index=False)):
        top = header_bottom + i * row_height
        if i % 2 == 0:
            draw.rectangle((TABLE_LEFT, top, TABLE_RIGHT, top + row_height), fill=ROW_STRIPE)
        for _, column, x, align in COLUMNS:
            anchor = "mm" if align == "center" else "lm"
            font = points_font if column == "pts" else body_font
            value = format_value(column, getattr(row, column))
            draw.text((x, top + row_height / 2), value, font=font, fill=WHITE, anchor=anchor)

    return Image.alpha_composite(base, overlay).convert("RGB")
