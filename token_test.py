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
    self.bcObj = None

  def read(self, fPath):
    raise NotImplementedError

_appCfg = AppConfig()

def _init(fPath):
  cfg_obj = configparser.ConfigParser()
  cfg_obj.optionxform = str  # will be case sensitive
  cfg_obj.read(fPath, encoding="utf-8")

  _appCfg.blockchain_url = cfg_obj["default"]["url"]
  for s in cfg_obj.sections():
    if(s.startswith("account")):
      acct = Account(cfg_obj[s]["public"], cfg_obj[s]["private"])
      _appCfg.accounts.append(acct)

def _token_balance(token, acctAddr):
  res = token.functions.balanceOf(acctAddr).call()
  logger.info("token balance: {}".format(res))
  return res

def _test_token(name, addr):
  abi = json.load(open("{}/abi.json".format(name), "r"))

  token = _appCfg.bcObj.eth.contract(address=addr, abi=abi)
  decimals = int(token.functions.decimals().call())
  sym = token.functions.symbol().call()
  #_appCfg.bcObj.eth.defaultAccount = _appCfg.bcObj.eth.accounts[0]
  _appCfg.bcObj.eth.defaultAccount = _appCfg.accounts[0].public_key

  res = _token_balance(token, _appCfg.accounts[0].public_key)
  if(res > 50 * (10 ** decimals)):
    logger.info("token burning ...")
    res = token.functions.burn(res - 5000).transact()
    _appCfg.bcObj.eth.waitForTransactionReceipt(res)
  res = _token_balance(token, _appCfg.accounts[0].public_key)
  if(res < 100 * (10 ** decimals)):
    logger.info("token minting ...")
    res = token.functions.mint(_appCfg.accounts[0].public_key, (10000 - res)).transact()
    _appCfg.bcObj.eth.waitForTransactionReceipt(res)
  _token_balance(token, _appCfg.accounts[0].public_key)

def mainApp():
  if(os.path.isfile(cliArgs["cfg"])):
    _init(cliArgs["cfg"])
  else:
    logger.error("file DOES NOT EXIST: {}".format(cliArgs["cfg"]))
    sys.exit(1)

  _appCfg.bcObj = web3.Web3(web3.Web3.HTTPProvider(_appCfg.blockchain_url))


  logger.info("last block: {}".format(_appCfg.bcObj.eth.blockNumber))
  logger.info("acct0 ETH: {}".format(_appCfg.bcObj.fromWei(_appCfg.bcObj.eth.getBalance(_appCfg.accounts[0].public_key), "ether")))

  if(_appCfg.bcObj.eth.chainId == 1337):
    logger.info("running on ganache")
    _test_token("FancyToken", "0xc2E14CfB37D4397C4a8B79b1fC02632B0201e2fe")

if (__name__ == "__main__"):
  modName = os.path.basename(__file__)
  modName = ".".join(modName.split(".")[:-1])

  #print("[{}] {}".format(modName, sys.prefix))
  #print("[{}] {}".format(modName, sys.exec_prefix))
  #print("[{}] {}".format(modName, sys.path))
  #for arg in sys.argv:
  #  print("[{}] {}".format(modName, arg))

  #appDir = sys.path[0]  # folder where the script was invoked
  #appDir = os.getcwd()  # current folder
  #appCfgPath = os.path.join(appDir, (modName + ".cfg"))
  #print("[{}] {}".format(modName, appDir))
  #print("[{}] {}".format(modName, appCfgPath))
  #os.chdir(appDir)

  #pyauto_base.misc.changeLoggerName("{}.log".format(modName))

  appDesc = "token test"
  parser = argparse.ArgumentParser(description=appDesc)
  parser.add_argument("cfg", help="config file (<file_name>.ini)")
  #parser.add_argument("-f", "--cfg", default=appCfgPath,
  #                    help="configuration file path")  
  #parser.add_argument("-l", "--list", action="store_true", default=False,
  #                    help="list config file options")  
  #parser.add_argument("-x", "--extra",          
  #                    choices=("", ""),         
  #                    help="extra parameters")  

  cliArgs = vars(parser.parse_args())
  #logger.info(cliArgs)

  #parser.print_help()
  mainApp()
