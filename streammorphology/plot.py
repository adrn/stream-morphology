# coding: utf-8

""" Plotting utilities for stream-morphology project """

from __future__ import division, print_function

__author__ = "adrn <adrn@astro.columbia.edu>"

# Third-party
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import numpy as np

__all__ = ['autosize_scatter', 'panel_plot']

def autosize_scatter(x, y, color_array=None, mask=None, mask_color='k',
                     subplots_kwargs=None, **kwargs):
    """
    Make a scatter plot of the input and automatically figure out the
    size of the marker so there is no whitespace between the markers.

    To switch to a log colorbar, for example, use the kwarg
    `norm=matplotlib.colors.LogNorm()`.

    Parameters
    ----------
    x : array_like
        x positions.
    y : array_like
        y positions.
    color_array : array_like (optional)
        Color the markers by values in this array.
    mask : array_like (optional)
        Boolean array masking out certain values from the input
        coordinates as 'bad'.
    mask_color : str, numeric (optional)
        Color for 'bad' values.
    subplots_kwargs : dict (optional)
        Keyword arguments passed through to the `plt.subplots()` call.
    kwargs : (optional)
        All other keyword arguments are passed through to
        the `plt.scatter()` call.

    Returns
    -------
    fig : matplotlib.Figure
        The matplotlib figure object drawn to.
    """

    if subplots_kwargs is None:
        subplots_kwargs = dict(figsize=(6,7.3))

    if 'cmap' not in kwargs:
        kwargs['cmap'] = 'Greys'

    if color_array is None:
        c = 'k'
    else:
        c = color_array

    if mask is None:
        mask = np.ones_like(x).astype(bool)

    # plot initial condition grid, colored by fractional diffusion rate
    fig = plt.figure(**subplots_kwargs)
    gs = GridSpec(100,100,bottom=0.12,left=0.15,right=0.95)

    ax = fig.add_subplot(gs[5:,:])
    cbaxes = fig.add_subplot(gs[:5,:])

    if np.allclose(y.max() - y.min(), x.max() - x.min()):
        ax.set_xlim(x.min(),x.max())
        ax.set_ylim(y.min(),y.max())
    else:
        ax.set_xlim(min([x[mask].min(),y[mask].min()]), max([x[mask].max(),y[mask].max()]))
        ax.set_ylim(*ax.get_xlim())

    # automatically determine symbol size
    xy_pixels = ax.transData.transform(np.vstack([x, y]).T)
    xpix, ypix = xy_pixels.T

    # In matplotlib, 0,0 is the lower left corner, whereas it's usually the upper
    # right for most image software, so we'll flip the y-coords
    width, height = fig.canvas.get_width_height()
    ypix = height - ypix

    # this assumes that your data-points are equally spaced
    sz = max((xpix[1]-xpix[0])**2, (ypix[1]-ypix[0])**2) - 1.

    # plot bad points
    ax.scatter(x[~mask], y[~mask], c=mask_color, s=sz, marker='s')

    # plot good points, colored
    sc = ax.scatter(x[mask], y[mask],
                    c=c, s=sz, marker='s', **kwargs)

    if color_array is not None:
        cb = fig.colorbar(sc, cax=cbaxes, orientation='horizontal')
        cb_ax = fig.axes[1]
        cb_ax.xaxis.set_ticks_position('top')
        cb_ax.xaxis.set_label_position('top')
        cb_ax.xaxis.set_label_coords(0.5,2.85)
        cb_ax.cb = cb

    ax.set_aspect('equal')

    return fig

def panel_plot(x, symbol, lim=None, relative=True):
    """ Make a 3-panel plot of projections of actions, angles, or frequency """

    if relative:
        x1,x2,x3 = ((x - x[0])/x[0]).T
    else:
        x1,x2,x3 = x.T

    fig,axes = plt.subplots(1, 3, figsize=(18,6),
                            sharex=True,sharey=True)

    with mpl.rc_context({'lines.marker': '.', 'lines.linestyle': 'none'}):
        axes[0].plot(x1, x3, alpha=0.25)
        axes[1].plot(x2, x3, alpha=0.25)
        axes[2].plot(x1, x2, alpha=0.25)

    if relative:
        axes[0].set_xlabel(r"$({sym}_1 - {sym}_{{1,{{\rm sat}}}})/{sym}_{{1,{{\rm sat}}}}$".format(sym=symbol))
        axes[1].set_xlabel(r"$({sym}_2 - {sym}_{{2,{{\rm sat}}}})/{sym}_{{2,{{\rm sat}}}}$".format(sym=symbol))
        axes[0].set_ylabel(r"$({sym}_3 - {sym}_{{3,{{\rm sat}}}})/{sym}_{{3,{{\rm sat}}}}$".format(sym=symbol))
        axes[2].set_ylabel(r"$({sym}_2 - {sym}_{{2,{{\rm sat}}}})/{sym}_{{2,{{\rm sat}}}}$".format(sym=symbol))
        axes[2].set_xlabel(r"$({sym}_1 - {sym}_{{1,{{\rm sat}}}})/{sym}_{{1,{{\rm sat}}}}$".format(sym=symbol))
    else:
        axes[0].set_xlabel(r"${sym}_1$".format(sym=symbol))
        axes[1].set_xlabel(r"${sym}_2$".format(sym=symbol))
        axes[0].set_ylabel(r"${sym}_3$".format(sym=symbol))
        axes[2].set_ylabel(r"${sym}_2$".format(sym=symbol))
        axes[2].set_xlabel(r"${sym}_1$".format(sym=symbol))

    with mpl.rc_context({'lines.marker': 'o', 'lines.markersize': 10}):
        axes[0].plot(x1[0], x3[0], alpha=0.75, color='r')
        axes[1].plot(x2[0], x3[0], alpha=0.75, color='r')
        axes[2].plot(x1[0], x2[0], alpha=0.75, color='r')

    plt.locator_params(nbins=5)

    if lim is not None:
        axes[0].set_xlim(*lim)
        axes[0].set_ylim(*lim)
    fig.tight_layout()

    return fig

def _hack_label_lines_annotate(ax, potential):
    from . import three_orbits as w0_dict
    from . import name_map

    slope = 1.
    xtext = 1.55
    for i,name in enumerate(w0_dict.keys()):
        ww0 = w0_dict[name]
        x = ww0[0] / potential.parameters['r_s']
        y = ww0[2] / potential.parameters['r_s'] - 0.02 # correct for arrow head

        dy = slope*(xtext-x) - 0.1

        armA = 50
        armB = 80
        if name_map[name] == 'A':
            offset = 0.
            dy += 0.037
            armA = 40
            armB = 90
        elif name_map[name] == 'C':
            offset = 0.
            dy -= 0.02
            armA = 55
            armB = 75
        else:
            offset = 0.

        xytext = [xtext, y+dy]

        ax.text(xytext[0]+0.02, xytext[1]-0.02+offset, name_map[name], fontsize=12, fontweight=600)
        ax.annotate("", xy=(x,y), xycoords='data',
                    xytext=xytext, textcoords='data',
                    arrowprops=dict(arrowstyle="-|>,head_length=0.75,head_width=0.1",
                                    shrinkA=0, shrinkB=0,
                                    connectionstyle="arc,angleA=180,angleB=48,armA={armA},armB={armB},rad=0".format(armA=armA, armB=armB),
                                    linewidth=1., color='#222222'),
                    horizontalalignment='left',
                    verticalalignment='bottom'
                    )

def _hack_label_lines(ax, potential, linecolor='#555555'):
    from . import three_orbits as w0_dict
    from . import name_map

    slope = 1.
    xtext = 1.55

    ytexts = dict()
    _ytexts = np.linspace(1.65,2,4)
    for i,(k,v) in enumerate(sorted(w0_dict.items(), key=lambda x: x[1][2])):
        ytexts[k] = _ytexts[i]

    for i,name in enumerate(w0_dict.keys()):
        ww0 = w0_dict[name]
        x0 = ww0[0] / potential.parameters['r_s']
        y0 = ww0[2] / potential.parameters['r_s']

        ytext = ytexts[name]
        xbreak = (ytext-y0)/slope + x0

        ax.plot([x0,xbreak,xtext], [y0,ytext,ytext], marker=None, color=linecolor)
        ax.text(xtext+0.02, ytext-0.022, name_map[name], fontsize=12, fontweight=600)
