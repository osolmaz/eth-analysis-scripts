#!/usr/bin/python
import argparse
import json
import web3
from web3 import Web3
from itertools import cycle

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

    # Create a colour code cycler e.g. 'C0', 'C1', etc.
    n_functions = len(contract.all_functions())
    color_codes = map('C{}'.format, cycle(range(max(10, n_functions))))

    batch_chunks = chunks(range(start_block, end_block+1), args.batch_size)
    batch_chunks = [list(i) for i in batch_chunks]

    if len(batch_chunks) > 1 and len(batch_chunks[-1]) == 1:
        batch_chunks[-2] += batch_chunks[-1]
        del batch_chunks[-1]

    pdf_file = PdfPages(args.output)
    plot_style_dict = {}

    for batch in batch_chunks:
        fn_call_dict = {}
        figure = plt.figure()

        ax = figure.gca()
        ax.set_xticks(batch)
        ax.set_xticklabels([str(i) for i in batch])

        for label in ax.get_xmajorticklabels():
            label.set_rotation(30)
            label.set_horizontalalignment("right")

        ax.set_xlim((min(batch)-0.5, max(batch)+0.5))

        ax.set_title('Fn calls for contract\n%s\nin blocks %d to %d'%(addr, batch[0], batch[-1]))

        for idx in batch:
            print('Fetching block %d, remaining: %d, progress: %d%%'%(
                idx, (end_block-idx), 100*(idx-start_block+1)/(end_block-start_block+1)))

            block = w3.eth.getBlock(idx, full_transactions=True)

            for tx in block.transactions:
                if tx['to']:
                    to_matches = tx['to'].lower() == addr.lower()
                else:
                    to_matches = False

                if tx['from']:
                    from_matches = tx['from'].lower() == addr.lower()
                else:
                    from_matches = False

                if to_matches or from_matches:

                    print('Found transaction with hash %s'%(tx['hash'].hex()[:8]+'...'))

                    tx = dict(tx)
                    tx_receipt = w3.eth.getTransactionReceipt(tx['hash'])

                    if tx['input'] == '0x':
                        fn_name = '0x'
                    else:
                        fn_name = contract.decode_function_input(tx['input'])[0].fn_name

                    if not tx_receipt['status'] == 1:
                        fn_name += " {failed}"

                    if not fn_name in plot_style_dict:
                        color_code = next(color_codes)
                        plot_style_dict[fn_name] = {"color": color_code, "edgecolor":"black"}
                        plot_style_dict[fn_name+" {failed}"] = {"color": color_code, "edgecolor":"black", "hatch":"/"}

                    if not fn_name in fn_call_dict:
                        fn_call_dict[fn_name] = {}

                    if not idx in fn_call_dict[fn_name]:
                        fn_call_dict[fn_name][idx] = 0

                    fn_call_dict[fn_name][idx] += 1

        bottom = [0 for i in batch]

        for fn_name, call_dict in fn_call_dict.items():
            pairs = [(k,v) for k,v in call_dict.items()]
            pairs = sorted(pairs, key=lambda item: item[0])
            X = [i[0] for i in pairs]
            Y = [i[1] for i in pairs]

            X, Y = fill_data(X, Y, batch[0], batch[-1])

            ax.bar(X, Y, bottom=bottom, label=fn_name, **plot_style_dict[fn_name])
            ax.legend()

            bottom = [a+b for a,b in zip(bottom, Y)]

        ax.set_axisbelow(True)
        ax.set_ylim(0, max(max(bottom), 10)*1.05)
        ax.set_yticks(list(range(0, max(bottom)+1)))
        ax.grid()

        pdf_file.savefig(figure)

    pdf_file.close()

if __name__ == '__main__':
    __main__()
