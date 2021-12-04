Requirements
============

For local testing please install [ganache](http://trufflesuite.com/docs/ganache/overview) and the python packages specified in **requirements.txt**.

    pip install -r requirements.txt
   

Config Files
============

First you need to create **ganache.cfg**:

    [default]
    url = http://127.0.0.1:7545

    [account_0]
    public = public_address_from_ganache_inteface
    [account_1]
    public = public_address_from_ganache_inteface

Then you will need to create/modify **tokens.cfg**

    [token2] # sub-folder of ./contracts where the vyper files are located
    address = address_on_blockchain_where_the_token_is_created
    deploy = JSON_list_of_deploy_parameters

Quick Test
==========

    python3 web3_token.py -f ganache.cfg info

This should print the last block number and the accounts and their ETH balance.

Compile the Token
=================

    cd contracts/token2
    vyper -f abi > abi.json
    vyper -f bytecode > bytecode.bin

Don't change the **abi.json** and **bytecode.bin** file names.
They are used by the python script.

Deploy the Token
================

    python3 web3_token.py -f ganache.cfg deploy
    
The script will print the address where the token is deployed. Copy this address and add it to your **tokens.cfg**

Test the Tokens
===============

    python3 web3_token.py -f ganache.cfg test
