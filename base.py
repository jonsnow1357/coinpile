#!/usr/bin/env python
# SPDX-License-Identifier: GPL-3.0-or-later
"""library"""

#import site #http://docs.python.org/library/site.html
import sys
import os
#import platform
import logging
#import re
#import time
#import datetime

#sys.path.append("./")
#sys.path.append("../")

#import math
#import csv
#import six

logger = logging.getLogger("lib")

class Account(object):

  def __init__(self, public="", private=""):
    self.public_key = public
    self.private_key = private

class Token(object):

  def __init__(self, contract):
    self.obj = contract
    self.symbol = self.obj.functions.symbol().call()
    self.decimals = int(self.obj.functions.decimals().call())

  def balanceOf(self, acctAddr):
    res = self.obj.functions.balanceOf(acctAddr).call()
    logger.info(f"token balance: {res / (10**self.decimals)} {self.symbol}")
    return res
