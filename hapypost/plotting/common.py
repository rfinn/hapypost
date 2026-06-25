import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt

def _as_float_array(tab, col):
    return np.array(tab[col], dtype=float)


def _get_col(tab, candidates):
    """
    Return first matching column name from a list of candidates.
    """
    for col in candidates:
        if col in tab.colnames:
            return col
    raise KeyError(f"None of these columns found: {candidates}")


def _finish_figure(fig, outpath_root=None, show=False, dpi=200):
    """
    Save png/pdf if outpath_root is given, then show or close.
    """
    fig.tight_layout()

    if outpath_root is not None:
        outpath_root = Path(outpath_root)
        outpath_root.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(outpath_root.with_suffix(".png"), dpi=dpi, bbox_inches="tight")
        fig.savefig(outpath_root.with_suffix(".pdf"), bbox_inches="tight")

    if show:
        plt.show()
    else:
        plt.close(fig)

def get_rsize(tab):
    return tab[_get_col(tab,["R75_ARCSEC",])]

def get_hsize(tab):
    return tab[_get_col(tab,["CSGR_H75_ARCSEC","H75_ARCSEC"],)]

def get_outer_size_ratio(v):
    rsize = get_rsize(v.halpha)
    hsize = get_hsize(v.halpha)
    #print(rsize)
    return hsize/rsize



def get_rmoment(tab):
    c = _get_col(
            tab,["CSGR_R_SC_SEMIMAJOR_SIGMA","R_SC_SEMIMAJOR_SIGMA"],        
        )
    return tab[c]

def get_hmoment(tab):
    c = _get_col(
            tab,["CSGR_H_SC_SEMIMAJOR_SIGMA","H_SC_SEMIMAJOR_SIGMA"],
        )
    return tab[c]
    

def get_moment_ratio(v):
    rmoment = get_rmoment(v.halpha)
    hmoment = get_hmoment(v.halpha)
    return hmoment/rmoment


def get_rflux(tab):
    c =  _get_col(
            tab,["R24_FLUX_CGS",],
        )
    return tab[c]

def get_hflux(tab):
    c =  _get_col(
            tab,["CSGR_H_TOT_FLUX_CGS",],
        )
    return tab[c]

def get_flux_ratio(v):
    r = get_rflux(v.halpha)
    h = get_hflux(v.halpha)
    return h/r


#-- HELPER FUNCTIONS
def get_dsfr(logmstar,sfr):
    return sfr - get_sfr_ms(logmstar)


def get_sfr_ms(logmstar):
    # from K. Conger+2026 : 0.80 log(M∗) − 8.56. (1)
    ms_slope = .8
    ms_intercept=-8.56
    sfr_ms = ms_slope * logmstar + ms_intercept
    return sfr_ms

def plot_ms(ax):
    x1,x2 = ax.get_xlim()
    xline = np.linspace(x1,x2,100)
    plt.plot(xline,get_sfr_ms(xline),'k--')

def get_logmstar(v):
    return np.log10(np.array(v.cigale['bayes.stellar.m_star'], dtype=float))

def get_logsfr(v):
    return np.log10(np.array(v.cigale['bayes.sfh.sfr'], dtype=float))

def fix_homedir(path):
    if path.startswith("/home/rfinn/"):
        return path.replace("/home/rfinn", os.getenv("HOME"))
    return path


def get_dwarf_flag(v,logmstar_min=7.5,logmstar_max=9):
    logmstar = np.log10(v.cigale['bayes.stellar.m_star'])
    flag = (logmstar > logmstar_min) & (logmstar <= logmstar_max)
    return flag


def get_halpha_detection_flag(v,snr_cut=5,npix=5):
    #colname='H_R24_FLUX_CGS'
    #snr = v.halpha[colname]/v.halpha[colname+'_ERR']
    flag = ( v.halpha['CSGR_HAPY_SNP_DET']  > snr_cut) & (v.halpha['CSGR_HAPY_NPIX'] > npix)
    return flag


def get_gr_color(v):
    g = 22.5 - np.log10(v.ephot['FLUX_AP06_G'])
    r = 22.5 - np.log10(v.ephot['FLUX_AP06_R'])    
    return g - r

def get_hapy_r_asym(tab):
    return tab["R_HAPY_ASYM"]

def get_hapy_h_asym(tab):
    return tab["CSGR_HAPY_ASYM"]

def get_hapy_delta_asym(v):
    r = get_hapy_r_asym(v.halpha)
    
    h = get_hapy_h_asym(v.halpha)
    return h - r


def get_hapy_delta_gini(v):
    r =  v.halpha["R_HAPY_GINI"]
    
    h =  v.halpha["CSGR_HAPY_GINI"]
    return h - r

def get_sc_delta_gini(v):
    r =  v.halpha["R_SC_GINI"]
    
    h =  v.halpha["CSGR_H_SC_GINI"]
    return h - r


def get_hapy_delta_m20(v):
    r = v.halpha["R_HAPY_M20"]
    
    h = v.halpha["CSGR_HAPY_M20"]
    return h - r

def science_ready_and_hasha_mask(
    v,
    haobs_key="HAPY_HAS_OBS",
    qc_tiers=("A", "B","C","D"),
    require_phot_ok=True,
    require_morph_ok=False,
    hasnr_cut=10
):
    """
    Basic reusable Halpha science-ready mask.

    Assumes HAPY row-matched table is v.halpha.
    """
    h = v.halpha

    sel = science_ready_mask(v)
    
    ssfrflag = np.log10(v.cigale['bayes.sfh.sfr']/v.cigale['bayes.stellar.m_star']) > -11.5
    maskflag = v.halpha['MASKFRAC_GUESS_ELLIPSE'] < 0.2
    hasnr = v.halpha['H_TOT_FLUX_CGS']/v.halpha['H_TOT_FLUX_CGS_ERR'] > hasnr_cut
    sel = sel & ssfrflag & hasnr
        
    return sel


def science_ready_mask(
    v,
    haobs_key="HAPY_HAS_OBS",
    qc_tiers=("A", "B","C","D"),
    require_phot_ok=True,
    require_morph_ok=False,
):
    """
    Basic reusable Halpha science-ready mask.

    Assumes HAPY row-matched table is v.halpha.
    """
    h = v.halpha

    sel = np.array(h[haobs_key]).astype(bool)

    #if "QC_TIER" in h.colnames:
    #    sel &= np.isin(np.array(h["QC_TIER"]).astype(str), qc_tiers)

    if require_phot_ok and "PHOT_OK" in h.colnames:
        sel &= np.array(h["PHOT_OK"]).astype(bool)

    if require_morph_ok and "HAPY_MORPH_OK" in h.colnames:
        sel &= np.array(h["HAPY_MORPH_OK"]).astype(bool)

    catflag = v.halpha['CATALOG_USE'] == 'CLEAN'
    incflag = v.halpha['ELLIP_BA'] > 0.3
    maskflag = v.halpha['MASKFRAC_GUESS_ELLIPSE'] < 0.2
    sel = sel & catflag & incflag &  maskflag 
        
    return sel

