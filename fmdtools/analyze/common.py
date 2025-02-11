# -*- coding: utf-8 -*-
"""
Some common methods for analysis used by other modules.

Has methods:

- :func:`bootstrap_confidence_interval`: Convenience wrapper for scipy.bootstrap
- :func:`nan_to_x`: Helper function for Result Class, returns nan as zero if present,
  otherwise returns the number
- :func:`is_numeric`: Helper function for Result Class, checks if a given value is
  numeric
- :func:`join_key`: Helper function for Result Class
- :func: `setup_plot` : initializes mpl figure.
- :func:`plot_err_hist`: Plots a line with a given range of uncertainty around it.
- :func:`plot_err_lines`: Plots error lines on the given plot.
- :func:`multiplot_legend_title`: Helper function for multiplot legends and titles.
- :func:`consolidate_legend`: Creates a single legend for a given multiplot where
  multiple groups are being compared.
"""
import numpy as np
import matplotlib.pyplot as plt

plt.rcParams['pdf.fonttype'] = 42


def get_sub_include(att, to_include):
    """Determines what attributes of att to include based on the provided
    dict/str/list/set to_include"""
    if type(to_include) in [list, set, tuple, str]:
        if att in to_include:
            new_to_include = 'default'
        elif type(to_include) == str and to_include == 'all':
            new_to_include = 'all'
        elif type(to_include) == str and to_include == 'default':
            new_to_include = 'default'
        else:
            new_to_include = False
    elif type(to_include) == dict and att in to_include:
        new_to_include = to_include[att]
    else:
        new_to_include = False
    return new_to_include


def to_include_keys(to_include):
    """Determine what dict keys to include from Result given nested to_include
    dictionary"""
    if type(to_include) == str:
        return [to_include]
    elif type(to_include) in [list, set, tuple]:
        return [to_i for to_i in to_include]
    elif type(to_include) == dict:
        keys = []
        for k, v in to_include.items():
            add = to_include_keys(v)
            keys.extend([k+'.'+v for v in add])
        return tuple(keys)


def is_numeric(val):
    """Checks if a given value is numeric"""
    try:
        return np.issubdtype(np.array(val).dtype, np.number)
    except:
        return type(val) in [float, bool, int]


def bootstrap_confidence_interval(data, method=np.mean, return_anyway=False, **kwargs):
    """
    Convenience wrapper for scipy.bootstrap.

    Parameters
    ----------
    data : list/array/etc
        Iterable with the data. May be float (for mean) or indicator (for proportion)
    method : method
        numpy method to give scipy.bootstrap.
    return_anyway: bool
        Gives a dummy interval of (stat, stat) if no . Used for plotting
    Returns
    ----------
    statistic, lower bound, upper bound
    """
    from scipy.stats import bootstrap
    if 'interval' in kwargs:
        kwargs['confidence_level'] = kwargs.pop('interval')*0.01
    if data.count(data[0]) != len(data):
        bs = bootstrap([data], np.mean, **kwargs)
        return method(data), bs.confidence_interval.low, bs.confidence_interval.high
    elif return_anyway:
        return method(data), method(data), method(data)
    else:
        raise Exception("All data are the same!")


def nan_to_x(metric, x=0.0):
    """returns nan as zero if present, otherwise returns the number"""
    if np.isnan(metric):
        return x
    else:
        return metric


def is_bool(val):
    try:
        return val.dtype in ['bool']
    except:
        return type(val) in [bool]


def join_key(k):
    if not isinstance(k, str):
        return '.'.join(k)
    else:
        return k


def setup_plot(fig=None, ax=None, z=False, figsize=(6, 4)):
    """
    Initialize a 2d or 3d figure at a given size.

    If there is a pre-existing figure or axis, uses that instead.
    """
    if not fig:
        if z or (type(z) in (int, float)):
            fig = plt.figure(figsize=figsize)
            ax = fig.add_subplot(111, projection='3d')
        else:
            fig, ax = plt.subplots(1, figsize=figsize)
    return fig, ax


def phase_overlay(ax, phasemap, label_phases=True):
    """Overlay phasemap information on plot."""
    ymin, ymax = ax.get_ylim()
    phaseseps = [i[0] for i in list(phasemap.phases.values())[1:]]
    ax.vlines(phaseseps, ymin, ymax, colors='gray', linestyles='dashed')
    if label_phases:
        for phase in phasemap.phases:
            if phasemap.modephases:
                phasetext = [m for m, p in phasemap.modephases.items() if phase in p][0]
            else:
                phasetext = phase
            bbox_props = dict(boxstyle="round,pad=0.3", fc="white", lw=0, alpha=0.5)
            ax.text(np.average(phasemap.phases[phase]),
                    (ymin+ymax)/2, phasetext, ha='center', bbox=bbox_props)


def plot_err_hist(err_hist, ax=None, fig=None, figsize=(6, 4), boundtype='fill',
                  boundcolor='gray', boundlinestyle='--', fillalpha=0.3,
                  xlabel='time', ylabel='', title='', **kwargs):
    """
    Plot a line with a given range of uncertainty around it.

    Parameters
    ----------
    err_hist : History
        hist of line, low, high values. Has the form:
        {'time': times, 'stat': stat_values, 'low': low_values, 'high': high_values}
    ax : mpl axis (optional)
        axis to plot the line on
    fig : mpl figure (optional)
        figure to plot line on
    figsize : tuple
        figure size (optional)
    boundtype : 'fill' or 'line'
        Whether the bounds should be marked with lines or a fill
    boundcolor : str, optional
        Color for bound fill The default is 'gray'.
    boundlinestyle : str, optional
        linestyle for bound lines (if any). The default is '--'.
    fillalpha : float, optional
        Alpha for fill. The default is 0.3.
    **kwargs : kwargs
        kwargs for the line

    Returns
    -------
    fig : mpl figure
    ax :mpl, axis
    """
    fig, ax = setup_plot(fig, ax, figsize)
    ax.plot(err_hist['stat'], **kwargs)
    if boundtype == 'fill':
        col = ax.lines[-1].get_color()
        ax.fill_between(err_hist['time'], err_hist['low'], err_hist['high'],
                        alpha=fillalpha, color=col)
        if 'med_high' in err_hist and 'med_low' in err_hist:
            ax.fill_between(err_hist['time'], err_hist['med_low'], err_hist['med_high'],
                            alpha=fillalpha, color=col)
    elif boundtype == 'line':
        plot_err_lines(err_hist['time'], err_hist['low'], err_hist['high'], ax=ax,
                       fig=fig, color=boundcolor, linestyle=boundlinestyle)
        if 'med_high' in err_hist and 'med_low' in err_hist:
            plot_err_lines(err_hist['time'], err_hist['med_low'], err_hist['med_high'],
                           ax=ax, fig=fig, color=boundcolor, linestyle=boundlinestyle)
    else:
        raise Exception("Invalid bound type: "+boundtype)
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title)
    return fig, ax


def plot_err_lines(times, lows, highs, ax=None, fig=None, figsize=(6, 4), **kwargs):
    """
    Plot error lines on the given plot.

    Parameters
    ----------
    times : list/array
        x data (time, typically)
    line : list/array
        y center data to plot
    lows : list/array
        y lower bound to plot
    highs : list/array
        y upper bound to plot
    **kwargs : kwargs
        kwargs for the line
    """
    fig, ax = setup_plot(ax, fig, figsize)
    ax.plot(times, highs, **kwargs)
    ax.plot(times, lows, **kwargs)
    return fig, ax


def unpack_plot_values(plot_values):
    """Helper function for enabling both dict and str plot_values."""
    if len(plot_values) == 1 and type(plot_values[0]) == dict:
        plot_values = to_include_keys(plot_values[0])
    if not plot_values:
        raise Exception("Empty plot_values--make sure to pass quantities to plot!")
    return plot_values


def multiplot_helper(cols, *plot_values, figsize='default', titles={}, sharex=True,
                     sharey=False):
    """Create multiple plot axes for plotting."""
    num_plots = len(plot_values)
    if num_plots == 1:
        cols = 1
    rows = int(np.ceil(num_plots/cols))
    if figsize == 'default':
        figsize = (cols*3, 2*rows)
    fig, axs = plt.subplots(rows, cols, sharex=sharex, sharey=sharey, figsize=figsize)

    if type(axs) == np.ndarray:
        axs = axs.flatten()
    else:
        axs = [axs]

    subplot_titles = {plot_value: plot_value for plot_value in plot_values}
    subplot_titles.update(titles)
    return fig, axs, cols, rows, subplot_titles


def multiplot_legend_title(groupmetrics, axs, ax,
                           legend_loc=False, title='', v_padding=None, h_padding=None,
                           title_padding=0.0, legend_title=None):
    """ Helper function for multiplot legends and titles"""
    if len(groupmetrics) > 1 and legend_loc != False:
        ax.legend()
        handles, labels = ax.get_legend_handles_labels()
        ax.get_legend().remove()
        ax_l = axs[legend_loc]
        by_label = dict(zip(labels, handles))
        if ax_l != ax and legend_loc in [-1, len(axs)]:
            ax_l.set_frame_on(False)
            ax_l.get_xaxis().set_visible(False)
            ax_l.get_yaxis().set_visible(False)
            ax_l.legend(by_label.values(), by_label.keys(),
                        prop={'size': 8}, loc='center', title=legend_title)
        else:
            ax_l.legend(by_label.values(), by_label.keys(),
                        prop={'size': 8}, title=legend_title)
    plt.subplots_adjust(hspace=v_padding, wspace=h_padding)
    if title:
        plt.suptitle(title, y=1.0+title_padding)


def consolidate_legend(ax, loc='upper left', bbox_to_anchor=(1.05, 1),
                       add_handles=[], **kwargs):
    """Create a single legend for a given multiplot where multiple groups are
    being compared"""
    ax.legend()
    hands, labels = ax.get_legend_handles_labels()
    ax.legend(handles=add_handles+hands)
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.get_legend().remove()
    ax.legend(by_label.values(), by_label.keys(),
              bbox_to_anchor=bbox_to_anchor, loc=loc, **kwargs)


def mark_times(ax, tick, time, *plot_values, fontsize=8):
    """
    Mark times on an axis at a particular tick interval.

    Parameters
    ----------
    ax : matplotlib axis
        Axis object to mark on
    tick : float
        Tick frequency.
    time : np.array
        Time vector.
    *plot_values : np.array
        x,y,z vectors
    fontsize : int, optional
        Size of the font. The default is 8.
    """
    for st in zip(*plot_values, time):
        tt = st[-1]
        xyz = st[:-1]
        if tt % tick == 0:
            ax.text(*xyz, 't='+str(tt), fontsize=fontsize)


def suite_for_plots(testclass, plottests=False):
    """
    Enables qualitative testing suite with or without plots in unittest. Plot tests
    should have "plot" in the title of their method, this enables this function to
    filter them out (or include them).

    Parameters
    ----------
    testclass : unittest.TestCase
        Test-case to create the suite for.
    plottests : bool/list, optional
        Whether to show the plot tests (True) or the non-plot tests (False). If a
        list is provided, only tests provided in the list will be run.

    Returns
    -------
    suite : unittest.TestSuite
        Test Suite to run with unittest.TextTestRunner() using runner.run
        (e.g., runner = unittest.TextTestRunner();
        runner.run(suite_for_plots(UnitTests, plottests=False)))
    """
    import unittest
    suite = unittest.TestSuite()
    if not plottests:
        tests = [func for func in dir(testclass)
                 if (func.startswith("test") and not ('plot' in func))]
    elif type(plottests) == list:
        tests = [func for func in dir(testclass)
                 if (func.startswith("test") and func in plottests)]
    else:
        tests = [func for func in dir(testclass)
                 if (func.startswith("test") and 'plot' in func)]
    for test in tests:
        suite.addTest(testclass(test))
    return suite