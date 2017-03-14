#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
from zipline_poloniex.skeleton import fib

__author__ = "Florian Wilhelm"
__copyright__ = "Florian Wilhelm"
__license__ = "new-bsd"


def test_fib():
    assert fib(1) == 1
    assert fib(2) == 1
    assert fib(7) == 13
    with pytest.raises(AssertionError):
        fib(-10)
