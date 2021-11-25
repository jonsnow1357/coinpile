#!/usr/bin/env python
# SPDX-License-Identifier: GPL-3.0-or-later
"""app"""

#import site #http://docs.python.org/library/site.html
import sys
import os
#import platform
import logging
import logging.config
#import re
#import time
#import datetime

#sys.path.append("./")
#sys.path.append("../")

#import math
#import csv
#import six
import argparse
import configparser
import web3
import json

logging.config.fileConfig("logging.cfg")
logger = logging.getLogger("app")

class Account(object):

  def __init__(self, public="", private=""):
    self.public_key = public
    self.private_key = private

class AppConfig(object):

  def __init__(self):
    self.blockchain_url = ""
    self.accounts = []
    self.tokens = {}

  def read(self, cfgPath, tokensPath):
    if (not os.path.isfile(cfgPath)):
      logger.error("file DOES NOT EXIST: {}".format(cliArgs["cfg"]))
      sys.exit(1)

    cfg_obj = configparser.ConfigParser()
    cfg_obj.optionxform = str  # will be case sensitive
    cfg_obj.read(cfgPath, encoding="utf-8")

    self.blockchain_url = cfg_obj["default"]["url"]
    for s in cfg_obj.sections():
      if (s.startswith("account")):
        acct = Account(cfg_obj[s]["public"])
        self.accounts.append(acct)

    if (not os.path.isfile(tokensPath)):
      logger.error("file DOES NOT EXIST: {}".format(cliArgs["cfg"]))
      sys.exit(1)

    cfg_obj = configparser.ConfigParser()
    cfg_obj.optionxform = str  # will be case sensitive
    cfg_obj.read(tokensPath, encoding="utf-8")

    for s in cfg_obj.sections():
      if (s.startswith("token")):
        tmp = {"address": "", "deploy": ""}
        if ("address" in cfg_obj[s].keys()):
          tmp["address"] = cfg_obj[s]["address"]
        if ("deploy" in cfg_obj[s].keys()):
          tmp["deploy"] = json.loads(cfg_obj[s]["deploy"])
        self.tokens[s] = tmp

_appCfg = AppConfig()
_bc = None  # THE blockchain

class Token(object):

  def __init__(self, contract):
    self.obj = contract
    self.symbol = self.obj.functions.symbol().call()
    self.decimals = int(self.obj.functions.decimals().call())

  def balanceOf(self, acctAddr):
    res = self.obj.functions.balanceOf(acctAddr).call()
    logger.info("token balance: {} {}".format(res / (10**self.decimals), self.symbol))
    return res

def _info():
  logger.info("last block: {}".format(_bc.eth.blockNumber))
  if (len(_bc.eth.accounts) > 0):
    for acct in _bc.eth.accounts:
      tmp = _bc.fromWei(_bc.eth.getBalance(acct), "ether")
      logger.info("acct {}: {} ETH".format(acct, tmp))
  else:
    for acct in _appCfg.accounts:
      tmp = _bc.fromWei(_bc.eth.getBalance(acct.public_key), "ether")
      logger.info("acct {}: {} ETH".format(acct.public_key, tmp))

def _test_token(name, addr):
  logger.info("testing {}".format(name))
  abi = json.load(open("contracts/{}/abi.json".format(name), "r"))
  token = Token(_bc.eth.contract(address=addr, abi=abi))

  bal1 = 50 * (10**token.decimals)
  bal2 = 100 * (10**token.decimals)
  res = token.balanceOf(_appCfg.accounts[0].public_key)
  if (res > bal1):
    logger.info("token burning ...")
    res = token.obj.functions.burn(res - bal1).transact()
    _bc.eth.waitForTransactionReceipt(res)
  res = token.balanceOf(_appCfg.accounts[0].public_key)
  if (res < bal2):
    logger.info("token minting ...")
    res = token.obj.functions.mint(_appCfg.accounts[0].public_key, (bal2 - res)).transact()
    _bc.eth.waitForTransactionReceipt(res)
  token.balanceOf(_appCfg.accounts[0].public_key)

def _test():
  if (_bc.eth.chainId != 1337):
    logger.warning("UNEXPECTED chain ID")
    return

  logger.info("running on ganache")
  #_bc.eth.defaultAccount = _bc.eth.accounts[0]
  _bc.eth.defaultAccount = _appCfg.accounts[0].public_key

  for k, v in _appCfg.tokens.items():
    if (v["address"] != ""):
      _test_token(k, v["address"])

def _deploy():
  if (_bc.eth.chainId != 1337):
    logger.warning("UNEXPECTED chain ID")
    return

  logger.info("running on ganache")
  #_bc.eth.defaultAccount = _bc.eth.accounts[0]
  _bc.eth.defaultAccount = _appCfg.accounts[0].public_key

  if (cliArgs["contract"] == ""):
    logger.info("nothing to deploy")
    return

  if (cliArgs["contract"] not in _appCfg.tokens.keys()):
    logger.info("contract not defined")
    return

  abi = json.load(open("contracts/{}/abi.json".format(cliArgs["contract"]), "r"))
  bytecode = open("contracts/{}/bytecode.bin".format(cliArgs["contract"]),
                  "r").read().strip(" \r\n")
  if (bytecode.startswith("0x")):
    bytecode = bytecode[2:]
  contract = _bc.eth.contract(abi=abi, bytecode=bytecode)

  params = _appCfg.tokens[cliArgs["contract"]]["deploy"]
  tx_hash = contract.constructor(*params).transact()
  tx_rec = _bc.eth.waitForTransactionReceipt(tx_hash)
  logger.info("contract address: {}".format(tx_rec["contractAddress"]))

def mainApp():
  global _bc

  _appCfg.read(cliArgs["cfg"], "tokens.cfg")
  _bc = web3.Web3(web3.Web3.HTTPProvider(_appCfg.blockchain_url))

  if (cliArgs["action"] == "info"):
    _info()
  elif (cliArgs["action"] == "test"):
    _test()
  elif (cliArgs["action"] == "deploy"):
    _deploy()

if (__name__ == "__main__"):
  modName = os.path.basename(__file__)
  modName = ".".join(modName.split(".")[:-1])

  #print("[{}] {}".format(modName, sys.prefix))
  #print("[{}] {}".format(modName, sys.exec_prefix))
  #print("[{}] {}".format(modName, sys.path))
  #for arg in sys.argv:
  #  print("[{}] {}".format(modName, arg))

  appDir = sys.path[0]  # folder where the script was invoked
  #appDir = os.getcwd()  # current folder
  appCfgPath = os.path.join(appDir, ("blockchain.cfg"))
  #print("[{}] {}".format(modName, appDir))
  #print("[{}] {}".format(modName, appCfgPath))
  #os.chdir(appDir)

  #pyauto_base.misc.changeLoggerName("{}.log".format(modName))

  appDesc = "token test"
  parser = argparse.ArgumentParser(description=appDesc)
  parser.add_argument("action", help="action", choices=("info", "test", "deploy"))
  parser.add_argument("-f", "--cfg", default=appCfgPath, help="configuration file path")
  parser.add_argument("-c", "--contract", default="", help="contract name")
  #parser.add_argument("-l", "--list", action="store_true", default=False,
  #                    help="list config file options")
  #parser.add_argument("-x", "--extra",
  #                    choices=("", ""),
  #                    help="extra parameters")

  cliArgs = vars(parser.parse_args())
  #logger.info(cliArgs)

  #parser.print_help()
  mainApp()
