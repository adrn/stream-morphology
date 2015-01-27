# coding: utf-8

""" Check the status of frequency mapping. """

from __future__ import division, print_function

__author__ = "adrn <adrn@astro.columbia.edu>"

# Standard library
import os

# Third-party
import numpy as np

from streammorphology.util import _shape

def main(path, index=None):
    basepath = os.path.split(path)[0]
    w0_path = os.path.join(basepath, 'w0.npy')

    w0 = np.load(w0_path)
    d = np.memmap(path, mode='r', shape=(len(w0),)+_shape, dtype='float64')

    n_done = int((d[:,0,7] == 1).sum())
    n_fail_some = int((np.any(np.isnan(d[:,0,:6]), axis=1) | np.any(np.isnan(d[:,1,:6]), axis=1)).sum())
    n_total_fail = int(np.all(np.isnan(d[:,0,:6]), axis=1).sum())

    print("Number of orbits: {}".format(len(w0)))
    print("Completed: {}".format(n_done))
    print("Some failures: {}".format(n_fail_some))
    print("Total failures: {}".format(n_total_fail))

    if index is not None:
        print("-"*79)
        print("w0: {}".format(w0[index]))
        print("max(∆E): {}".format(d[index,0,6]))
        print("dt, nsteps: {}, {}".format(d[index,0,9],d[index,0,10]))
        if d[index,0,8] == 1.:
            print("Loop orbit")
        else:
            print("Box orbit")
        print("1st half freqs.:")
        print("\t xyz: {}".format(d[index,0,:3]))
        print("\t rφz: {}".format(d[index,0,3:6]))
        print("2nd half freqs.:")
        print("\t xyz: {}".format(d[index,1,:3]))
        print("\t rφz: {}".format(d[index,1,3:6]))

if __name__ == '__main__':
    from argparse import ArgumentParser

    # Define parser object
    parser = ArgumentParser(description="")
    parser.add_argument("-p", "--path", dest="path", required=True,
                        help="Path to a Numpy memmap file containing the results "
                             "of frequency mapping.")
    parser.add_argument("-i", "--index", dest="index", default=None,
                        help="Index of an orbit to check.")

    args = parser.parse_args()

    main(args.path, index=args.index)