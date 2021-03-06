# coding: utf-8
# /*##########################################################################
#
# Copyright (c) 2004-2018 European Synchrotron Radiation Facility
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
"""
:mod:`silx.gui.plot.actions.medfilt` provides a set of QAction to apply filter
on data contained in a :class:`.PlotWidget`.

The following QAction are available:

- :class:`MedianFilterAction`
- :class:`MedianFilter1DAction`
- :class:`MedianFilter2DAction`

"""

from __future__ import division

__authors__ = ["V.A. Sole", "T. Vincent", "P. Knobel"]
__license__ = "MIT"

__date__ = "03/01/2018"

from . import PlotAction
from silx.gui.widgets.MedianFilterDialog import MedianFilterDialog
from silx.math.medianfilter import medfilt2d
import logging

_logger = logging.getLogger(__name__)


class MedianFilterAction(PlotAction):
    """QAction to plot the pixels intensities diagram

    :param plot: :class:`.PlotWidget` instance on which to operate
    :param parent: See :class:`QAction`
    """

    def __init__(self, plot, parent=None):
        PlotAction.__init__(self,
                            plot,
                            icon='median-filter',
                            text='median filter',
                            tooltip='Apply a median filter on the image',
                            triggered=self._triggered,
                            parent=parent)
        self._originalImage = None
        self._legend = None
        self._filteredImage = None
        self._popup = MedianFilterDialog(parent=plot)
        self._popup.sigFilterOptChanged.connect(self._updateFilter)
        self.plot.sigActiveImageChanged.connect(self._updateActiveImage)
        self._updateActiveImage()

    def _triggered(self, checked):
        """Update the plot of the histogram visibility status

        :param bool checked: status  of the action button
        """
        self._popup.show()

    def _updateActiveImage(self):
        """Set _activeImageLegend and _originalImage from the active image"""
        self._activeImageLegend = self.plot.getActiveImage(just_legend=True)
        if self._activeImageLegend is None:
            self._originalImage = None
            self._legend = None
        else:
            self._originalImage = self.plot.getImage(self._activeImageLegend).getData(copy=False)
            self._legend = self.plot.getImage(self._activeImageLegend).getLegend()

    def _updateFilter(self, kernelWidth, conditional=False):
        if self._originalImage is None:
            return

        self.plot.sigActiveImageChanged.disconnect(self._updateActiveImage)
        filteredImage = self._computeFilteredImage(kernelWidth, conditional)
        self.plot.addImage(data=filteredImage,
                           legend=self._legend,
                           replace=True)
        self.plot.sigActiveImageChanged.connect(self._updateActiveImage)

    def _computeFilteredImage(self, kernelWidth, conditional):
        raise NotImplementedError('MedianFilterAction is a an abstract class')

    def getFilteredImage(self):
        """
        :return: the image with the median filter apply on"""
        return self._filteredImage


class MedianFilter1DAction(MedianFilterAction):
    """Define the MedianFilterAction for 1D

    :param plot: :class:`.PlotWidget` instance on which to operate
    :param parent: See :class:`QAction`
    """
    def __init__(self, plot, parent=None):
        MedianFilterAction.__init__(self,
                                    plot,
                                    parent=parent)

    def _computeFilteredImage(self, kernelWidth, conditional):
        assert(self.plot is not None)
        return medfilt2d(self._originalImage,
                         (kernelWidth, 1),
                         conditional)


class MedianFilter2DAction(MedianFilterAction):
    """Define the MedianFilterAction for 2D

    :param plot: :class:`.PlotWidget` instance on which to operate
    :param parent: See :class:`QAction`
    """
    def __init__(self, plot, parent=None):
        MedianFilterAction.__init__(self,
                                    plot,
                                    parent=parent)

    def _computeFilteredImage(self, kernelWidth, conditional):
        assert(self.plot is not None)
        return medfilt2d(self._originalImage,
                         (kernelWidth, kernelWidth),
                         conditional)
