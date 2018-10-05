#!/usr/bin/python
import argparse
import json
import web3
from mnemonic import Mnemonic

from datetime import datetime
from web3 import Web3
from hexbytes import HexBytes

# Exports transactions to a JSON file where each line
# contains the data returned from the JSONRPC interface

provider = Web3.HTTPProvider('https://mainnet.infura.io/')
w3 = Web3(provider)

parser = argparse.ArgumentParser()
parser.add_argument('-o', '--output', type=str, help='Path to the output JSON file', required=True)
parser.add_argument('-s', '--start-block', type=int, help='Start block', default=0)
parser.add_argument('-e', '--end-block',  type=int, help='End block', default=w3.eth.blockNumber)
parser.add_argument('--sort', type=str, help='Sort interblock txs w.r.t. given key')
parser.add_argument('-r', '--readable', action='store_true', help='Make output more readable')
parser.add_argument('--mnemonic', action='store_true', help='Replace addresses with mnemonics')

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

    return result

def __main__():
    args = parser.parse_args()

    start_block = args.start_block
    end_block = args.end_block

    ofile = open(args.output, 'w')

    filtered_addrs = []
    if args.addr:
        filtered_addrs += args.addr.split(',')
    elif args.file:
        filtered_addrs += open(args.file, 'r').read().split('\n')

    filtered_addrs = [i.lower() for i in filtered_addrs if Web3.isAddress(i)]

    for idx in range(start_block, end_block+1):
        print('Fetching block %d, remaining: %d, progress: %d%%'%(
            idx, (end_block-idx), 100*(idx-start_block)/(end_block-start_block)))

        block = w3.eth.getBlock(idx, full_transactions=True)

        if args.sort:
            txs = sorted(block.transactions, key=lambda t: t[args.sort])
        else:
            txs = block.transactions

        lines = []

        for tx in txs:
            if tx['to']:
                to_matches = tx['to'].lower() in filtered_addrs
            else:
                to_matches = False

            if tx['from']:
                from_matches = tx['from'].lower() in filtered_addrs
            else:
                from_matches = False

            tx_dict = tx_to_dict(tx)


            if args.readable:
                del tx_dict['blockHash']
                del tx_dict['blockNumber']

            if args.mnemonic:
                if tx_dict['to']:
                    tx_dict['to'] = Mnemonic.from_addr(tx_dict['to']).get_trunc_str()
                if tx_dict['from']:
                    tx_dict['from'] = Mnemonic.from_addr(tx_dict['from']).get_trunc_str()


            if to_matches or from_matches or filtered_addrs == []:
                print('Found transaction with hash %s'%tx['hash'].hex())
                lines.append(json.dumps(tx_dict))
                # ofile.flush()

        unique_addresses = set()
        for tx in block.transactions:
            if tx['to']:
                unique_addresses.add(tx['to'].lower())
            if tx['from']:
                unique_addresses.add(tx['from'].lower())

        if len(block.transactions) > 0:
            diversity = len(unique_addresses)/len(block.transactions)/2
        else:
            diversity = 1

        # if len(lines) > 0:
        if args.readable:
            ofile.write('// Block %d at %s including %d txs, %d unique addresses, diversity: %d%%, gas used: %d\n'%(block.number, datetime.fromtimestamp(block.timestamp), len(block.transactions), len(unique_addresses), diversity*100, block.gasUsed))

        for line in lines:
            ofile.write(line+'\n')

        if args.readable:
            ofile.write('\n')

        ofile.flush()


if __name__ == '__main__':
    __main__()
