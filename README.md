Requirements
============

For local testing please install [ganache](http://trufflesuite.com/docs/ganache/overview) and the python packages specified in **requirements.txt**.

    pip install -r requirements.txt
   

Config Files
============

    cp ganache_example.cfg ganache.cfg

Change *account_0* and *account_1* addresses according to your setup.

    cp tokens_example.cfg tokens.cfg

Change *deploy* according to your wishes. These are the parameters for the token constructor.

Quick Test
==========

    python3 web3_token.py -f ganache.cfg info

This should print the last block number, the accounts and their ETH balance.

Compile the Token
=================

    cd contracts/token2
    vyper -f abi token.vy > abi.json
    vyper -f bytecode token.vy > bytecode.bin

Don't change the **abi.json** and **bytecode.bin** file names.
They are used by the python script.

Deploy the Token
================

    python3 web3_token.py -f ganache.cfg -c token2 deploy
    
The script will print the address where the token is deployed. Copy this address and add it to your **tokens.cfg**

Test the Tokens
===============

    python3 web3_token.py -f ganache.cfg test
