# coding: utf-8

from __future__ import division, print_function

__author__ = "adrn <adrn@astro.columbia.edu>"

# Third-party
import numpy as np
from scipy.signal import argrelmax, argrelmin

# Project
import gary.dynamics as gd
import gary.integrate as gi

__all__ = ['ptp_periods', 'estimate_max_period', 'estimate_dt_nsteps']

def ptp_periods(t, *coords):
    """
    Estimate the dominant periods of given coordinates by
    computing the mean peak-to-peak time.

    Parameters
    ----------
    t : array_like
        Array of times. Must have same shape as individual coordinates.
    *coords
        Positional arguments allow specifying coordinates to compute the
        periods of. For example, these could simply be x,y,z, or
        could be R,phi,z for cylindrical coordinates.

    """

    freqs = []
    for x in coords:
        # first compute mean peak-to-peak
        ix = argrelmax(x, mode='wrap')[0]
        f_max = np.mean(t[ix[1:]] - t[ix[:-1]])

        # now compute mean trough-to-trough
        ix = argrelmin(x, mode='wrap')[0]
        f_min = np.mean(t[ix[1:]] - t[ix[:-1]])

        # then take the mean of these two
        freqs.append(np.mean([f_max, f_min]))

    return np.array(freqs)

def estimate_max_period(t, w):
    """
    Given an array of times and an orbit, estimate the longest period
    in the orbit. We will then use this to figure out how long to
    integrate for when frequency mapping.

    Parameters
    ----------
    t : array_like
        Array of times.
    w : array_like
        Single orbit -- should have shape (len(t), 6)

    """

    # circulation
    circ = gd.classify_orbit(w)

    if np.any(circ):  # TUBE ORBIT - pass R,φ,z
        # flip coords
        new_w = gd.align_circulation_with_z(w, circ[0])[:,0]

        # convert to cylindrical
        R = np.sqrt(new_w[:,0]**2 + new_w[:,1]**2)
        phi = np.arctan2(new_w[:,1], new_w[:,0])
        z = new_w[:,2]

        T = ptp_periods(t, R, phi, z)

    else:  # BOX ORBIT - pass x,y,z
        T = ptp_periods(t, *w[:,:3].T)

    return T.max()

def estimate_dt_nsteps(potential, w0, nperiods=200, nsteps_per_period=100):
    """
    Estimate the timestep and number of steps to integrate for given a potential
    and set of initial conditions.

    Parameters
    ----------
    potential : :class:`~gary.potential.Potential`
    w0 : array_like
    nperiods : int (optional)
        Number of (max) periods to integrate.
    nsteps_per_period : int (optional)
        Number of steps to take per (max) orbital period.

    """

    # integrate orbit
    t,w = potential.integrate_orbit(w0, dt=2., nsteps=25000,
                                    Integrator=gi.DOPRI853Integrator)

    # estimate the maximum period
    max_T = estimate_max_period(t, w)

    # timestep from number of steps per period
    dt = float(max_T) / float(nsteps_per_period)

    # integrate for nperiods times the max period
    nsteps = int(round(nperiods * nsteps_per_period, -4))

    if dt == 0.:
        raise ValueError("Timestep is zero!")

    return dt, nsteps