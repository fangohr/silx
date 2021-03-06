# coding: utf-8
# /*##########################################################################
#
# Copyright (c) 2016-2018 European Synchrotron Radiation Facility
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# ###########################################################################*/
"""This is a convenient package to use from Python or IPython interpreter.
It loads the main features of silx and provides high-level functions.

>>> from silx import sx

When used in an interpreter is sets-up Qt and loads some silx widgets.
When used in a `jupyter <https://jupyter.org/>`_  /
`IPython <https://ipython.org/>`_ notebook, neither Qt nor silx widgets are loaded.

When used in `IPython <https://ipython.org/>`_, it also runs ``%pylab``,
thus importing `numpy <http://www.numpy.org/>`_ and `matplotlib <https://matplotlib.org/>`_.
"""


__authors__ = ["T. Vincent"]
__license__ = "MIT"
__date__ = "16/01/2017"


import logging as _logging
import sys as _sys


_logger = _logging.getLogger(__name__)


# Init logging when used from the console
if hasattr(_sys, 'ps1'):
    _logging.basicConfig()

# Probe ipython
try:
    from IPython import get_ipython as _get_ipython
except (NameError, ImportError):
    _get_ipython = None

# Probe ipython/jupyter notebook
if _get_ipython is not None and _get_ipython() is not None:

    # Notebook detection probably fragile
    _IS_NOTEBOOK = ('parent_appname' in _get_ipython().config['IPKernelApp'] or
                    hasattr(_get_ipython(), 'kernel'))
else:
    _IS_NOTEBOOK = False


# Load Qt and widgets only if running from console
if _IS_NOTEBOOK:
    _logger.warning(
        'Not loading silx.gui features: Running from the notebook')

else:
    from silx.gui import qt

    if hasattr(_sys, 'ps1'):  # If from console, make sure QApplication runs
        qapp = qt.QApplication.instance() or qt.QApplication([])

        # Change windows default icon
        from silx.gui import icons as _icons
        qapp.setWindowIcon(_icons.getQIcon('silx'))
        del _icons  # clean-up namespace

    from silx.gui.plot import *  # noqa
    from ._plot import plot, imshow, ginput  # noqa

    try:
        import OpenGL as _OpenGL
    except ImportError:
        _logger.warning(
            'Not loading silx.gui.plot3d features: PyOpenGL is not installed')
    else:
        del _OpenGL  # clean-up namespace
        from ._plot3d import contour3d, points3d  # noqa


# %pylab
if _get_ipython is not None and _get_ipython() is not None:
    _get_ipython().enable_pylab(gui='inline' if _IS_NOTEBOOK else 'qt',
                                import_all=False)


# Clean-up
del _sys
del _get_ipython
del _IS_NOTEBOOK


# Load some silx stuff in namespace
from silx import version  # noqa
from silx.io import open  # noqa
from silx.io import *  # noqa
from silx.math import Histogramnd, HistogramndLut  # noqa
from silx.math.fit import leastsq  # noqa
