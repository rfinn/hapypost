
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.patches import Ellipse, Rectangle
import matplotlib.transforms as transforms
from matplotlib.offsetbox import AnchoredOffsetbox, AuxTransformBox
import matplotlib.ticker as ticker

mycolors = plt.rcParams['axes.prop_cycle'].by_key()['color']
def add_spine(ax,color='c'):
    from astropy.table import Table
    
    spinedir = homedir+'/research/Virgo/tables-north/v2/spines/'
    spine  = Table.read(spinedir+'filament_spine_VirgoIII.fits')
    ax.plot(spine['ra'],spine['dec'],'c--',color=color,transform=ax.get_transform('world'))#, ,label='Filament Spine')

def plot_spines(multicolor=True,colorone=None,color=None,legend=True):
    import glob
    import os
    from astropy.table import Table
    sfiles = glob.glob(os.getenv("HOME")+'/research/Virgo/tables-north/spines/filament*.fits')
    ncolor = 0
    for i,f in enumerate(sfiles):
        spine  = Table.read(f)
        if legend:
            mylabel = os.path.basename(f).replace('filament_spine_','').replace('.fits','').replace('_Filament','')
        else:
            mylabel = None
        
        if multicolor:
            plt.plot(spine['ra'],spine['dec'],c=mycolors[ncolor],label=mylabel,lw=3)
        
            ncolor += 1
            if ncolor > len(mycolors)-1:
                ncolor = 0
        else:
            if colorone is not None:
                if colorone in f:
                    plt.plot(spine['ra'],spine['dec'],c=color,label=mylabel,lw=3,alpha=.6)
                else:
                    plt.plot(spine['ra'],spine['dec'],c='0.5',label=mylabel,lw=3)
            else:
                plt.plot(spine['ra'],spine['dec'],c='0.5',label=mylabel,lw=3)
                
def plot_cluster_center():
    pass

def plot_virial_radius():
    pass

def plot_density_contours():
    pass
