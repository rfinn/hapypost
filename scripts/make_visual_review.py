#!/usr/bin/env python

from pathlib import Path
import re
import argparse
import pandas as pd
from PIL import Image
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


def clean_string(x):
    x = str(x)
    if x.startswith("b'") and x.endswith("'"):
        x = x[2:-1]
    return x


def get_largest_legacy_jpg(cutout_dir, tag):
    files = sorted(Path(cutout_dir).glob(f"{tag}-legacy-*.jpg"))

    def get_number(path):
        m = re.search(r"legacy-(\d+)\.jpg$", path.name)
        return int(m.group(1)) if m else -1

    return max(files, key=get_number) if files else None


def draw_image_fit(c, imgfile, x, y, w, h):
    im = Image.open(imgfile)
    iw, ih = im.size
    scale = min(w / iw, h / ih)
    dw = iw * scale
    dh = ih * scale
    c.drawImage(ImageReader(im), x + 0.5 * (w - dw), y + 0.5 * (h - dh), dw, dh)
from reportlab.lib.pagesizes import letter

# # two pages, with note
# def make_region_pdf(
#     df,
#     region,
#     outfile,
#     base_dir,
#     n_per_page=5,
# ):
#     page_w, page_h = letter
#     c = canvas.Canvas(str(outfile), pagesize=letter)

#     sub = df[df["group"] == region].sort_values("TAG").reset_index(drop=True)

#     margin = 20
#     title_h = 24
#     row_h = (page_h - 2 * margin - title_h) / n_per_page

#     img_gap = 4
#     notes_gap = 14
#     notes_w = 150

#     img_w = (page_w - 2 * margin - notes_w - notes_gap - img_gap) / 2
#     img_h = row_h - 18

#     x_legacy = margin
#     x_csgr = x_legacy + img_w + img_gap
#     x_notes = x_csgr + img_w + notes_gap

#     for start in range(0, len(sub), n_per_page):
#         page = sub.iloc[start:start + n_per_page]
#         page_num = start // n_per_page + 1

#         c.setFont("Helvetica-Bold", 15)
#         c.drawString(margin, page_h - margin, f"Region {region} - page {page_num}")

#         for local_i, (_, row) in enumerate(page.iterrows()):
#             y_top = page_h - margin - title_h - local_i * row_h
#             y_img = y_top - row_h + 5

#             tag = clean_string(row["TAG"])

#             cutout_dir = Path(base_dir) / "html" / "cutouts" / tag
#             legacy_file = get_largest_legacy_jpg(cutout_dir, tag)
#             csgr_file = cutout_dir / f"{tag}-CS-gr.png"

#             if legacy_file is not None:
#                 draw_image_fit(c, legacy_file, x_legacy, y_img, img_w, img_h)
#             else:
#                 c.setFont("Helvetica", 7)
#                 c.drawString(x_legacy, y_img + img_h / 2, "Missing legacy")

#             if csgr_file.exists():
#                 draw_image_fit(c, csgr_file, x_csgr, y_img, img_w, img_h)
#             else:
#                 c.setFont("Helvetica", 7)
#                 c.drawString(x_csgr, y_img + img_h / 2, "Missing CS-gr")

#             c.setFont("Helvetica-Bold", 7)
#             c.drawString(x_notes, y_top - 8, tag)

#             c.setFont("Helvetica", 7)
#             c.drawString(x_notes, y_top - 22, "Notes:")

#             # light note lines
#             for j in range(4):
#                 yline = y_top - 36 - 14 * j
#                 c.line(x_notes, yline, page_w - margin, yline)

#         c.showPage()

#     c.save()




def make_region_pdf(
    df,
    region,
    outfile,
    base_dir,
    n_per_page=20,
):
    page_w, page_h = letter
    c = canvas.Canvas(str(outfile), pagesize=letter)

    sub = df[df["group"] == region].sort_values("TAG").reset_index(drop=True)

    margin = 18
    title_h = 24

    ncols = 2
    nrows = 5
    tile_gap_x = 10
    tile_gap_y = 8

    tile_w = (page_w - 2 * margin - tile_gap_x) / ncols
    tile_h = (page_h - 2 * margin - title_h - (nrows - 1) * tile_gap_y) / nrows

    pair_gap = 3
    img_w = (tile_w - pair_gap) / 2
    img_h = tile_h - 14

    for start in range(0, len(sub), n_per_page):
        page = sub.iloc[start:start + n_per_page]
        page_num = start // n_per_page + 1

        c.setFont("Helvetica-Bold", 15)
        c.drawString(margin, page_h - margin, f"Region {region}")

        for local_i, (_, row) in enumerate(page.iterrows()):
            col = local_i % ncols
            rownum = local_i // ncols

            x0 = margin + col * (tile_w + tile_gap_x)
            y_top = page_h - margin - title_h - rownum * (tile_h + tile_gap_y)
            y_img = y_top - tile_h

            tag = clean_string(row["TAG"])

            c.setFont("Helvetica-Bold", 6.5)
            c.drawString(x0, y_top - 7, tag)

            cutout_dir = Path(base_dir) / "html" / "cutouts" / tag
            legacy_file = get_largest_legacy_jpg(cutout_dir, tag)
            csgr_file = cutout_dir / f"{tag}-CS-gr.png"

            if legacy_file is not None:
                draw_image_fit(c, legacy_file, x0, y_img, img_w, img_h)
            else:
                c.setFont("Helvetica", 6)
                c.drawString(x0, y_img + img_h / 2, "Missing legacy")

            if csgr_file.exists():
                draw_image_fit(c, csgr_file, x0 + img_w + pair_gap, y_img, img_w, img_h)
            else:
                c.setFont("Helvetica", 6)
                c.drawString(x0 + img_w + pair_gap, y_img + img_h / 2, "Missing CS-gr")

        c.showPage()

    c.save()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("csvfile")
    parser.add_argument("--base-dir", default="/data-pool/Halpha/hapy-output-20260620")
    parser.add_argument("--outdir", default="visual_review_pdfs")
    parser.add_argument("--group-column", default="umap_region")
    parser.add_argument("--n-per-page", type=int, default=5)
    args = parser.parse_args()

    df = pd.read_csv(args.csvfile)

    for col in ["VFID", "objname", "TAG", args.group_column]:
        if col in df.columns:
            df[col] = df[col].apply(clean_string)

    df = df.rename(columns={args.group_column: "group"})

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    for region in sorted(df["group"].unique()):
        outfile = outdir / f"Region_{region}.pdf"
        make_region_pdf(
            df,
            region,
            outfile,
            base_dir=args.base_dir,
            n_per_page=args.n_per_page,
        )
        print(f"Wrote {outfile}")


if __name__ == "__main__":
    main()
