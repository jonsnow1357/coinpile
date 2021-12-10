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
import configparser
import json

logger = logging.getLogger("lib")
import base

class AppConfig(object):

  def __init__(self):
    self.blockchain_url = ""
    self.accounts = []
    self.tokens = {}

  def _read_blockchain(self, cfgPath: str):
    if (not os.path.isfile(cfgPath)):
      logger.error(f"file DOES NOT EXIST: {cfgPath}")
      sys.exit(1)

    cfg_obj = configparser.ConfigParser()
    cfg_obj.optionxform = str  # will be case sensitive
    cfg_obj.read(cfgPath, encoding="utf-8")

    self.blockchain_url = cfg_obj["default"]["url"]
    for s in cfg_obj.sections():
      if (s.startswith("account")):
        acct = base.Account(cfg_obj[s]["public"])
        self.accounts.append(acct)

  def _read_tokens(self, tokensPath: str):
    if (not os.path.isfile(tokensPath)):
      logger.error(f"file DOES NOT EXIST: {tokensPath}")
      sys.exit(1)

    cfg_obj = configparser.ConfigParser()
    cfg_obj.optionxform = str  # will be case sensitive
    cfg_obj.read(tokensPath, encoding="utf-8")

    for s in cfg_obj.sections():
      if (s.startswith("token")):
        tmp = {"contract": "", "address": "", "deploy": ""}
        if ("contract" in cfg_obj[s].keys()):
          tmp["contract"] = os.path.join(".", "contracts", cfg_obj[s]["contract"])
        if ("address" in cfg_obj[s].keys()):
          tmp["address"] = cfg_obj[s]["address"]
        if ("deploy" in cfg_obj[s].keys()):
          tmp["deploy"] = json.loads(cfg_obj[s]["deploy"])

        if (tmp["contract"] == ""):
          logger.info(f"ignoring {s} - no contract")
        elif (not os.path.isdir(tmp["contract"])):
          logger.info(f"ignoring {s} - no folder")
        else:
          self.tokens[s] = tmp

  def read(self, cfgPath: str, tokensPath: str):
    self._read_blockchain(cfgPath)
    self._read_tokens(tokensPath)

  def showInfo(self):
    logger.info(f"blockchain URL: {self.blockchain_url}")

    logger.info(f"{len(self.accounts)} account(s)")

    logger.info(f"{len(self.tokens)} token(s)")
