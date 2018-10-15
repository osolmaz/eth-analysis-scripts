#!/usr/bin/python
import argparse
import json
import web3
import sys
import logging
# import pymongo
import progressbar

from pymongo import MongoClient
from bson import Decimal128

from mnemonic import Mnemonic

from datetime import datetime
from web3 import Web3
from hexbytes import HexBytes

from helper import query_yes_no

logging.basicConfig(level=logging.INFO)

parser = argparse.ArgumentParser()
parser.add_argument('-d', '--database', type=str, help='Name of the MongoDB database', required=True)
parser.add_argument('-s', '--start-block', type=int, help='Start block')
parser.add_argument('-e', '--end-block',  type=int, help='End block')
parser.add_argument('--drop', action='store_true', help='Drop existing DB before scraping')
parser.add_argument('--skip-confirmation', action='store_true', help='Skip asking for confirmation for dropping the DB')

group = parser.add_mutually_exclusive_group()
group.add_argument('-a', '--addr', type=str, help='Comma-separated list of addresses from and to which txs will be filtered')
group.add_argument('-f', '--file', type=str, help='File containing addresses from and to which txs will be filtered')


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

def __main__():
    args = parser.parse_args()

    provider = Web3.HTTPProvider('https://mainnet.infura.io/')
    # provider = Web3.IPCProvider()
    w3 = Web3(provider)

    if args.start_block:
        start_block = args.start_block
    else:
        start_block = 0

    if args.end_block:
        end_block = args.end_block
    else:
        end_block = w3.eth.blockNumber

    client = MongoClient()

    if args.drop:
        if not args.skip_confirmation:
            if not query_yes_no('Are you sure you want to drop existing DB: '+args.database, default='no'):
                sys.exit()

        client.drop_database(args.database)

    db = client[args.database]

    tx_collection = db['transactions']
    txreceipt_collection = db['txreceipts']

    filtered_addrs = []
    if args.addr:
        filtered_addrs += args.addr.split(',')
    elif args.file:
        filtered_addrs += open(args.file, 'r').read().split('\n')

    filtered_addrs = [i.lower() for i in filtered_addrs if Web3.isAddress(i)]

    bar = progressbar.ProgressBar(max_value=end_block-start_block)

    tx_count = 0

    for idx in range(start_block, end_block+1):
        bar.update(idx-start_block)

        block = w3.eth.getBlock(idx, full_transactions=True)

        txs = block.transactions

        lines = []

        for n, tx in enumerate(txs):
            if tx['to']:
                to_matches = tx['to'].lower() in filtered_addrs
            else:
                to_matches = False

            if tx['from']:
                from_matches = tx['from'].lower() in filtered_addrs
            else:
                from_matches = False

            if to_matches or from_matches or filtered_addrs == []:
                # print('Found tx: %s'%tx['hash'].hex())

                tx_collection.insert_one(tx_to_dict(tx))

                tx_receipt = w3.eth.getTransactionReceipt(tx['hash'])
                txreceipt_collection.insert_one(tx_to_dict(tx_receipt))

                tx_count += 1

    bar.finish()
    txreceipts.create_index('transactionHash')

    logging.info('Finished importing %d txs from %d blocks'%(tx_count, end_block-start_block))

    # if len(lines) > 0:
    # if args.readable:
    #     ofile.write('// Block %d at %s including %d txs, %d unique addresses, diversity: %d%%, gas used: %d\n'%(block.number, datetime.fromtimestamp(block.timestamp), len(block.transactions), len(unique_addresses), diversity*100, block.gasUsed))


if __name__ == '__main__':
    __main__()
