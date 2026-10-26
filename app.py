from io import BytesIO

import pandas as pd
import streamlit as st
from PIL import Image

from ladder import COLUMN_NAMES, DEFAULT_CSV, DEFAULT_TEMPLATE, clean_ladder, render_ladder, sort_ladder

st.set_page_config(page_title="Ladder Graphic Maker", page_icon="⚽", layout="wide")
st.title("⚽ Ladder Graphic Maker")
st.write("Upload your ladder and background, fix any numbers in the table, then download your graphic.")

left, right = st.columns([1, 1])

with left:
    st.subheader("1. Choose your files")
    csv_file = st.file_uploader("Ladder spreadsheet (CSV)", type="csv")
    template_file = st.file_uploader("Background image (PNG/JPG)", type=["png", "jpg", "jpeg"])
    st.caption("Leave these empty to use the sample Bubble Soccer WA - DIV 1 files.")

    ladder = pd.read_csv(csv_file if csv_file else DEFAULT_CSV)
    template = Image.open(template_file if template_file else DEFAULT_TEMPLATE)

    missing = [c for c in COLUMN_NAMES if c not in ladder.columns]
    if missing:
        st.error(f"Your spreadsheet is missing these columns: {', '.join(missing)}")
        st.stop()

    st.subheader("2. Check the ladder")
    st.caption("Click any cell to edit it. Changes show up in the preview straight away.")
    ladder = st.data_editor(
        ladder[COLUMN_NAMES],
        hide_index=True,
        num_rows="dynamic",
        width="stretch",
        column_config={
            "index": "Pos", "teamname": "Team", "p": "Played", "w": "Won",
            "d": "Drawn", "l": "Lost", "gd": "Goal Diff", "pts": "Points",
        },
    )
    sort_by_points = st.checkbox("Sort by points (then goal difference)", value=False)
    bold_points = st.checkbox("Bold points column", value=True)

ladder = clean_ladder(ladder)
if sort_by_points:
    ladder = sort_ladder(ladder)

graphic = render_ladder(ladder, template, bold_points)

with right:
    st.subheader("3. Preview & download")
    st.image(graphic, width="stretch")
    buffer = BytesIO()
    graphic.save(buffer, format="PNG")
    st.download_button(
        "⬇️ Download graphic",
        data=buffer.getvalue(),
        file_name="ladder_graphic.png",
        mime="image/png",
        type="primary",
        width="stretch",
    )
