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

def make_region_pdf(
    df,
    region,
    outfile,
    base_dir,
    n_per_page=5,
):
    page_w, page_h = letter
    c = canvas.Canvas(str(outfile), pagesize=letter)

    sub = df[df["group"] == region].sort_values("TAG").reset_index(drop=True)

    margin = 24
    title_h = 28
    row_h = (page_h - 2 * margin - title_h) / n_per_page

    gap = 10
    img_w = (page_w - 2 * margin - gap) / 2
    img_h = row_h - 24

    x_legacy = margin
    x_csgr = margin + img_w + gap

    for start in range(0, len(sub), n_per_page):
        page = sub.iloc[start:start + n_per_page]
        page_num = start // n_per_page + 1

        c.setFont("Helvetica-Bold", 16)
        c.drawString(margin, page_h - margin, f"Region {region} - page {page_num}")

        for local_i, (_, row) in enumerate(page.iterrows()):
            y_top = page_h - margin - title_h - local_i * row_h
            y_img = y_top - row_h + 6

            tag = clean_string(row["TAG"])

            c.setFont("Helvetica-Bold", 8)
            c.drawString(margin, y_top - 9, tag)

            cutout_dir = Path(base_dir) / "html" / "cutouts" / tag
            legacy_file = get_largest_legacy_jpg(cutout_dir, tag)
            csgr_file = cutout_dir / f"{tag}-CS-gr.png"

            if legacy_file is not None:
                draw_image_fit(c, legacy_file, x_legacy, y_img, img_w, img_h)
            else:
                c.setFont("Helvetica", 8)
                c.drawString(x_legacy, y_img + img_h / 2, "Missing legacy image")

            if csgr_file.exists():
                draw_image_fit(c, csgr_file, x_csgr, y_img, img_w, img_h)
            else:
                c.setFont("Helvetica", 8)
                c.drawString(x_csgr, y_img + img_h / 2, "Missing CS-gr image")

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
