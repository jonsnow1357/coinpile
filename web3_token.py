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
import json
import web3
import web3.exceptions

logging.config.fileConfig("logging.cfg")
logger = logging.getLogger("app")

import base
import config

_appCfg = config.AppConfig()
_bc = None  # THE blockchain

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

def _test_token_mint_burn(tknName: str, tknDict: dict):
  abi = json.load(open(os.path.join(tknDict["contract"], "abi.json"), "r"))
  token = base.Token(_bc.eth.contract(address=tknDict["address"], abi=abi))

  #_bc.eth.defaultAccount = _bc.eth.accounts[0]
  _bc.eth.defaultAccount = _appCfg.accounts[0].public_key

  bal = token.balanceOf(_appCfg.accounts[0].public_key)
  burn = False
  if (bal > 0):
    logger.info("burning ...")
    burn = True
    res = token.obj.functions.burn(bal).transact()
    _bc.eth.waitForTransactionReceipt(res)
  bal = token.balanceOf(_appCfg.accounts[0].public_key)
  assert bal == 0

  ref1 = 200 * (10**token.decimals)
  ref2 = 100 * (10**token.decimals)

  if (burn):
    logger.info("minting ...")
    res = token.obj.functions.mint(_appCfg.accounts[0].public_key, (ref2)).transact()
    _bc.eth.waitForTransactionReceipt(res)
    bal = token.balanceOf(_appCfg.accounts[0].public_key)
    assert bal == ref2
  else:
    logger.info("minting ...")
    res = token.obj.functions.mint(_appCfg.accounts[0].public_key, (ref1)).transact()
    _bc.eth.waitForTransactionReceipt(res)
    bal = token.balanceOf(_appCfg.accounts[0].public_key)
    assert bal == ref1

    logger.info("burning ...")
    res = token.obj.functions.burn(bal - ref2).transact()
    _bc.eth.waitForTransactionReceipt(res)
    bal = token.balanceOf(_appCfg.accounts[0].public_key)
    assert bal == ref2

def _test_token_transfer(tknName: str, tknDict: dict):
  abi = json.load(open(os.path.join(tknDict["contract"], "abi.json"), "r"))
  token = base.Token(_bc.eth.contract(address=tknDict["address"], abi=abi))

  #_bc.eth.defaultAccount = _bc.eth.accounts[0]
  _bc.eth.defaultAccount = _appCfg.accounts[0].public_key

  bal0 = token.balanceOf(_appCfg.accounts[0].public_key)
  ref0 = bal0
  bal1 = token.balanceOf(_appCfg.accounts[1].public_key)
  ref1 = bal1
  assert bal0 > 0

  try:
    res = token.obj.functions.transfer(_appCfg.accounts[0].public_key,
                                       (bal0 + 1)).transact()
    _bc.eth.waitForTransactionReceipt(res)
    assert True
  except web3.exceptions.ContractLogicError:
    logger.info("transfer 0 -> 1 refused ...")

  logger.info("transfer 0 -> 1 ...")
  res = token.obj.functions.transfer(_appCfg.accounts[1].public_key, bal0).transact()
  _bc.eth.waitForTransactionReceipt(res)

  bal0 = token.balanceOf(_appCfg.accounts[0].public_key)
  assert bal0 == 0
  bal1 = token.balanceOf(_appCfg.accounts[1].public_key)
  assert bal1 == ref0 + ref1

  try:
    res = token.obj.functions.transfer(_appCfg.accounts[1].public_key, 1).transact()
    _bc.eth.waitForTransactionReceipt(res)
    assert True
  except web3.exceptions.ContractLogicError:
    logger.info("transfer 0 -> 1 refused ...")

  bal0 = token.balanceOf(_appCfg.accounts[0].public_key)
  assert bal0 == 0
  bal1 = token.balanceOf(_appCfg.accounts[1].public_key)
  assert bal1 == ref0 + ref1

  _bc.eth.defaultAccount = _appCfg.accounts[1].public_key
  logger.info("transfer 1 -> 0 ...")
  res = token.obj.functions.transfer(_appCfg.accounts[0].public_key, ref0).transact()
  _bc.eth.waitForTransactionReceipt(res)

  bal0 = token.balanceOf(_appCfg.accounts[0].public_key)
  assert bal0 == ref0
  bal1 = token.balanceOf(_appCfg.accounts[1].public_key)
  assert bal1 == ref1

  _bc.eth.defaultAccount = _appCfg.accounts[0].public_key

def _test():
  if (_bc.eth.chainId != 1337):
    logger.warning("UNEXPECTED chain ID")
    return

  logger.info("running on ganache")
  for k, v in _appCfg.tokens.items():
    if (v["address"] != ""):
      logger.info(f"testing {k} @ {v['address']}")
      _test_token_mint_burn(k, v)
      _test_token_transfer(k, v)

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

  try:
    cfg_token = _appCfg.tokens[cliArgs["contract"]]
  except KeyError:
    logger.error("token NOT defined")
    return

  if (cfg_token["address"] != ""):
    logger.error("token already HAS address")
    return

  abi = json.load(open(os.path.join(cfg_token["contract"], "abi.json"), "r"))
  bytecode = open(os.path.join(cfg_token["contract"], "bytecode.bin"),
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
  if (cliArgs["list"]):
    _appCfg.showInfo()
    sys.exit(0)
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
  parser.add_argument("-c", "--contract", default="", help="contract folder name")
  parser.add_argument("-l",
                      "--list",
                      action="store_true",
                      default=False,
                      help="list config file options")
  #parser.add_argument("-x", "--extra",
  #                    choices=("", ""),
  #                    help="extra parameters")

  cliArgs = vars(parser.parse_args())
  #logger.info(cliArgs)

  #parser.print_help()
  mainApp()
