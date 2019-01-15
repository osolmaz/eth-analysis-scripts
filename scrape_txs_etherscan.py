#!/usr/bin/python
import argparse
import json
import web3
import sys
import logging
import pymongo
import progressbar
import requests
import time

from pymongo import MongoClient
from bson import Decimal128

from mnemonic import Mnemonic

from datetime import datetime
from web3 import Web3
from hexbytes import HexBytes

from helper import query_yes_no

logging.basicConfig(level=logging.INFO)

parser = argparse.ArgumentParser()
parser.add_argument('-a', '--addr', type=str, help='Address for which the txs will be scraped', required=True)
parser.add_argument('-d', '--database', type=str, help='Name of the MongoDB database', required=True)
parser.add_argument('-s', '--start-block', type=int, help='Start block', default=0)
parser.add_argument('-e', '--end-block',  type=int, help='End block', default=99999999)
parser.add_argument('--drop', action='store_true', help='Drop existing DB before scraping')
parser.add_argument('--skip-confirmation', action='store_true', help='Skip asking for confirmation for dropping the DB')
parser.add_argument('--delay',  type=int, help='Scraping delay in seconds', default=5)


def get_url(addr, start, end):
    return "http://api.etherscan.io/api?module=account&action=txlist&address=%s&startblock=%d&endblock=%d&sort=asc"%(addr, start, end)

def tx_to_dict(tx):
    result = {}
    for key, val in tx.items():
        if isinstance(val, HexBytes):
            result[key] = val.hex()
        else:
            result[key] = val

    if 'value' in result: result['value'] = Decimal128(str(result['value']))
    if 'gasPrice' in result: result['gasPrice'] = Decimal128(str(result['gasPrice']))

    return result

def block_to_dict(tx):
    result = {}
    for key, val in tx.items():
        if isinstance(val, HexBytes):
            result[key] = val.hex()
        else:
            result[key] = val

    if 'difficulty' in result: result['difficulty'] = Decimal128(str(result['difficulty']))
    if 'totalDifficulty' in result: result['totalDifficulty'] = Decimal128(str(result['totalDifficulty']))

    return result


def __main__():
    args = parser.parse_args()

    client = MongoClient()

    dbnames = client.list_database_names()

    if args.drop and args.database in dbnames:
        if not args.skip_confirmation:
            if not query_yes_no('Are you sure you want to drop existing DB: '+args.database, default='no'):
                sys.exit()

        client.drop_database(args.database)

    db = client[args.database]

    tx_collection = db['transactions']
    tx_collection.create_index([("hash", pymongo.ASCENDING)], unique=True)

    filtered_addrs = []
    if args.addr:
        filtered_addrs += args.addr.split(',')
    elif args.file:
        filtered_addrs += open(args.file, 'r').read().split('\n')

    filtered_addrs = [i.lower() for i in filtered_addrs if Web3.isAddress(i)]

    bar = progressbar.ProgressBar(max_value=args.end_block-args.start_block)

    tx_count = 0

    start = args.start_block
    end = args.end_block

    while True:
        response = requests.get(get_url(args.addr, start, end))
        txs = response.json()['result']

        if txs == None:
            time.sleep(args.delay)
            print('Nothing returned. Repeating API call.')
            continue

        # txs = sorted(txs, key=lambda x: x['blockNumber'])

        for n, tx in enumerate(txs):
            try:
                tx_collection.insert_one(tx_to_dict(tx))
                tx_count += 1
            except pymongo.errors.DuplicateKeyError:
                pass

        if len(txs) == 0:
            break

        if int(txs[-1]['blockNumber']) >= end:
            break

        start = int(txs[-1]['blockNumber'])
        # end = txs[-1]['blockNumber']

        print('Scraped', txs[0]['blockNumber'], '-',txs[-1]['blockNumber'])

        time.sleep(args.delay)

    import ipdb; ipdb.set_trace()



    logging.info('Finished importing %d txs from %d blocks'%(tx_count, args.end_block-args.start_block))


if __name__ == '__main__':
    __main__()
