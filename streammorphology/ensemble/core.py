# coding: utf-8

from __future__ import division, print_function

__author__ = "adrn <adrn@astro.columbia.edu>"

# Third-party
from astropy import log as logger
import astropy.units as u
from astropy.coordinates.angles import rotation_matrix
import gary.integrate as gi
import numpy as np
from scipy.signal import argrelmin, argrelmax

from sklearn.grid_search import GridSearchCV
from sklearn.neighbors import KernelDensity

from ..util import _validate_nd_array
from ..freqmap import estimate_periods
from .fast_ensemble import ensemble_integrate

__all__ = ['create_ensemble', 'nearest_pericenter', 'nearest_apocenter',
           'align_ensemble', 'do_the_kld']

def create_ensemble(w0, potential, n=1000, m_scale=1E4):
    """
    Generate an ensemble of test-particle orbits around the specified initial
    conditions in the specified potential. The position and velocity scales of
    the ensemble are set by the mass scale (`m_scale`).

    Parameters
    ----------
    w0 : array_like
        The parent orbit initial conditions as a 1D numpy array.
    potential : `gary.potential.PotentialBase`
        The gravitational potential.
    n : int (optional)
        Number of orbits in the ensemble.
    m_scale : numeric (optional)
        Mass scale of the ensemble.

    Returns
    -------
    ensemble_w0 : :class:`numpy.ndarray`
        The initial conditions for the ensemble. Will have shape (n+1,6),
        where the first (index 0) initial conditions are the parent orbit
        (e.g., specified when calling the function).
    """
    w0 = _validate_nd_array(w0, expected_ndim=1)

    # compute enclosed mass and position, velocity scales
    menc = potential.mass_enclosed(w0)
    rscale = (m_scale / menc)**(1/3.) * np.sqrt(np.sum(w0[:3]**2))
    vscale = (m_scale / menc)**(1/3.) * np.sqrt(np.sum(w0[3:]**2))

    ensemble_w0 = np.zeros((n,6))
    ensemble_w0[:,:3] = np.random.normal(w0[:3], rscale, size=(n,3))
    ensemble_w0[:,3:] = np.random.normal(w0[3:], vscale, size=(n,3))

    return np.vstack((w0,ensemble_w0))

def nearest_pericenter(w0, potential, forward=True, period=None):
    """
    Find the nearest pericenter to the initial conditions.

    By default, this looks for the nearest pericenter *forward* in time,
    but this can be changed by setting the `forward` argument to `False`.

    Parameters
    ----------
    w0 : array_like
        The parent orbit initial conditions as a 1D numpy array.
    potential : `gary.potential.PotentialBase`
        The gravitational potential.
    forward : bool (optional)
        Find the nearest pericenter either forward (True) in time
        or backward (False) in time.
    period : numeric (optional)
        The period of the orbit. If not specified, will estimate
        it internally. Used to figured out how long to integrate
        for when searching for the nearest pericenter.

    Returns
    -------
    peri_w0 : :class:`numpy.ndarray`
        The 6D phase-space position of the nearest pericenter.

    """
    w0 = _validate_nd_array(w0, expected_ndim=1)

    if period is None:
        periods = estimate_periods(w0, potential)
        period = periods[0] # R or x period

    dt = period / 256. # 512 steps per orbital period
    if not forward:
        dt *= -1

    nsteps = int(10.*period / dt)
    t,w = potential.integrate_orbit(w0, dt=dt, nsteps=nsteps,
                                    Integrator=gi.DOPRI853Integrator)

    r = np.sqrt(np.sum(w[:,0,:3]**2, axis=-1))
    peris, = argrelmin(r)

    # nearest peri:
    peri_idx = peris[0]
    return w[peri_idx, 0]

def nearest_apocenter(w0, potential, forward=True, period=None):
    """
    Find the nearest apocenter to the initial conditions.

    By default, this looks for the nearest apocenter *forward* in time,
    but this can be changed by setting the `forward` argument to `False`.

    Parameters
    ----------
    w0 : array_like
        The parent orbit initial conditions as a 1D numpy array.
    potential : `gary.potential.PotentialBase`
        The gravitational potential.
    forward : bool (optional)
        Find the nearest apocenter either forward (True) in time
        or backward (False) in time.
    period : numeric (optional)
        The period of the orbit. If not specified, will estimate
        it internally. Used to figured out how long to integrate
        for when searching for the nearest apocenter.

    Returns
    -------
    apo_w0 : :class:`numpy.ndarray`
        The 6D phase-space position of the nearest apocenter.

    """
    w0 = _validate_nd_array(w0, expected_ndim=1)

    if period is None:
        # TODO: better way to estimate period?
        t,w = potential.integrate_orbit(w0, dt=1., nsteps=5000,
                                        Integrator=gi.DOPRI853Integrator)
        periods = estimate_periods(t, w)
        period = periods[0] # R or x period

    dt = period / 256. # 512 steps per orbital period
    if not forward:
        dt *= -1

    nsteps = int(10.*period / dt)
    t,w = potential.integrate_orbit(w0, dt=dt, nsteps=nsteps,
                                    Integrator=gi.DOPRI853Integrator)

    r = np.sqrt(np.sum(w[:,0,:3]**2, axis=-1))
    apos, = argrelmax(r)

    # nearest peri:
    apo_idx = apos[0]
    return w[apo_idx, 0]

def compute_align_matrix(w):
    """
    Given a single phase-space position, compute the rotation matrix that
    orients the angular momentum with the z axis and places the point
    along the x axis.

    Parameters
    ----------
    w : array_like
        The point to transform.

    Returns
    -------
    R : :class:`numpy.ndarray`
        A 2D numpy array (rotation matrix).

    """
    w = _validate_1d_array(w)

    x = w[:3].copy()
    v = w[3:].copy()

    # first rotate about z to put on x-z plane
    theta = np.arctan2(x[1], x[0]) * u.radian
    R1 = rotation_matrix(theta, 'z')
    x = np.asarray(R1.dot(x))[0]
    v = np.asarray(R1.dot(v))[0]

    # now rotate about y to put on x axis
    theta = np.arctan2(x[2], x[0]) * u.radian
    R2 = rotation_matrix(-theta, 'y')
    x = np.asarray(R2.dot(x))[0]
    v = np.asarray(R2.dot(v))[0]

    # now align L with z axis
    # theta = np.arccos(L[2] / np.sqrt(np.sum(L**2))) * u.radian
    L = np.cross(x, v)
    theta = np.arctan2(L[2], L[1]) * u.radian
    R3 = rotation_matrix(theta - 90*u.deg, 'x')
    x = np.asarray(R3.dot(x))[0]
    v = np.asarray(R3.dot(v))[0]

    return R3*R2*R1

def align_ensemble(ws):
    """
    Given a collection of orbits (e.g., ensemble orbits), rotate the
    ensemble so that the 0th orbit is along the x-axis with angular
    momentum vector aligned with the z-axis.

    Parameters
    ----------
    ws : array_like
        A 3D array of orbits with shape (ntimes, norbits, 6).

    Returns
    -------
    new_ws : :class:`numpy.ndarray`
        The transformed orbits.
    """
    R = compute_align_matrix(ws[-1,0])
    new_x = np.array(R.dot(ws[-1,:,:3].T).T)
    new_v = np.array(R.dot(ws[-1,:,3:].T).T)
    new_w = np.vstack((new_x.T, new_v.T)).T
    return new_w
