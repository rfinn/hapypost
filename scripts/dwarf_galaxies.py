from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

from hapypost.plotting.environment import plot_spines, mycolors
from hapypost.plotting.common import get_dsfr, get_sfr_ms, plot_ms, get_mstar, get_sfr, fix_homedir, get_dwarf_flag, get_halpha_detection_flag
from hapypost.io.vfs_tables import VTables
import os
import argparse

# #-- HELPER FUNCTIONS
# def get_dsfr(logmstar,sfr):
#     return sfr - get_sfr_ms(logmstar)


# def get_sfr_ms(logmstar):
#     # from K. Conger+2026 : 0.80 log(M∗) − 8.56. (1)
#     ms_slope = .8
#     ms_intercept=-8.56
#     sfr_ms = ms_slope * logmstar + ms_intercept
#     return sfr_ms
# def plot_ms(ax):
#     x1,x2 = ax.get_xlim()
#     xline = np.linspace(x1,x2,100)
#     plt.plot(xline,get_sfr_ms(xline),'k--')

# def get_mstar(v):
#     return np.log10(np.array(v.cigale['bayes.stellar.m_star'], dtype=float))

# def get_sfr(v):
#     return np.log10(np.array(v.cigale['bayes.sfh.sfr'], dtype=float))

# def fix_homedir(path):
#     if path.startswith("/home/rfinn/"):
#         return path.replace("/home/rfinn", os.getenv("HOME"))
#     return path


# def get_dwarf_flag(v,logmstar_min=7.5,logmstar_max=9):
#     logmstar = np.log10(v.cigale['bayes.stellar.m_star'])
#     flag = (logmstar > logmstar_min) & (logmstar <= logmstar_max)
#     return flag


# def get_halpha_detection_flag(v,snr_cut=5,npix=5):
#     #colname='H_R24_FLUX_CGS'
#     #snr = v.halpha[colname]/v.halpha[colname+'_ERR']
#     flag = ( v.halpha['CSGR_HAPY_SNP_DET']  > snr_cut) & (v.halpha['CSGR_HAPY_NPIX'] > npix)
#     return flag

#-- PLOT FIGURES
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

    
    ha_detect_flag = get_halpha_detection_flag(v)
    flag_ha_detect = ha_detect_flag & has_valid_mass & has_ha

    
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

    ax.plot(
        x[flag_ha_detect],
        y[flag_ha_detect],
        "*",
        color="m",
        alpha=0.8,
        label=r"H$\alpha$ Detected",
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
    plot_ms(ax)
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
    outfile_root="dwarf_environ_distribution_halpha",
    haobs_key="HAPY_HAS_OBS",
    show=False,
    title=False,
    logmstar_min=7.5,

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

    
    dwarf_flag = get_dwarf_flag(v,logmstar_min=logmstar_min)
    ha_detect_flag = get_halpha_detection_flag(v)

    
    n_full_total = np.sum(dwarf_flag)
    n_tot_ha_obs = np.sum(has_ha & dwarf_flag)
    n_tot_ha_detect = np.sum(has_ha & dwarf_flag & ha_detect_flag)    

    print(f"number of dwarf galaxies observed with Halpha = {np.sum(n_tot_ha_obs)}")
    print(f"number of dwarf galaxies detected with Halpha = {np.sum(n_tot_ha_detect)}")    
    
    n_full = []
    n_ha_obs = []
    n_ha_detect = []    

    for col in env_cols:
        flag = np.array(v.env[col]).astype(bool)
        n_full.append(np.sum(flag & dwarf_flag))
        n_ha_obs.append(np.sum(flag & has_ha & dwarf_flag))
        n_ha_detect.append(np.sum(flag & has_ha & dwarf_flag & ha_detect_flag))        

    n_full = np.array(n_full, dtype=float)
    n_ha_obs = np.array(n_ha_obs, dtype=float)
    n_ha_detect = np.array(n_ha_detect, dtype=float)    

    frac_full = n_full / n_full_total
    frac_ha_obs = n_ha_obs / n_tot_ha_obs
    frac_ha_detect = n_ha_detect / n_tot_ha_obs  

    completeness = np.divide(
        n_ha_detect,
        n_ha_obs,
        out=np.zeros_like(n_ha_detect),
        where=n_full > 0,
    )

    x = np.arange(len(env_cols))
    width = 0.38

    fig, ax = plt.subplots(figsize=(8, 6))

    # ax.bar(
    #     x - width / 2,
    #     frac_ha_obs,
    #     width,
    #     label="Full VFS Dwarf Sample",
    #     alpha=0.6,
    # )

    ax.bar(
        x - width / 2,
        frac_ha_obs,
        width,
        label=r"Dwarf with H$\alpha$ observation",
        alpha=0.8,
    )
    ax.bar(
        x +  width / 2,
        frac_ha_detect,
        width,
        label=r"Dwarf with H$\alpha$ Detection",
        alpha=0.8,
    )

    for i, comp in enumerate(completeness):
        ax.text(
            x[i] + width / 2,
            frac_ha_detect[i] + 0.015,
            f"{100 * comp:.0f}%",
            ha="center",
            va="bottom",
            fontsize=12,
        )

    ax.set_xticks(x)
    ax.set_xticklabels(env_labels, fontsize=14)
    ax.set_ylabel("Fraction of galaxies", fontsize=16)
    ax.tick_params(axis="y", labelsize=14)

    ymax = max(np.max(frac_full), np.max(frac_ha_obs))
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

def plot_halpha_detection_completeness_by_environment(
    v,
    plotdir,
    outfile_root="dwarf_halpha_detection_completeness_by_environment",
    haobs_key="HAPY_HAS_OBS",
    show=False,
    title=False,
    logmstar_min=7.5,
    logmstar_max=9.0,
    ha_snr_cut=5,
    npix=5,
):
    """
    Plot Halpha detection fraction among Halpha-observed dwarf galaxies
    as a function of environment.

    Error bars are binomial:
        sigma_p = sqrt(p * (1 - p) / Nobs)
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
    dwarf_flag = get_dwarf_flag(v, logmstar_min=logmstar_min, logmstar_max=logmstar_max)
    ha_detect_flag = get_halpha_detection_flag(v,snr_cut=ha_snr_cut, npix=npix)

    n_ha_obs = []
    n_ha_detect = []

    for col in env_cols:
        env_flag = np.array(v.env[col]).astype(bool)

        nobs = np.sum(env_flag & dwarf_flag & has_ha)
        ndet = np.sum(env_flag & dwarf_flag & has_ha & ha_detect_flag)

        n_ha_obs.append(nobs)
        n_ha_detect.append(ndet)

    n_ha_obs = np.array(n_ha_obs, dtype=float)
    n_ha_detect = np.array(n_ha_detect, dtype=float)

    completeness = np.divide(
        n_ha_detect,
        n_ha_obs,
        out=np.zeros_like(n_ha_detect),
        where=n_ha_obs > 0,
    )

    completeness_err = np.zeros_like(completeness)
    good = n_ha_obs > 0
    completeness_err[good] = np.sqrt(
        completeness[good] * (1.0 - completeness[good]) / n_ha_obs[good]
    )

    x = np.arange(len(env_cols))

    fig, ax = plt.subplots(figsize=(8, 6))

    ax.errorbar(
        x,
        completeness,
        yerr=completeness_err,
        fmt="o",
        capsize=5,
        markersize=8,
        linestyle="none",
        label=r"H$\alpha$ detection fraction",
    )

    # add shading for field value
    x1,x2 = plt.xlim()
    xline=np.linspace(x1,x2,100)
    yline = completeness[0]*np.ones_like(xline)
    plt.fill_between(xline,y1=yline+completeness_err[0],y2=yline-completeness_err[0], alpha=0.2)

    for i, (p, err, nobs, ndet) in enumerate(
        zip(completeness, completeness_err, n_ha_obs, n_ha_detect)
    ):
        ax.text(
            x[i],
            p + err + 0.04,
            f"{100*p:.0f}%\n({int(ndet)}/{int(nobs)})",
            ha="center",
            va="bottom",
            fontsize=12,
        )

    ax.set_xticks(x)
    ax.set_xticklabels(env_labels, fontsize=14)
    ax.set_ylabel(
        r"Fraction of H$\alpha$-observed dwarfs detected in H$\alpha$",
        fontsize=16,
    )
    ax.tick_params(axis="y", labelsize=14)
    ax.set_ylim(0, 1.12)

    if title:
        ax.set_title(
            f"{logmstar_min} < log(Mstar) < {logmstar_max}",
            fontsize=18,
        )

    fig.tight_layout()
    fig.savefig(plotdir / f"{outfile_root}.png", dpi=200, bbox_inches="tight")
    fig.savefig(plotdir / f"{outfile_root}.pdf", bbox_inches="tight")

    if show:
        plt.show()
    else:
        plt.close(fig)

    return {
        "env_cols": env_cols,
        "env_labels": env_labels,
        "n_ha_obs": n_ha_obs,
        "n_ha_detect": n_ha_detect,
        "completeness": completeness,
        "completeness_err": completeness_err,
    }

def plot_dwarf_redshift_by_environment(
    v,
    plotdir,
    outfile_root="dwarf_halpha_detection_completeness_by_environment",
    haobs_key="HAPY_HAS_OBS",
    show=False,
    title=False,
    logmstar_min=7.5,
    logmstar_max=9.0,
):
    """
    Plot Halpha detection fraction among Halpha-observed dwarf galaxies
    as a function of environment.

    Error bars are binomial:
        sigma_p = sqrt(p * (1 - p) / Nobs)
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
    dwarf_flag = get_dwarf_flag(v, logmstar_min=logmstar_min, logmstar_max=logmstar_max)


    n_ha_obs = []
    n_ha_detect = []

    plt.figure()

    for env in env_cols:
        flag = dwarf_flag & has_ha & v.env[env]
        plt.hist(v.main['vr'][flag],bins=np.sum(flag), cumulative=True, histtype='step', density=True,label=env.replace("_member","").replace("_memb","").replace("_"," "))

    plt.xlabel("vr (km/s)",fontsize=14)
    plt.ylabel("Distribution",fontsize=14)
    plt.legend()



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
    
    
