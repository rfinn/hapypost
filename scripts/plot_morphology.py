from hapypost.io.vfs_tables import VTables
# from hapypost.plotting.morphology import (
#     science_ready_mask,
#     plot_size_mass_relation,
#     plot_size_ratio_mass,
#     plot_gini_comparison,
#     plot_delta_gini_m20,
# )
import argparse
import os


"""
Reusable morphology plotting functions for HAPY/VFS first-look science plots.
"""

from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

from hapypost.plotting.common import _as_float_array, _get_col, _finish_figure





def plot_size_mass_relation(
    v,
    plotdir,
    outfile_root="size_mass_halpha_r",
    selection=None,
    mass_col="bayes.stellar.m_star",
    r_size_col=None,
    h_size_col=None,
    size_label=r"$R_{75}$",
    size_units="arcsec",
    log_y=True,
    show=False,
    
):
    """
    Plot r-band and Halpha size versus stellar mass.

    Parameters
    ----------
    v : VTables
        VFS table container.
    plotdir : str or Path
        Output directory.
    selection : array-like, optional
        Boolean mask. If None, uses science_ready_mask(v).
    r_size_col, h_size_col : str, optional
        Size columns in v.halpha. If None, tries common candidates.
    """

    plotdir = Path(plotdir)

    h = v.halpha

    if selection is None:
        selection = science_ready_mask(v)

    if r_size_col is None:
        r_size_col = get_rsize(h)

    if h_size_col is None:
        h_size_col = get_hsize(h)

    x = np.log10(_as_float_array(v.cigale, mass_col))
    r_size = _as_float_array(h, r_size_col)
    h_size = _as_float_array(h, h_size_col)

    sel = (
        selection
        & np.isfinite(x)
        & np.isfinite(r_size)
        & np.isfinite(h_size)
        & (r_size > 0)
        & (h_size > 0)
    )
    yvar = [r_size, h_size]
    ylabels = [r"$r$ band",r"H$\alpha$"]
    fig = plt.figure(figsize=(10, 5))
    allax = []

    for i,y in enumerate(yvar):
        plt.subplot(1,2,i+1)
        plt.scatter(
            x[sel],
            yvar[i][sel],
            marker="o",
            alpha=0.55,
            s=20,
            label=ylabels[i],
        )
        ax = plt.gca()
        allax.append(plt.gca())
   
        m = 0.33
        b = -1.6

        xline = np.linspace(6.5,12,100)
        yline =10**(m*xline + b)
        plt.plot(xline,yline,'k-')
        sigma=.20
        plt.fill_between(xline,yline*10**sigma,y2=yline*10**(-sigma),alpha=.3,color='0.5')

        if log_y:
            plt.gca().set_yscale("log")

        ax.set_xlabel(r"$\log(M_\star/M_\odot)$", fontsize=16)
        ax.set_ylabel(f"{size_label} ({size_units})", fontsize=16)
        ax.tick_params(labelsize=14)

        ax.legend(
            fontsize=12,
            frameon=True,
            framealpha=0.5,
            facecolor="white",
            edgecolor="0.5",
            )
        plt.axis([6.5,12,.8,150])

    #ax.set_title(r"Sizes of stellar and H$\alpha$ light", fontsize=16)

    _finish_figure(
        fig,
        plotdir / outfile_root,
        show=show,
    )


def plot_size_ratio_mass(
    v,
    plotdir,
    outfile_root="size_ratio_mass_halpha_r",
    selection=None,
    mass_col="bayes.stellar.m_star",
    r_size_col=None,
    h_size_col=None,
    ratio_label=r"$R_{50}({\rm H}\alpha)/R_{50}(r)$",
    show=False,
):
    """
    Plot Halpha-to-r size ratio versus stellar mass.
    """

    plotdir = Path(plotdir)
    h = v.halpha

    if selection is None:
        selection = science_ready_mask(v)
    if r_size_col is None:
        r_size_col = get_rsize(h)

    if h_size_col is None:
        h_size_col = get_hsize(h)


    x = _as_float_array(v.cigale, mass_col)
    r_size = _as_float_array(h, r_size_col)
    h_size = _as_float_array(h, h_size_col)

    ratio = h_size / r_size

    sel = (
        selection
        & np.isfinite(x)
        & np.isfinite(ratio)
        & (ratio > 0)
        & (ratio < 5)
    )

    fig, ax = plt.subplots(figsize=(8, 6))

    ax.axhline(1, color="0.4", ls="--", lw=1.5)

    ax.plot(
        x[sel],
        ratio[sel],
        "o",
        alpha=0.7,
        markersize=6,
    )

    ax.set_xlabel(r"$\log(M_\star/M_\odot)$", fontsize=16)
    ax.set_ylabel(ratio_label, fontsize=16)
    ax.tick_params(labelsize=14)
    ax.set_ylim(0, min(3, 1.1 * np.nanmax(ratio[sel])))

    ax.set_title(r"Relative extent of H$\alpha$ emission", fontsize=16)

    _finish_figure(
        fig,
        plotdir / outfile_root,
        show=show,
    )


def plot_gini_comparison(
    v,
    plotdir,
    outfile_root="gini_halpha_vs_r",
    selection=None,
    r_gini_col="R_HAPY_GINI",
    h_gini_col="H_HAPY_GINI",
    color_by_size_ratio=True,
    r_size_col=None,
    h_size_col=None,
    show=False,
):
    """
    Plot Gini(Halpha) versus Gini(r), with a 1:1 line.
    """

    plotdir = Path(plotdir)
    h = v.halpha

    if selection is None:
        selection = science_ready_mask(v, require_morph_ok=True)

    r_gini = _as_float_array(h, r_gini_col)
    h_gini = _as_float_array(h, h_gini_col)

    sel = (
        selection
        & np.isfinite(r_gini)
        & np.isfinite(h_gini)
        & (r_gini >= 0)
        & (h_gini >= 0)
    )

    color = None
    if color_by_size_ratio:
        if r_size_col is None:
            r_size_col = get_rsize(h)

        if h_size_col is None:
            h_size_col = get_hsize(h)


        ratio = _as_float_array(h, h_size_col) / _as_float_array(h, r_size_col)
        sel &= np.isfinite(ratio) & (ratio > 0) & (ratio < 5)
        color = ratio

    fig, ax = plt.subplots(figsize=(7, 6))

    if color_by_size_ratio and color is not None:
        sc = ax.scatter(
            r_gini[sel],
            h_gini[sel],
            c=color[sel],
            vmin=0.5,
            vmax=1.8,
            s=35,
            alpha=0.75,
        )
        cbar = fig.colorbar(sc, ax=ax)
        cbar.set_label(r"$R_{50}({\rm H}\alpha)/R_{50}(r)$", fontsize=14)
        cbar.ax.tick_params(labelsize=12)
    else:
        ax.plot(r_gini[sel], h_gini[sel], "o", alpha=0.7, markersize=6)

    lim = [
        min(np.nanmin(r_gini[sel]), np.nanmin(h_gini[sel])) - 0.03,
        max(np.nanmax(r_gini[sel]), np.nanmax(h_gini[sel])) + 0.03,
    ]

    ax.plot(lim, lim, "--", color="0.4", lw=1.5)

    ax.set_xlim(lim)
    ax.set_ylim(lim)

    ax.set_xlabel(r"$G(r)$", fontsize=16)
    ax.set_ylabel(r"$G({\rm H}\alpha)$", fontsize=16)
    ax.tick_params(labelsize=14)

    ax.set_title(r"Gini of H$\alpha$ versus stellar light", fontsize=16)

    _finish_figure(
        fig,
        plotdir / outfile_root,
        show=show,
    )


def plot_delta_gini_m20(
    v,
    plotdir,
    outfile_root="delta_gini_delta_m20",
    selection=None,
    r_gini_col="R_HAPY_GINI",
    h_gini_col="H_HAPY_GINI",
    r_m20_col="R_HAPY_M20",
    h_m20_col="H_HAPY_M20",
    show=False,
):
    """
    Plot Delta Gini and Delta M20 between Halpha and r band.

    Delta = Halpha - r.
    """

    plotdir = Path(plotdir)
    h = v.halpha

    if selection is None:
        selection = science_ready_mask(v, require_morph_ok=True)

    r_gini = _as_float_array(h, r_gini_col)
    h_gini = _as_float_array(h, h_gini_col)
    r_m20 = _as_float_array(h, r_m20_col)
    h_m20 = _as_float_array(h, h_m20_col)

    dgini = h_gini - r_gini
    dm20 = h_m20 - r_m20

    sel = (
        selection
        & np.isfinite(dgini)
        & np.isfinite(dm20)
    )

    fig, ax = plt.subplots(figsize=(7, 6))

    ax.axhline(0, color="0.5", lw=1)
    ax.axvline(0, color="0.5", lw=1)

    ax.plot(
        dm20[sel],
        dgini[sel],
        "o",
        alpha=0.7,
        markersize=6,
    )

    ax.set_xlabel(r"$\Delta M_{20} = M_{20}({\rm H}\alpha) - M_{20}(r)$", fontsize=16)
    ax.set_ylabel(r"$\Delta G = G({\rm H}\alpha) - G(r)$", fontsize=16)
    ax.tick_params(labelsize=14)

    ax.text(
        0.97,
        0.95,
        "uneven + off-center\nbright Hα regions",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=12,
    )

    ax.set_title(r"H$\alpha$ morphology relative to stellar morphology", fontsize=16)

    _finish_figure(
        fig,
        plotdir / outfile_root,
        show=show,
    )


def parse_args():
    parser = argparse.ArgumentParser(
        description="Make sample overview plots for the Virgo Halpha survey"
    )
    parser.add_argument(
        "--tabledir",
        default="/home/rfinn/research/Virgo/tables-north/v2/",
        help="Directory where VFS tables are stored",
    )
    parser.add_argument(
        "--tableprefix",
        default="vf_v2_",
        help="Prefix for VFS tables",
    )
    parser.add_argument(
        "--plotdir",
        default="plots/sample_overview",
        help="Output directory for plots",
    )
    return parser.parse_args()


def fix_homedir(path):
    if path.startswith("/home/rfinn/"):
        return path.replace("/home/rfinn", os.getenv("HOME"))
    return path


def main():
    args = parse_args()

    tabledir = fix_homedir(args.tabledir)

    print(f"table directory = {tabledir}")

    v = VTables(tabledir, args.tableprefix)
    v.read_all()

    #plot_halpha_sky_positions(v, args.plotdir)
    return v, args

if __name__ == "__main__":
    v, args = main()
    

