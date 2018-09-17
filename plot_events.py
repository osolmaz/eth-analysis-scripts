#!/usr/bin/python
import argparse
import json
import web3
from web3 import Web3

from hexbytes import HexBytes
from statistics import mean
from helper import etherscan_fetch_abi, chunks, fill_data

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib import rcParams
from matplotlib.ticker import MaxNLocator
from matplotlib.backends.backend_pdf import PdfPages

rcParams['font.family'] = 'monospace'
rcParams['figure.figsize'] = 12, 9
# rcParams['font.sans-serif'] = ['Helvetica', 'Arial']


provider = Web3.HTTPProvider('https://mainnet.infura.io/')
w3 = Web3(provider)

parser = argparse.ArgumentParser()
parser.add_argument('addr', type=str, help='Address to print the transactions for')
parser.add_argument('-o', '--output', type=str, help="Path to the output plot", required=True)
parser.add_argument('-s', '--start-block', type=int, help='Start block', default=0)
parser.add_argument('-e', '--end-block',  type=int, help='End block', default=w3.eth.blockNumber)
parser.add_argument('-b', '--batch-size',  type=int, help='Block batch size for the plots', default=20)


def __main__():
    args = parser.parse_args()

    addr = Web3.toChecksumAddress(args.addr)

    start_block = args.start_block
    end_block = args.end_block

    # provider = Web3.IPCProvider('/home/onur/.ethereum/geth.ipc')
    # provider = Web3.HTTPProvider('https://mainnet.infura.io/')
    provider = Web3.WebsocketProvider('wss://mainnet.infura.io/ws/')


    w3 = Web3(provider)

    # compiled_source = compile_source(open('fomo3d.sol').read())
    contract_abi = etherscan_fetch_abi(addr)

    # fomo3d_contract = w3.eth.contract(FOMO3D_CONTRACT_ADDRESS)
    contract = w3.eth.contract(addr, abi=contract_abi)

    event_names = [i['name'] for i in contract.events._events]
    filters = [contract.events.__dict__[name].createFilter(fromBlock=start_block, toBlock=end_block) for name in event_names]


    block_event_dict = {}
    for i in range(start_block, end_block+1):
        block_event_dict[i] = {}
        # for name in event_names:
        #     block_event_dict[i][name] = 0

    for filter_ in filters:
        entries = filter_.get_all_entries()

        for entry in entries:
            name = entry['event']
            block_number = entry['blockNumber']

            if not name in block_event_dict[block_number]:
                block_event_dict[block_number][name] = 0

            block_event_dict[block_number][name] += 1

    # Now plot

    batch_chunks = chunks(range(start_block, end_block+1), args.batch_size)
    batch_chunks = [list(i) for i in batch_chunks]

    if len(batch_chunks) > 1 and len(batch_chunks[-1]) == 1:
        batch_chunks[-2] += batch_chunks[-1]
        del batch_chunks[-1]

    pdf_file = PdfPages(args.output)

    for batch in batch_chunks:

        fn_call_dict = {}
        figure = plt.figure()

        ax = figure.gca()
        # plt.xticks(rotation=45)
        ax.set_xticks(batch)
        ax.set_xticklabels([str(i) for i in batch])

        for label in ax.get_xmajorticklabels():
            label.set_rotation(30)
            label.set_horizontalalignment("right")

        ax.set_xlim((min(batch)-0.5, max(batch)+0.5))

        ax.set_title('Events for contract\n%s\nin blocks %d to %d'%(addr, batch[0], batch[-1]))

        for idx in batch:
            for key, val in block_event_dict[idx].items():
                if not key in fn_call_dict:
                    fn_call_dict[key] = {}

                fn_call_dict[key][idx] = val


        bottom = [0 for i in batch]

        for fn_name, call_dict in fn_call_dict.items():
            pairs = [(k,v) for k,v in call_dict.items()]
            pairs = sorted(pairs, key=lambda item: item[0])
            X = [i[0] for i in pairs]
            Y = [i[1] for i in pairs]

            X, Y = fill_data(X, Y, batch[0], batch[-1])

            ax.bar(X, Y, bottom=bottom, label=fn_name)
            ax.legend()

            bottom = [a+b for a,b in zip(bottom, Y)]

        ax.set_axisbelow(True)
        ax.set_ylim(0, max(bottom)*1.05)
        ax.set_yticks(list(range(0, max(bottom)+1)))
        ax.grid()

        pdf_file.savefig(figure)


    pdf_file.close()

if __name__ == '__main__':
    __main__()
