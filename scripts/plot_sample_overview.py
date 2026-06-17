from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

from hapypost.plotting.environment import plot_spines, mycolors

from hapypost.io.vfs_tables import VTables

def plot_halpha_sky_positions(
    v,
    plotdir,
    haobs_key="HAPY_HAS_OBS",
    outfile_root="halpha_positions",
):
    """
    Plot Virgo Filament Catalog sky positions, highlighting Halpha and CO coverage.
    """

    plotdir = Path(plotdir)
    plotdir.mkdir(parents=True, exist_ok=True)

    ra = v.main["RA"]
    dec = v.main["DEC"]

    has_ha = v.halpha[haobs_key]
    has_co = v.main["COflag"]

    fig, ax = plt.subplots(figsize=(12, 6))
    fig.subplots_adjust(right=0.8)

    plot_spines()

    ax.plot(
        ra,
        dec,
        "k.",
        alpha=0.1,
        label="Virgo Filament Catalog",
    )

    flag = has_ha & ~has_co
    ax.plot(
        ra[flag],
        dec[flag],
        "bo",
        alpha=0.5,
        markersize=8,
        label=r"H$\alpha$",
    )

    flag = has_co & ~has_ha
    ax.plot(
        ra[flag],
        dec[flag],
        "o",
        color="purple",
        markersize=8,
        alpha=0.7,
        mec="0.5",
        label=r"CO, No H$\alpha$",
    )
    # print out these galaxies
    vfids = v.main['VFID'][flag]
    print("CO galaxies with no Halpha")
    
    for vfid in vfids:
        print(vfid)
    flag = has_co & has_ha
    ax.plot(
        ra[flag],
        dec[flag],
        "co",
        markersize=8,
        alpha=0.7,
        mec="0.5",
        label=r"CO + H$\alpha$",
    )

    ax.invert_xaxis()
    ax.set_xlabel("RA (deg)", fontsize=20)
    ax.set_ylabel("DEC (deg)", fontsize=20)
    ax.tick_params(labelsize=14)
    ax.set_title(
        "Filamentary Structures Surrounding the Virgo Cluster",
        fontsize=18,
    )

    ax.legend(bbox_to_anchor=(1.01, 1), loc="upper left")

    fig.savefig(plotdir / f"{outfile_root}.png", dpi=200, bbox_inches="tight")
    fig.savefig(plotdir / f"{outfile_root}.pdf", bbox_inches="tight")
    #plt.close(fig)

    

def plot_sfr_mstar_sample(
    v,
    plotdir,
    outfile_root="sfr-mstar-halpha",
    haobs_key="HAPY_HAS_OBS",
):
    """
    Plot SFR--stellar mass plane, highlighting Halpha and CO samples.
    """

    plotdir = Path(plotdir)
    plotdir.mkdir(parents=True, exist_ok=True)

    x = np.log10(np.array(v.cigale['bayes.stellar.m_star'], dtype=float))
    y = np.log10(np.array(v.cigale['bayes.sfh.sfr'], dtype=float))

    has_valid_mass = x > 7
    has_ha = np.array(v.halpha[haobs_key]).astype(bool)
    has_co = np.array(v.main["COflag"]).astype(bool)

    flag_all = has_valid_mass & ~has_ha & ~has_co
    flag_ha = has_valid_mass & has_ha
    flag_co = has_valid_mass & has_co

    fig, ax = plt.subplots(figsize=(8, 6))

    ax.plot(
        x[flag_all],
        y[flag_all],
        "k.",
        alpha=0.1,
        label=r"All VFS $\rm \log_{10}(M_\star/M_\odot) > 7$",
    )

    ax.plot(
        x[flag_ha],
        y[flag_ha],
        "s",
        color=mycolors[0],
        mec="k",
        alpha=0.7,
        label=r"Observed H$\alpha$ Sample",
        markersize=9,
    )

    ax.plot(
        x[flag_co],
        y[flag_co],
        "o",
        color=mycolors[1],
        alpha=0.8,
        label="Primary CO Sample",
        markersize=5,
    )

    ax.set_xlabel(r"$\rm \log(M_\star/M_\odot)$", fontsize=16)
    ax.set_ylabel(r"$\rm \log({\rm SFR}/M_\odot\,{\rm yr}^{-1})$", fontsize=16)

    ax.set_xlim(6.9, 11.1)
    ax.tick_params(labelsize=14)
    #ax.legend(frameon=False)
    #ax.legend(frameon=True, fontsize=14)
    ax.legend(
    fontsize=12,
    frameon=True,
    framealpha=0.5,
    facecolor='white',
    edgecolor='0.5',
    )

    fig.savefig(plotdir / f"{outfile_root}.png", dpi=200, bbox_inches="tight")
    fig.savefig(plotdir / f"{outfile_root}.pdf", bbox_inches="tight")
    #plt.close(fig)

def plot_mass_distribution():
    pass

def plot_redshift_distribution(
    v,
    plotdir,
    outfile_root="redshift_distribution_halpha",
    z_col="vr",
    haobs_key="HAPY_HAS_OBS",
):
    """
    Plot redshift / velocity distribution of the Halpha sample
    relative to the full Virgo Filament Survey.
    """

    plotdir = Path(plotdir)
    plotdir.mkdir(parents=True, exist_ok=True)

    z = np.array(v.main[z_col], dtype=float)
    has_ha = np.array(v.halpha[haobs_key]).astype(bool)

    valid = np.isfinite(z)
    full = valid
    ha = valid & has_ha

    fig, ax = plt.subplots(figsize=(8, 6))

    bins = np.arange(0, 3500 + 250, 250)

    ax.hist(
        z[full],
        bins=bins,
        histtype="stepfilled",
        alpha=0.25,
        label="Full VFS",
    )

    ax.hist(
        z[ha],
        bins=bins,
        histtype="step",
        linewidth=2.5,
        label=r"H$\alpha$ sample",
    )

    ax.set_xlabel(r"$cz$ / velocity (km s$^{-1}$)", fontsize=16)
    ax.set_ylabel("Number of galaxies", fontsize=16)
    ax.tick_params(labelsize=14)

    ax.legend(
        fontsize=12,
        frameon=True,
        framealpha=0.5,
        facecolor="white",
        edgecolor="0.5",
    )

    fig.savefig(plotdir / f"{outfile_root}.png", dpi=200, bbox_inches="tight")
    fig.savefig(plotdir / f"{outfile_root}.pdf", bbox_inches="tight")
    #plt.close(fig)


def plot_environment_distribution(
    v,
    plotdir,
    outfile_root="environment_distribution_halpha",
    haobs_key="HAPY_HAS_OBS",
    show=False,
    title=False,
):
    """
    Compare environment membership fractions for the full VFS and Halpha samples.

    Environment classes are not assumed to be mutually exclusive.
    """

    plotdir = Path(plotdir)
    plotdir.mkdir(parents=True, exist_ok=True)

    env_cols = [
        "pure_field",
        "poor_group_memb",
        "filament_member",
        "rich_group_memb",
        "cluster_member",
    ]

    env_labels = [
        "Field",
        "Poor\nGroup",
        "Filament",
        "Rich\nGroup",
        "Cluster",
    ]

    has_ha = np.array(v.halpha[haobs_key]).astype(bool)

    n_full_total = len(v.main)
    n_ha_total = np.sum(has_ha)

    n_full = []
    n_ha = []

    for col in env_cols:
        flag = np.array(v.env[col]).astype(bool)
        n_full.append(np.sum(flag))
        n_ha.append(np.sum(flag & has_ha))

    n_full = np.array(n_full, dtype=float)
    n_ha = np.array(n_ha, dtype=float)

    frac_full = n_full / n_full_total
    frac_ha = n_ha / n_ha_total

    completeness = np.divide(
        n_ha,
        n_full,
        out=np.zeros_like(n_ha),
        where=n_full > 0,
    )

    x = np.arange(len(env_cols))
    width = 0.38

    fig, ax = plt.subplots(figsize=(8, 6))

    ax.bar(
        x - width / 2,
        frac_full,
        width,
        label="Full VFS",
        alpha=0.6,
    )

    ax.bar(
        x + width / 2,
        frac_ha,
        width,
        label=r"Observed H$\alpha$ sample",
        alpha=0.8,
    )

    for i, comp in enumerate(completeness):
        ax.text(
            x[i] + width / 2,
            frac_ha[i] + 0.015,
            f"{100 * comp:.0f}%",
            ha="center",
            va="bottom",
            fontsize=12,
        )

    ax.set_xticks(x)
    ax.set_xticklabels(env_labels, fontsize=14)
    ax.set_ylabel("Fraction of galaxies", fontsize=16)
    ax.tick_params(axis="y", labelsize=14)

    ymax = max(np.max(frac_full), np.max(frac_ha))
    ax.set_ylim(0, ymax * 1.25)

    ax.legend(
        fontsize=12,
        frameon=True,
        framealpha=0.5,
        facecolor="white",
        edgecolor="0.5",
    )

    if title:
        ax.set_title(
            r"Environment membership of the H$\alpha$ sample",
            fontsize=18,
        )

    fig.tight_layout()
    fig.savefig(plotdir / f"{outfile_root}.png", dpi=200, bbox_inches="tight")
    fig.savefig(plotdir / f"{outfile_root}.pdf", bbox_inches="tight")

    if show:
        plt.show()
    else:
        plt.close(fig)


import os
import argparse

from hapypost.io.vfs_tables import VTables


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
    
    
