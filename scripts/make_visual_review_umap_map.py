#!/usr/bin/env python

from pathlib import Path
import re
import argparse
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image, ImageOps, ImageDraw
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

import matplotlib.pyplot as plt


import matplotlib.pyplot as plt
from PIL import Image, ImageOps

# use the default matplotlib color cycle
colors = plt.rcParams['axes.prop_cycle'].by_key()['color']

REGION_COLORS = {
    "A": colors[0],
    "B": colors[1],
    "C": colors[2],
    "D": colors[3],
    "E": colors[4],
    "F": colors[5],
    "G": colors[6],
    "H": colors[7],
    "I": colors[8],
}


def make_single_thumbnail(
    image_file,
    region,
    thumb_h=80,
    border=2,
):
    """
    Create a thumbnail with a colored border corresponding
    to the UMAP region.
    """

    im = Image.open(image_file).convert("RGB")
    im = im.resize((int(im.width * thumb_h / im.height), thumb_h))

    border_color = REGION_COLORS.get(region, "black")

    im = ImageOps.expand(
        im,
        border=border,
        fill=border_color,
    )

    return im



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


def make_pair_thumbnail(
    legacy_file,
    csgr_file,
    tag=None,
    thumb_h=90,
    gap=4,
    border=3,
):
    im1 = Image.open(legacy_file).convert("RGB")
    im2 = Image.open(csgr_file).convert("RGB")

    # resize both to same height
    im1 = im1.resize((int(im1.width * thumb_h / im1.height), thumb_h))
    im2 = im2.resize((int(im2.width * thumb_h / im2.height), thumb_h))

    w = im1.width + im2.width + gap
    h = thumb_h

    pair = Image.new("RGB", (w, h), "white")
    pair.paste(im1, (0, 0))
    pair.paste(im2, (im1.width + gap, 0))

    # add border around pair
    pair = ImageOps.expand(pair, border=border, fill="black")

    return pair


def plot_cutouts_in_umap_space(
    csvfile,
    base_dir="/data-pool/Halpha/hapy-output-20260620",
    outfile="umap_cutouts_legacy_csgr.png",
    group_col="umap_region",
    tag_col="TAG",
    xcol="UMAP1",
    ycol="UMAP2",
    thumb_h=80,
    zoom=0.55,
    figsize=(16, 10),
    dpi=200,
):
    df = pd.read_csv(csvfile)

    for col in [tag_col, group_col]:
        if col in df.columns:
            df[col] = df[col].apply(clean_string)

    fig, ax = plt.subplots(figsize=figsize)

    # faint background points
    ax.scatter(
        df[xcol],
        df[ycol],
        s=12,
        color="0.75",
        alpha=0.35,
        zorder=1,
    )

    base_dir = Path(base_dir)

    for _, row in df.iterrows():
        tag = clean_string(row[tag_col])
        x = row[xcol]
        y = row[ycol]

        cutout_dir = base_dir / "html" / "cutouts" / tag
        legacy_file = get_largest_legacy_jpg(cutout_dir, tag)
        csgr_file = cutout_dir / f"{tag}-CS-gr.png"

        if legacy_file is None or not csgr_file.exists():
            print(f"Skipping {tag}: missing legacy or CS-gr")
            continue

        pair = make_pair_thumbnail(
            legacy_file,
            csgr_file,
            tag=tag,
            thumb_h=thumb_h,
        )

        imagebox = OffsetImage(pair, zoom=zoom)

        ab = AnnotationBbox(
            imagebox,
            (x, y),
            frameon=False,
            pad=0.0,
            zorder=3,
        )

        ax.add_artist(ab)

    ax.set_xlabel("UMAP1", fontsize=16)
    ax.set_ylabel("UMAP2", fontsize=16)
    ax.set_title("Representative galaxies in UMAP morphology space", fontsize=18)

    dx = 0.08 * (df[xcol].max() - df[xcol].min())
    dy = 0.08 * (df[ycol].max() - df[ycol].min())

    ax.set_xlim(df[xcol].min() - dx, df[xcol].max() + dx)
    ax.set_ylim(df[ycol].min() - dy, df[ycol].max() + dy)

    ax.tick_params(labelsize=12)

    fig.tight_layout()
    fig.savefig(outfile, dpi=dpi, bbox_inches="tight")
    print(f"Wrote {outfile}")

    plt.show()

def plot_cutouts_in_umap_space_single(
    csvfile,
    base_dir="/data-pool/Halpha/hapy-output-20260620",
    outfile="umap_cutouts.png",
    image_type="legacy",   # "legacy" or "csgr"
    group_col="umap_region",
    tag_col="TAG",
    xcol="UMAP1",
    ycol="UMAP2",
    thumb_h=85,
    zoom=0.65,
    figsize=(16, 10),
    dpi=200,
):
    df = pd.read_csv(csvfile)

    for col in [tag_col, group_col]:
        if col in df.columns:
            df[col] = df[col].apply(clean_string)

    fig, ax = plt.subplots(figsize=figsize)

    ax.scatter(
        df[xcol],
        df[ycol],
        s=14,
        color="0.75",
        alpha=0.35,
        zorder=1,
    )

    base_dir = Path(base_dir)

    for _, row in df.iterrows():
        tag = clean_string(row[tag_col])
        x = row[xcol]
        y = row[ycol]

        cutout_dir = base_dir / "html" / "cutouts" / tag

        if image_type == "legacy":
            image_file = get_largest_legacy_jpg(cutout_dir, tag)
        elif image_type == "csgr":
            image_file = cutout_dir / f"{tag}-CS-gr.png"
        else:
            raise ValueError("image_type must be 'legacy' or 'csgr'")

        if image_file is None or not Path(image_file).exists():
            print(f"Skipping {tag}: missing {image_type}")
            continue
        region = row["umap_region"]

        thumb = make_single_thumbnail(
            image_file,
            region=region,
            thumb_h=thumb_h,
            )
        # thumb = make_single_thumbnail(
        #     image_file,
        #     thumb_h=thumb_h,
        # )

        imagebox = OffsetImage(thumb, zoom=zoom)

        ab = AnnotationBbox(
            imagebox,
            (x, y),
            frameon=False,
            pad=0.0,
            zorder=3,
        )

        ax.add_artist(ab)

    ax.set_xlabel("UMAP1", fontsize=16)
    ax.set_ylabel("UMAP2", fontsize=16)

    title = "Legacy cutouts in UMAP space" if image_type == "legacy" else "CS-gr Hα cutouts in UMAP space"
    ax.set_title(title, fontsize=18)

    dx = 0.08 * (df[xcol].max() - df[xcol].min())
    dy = 0.08 * (df[ycol].max() - df[ycol].min())

    ax.set_xlim(df[xcol].min() - dx, df[xcol].max() + dx)
    ax.set_ylim(df[ycol].min() - dy, df[ycol].max() + dy)

    ax.tick_params(labelsize=12)

    fig.tight_layout()
    fig.savefig(outfile, dpi=dpi, bbox_inches="tight")
    print(f"Wrote {outfile}")

    plt.close(fig)

    
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("csvfile")
    parser.add_argument("--base-dir", default="/data-pool/Halpha/hapy-output-20260620")
    parser.add_argument("--outfile", default="umap_cutouts_legacy_csgr.png")
    parser.add_argument("--thumb-h", type=int, default=80)
    parser.add_argument("--zoom", type=float, default=0.55)
    args = parser.parse_args()

    # plot_cutouts_in_umap_space(
    #     args.csvfile,
    #     base_dir=args.base_dir,
    #     outfile=args.outfile,
    #     thumb_h=args.thumb_h,
    #     zoom=args.zoom,
    # )

    plot_cutouts_in_umap_space_single(
        "umap_region_spread5_input.csv",
        image_type="legacy",
        outfile="umap_legacy_cutouts.png",
        thumb_h=90,
        zoom=0.65,
        )

    plot_cutouts_in_umap_space_single(
        "umap_region_spread5_input.csv",
        image_type="csgr",
        outfile="umap_csgr_cutouts.png",
        thumb_h=90,
        zoom=0.65,
        )


if __name__ == "__main__":
    main()
