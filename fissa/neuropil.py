'''
Functions for removal of neuropil from calcium signals.

Authors: Sander Keemink (swkeemink@scimail.eu) and Scott Lowe
Created: 2015-05-15
'''

import numpy as np
import numpy.random as rand
import nimfa
from sklearn.decomposition import FastICA, NMF, PCA
from scipy.optimize import minimize_scalar


def separate(
        S, sep_method='ica', n_components=0.001, maxiter=500, tol=1e-5,
        random_state=892, maxtries=10):
    '''
    For the signals in S, finds the independent signals underlying it,
    using ica or nmf. Several methods for signal picking are
    implemented, see below, of which method 5 works best in general.

    Parameters
    ----------
    S : array_like
        2d array with signals. S[i,j], j = each signal, i = signal content.
        j = 0 is considered the primary signal. (i.e. the somatic signal)
    sep_method : {'ica','nmf','nmf_sklearn'}
        Which source separation method to use, ica or nmf.
            * ica: independent component analysis
            * nmf: The nimfa implementation of non-negative matrix
              factorization.
            * nmf_sklearn: The sklearn implementation of non-negative
              matrix factorization (which is slower).
    n_components : int, optional
        How many source components to estimate from the observed
        signals. If `0 < n_components < 1`, PCA is used on the observed
        signals and there is a source component included for every PCA
        component which explains at least this much of the overall
        variance. Default is `0.001`, so there are assumed to be as
        many source components as there are PCA components which
        explain 0.1% of the overall variance.
    maxiter : int, optional
        Number of maximally allowed iterations. Default is 500.
    tol : float, optional
        Error tolerance for termination. Default is 1e-5.
    random_state : int, optional
        Initial random state for seeding. Default is 892.
    maxtries : int, optional
        Maximum number of tries before algorithm should terminate.
        Default is 10.

    Returns
    -------
    S_sep : numpy.ndarray
        The raw separated traces
    S_matched :
        The separated traces matched to the primary signal, in order
        of matching quality (see Implementation below).
    A_sep :
    convergence : dict
        Metadata for the convergence result, with keys:
            * random_state: seed for ica initiation
            * iterations: number of iterations needed for convergence
            * max_iterations: maximun number of iterations allowed
            * converged: whether the algorithm converged or not (bool)

    Implementation
    --------------
    Concept by Scott Lowe and Sander Keemink.
    Normalize the columns in estimated mixing matrix A so that sum(column)=1
    This results in a relative score of how strongly each separated signal
    is represented in each ROI signal.
    '''
    # TODO for edge cases, reduce the number of npil regions according to
    #      possible orientations
    # TODO split into several functions. Maybe turn into a class.

    # Ensure array_like input is a numpy.ndarray
    S = np.asarray(S)

    # estimate number of signals to find, if not given
    if 0 < n_components < 1:
        # Perform PCA, without whitening because the mean is important to us.
        pca = PCA(whiten=False)
        pca.fit(S.T)
        # Method 1:
        # Find cumulative explained variance (old method)
        #   exp_var = np.cumsum(pca.explained_variance_ratio_)
        # Find the number of components which are needed to explain a
        # set fraction of the variance.
        # The optimal fraction of variance is dependent on number of
        # signals, see when variance exceeds
        # n_components= 4: 0.9, n_components=5, 0.99, etc.
        #   n_components = np.where(exp_var > 0.99)[0][0]+1
        #   print exp_var
        # Method 2:
        # Find how many components explain at least `x` fraction of
        # the overall observed variance.
        n_components = sum(pca.explained_variance_ratio_ > n_components)

    if sep_method == 'ica':
        # Use sklearn's implementation of ICA.

        for ith_try in range(maxtries):
            # Make an instance of the FastICA class. We can do whitening of
            # the data now.
            ica = FastICA(
                n_components=n_components, whiten=True, max_iter=maxiter,
                tol=tol, random_state=random_state,
                )

            # Perform ICA and find separated signals
            S_sep = ica.fit_transform(S.T)

            # check if max number of iterations was reached
            if ica.n_iter_ < maxiter:
                print((
                    'ICA converged after {} iterations.'
                    ).format(ica.n_iter_))
                break
            print((
                'Attempt {} failed to converge at {} iterations.'
                ).format(ith_try+1, ica.n_iter_))
            if ith_try+1 < maxtries:
                print('Trying a new random state.')
                # Change to a new random_state
                random_state = rand.randint(8000)

        if ica.n_iter_ == maxiter:
            print((
                'Warning: maximum number of allowed tries reached at {} '
                'iterations for {} tries of different random seed states.'
                ).format(ica.n_iter_, ith_try+1))

        A_sep = ica.mixing_

    elif sep_method == 'nmf_sklearn':
        for ith_try in range(maxtries):
            # Make an instance of the sklearn NMF class
            nmf = NMF(
                init='nndsvd', l1_ratio=0.25, alpha=5, max_iter=maxiter,
                n_components=n_components, tol=tol, random_state=random_state,
                )

            # Perform ICA and find separated signals
            S_sep = nmf.fit_transform(S.T)

            # check if max number of iterations was reached
            if nmf.n_iter_ < maxiter-1:
                print((
                    'NMF converged after {} iterations.'
                    ).format(nmf.n_iter_+1))
                break
            print((
                'Attempt {} failed to converge at {} iterations.'
                ).format(ith_try, nmf.n_iter_+1))
            if ith_try+1 < maxtries:
                print('Trying a new random state.')
                # Change to a new random_state
                random_state = rand.randint(8000)

        if nmf.n_iter_ == maxiter-1:
            print((
                'Warning: maximum number of allowed tries reached at {} '
                'iterations for {} tries of different random seed states.'
                ).format(nmf.n_iter_+1, ith_try+1))

        A_sep = nmf.components_.T

    elif sep_method == 'nmf':
        # The NIMFA implementation of NMF is fast and reliable.

        # Make an instance of the Nmf class from nimfa
        nmf = nimfa.Nmf(
            S.T, max_iter=maxiter, rank=n_components, seed='random_vcol',
            method='snmf', version='l', objective='conn',
            conn_change=3000, eta=1e-5, beta=1e-5,
            )
        # NB: Previously was using `eta=1e-5`, `beta=1e-5` too

        # fit the model
        nmf_fit = nmf()

        # get fit summary
        fs = nmf_fit.summary()
        # check if max number of iterations was reached
        if fs['n_iter'] < maxiter:
            print((
                'NMF converged after {} iterations.'
                ).format(fs['n_iter']))
        else:
            print((
                'Warning: maximum number of allowed iterations reached at {} '
                'iterations.'
                ).format(fs['n_iter']))

        # get the mixing matrix and estimated data
        S_sep = np.array(nmf_fit.basis())
        A_sep = np.array(nmf_fit.coef()).T

    else:
        raise ValueError('Unknown separation method "{}".'.format(sep_method))

    # make empty matched structure
    S_matched = np.zeros(np.shape(S_sep))

    # Normalize the columns in A so that sum(column)=1 (can be done in one line
    # too).
    # This results in a relative score of how strongly each separated signal
    # is represented in each ROI signal.
    A = abs(np.copy(A_sep))
    for j in range(n_components):
        if np.sum(A[:, j]) != 0:
            A[:, j] /= np.sum(A[:, j])

    # get the scores for the somatic signal
    scores = A[0,:]

    # get the order of scores
    order = np.argsort(scores)[::-1]

    # order the signals according to their scores
    for j in range(n_components):
        s_ = A_sep[0, order[j]]*S_sep[:, order[j]]
        S_matched[:, j] = s_
        # set the mean to be the same as the raw data
        if sep_method == 'ica':
            S_matched[:, j] += S[0,:].mean()
        elif sep_method == 'nmf' or sep_method == 'nmf_sklearn':
            S_matched[:, j] += S[0,:].mean() - S_matched[:, j].mean()

    # save the algorithm convergence info
    convergence = {}
    convergence['max_iterations'] = maxiter
    if sep_method == 'ica':
        convergence['random_state'] = random_state
        convergence['iterations'] = ica.n_iter_
        convergence['converged'] = not ica.n_iter_ == maxiter
    elif sep_method == 'nmf':
        convergence['random_state'] = 'not yet implemented'
        convergence['iterations'] = fs['n_iter']
        convergence['converged'] = not fs['n_iter'] == maxiter
    elif sep_method == 'nmf_sklearn':
        convergence['random_state'] = 'not yet implemented'
        convergence['iterations'] = 'not yet implemented'
        convergence['converged'] = 'not yet implemented'

    return S_sep.T, S_matched.T, A_sep, convergence


def subtract_pil(sig, pil, lower_bound=0, upper_bound=1.5):
    '''
    Subtract the neuropil from the signal, weighted such that the
    correlation between the two is minimized.

    Parameters
    ----------
    sig : array_like
        Signal
    pil : array_like
        Neuropil/s.
    lower_bound : float, optional
        Lower bound on the value of `a`, the gain on the neuropil
        before subtraction. Default is `0`.
    upper_bound : float, optional
        Upper bound on the value of `a`, the gain on the neuropil
        before subtraction. Default is `1.5`.

    Returns
    -------
    sig_corrected : numpy.ndarray
        The neuropil-subtracted signal.
    a : float
        The subtraction parameter that results in the best subtraction.

    Notes
    -----
    Will return
        sig_corrected = sig - a * pil
    where the `a` has been set so that `cor(sig_corrected, pil)` is
    minimized. The region of values for `a` which is searched is given
    by `(lower_bound, upper_bound)`.
    '''
    # Ensure array_like input is a numpy.ndarray
    sig = np.asarray(sig)
    pil = np.asarray(pil)

    def mincorr(x):
        '''Find the correlation between sig and pil, for subtraction
        with gain equal to `x`.'''
        sig_ = sig - x*pil
        corr = np.corrcoef(sig_, pil)[0, 1]
        return np.sqrt(corr**2)

    search_bounds = (lower_bound, upper_bound)
    res = minimize_scalar(mincorr, bounds=search_bounds, method='bounded')
    a = res.x  # the gain resulting in minimal correlation
    sig_corrected = sig - a*pil + np.mean(a*pil)

    return sig_corrected, a


def subtract_dict(S, n_noncell):
    '''
    Returns dictionary with the cell traces minus the background traces,
    with the subtraction method in subtractpil

    Parameters
    ----------
    S : dict
        Dictionary containing sets of traces
    n_noncell : int
        How many noncells there are (i.e. ROIs without neuropils)

    Returns
    -------
    ???
    '''
    S_subtract = {}
    a = {}
    for i in range(n_noncell, len(S)):
        S_subtract[i], a[i] = subtract_pil(S[i][:, 0],
                                           np.mean(S[i][:, 1:], axis=1))

    return S_subtract, a
