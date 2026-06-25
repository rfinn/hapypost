#!/usr/bin/env python

from pathlib import Path
import re
import argparse
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


def decode_vfid(x):
    if isinstance(x, bytes):
        return x.decode("utf-8")
    x = str(x)
    if x.startswith("b'") and x.endswith("'"):
        x = x[2:-1]
    return x


def find_cutout_dir(base_dir, vfid, tag=None):
    cutout_root = Path(base_dir) / "html" / "cutouts"

    if tag is not None and str(tag) != "nan":
        d = cutout_root / str(tag)
        if d.exists():
            return d

    matches = sorted(cutout_root.glob(f"{vfid}-*"))
    if len(matches) == 0:
        return None

    return matches[0]


def get_largest_legacy_jpg(cutout_dir, tag):
    files = sorted(cutout_dir.glob(f"{tag}-legacy-*.jpg"))

    if len(files) == 0:
        return None

    def get_number(path):
        m = re.search(r"legacy-(\d+)\.jpg$", path.name)
        return int(m.group(1)) if m else -1

    return max(files, key=get_number)


def make_pair_image(
    legacy_file,
    csgr_file,
    outfile,
    title,
    width_each=500,
    pad=20,
    title_height=45,
):
    im1 = Image.open(legacy_file).convert("RGB")
    im2 = Image.open(csgr_file).convert("RGB")

    # Resize to common width
    im1 = im1.resize((width_each, int(im1.height * width_each / im1.width)))
    im2 = im2.resize((width_each, int(im2.height * width_each / im2.width)))

    h = max(im1.height, im2.height)
    w = 2 * width_each + 3 * pad

    canvas_img = Image.new("RGB", (w, h + title_height + 2 * pad), "white")
    draw = ImageDraw.Draw(canvas_img)

    try:
        font_title = ImageFont.truetype("DejaVuSans.ttf", 28)
        font_label = ImageFont.truetype("DejaVuSans.ttf", 18)
    except Exception:
        font_title = None
        font_label = None

    draw.text((w / 2, pad), title, fill="black", anchor="mm", font=font_title)

    y0 = pad + title_height
    x1 = pad
    x2 = 2 * pad + width_each

    draw.text((x1 + width_each / 2, y0 - 10), "Legacy RGB", fill="black", anchor="mm", font=font_label)
    draw.text((x2 + width_each / 2, y0 - 10), "CS-gr Hα", fill="black", anchor="mm", font=font_label)

    canvas_img.paste(im1, (x1, y0))
    canvas_img.paste(im2, (x2, y0))

    outfile.parent.mkdir(parents=True, exist_ok=True)
    canvas_img.save(outfile)

    return outfile


def make_pdf(image_files, pdf_file):
    page_w, page_h = landscape(letter)
    c = canvas.Canvas(str(pdf_file), pagesize=landscape(letter))

    for imgfile in image_files:
        im = Image.open(imgfile)
        iw, ih = im.size

        scale = min(page_w / iw, page_h / ih)
        draw_w = iw * scale
        draw_h = ih * scale

        x = 0.5 * (page_w - draw_w)
        y = 0.5 * (page_h - draw_h)

        c.drawImage(ImageReader(im), x, y, width=draw_w, height=draw_h)
        c.showPage()

    c.save()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("csvfile", help="CSV from selected_umap")
    parser.add_argument(
        "--base-dir",
        default="/data-pool/Halpha/hapy-output-20260620",
        help="Base HAPY output directory",
    )
    parser.add_argument(
        "--outdir",
        default="umap_region_inspection",
        help="Output directory",
    )
    parser.add_argument(
        "--region-col",
        default="umap_region",
        help="Column with UMAP region labels",
    )
    parser.add_argument(
        "--tag-col",
        default="TAG",
        help="Optional column containing cutout TAG",
    )
    args = parser.parse_args()

    df = pd.read_csv(args.csvfile)
    df["VFID"] = df["VFID"].apply(decode_vfid)

    outdir = Path(args.outdir)
    pair_dir = outdir / "pairs"
    outdir.mkdir(parents=True, exist_ok=True)

    all_pair_images = []

    for region in sorted(df[args.region_col].unique()):
        sub = df[df[args.region_col] == region].copy()
        sub = sub.sort_values("VFID")

        region_images = []

        for _, row in sub.iterrows():
            vfid = row["VFID"]
            objname = row.get("objname", "")
            tag = row[args.tag_col] if args.tag_col is not None and args.tag_col in row else None

            cutout_dir = find_cutout_dir(args.base_dir, vfid, tag=tag)

            if cutout_dir is None:
                print(f"WARNING: no cutout directory found for {vfid}")
                continue

            tag = cutout_dir.name

            csgr_file = cutout_dir / f"{tag}-CS-gr.png"
            legacy_file = get_largest_legacy_jpg(cutout_dir, tag)

            if not csgr_file.exists():
                print(f"WARNING: missing CS-gr png for {tag}")
                continue

            if legacy_file is None:
                print(f"WARNING: missing legacy jpg for {tag}")
                continue

            title = f"Region {region}  {vfid}  {objname}"
            pair_file = pair_dir / f"Region_{region}_{vfid}_{tag}.png"

            make_pair_image(
                legacy_file,
                csgr_file,
                pair_file,
                title=title,
            )

            region_images.append(pair_file)
            all_pair_images.append(pair_file)

        if len(region_images) > 0:
            make_pdf(
                region_images,
                outdir / f"Region_{region}_inspection.pdf",
            )

    if len(all_pair_images) > 0:
        make_pdf(
            all_pair_images,
            outdir / "All_regions_inspection.pdf",
        )

    print(f"Done. Output written to {outdir}")


if __name__ == "__main__":
    main()
