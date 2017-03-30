# -*- encoding: utf-8 -*-
"""
pyvas Response
==============
"""
from __future__ import unicode_literals

from .utils import lxml_to_dict
from .exceptions import ResultError, HTTPError, ElementExists


class Response(dict):
    """Object which contains an server"s response to an OMP request."""

    def __init__(self, req=None, resp=None, callback=None):
        super(Response, self).__init__()
        try:
            self.status_code = int(resp.get("status"))
        except (ValueError, TypeError):
            raise TypeError("The status code must be an integer.")

        self.reason = resp.get("status_text", None)
        self.command = resp.tag.replace("_response", "")
        self.raw = resp
        self.request = req
        try:
            if callback is None:
                self.data = list(lxml_to_dict(resp).values())[0]
            else:
                self.data = callback(resp)
        except (KeyError, TypeError):
            raise ResultError(self.command, self.reason)

    def __str__(self):
        return str(self.data)

    def __bool__(self):
        """Returns True if status code between 200 and 400."""
        return self.ok

    __nonzero__ = __bool__

    def __repr__(self):
        return "<Response {} [{}]>".format(self.command, self.status_code)

    def __getitem__(self, key):
        return self.data[key]

    def __delitem__(self, key):
        del self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __contains__(self, key):
        return key in self.data

    def __iter__(self):
        return iter(self.data)

    def get(self, key, default=None):
        return self.data.get(key, default)

    def update(self, *args, **kwargs):
        self.data.update(*args, **kwargs)

    def pop(self, key, default=None):
        return self.data.pop(key, default)

    @property
    def ok(self):
        """Returns True if response code between 100 and 399"""
        try:
            self.raise_for_status()
        except HTTPError:
            return False
        return True

    @property
    def xml(self):
        """Returns response in lxml element tree object"""
        return self.raw

    def raise_for_status(self):
        """Raises HTTPError, if one occured."""
        error_msg = ""

        if 400 <= self.status_code < 500:
            error_msg = "{} Client Error: {}".format(self.status_code,
                                                     self.reason)

            if self.status_code == 400:
                if "exists" in self.reason:
                    raise ElementExists(error_msg, response=self)

        elif 500 <= self.status_code < 600:
            error_msg = "{} Server Error: {}".format(self.status_code,
                                                     self.reason)

        if error_msg:
            raise HTTPError(error_msg, response=self)
