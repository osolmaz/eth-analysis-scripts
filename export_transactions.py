#!/usr/bin/python
import argparse
import json
import web3

from web3 import Web3
from hexbytes import HexBytes

# Exports transactions to a JSON file where each line
# contains the data returned from the JSONRPC interface

provider = Web3.HTTPProvider('https://mainnet.infura.io/')
w3 = Web3(provider)

parser = argparse.ArgumentParser()
parser.add_argument('addr', type=str, help='Address to print the transactions for')
parser.add_argument('-o', '--output', type=str, help="Path to the output JSON file", required=True)
parser.add_argument('-s', '--start-block', type=int, help='Start block', default=0)
parser.add_argument('-e', '--end-block',  type=int, help='End block', default=w3.eth.blockNumber)

def tx_to_json(tx):
    result = {}
    for key, val in tx.items():
        if isinstance(val, HexBytes):
            result[key] = val.hex()
        else:
            result[key] = val

    return json.dumps(result)

def __main__():
    args = parser.parse_args()

    start_block = args.start_block
    end_block = args.end_block

    address_lowercase = args.addr.lower()

    ofile = open(args.output, 'w')

    for idx in range(start_block, end_block):
        print('Fetching block %d, remaining: %d, progress: %d%%'%(
            idx, (end_block-idx), 100*(idx-start_block)/(end_block-start_block)))

        block = w3.eth.getBlock(idx, full_transactions=True)

        for tx in block.transactions:
            if tx['to']:
                to_matches = tx['to'].lower() == address_lowercase
            else:
                to_matches = False

            if tx['from']:
                from_matches = tx['from'].lower() == address_lowercase
            else:
                from_matches = False

            if to_matches or from_matches:
                print('Found transaction with hash %s'%tx['hash'].hex())
                ofile.write(tx_to_json(tx)+'\n')
                ofile.flush()

if __name__ == '__main__':
    __main__()
