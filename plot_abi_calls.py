#!/usr/bin/python
import argparse
import web3
import pymongo

from web3 import Web3
from pymongo import MongoClient
from helper import etherscan_fetch_abi
from batch_plotter import BatchPlotter
from matplotlib import rcParams

rcParams['font.family'] = 'monospace'
rcParams['figure.figsize'] = 12, 9

parser = argparse.ArgumentParser()
parser.add_argument('addr', type=str, help='Address to print the transactions for')
parser.add_argument('-o', '--output', type=str, help="Path to the output plot", required=True)
parser.add_argument('-d', '--database', type=str, help="Name of the MongoDB database containing transaction data", required=True)

parser.add_argument('-s', '--start-block', type=int, help='Start block')
parser.add_argument('-e', '--end-block',  type=int, help='End block')
parser.add_argument('-b', '--batch-size',  type=int, help='Block batch size for the plots', default=20)


class AbiCallPlotter(BatchPlotter):

    def get_block_dict(self, block_number):
        result_dict = {}

        txs = self.tx_collection.find({'$and':[{'blockNumber': {'$eq': block_number}}, {'$or': [{'to': {'$eq':self.contract.address}}, {'from': {'$eq':self.contract.address}}]}]})

        for tx in txs:

            tx = dict(tx)
            tx_receipt = self.txreceipt_collection.find_one({'transactionHash': {'$eq': tx['hash']}})

            if not tx_receipt:
                print('Tx receipt not scraped, doing manually:', tx['hash'])
                tx_receipt = w3.eth.getTransactionReceipt(tx['hash'])
                # raise Exception('Tx receipt not scraped:', tx['hash'])

            if tx['input'] == '0x':
                fn_name = '0x'
            else:
                fn_name = self.contract.decode_function_input(tx['input'])[0].fn_name

            if not tx_receipt['status'] == 1:
                fn_name += " {failed}"

            if not fn_name in result_dict:
                result_dict[fn_name] = 0

            result_dict[fn_name] += 1

        return result_dict

def __main__():
    args = parser.parse_args()

    addr = Web3.toChecksumAddress(args.addr)

    client = MongoClient()
    db = client[args.database]

    tx_collection = db['transactions']
    txreceipt_collection = db['txreceipts']

    if not args.start_block:
        start_block = tx_collection.find().sort('blockNumber', pymongo.ASCENDING).next()['blockNumber']
    else:
        start_block = args.start_block

    if not args.end_block:
        end_block = tx_collection.find().sort('blockNumber', pymongo.DESCENDING).next()['blockNumber']
    else:
        end_block = args.end_block

    # provider = Web3.IPCProvider()
    provider = Web3.WebsocketProvider('wss://mainnet.infura.io/ws/')
    w3 = Web3(provider)

    contract_abi = etherscan_fetch_abi(addr)

    contract = w3.eth.contract(addr, abi=contract_abi)

    plotter = AbiCallPlotter(contract, db)
    plotter.plot(start_block, end_block, args.output, args.batch_size)


if __name__ == '__main__':
    __main__()
