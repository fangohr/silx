# coding: utf-8
#/*##########################################################################
# Copyright (C) 2004-2016 V.A. Sole, European Synchrotron Radiation Facility
#
# This file is part of the PyMca X-ray Fluorescence Toolkit developed at
# the ESRF by the Software group.
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
# #########################################################################*/
"""Background configuration widget"""
import sys
import numpy
from silx.gui import qt
from silx.gui.plot import PlotWindow
from silx.math.fit import filters

__authors__ = ["V.A. Sole", "P. Knobel"]
__license__ = "MIT"
__date__ = "05/10/2016"


class HorizontalSpacer(qt.QWidget):
    def __init__(self, *args):
        qt.QWidget.__init__(self, *args)
        self.setSizePolicy(qt.QSizePolicy(qt.QSizePolicy.Expanding,
                                          qt.QSizePolicy.Fixed))


class BackgroundParamWidget(qt.QWidget):
    """Background configuration widget.

    Strip and snip filters parameters can be adjusted, and
    the computed backgrounds are plotted next to the original data to
    show the result."""
    sigBackgroundParamWidgetSignal = qt.pyqtSignal(object)

    def __init__(self, parent=None):
        qt.QWidget.__init__(self, parent)

        self.mainLayout = qt.QGridLayout(self)
        self.mainLayout.setColumnStretch(1, 1)

        # Algorithm choice ---------------------------------------------------
        self.algorithmComboLabel = qt.QLabel(self)
        self.algorithmComboLabel.setText("Background algorithm")
        self.algorithmCombo = qt.QComboBox(self)
        self.algorithmCombo.addItem("Strip")
        self.algorithmCombo.addItem("Snip")
        self.algorithmCombo.activated[int].connect(
                self._algorithmComboActivated)

        # Strip parameters ---------------------------------------------------
        self.stripWidthLabel = qt.QLabel(self)
        self.stripWidthLabel.setText("Strip Width")

        self.stripWidthSpin = qt.QSpinBox(self)
        self.stripWidthSpin.setMaximum(100)
        self.stripWidthSpin.setMinimum(1)
        self.stripWidthSpin.valueChanged[int].connect(self._emitSignal)

        self.stripIterLabel = qt.QLabel(self)
        self.stripIterLabel.setText("Strip Iterations")
        self.stripIterValue = qt.QLineEdit(self)
        validator = qt.QIntValidator(self.stripIterValue)
        self.stripIterValue._v = validator
        self.stripIterValue.setText("0")
        self.stripIterValue.editingFinished[()].connect(self._emitSignal)

        # Snip parameters ----------------------------------------------------
        self.snipWidthLabel = qt.QLabel(self)
        self.snipWidthLabel.setText("SNIP Width")

        self.snipWidthSpin = qt.QSpinBox(self)
        self.snipWidthSpin.setMaximum(300)
        self.snipWidthSpin.setMinimum(0)
        self.snipWidthSpin.valueChanged[int].connect(self._emitSignal)


        # Smoothing parameters -----------------------------------------------
        self.smoothingFlagCheck = qt.QCheckBox(self)
        self.smoothingFlagCheck.setText("Smoothing Width (Savitsky-Golay)")
        self.smoothingFlagCheck.toggled.connect(self._smoothingToggled)

        self.smoothingSpin = qt.QSpinBox(self)
        self.smoothingSpin.setMinimum(3)
        #self.smoothingSpin.setMaximum(40)
        self.smoothingSpin.setSingleStep(2)
        self.smoothingSpin.valueChanged[int].connect(self._emitSignal)

        # Anchors ------------------------------------------------------------

        self.anchorsGroup = qt.QWidget(self)
        anchorsLayout = qt.QHBoxLayout(self.anchorsGroup)
        anchorsLayout.setSpacing(2)
        anchorsLayout.setContentsMargins(0, 0, 0, 0)

        self.anchorsFlagCheck = qt.QCheckBox(self.anchorsGroup)
        self.anchorsFlagCheck.setText("Use anchors")
        self.anchorsFlagCheck.setToolTip(
                "Define X coordinates of points that must remain fixed")
        self.anchorsFlagCheck.stateChanged[int].connect(
                self._anchorsToggled)
        anchorsLayout.addWidget(self.anchorsFlagCheck)

        maxnchannel = 16384 * 4    # Fixme ?
        self.anchorsList = []
        num_anchors = 4
        for i in range(num_anchors):
            anchorSpin = qt.QSpinBox(self.anchorsGroup)
            anchorSpin.setMinimum(0)
            anchorSpin.setMaximum(maxnchannel)
            anchorSpin.valueChanged[int].connect(self._emitSignal)
            anchorsLayout.addWidget(anchorSpin)
            self.anchorsList.append(anchorSpin)

        # Layout ------------------------------------------------------------
        self.mainLayout.addWidget(self.algorithmComboLabel, 0, 0)
        self.mainLayout.addWidget(self.algorithmCombo, 0, 2)
        self.mainLayout.addWidget(self.stripWidthLabel, 1, 0)
        self.mainLayout.addWidget(self.stripWidthSpin, 1, 2)
        self.mainLayout.addWidget(self.stripIterLabel, 2, 0)
        self.mainLayout.addWidget(self.stripIterValue, 2, 2)
        self.mainLayout.addWidget(self.snipWidthLabel, 3, 0)
        self.mainLayout.addWidget(self.snipWidthSpin, 3, 2)
        self.mainLayout.addWidget(self.smoothingFlagCheck, 4, 0)
        self.mainLayout.addWidget(self.smoothingSpin, 4, 2)
        self.mainLayout.addWidget(self.anchorsGroup, 5, 0, 1, 4)

        # Initialize interface -----------------------------------------------
        self._setAlgorithm("strip")
        self.smoothingFlagCheck.setChecked(False)
        self._smoothingToggled(is_checked=False)
        self.anchorsFlagCheck.setChecked(False)
        self._anchorsToggled(is_checked=False)

    def _algorithmComboActivated(self, algorithm_index):
        self._setAlgorithm("strip" if algorithm_index == 0 else "snip")

    def _setAlgorithm(self, algorithm):
        """Enable/disable snip and snip input widgets, depending on the
        chosen algorithm.
        :param algorithm: "snip" or "strip"
        """
        if algorithm not in ["strip", "snip"]:
            raise ValueError(
                    "Unknown background filter algorithm %s" % algorithm)

        self.algorithm = algorithm
        self.stripWidthSpin.setEnabled(algorithm == "strip")
        self.stripIterValue.setEnabled(algorithm == "strip")
        self.snipWidthSpin.setEnabled(algorithm == "snip")

    def _smoothingToggled(self, is_checked):
        """Enable/disable smoothing input widgets, emit dictionary"""
        self.smoothingSpin.setEnabled(is_checked)
        self._emitSignal()

    def _anchorsToggled(self, is_checked):
        """Enable/disable all spin widgets defining anchor X coordinates,
        emit signal.
        """
        for anchor_spin in self.anchorsList:
            anchor_spin.setEnabled(is_checked)
        self._emitSignal()

    def setParameters(self, ddict):
        if "algorithm" in ddict:
            self._setAlgorithm(ddict["algorithm"])

        if "snipwidth" in ddict:
            self.snipWidthSpin.setValue(int(ddict["snipwidth"]))

        if "stripwidth" in ddict:
            self.stripWidthSpin.setValue(int(ddict["stripwidth"]))

        if "stripiterations" in ddict:
            self.stripIterValue.setText("%d" % int(ddict["stripiterations"]))

        if "smoothingflag" in ddict:
            self.self.smoothingFlagCheck.setChecked(bool(ddict["smoothingflag"]))

        if "smoothingwidth" in ddict:
            self.smoothingSpin.setValue(int(ddict["smoothingwidth"]))

        if "anchorsflag" in ddict:
            self.anchorsFlagCheck.setChecked(bool(ddict["anchorsflag"]))

        if "anchorslist" in ddict:
            anchorslist = ddict["anchorslist"]
            if anchorslist in [None, 'None']:
                anchorslist = []
            for spin in self.anchorsList:
                spin.setValue(0)

            i = 0
            for value in anchorslist:
                self.anchorsList[i].setValue(int(value))
                i += 1

    def getParameters(self):
        """Return dictionary of parameters defined in the GUI

        The returned dictionary contains following values:

            - *algorithm*: *"strip"* or *"snip"*
            - *stripwidth*: width of strip iterator
            - *stripiterations*: number of iterations
            - *snipwidth*: width of snip algorithm
            - *smoothingflag*: flag to enable/disable smoothing
            - *smoothingwidth*: width of Savitsky-Golay smoothing filter
            - *anchorsflag*: flag to enable/disable anchors
            - *anchorslist*: list of anchors (X coordinates of fixed values)
            """
        stripitertext = self.stripIterValue.text()
        stripiter = int(stripitertext) if len(stripitertext) else 0

        return {"algorithm": self.algorithm,
                "stripthreshold": 1.0,
                "snipwidth": self.snipWidthSpin.value(),
                "stripiterations": stripiter,
                "stripwidth": self.stripWidthSpin.value(),
                "smoothingflag": self.smoothingFlagCheck.isChecked(),
                "smoothingwidth": self.smoothingSpin.value(),
                "anchorsflag": self.anchorsFlagCheck.isChecked(),
                "anchorslist": [spin.value() for spin in self.anchorsList]}

    def _emitSignal(self, dummy=None):
        self.sigBackgroundParamWidgetSignal.emit(
            {'event': 'ParametersChanged',
             'parameters': self.getParameters()})


class BackgroundWidget(qt.QWidget):
    """Background configuration widget, with a :class:`PlotWindow`.

    Strip and snip filters parameters can be adjusted, and
    the computed backgrounds are plotted next to the original data to
    show the result."""
    def __init__(self, parent=None):
        qt.QWidget.__init__(self, parent)
        self.setWindowTitle("Strip and SNIP Configuration Window")
        self.mainLayout = qt.QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(2)
        self.parametersWidget = BackgroundParamWidget(self)
        self.graphWidget = PlotWindow(parent=self,
                                      colormap=False,
                                      roi=False,
                                      mask=False,
                                      fit=False)
        self.mainLayout.addWidget(self.parametersWidget)
        self.mainLayout.addWidget(self.graphWidget)
        self.getParameters = self.parametersWidget.getParameters
        self.setParameters = self.parametersWidget.setParameters
        self._x = None
        self._y = None
        self.parametersWidget.sigBackgroundParamWidgetSignal.connect(self._slot)

    def setData(self, x, y):
        self._x = x
        self._y = y
        self.update(resetzoom=True)

    def _slot(self, ddict):
        self.update()

    def update(self, resetzoom=False):
        if self._y is None:
            return

        pars = self.getParameters()

        # smoothed data
        y = numpy.ravel(numpy.array(self._y)).astype(numpy.float)
        if pars["smoothingflag"]:
            ysmooth = filters.savitsky_golay(y, pars['smoothingwidth'])
            f = [0.25, 0.5, 0.25]
            ysmooth[1:-1] = numpy.convolve(ysmooth, f, mode=0)
            ysmooth[0] = 0.5 * (ysmooth[0] + ysmooth[1])
            ysmooth[-1] = 0.5 * (ysmooth[-1] + ysmooth[-2])
        else:
            ysmooth = y


        # loop for anchors
        x = self._x
        niter = pars['stripiterations']
        anchors_indices = []
        if pars['anchorsflag'] and pars['anchorslist'] is not None:
            ravelled = x
            for channel in pars['anchorslist']:
                if channel <= ravelled[0]:
                    continue
                index = numpy.nonzero(ravelled >= channel)[0]
                if len(index):
                    index = min(index)
                    if index > 0:
                        anchors_indices.append(index)

        stripBackground = filters.strip(ysmooth,
                                        w=pars['stripwidth'],
                                        niterations=niter,
                                        factor=pars['stripthreshold'],
                                        anchors=anchors_indices)

        if niter >= 1000:
            # final smoothing
            stripBackground = filters.strip(stripBackground,
                                            w=1,
                                            niterations=50*pars['stripwidth'],
                                            factor=pars['stripthreshold'],
                                            anchors=anchors_indices)

        if len(anchors_indices) == 0:
            anchors_indices = [0, len(ysmooth)-1]
        anchors_indices.sort()
        snipBackground = 0.0 * ysmooth
        lastAnchor = 0
        width = pars['snipwidth']
        for anchor in anchors_indices:
            if (anchor > lastAnchor) and (anchor < len(ysmooth)):
                snipBackground[lastAnchor:anchor] =\
                            filters.snip1d(ysmooth[lastAnchor:anchor], width)
                lastAnchor = anchor
        if lastAnchor < len(ysmooth):
            snipBackground[lastAnchor:] =\
                            filters.snip1d(ysmooth[lastAnchor:], width)

        self.graphWidget.addCurve(x, y,
                                  legend='Input Data',
                                  replace=True,
                                  resetzoom=resetzoom)
        self.graphWidget.addCurve(x, stripBackground,
                                  legend='Strip Background',
                                  resetzoom=False)
        self.graphWidget.addCurve(x, snipBackground,
                                  legend='SNIP Background',
                                  resetzoom=False)


class BackgroundDialog(qt.QDialog):
    def __init__(self, parent=None):
        qt.QDialog.__init__(self, parent)
        self.setWindowTitle("Strip and SNIP Configuration Window")
        self.mainLayout = qt.QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(2)
        self.parametersWidget = BackgroundWidget(self)
        self.setData = self.parametersWidget.setData
        self.getParameters = self.parametersWidget.getParameters
        self.setParameters = self.parametersWidget.setParameters
        self.mainLayout.addWidget(self.parametersWidget)
        hbox = qt.QWidget(self)
        hboxLayout = qt.QHBoxLayout(hbox)
        hboxLayout.setContentsMargins(0, 0, 0, 0)
        hboxLayout.setSpacing(2)
        self.okButton = qt.QPushButton(hbox)
        self.okButton.setText("OK")
        self.okButton.setAutoDefault(False)
        self.dismissButton = qt.QPushButton(hbox)
        self.dismissButton.setText("Cancel")
        self.dismissButton.setAutoDefault(False)
        hboxLayout.addWidget(HorizontalSpacer(hbox))
        hboxLayout.addWidget(self.okButton)
        hboxLayout.addWidget(self.dismissButton)
        self.mainLayout.addWidget(hbox)
        self.dismissButton.clicked.connect(self.reject)
        self.okButton.clicked.connect(self.accept)

    def sizeHint(self):
        return qt.QSize(int(1.5*qt.QDialog.sizeHint(self).width()),
                        qt.QDialog.sizeHint(self).height())


def main():
    # synthetic data
    from silx.math.fit.functions import sum_gauss

    x = numpy.arange(5000)
    # (height1, center1, fwhm1, ...) 5 peaks
    params1 = (50, 500, 100,
               20, 2000, 200,
               50, 2250, 100,
               40, 3000, 75,
               23, 4000, 150)
    y0 = sum_gauss(x, *params1)

    # random values between [-1;1]
    noise = 2 * numpy.random.random(5000) - 1
    # make it +- 5%
    noise *= 0.05

    # 2 gaussians with very large fwhm, as background signal
    actual_bg = sum_gauss(x, 15, 3500, 3000, 5, 1000, 1500)

    # Add 5% random noise to gaussians and add background
    y = y0 + numpy.average(y0) * noise + actual_bg

    # Open widget
    a = qt.QApplication(sys.argv)
    a.lastWindowClosed.connect(a.quit)

    def mySlot(ddict):
        print(ddict)

    w = BackgroundDialog()
    w.parametersWidget.parametersWidget.sigBackgroundParamWidgetSignal.connect(mySlot)
    w.setData(x, y)
    w.exec_()
    #a.exec_()

if __name__ == "__main__":
    main()
