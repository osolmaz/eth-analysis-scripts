#!/usr/bin/python
import argparse
import json
import web3

from web3 import Web3
from hexbytes import HexBytes
from statistics import mean
import pylab as plt

from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import rcParams

rcParams['font.family'] = 'monospace'

# Exports transactions to a JSON file where each line
# contains the data returned from the JSONRPC interface

provider = Web3.HTTPProvider('https://mainnet.infura.io/')
w3 = Web3(provider)

parser = argparse.ArgumentParser()
parser.add_argument('start_block', type=int, help='Start block')
parser.add_argument('end_block',  type=int, help='End block')
parser.add_argument('-o', '--output', type=str, help="Output plot pdf")
parser.add_argument('-d', '--data-file', type=str, help="Output data file (optional)")

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

    pdf_file = PdfPages(args.output)

    if args.data_file:
        data_file = open(args.data_file, 'w')
        data_file.write('#block_number,avg_gas_price,n_txs,diversity')

    for idx in range(start_block, end_block+1):
        print('Fetching block %d, remaining: %d, progress: %d%%'%(
            idx, (end_block-idx), 100*(idx-start_block+1)/(end_block-start_block+1)))

        fig = plt.figure()

        block = w3.eth.getBlock(idx, full_transactions=True)

        gas_prices = [ tx.gasPrice*1e-9 for tx in block.transactions ]

        if len(gas_prices) > 0:
            avg_gas_price = mean(gas_prices)
        else:
            avg_gas_price = 0

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

        if args.data_file:
            data_file.write('%d %e %d %e\n'%(block.number, avg_gas_price, len(block.transactions), diversity))
            data_file.flush()


        plt.hist(gas_prices, edgecolor = 'black')
        plt.title('Gas prices for block %d\nAvg = %.1f Gwei. # tx = %d. Diversity = %d%%'%(block.number, avg_gas_price, len(block.transactions), diversity*100))
        pdf_file.savefig(fig)
        plt.close(fig)

    pdf_file.close()

if __name__ == '__main__':
    __main__()
