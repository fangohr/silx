# coding: utf-8
# /*##########################################################################
#
# Copyright (c) 2016-2017 European Synchrotron Radiation Facility
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
"""URL module"""

__authors__ = ["V. Valls"]
__license__ = "MIT"
__date__ = "11/12/2017"


class DataUrl(object):
    """Non-mutable object to parse a string representing a resource data
    locator.

    It supports:

    - path to file and path inside file to the data
    - data slicing
    - fabio or silx access to the data
    - absolute and relative file access

    >>> # fabio access using absolute path
    >>> DataUrl("fabio:///data/image.edf::[2]")
    >>> DataUrl("fabio:///C:/data/image.edf::[2]")

    >>> # silx access using absolute path
    >>> DataUrl("silx:///data/image.h5::/data/dataset[1,5]")
    >>> DataUrl("silx:///data/image.edf::/scan_0/detector/data")
    >>> DataUrl("silx:///C:/data/image.edf::/scan_0/detector/data")

    >>> # Relative path access
    >>> DataUrl("silx:./image.h5")
    >>> DataUrl("fabio:./image.edf")
    >>> DataUrl("silx:image.h5")
    >>> DataUrl("fabio:image.edf")

    >>> # Is also support parsing of file access for convenience
    >>> DataUrl("./foo/bar/image.edf")
    >>> DataUrl("C:/data/")

    :param str path: Path representing a link to a data. If specified, other
        arguments are not used.
    :param str file_path: Link to the file containing the the data.
        None if there is no data selection.
    :param str data_path: Data selection applyed to the data file selected.
        None if there is no data selection.
    :param Tuple[int,slice,Ellipse] data_slice: Slicing applyed of the selected
        data. None if no slicing applyed.
    :param Union[str,None] scheme: Scheme of the URL. "silx", "fabio" or None
        is supported. Other strings can be provided, but :meth:`is_valid` while
        be false.
    """
    def __init__(self, path=None, file_path=None, data_path=None, data_slice=None, scheme=None):
        self.__is_valid = False
        if path is not None:
            assert(file_path is None)
            assert(data_path is None)
            assert(data_slice is None)
            assert(scheme is None)
            self.__parse_from_path(path)
        else:
            self.__file_path = file_path
            self.__data_path = data_path
            self.__data_slice = data_slice
            self.__scheme = scheme
            self.__path = None
            self.__check_validity()

    def __check_validity(self):
        """Check the validity of the attributes."""
        if self.__file_path in [None, ""]:
            self.__is_valid = False
            return

        if self.__scheme is None:
            self.__is_valid = True
        elif self.__scheme == "fabio":
            self.__is_valid = self.__data_path is None
        elif self.__scheme == "silx":
            # If there is a slice you must have a data path
            # But you can have a data path without slice
            slice_implies_data = (self.__data_path is None and self.__data_slice is None) or self.__data_path is not None
            self.__is_valid = slice_implies_data
        else:
            self.__is_valid = False

    def __parse_from_path(self, path):
        """Parse the path and initialize attributes.

        :param str path: Path representing the URL.
        """
        def str_to_slice(string):
            if string == "...":
                return Ellipsis
            elif string == ":":
                return slice(None)
            else:
                return int(string)

        elements = path.split("::", 1)
        self.__path = path

        scheme_and_filepath = elements[0].split(":", 1)
        if len(scheme_and_filepath) == 2:
            if len(scheme_and_filepath[0]) <= 2:
                # Windows driver
                self.__scheme = None
                file_path = elements[0]
            else:
                self.__scheme = scheme_and_filepath[0]
                file_path = scheme_and_filepath[1]
        else:
            self.__scheme = None
            file_path = scheme_and_filepath[0]

        if file_path.startswith("///"):
            # absolute path
            file_path = file_path[3:]
            if len(file_path) > 2 and (file_path[1] == ":" or file_path[2] == ":"):
                # Windows driver
                pass
            else:
                file_path = "/" + file_path
        self.__file_path = file_path

        self.__data_slice = None
        self.__data_path = None
        if len(elements) == 1:
            pass
        else:
            selector = elements[1]
            selectors = selector.split("[", 1)
            data_path = selectors[0]
            if len(data_path) == 0:
                data_path = None
            self.__data_path = data_path

            if len(selectors) == 2:
                data_slice = selectors[1].split("]", 1)
                if len(data_slice) < 2 or data_slice[1] != "":
                    self.__is_valid = False
                    return
                data_slice = data_slice[0].split(",")
                try:
                    data_slice = tuple(str_to_slice(s) for s in data_slice)
                    self.__data_slice = data_slice
                except ValueError:
                    self.__is_valid = False
                    return

        self.__check_validity()

    def is_valid(self):
        """Returns true if the URL is valid. Else attributes can be None.

        :rtype: bool
        """
        return self.__is_valid

    def path(self):
        """Returns the string representing the URL.

        :rtype: str
        """
        if self.__path is not None:
            return self.__path

        def slice_to_string(data_slice):
            if data_slice == Ellipsis:
                return "..."
            elif data_slice == slice(None):
                return ":"
            elif isinstance(data_slice, int):
                return str(data_slice)
            else:
                raise TypeError("Unexpected slicing type. Found %s" % type(data_slice))

        path = ""
        selector = ""
        if self.__file_path is not None:
            path += self.__file_path
        if self.__data_path is not None:
            selector += self.__data_path
        if self.__data_slice is not None:
            selector += "[%s]" % ",".join([slice_to_string(s) for s in self.__data_slice])

        if selector != "":
            path = path + "::" + selector

        if self.__scheme is not None:
            if self.is_absolute():
                if path.startswith("/"):
                    path = self.__scheme + "://" + path
                else:
                    path = self.__scheme + ":///" + path
            else:
                path = self.__scheme + ":" + path

        return path

    def is_absolute(self):
        """Returns true if the file path is an absolute path.

        :rtype: bool
        """
        file_path = self.file_path()
        if len(file_path) > 0:
            if file_path[0] == "/":
                return True
        if len(file_path) > 2:
            # Windows
            if file_path[1] == ":" or file_path[2] == ":":
                return True
        elif len(file_path) > 1:
            # Windows
            if file_path[1] == ":":
                return True
        return False

    def file_path(self):
        """Returns the path to the file containing the data.

        :rtype: str
        """
        return self.__file_path

    def data_path(self):
        """Returns the path inside the file to the data.

        :rtype: str
        """
        return self.__data_path

    def data_slice(self):
        """Returns the slicing applyed to the data.

        It is a tuple containing numbers, slice or ellipses.

        :rtype: Tuple[int, slice, Ellipse]
        """
        return self.__data_slice

    def scheme(self):
        """Returns the scheme. It can be None if no scheme is specified.

        :rtype: Union[str, None]
        """
        return self.__scheme