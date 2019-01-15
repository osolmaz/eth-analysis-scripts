#!/usr/bin/python
import argparse
import web3
import pymongo
import progressbar

from datetime import datetime
from web3 import Web3
from pymongo import MongoClient
from statistics import mean
from helper import etherscan_fetch_abi, get_abi_fn_from_tx, get_events_from_receipt, diversities

parser = argparse.ArgumentParser()
parser.add_argument('addr', type=str, help='Address to print the transactions for')
parser.add_argument('-o', '--output', type=str, help="Path to the output plot", required=True)
parser.add_argument('-d', '--database', type=str, help="Name of the MongoDB database containing transaction data", required=True)

parser.add_argument('-s', '--start-block', type=int, help='Start block')
parser.add_argument('-e', '--end-block',  type=int, help='End block')
parser.add_argument('-b', '--batch-size',  type=int, help='Block batch size for the plots', default=20)

# group = parser.add_mutually_exclusive_group()
# group.add_argument('-a', '--addr', type=str, help='Comma-separated list of addresses from and to which txs will be filtered')
parser.add_argument('-f', '--file', type=str, help='File containing addresses from and to which txs will be filtered')

def crop_hex(addr):
    return addr[:5]+'…'+addr[-3:]

def etherscan_tx_link(hash_):
    return 'https://etherscan.io/tx/'+hash_

def etherscan_addr_link(addr):
    return 'https://etherscan.io/address/'+addr

def etherscan_block_link(block_number):
    return 'https://etherscan.io/block/'+str(block_number)


def __main__():
    args = parser.parse_args()

    addr = Web3.toChecksumAddress(args.addr)

    client = MongoClient()
    db = client[args.database]

    tx_collection = db['transactions']
    txreceipt_collection = db['txreceipts']
    block_collection = db['blocks']

    if not args.start_block:
        start_block = tx_collection.find().sort('blockNumber', pymongo.ASCENDING).next()['blockNumber']
    else:
        start_block = args.start_block

    if not args.end_block:
        end_block = tx_collection.find().sort('blockNumber', pymongo.DESCENDING).next()['blockNumber']
    else:
        end_block = args.end_block

    filtered_addrs = []
    # if args.addr:
        # filtered_addrs += args.addr.split(',')
    if args.file:
        filtered_addrs += open(args.file, 'r').read().split('\n')

    # import ipdb; ipdb.set_trace()
    filtered_addrs = [Web3.toChecksumAddress(i) for i in filtered_addrs if Web3.isAddress(i)]

    # provider = Web3.IPCProvider()
    provider = Web3.WebsocketProvider('wss://mainnet.infura.io/ws/')
    w3 = Web3(provider)

    contract_abi = etherscan_fetch_abi(addr)

    contract = w3.eth.contract(addr, abi=contract_abi)

    n_functions = len(contract.all_functions())

    bar = progressbar.ProgressBar(max_value=end_block-start_block)

    ofile = open(args.output, 'w')

    ofile.write('''<html>
<style>
* {
    font-family: monospace;
    color: #ecf0f1;
    text-decoration: none;
}
table {
    border-style: outset;
    border-color: white;
    border-collapse:collapse;
}
.failed {
    text-decoration: line-through;
}
.highlighted {
    background-color: #c0392b;
}
body {
    background-color: #2c3e50;
    padding-left: 2cm;
}
tr {
    border: none;
}
td, th {
    border-right: solid 1px #fff;
    border-left: solid 1px #fff;
    border-collapse:collapse;
    padding: 0.5ex;
}
</style>
<body>
''')

    bar = progressbar.ProgressBar(max_value=end_block-start_block)

    for block_number in range(start_block, end_block+1):
        block = block_collection.find_one({'number': {'$eq': block_number}})
        txs = [i for i in tx_collection.find({'blockNumber': {'$eq': block_number}})]
        tx_receipts = [i for i in txreceipt_collection.find({'blockNumber': {'$eq': block_number}})]

        tx_receipt_dict = {}
        for i in tx_receipts:
            tx_receipt_dict[i['transactionHash']] = i

        from_diversity, to_diversity = diversities(txs)
        gas_prices = [int(tx['gasPrice'].to_decimal())*1e-9 for tx in txs]
        gas_used_list = [tx_receipt_dict[tx['hash']]['gasUsed'] for tx in txs]
        gas_limits = [tx['gas'] for tx in txs]
        eth_spent_on_gas_list = [float(tx['gasPrice'].to_decimal())*tx_receipt['gasUsed']*1e-18 for tx, tx_receipt in zip(txs, tx_receipts)]
        values = [int(tx['value'].to_decimal())*1e-18 for tx in txs]


        ofile.write('<h1><a href="%s">Block %d</a></h1>\n'%(etherscan_block_link(block_number), block_number))
        ofile.write('<p>%s, ts:%d</p>\n'%(datetime.utcfromtimestamp(block['timestamp']).strftime('%Y-%m-%d %H:%M:%S'), block['timestamp']))
        # ofile.write('<p>From diversity: %d%%, To diversity: %d%%</p>\n'%(int(from_diversity*100), int(to_diversity*100)))
        ofile.write('<p>Average gas price: %.1f Gwei</p>\n'%(mean(gas_prices)))

        ofile.write( \
'''<table>
<tr>
<th>Idx</th>
<th>From</th>
<th>To</th>
<th>Hash</th>
<th>ETH sent</th>
<th>Gas Price<br>[Gwei]</th>
<th>Gas Limit</th>
<th>Gas Used</th>
<th>ETH spent<br>on gas</th>
<th>ABI Call</th>
<th>Events</th>
</tr>
''')
        bar.update(block_number-start_block)

        for tx in txs:

            # tx_receipt = txreceipt_collection.find_one({'transactionHash': {'$eq': tx['hash']}})
            tx_receipt = tx_receipt_dict[tx['hash']]

            if addr in [tx['to'], tx['from']]:
                try:
                    abi_fn = get_abi_fn_from_tx(contract, tx)
                except:
                    abi_fn = None

                event_dict = get_events_from_receipt(contract, tx_receipt)
                events = ', '.join(event_dict.keys())

                # import ipdb; ipdb.set_trace()
            else:
                abi_fn = None
                events = None

            classes = []
            failed = not tx_receipt['status'] == 1

            if failed: classes.append('failed')

            if tx['from'] in filtered_addrs or tx['to'] in filtered_addrs: classes.append('highlighted')

            if classes:
                ofile.write('<tr class="%s">\n'%(' '.join(classes)))
            else:
                ofile.write('<tr>\n')


            ofile.write('<td>%d</td>\n'%(tx['transactionIndex']))

            if tx['from']:
                ofile.write('<td><a href="%s">%s</a></td>\n'%(
                    etherscan_addr_link(tx['from']), crop_hex(tx['from'])))
            else:
                ofile.write('<td></td>\n')

            if tx['to']:
                ofile.write('<td><a href="%s">%s</a></td>\n'%(
                    etherscan_addr_link(tx['to']), crop_hex(tx['to'])))
            else:
                ofile.write('<td></td>\n')

            ofile.write('<td><a href="%s">%s</a></td>\n'%(
                etherscan_tx_link(tx['hash']), crop_hex(tx['hash'])))

            value = int(tx['value'].to_decimal())*1e-18
            ofile.write('<td>%g</td>\n'%(value))

            gas_price = int(tx['gasPrice'].to_decimal())*1e-9
            ofile.write('<td>%.1f</td>\n'%(gas_price))

            gas_limit = tx['gas']
            ofile.write('<td>{:,}</td>\n'.format(gas_limit))

            gas_used = tx_receipt['gasUsed']
            ofile.write('<td>{:,}</td>\n'.format(gas_used))

            eth_spent_on_gas = float(tx['gasPrice'].to_decimal())*tx_receipt['gasUsed']*1e-18
            ofile.write('<td>%g</td>\n'%(eth_spent_on_gas))

            if abi_fn:
                ofile.write('<td>%s</td>\n'%(abi_fn))
            else:
                ofile.write('<td></td>\n')

            if events:
                ofile.write('<td>%s</td>\n'%(events))
            else:
                ofile.write('<td></td>\n')


            ofile.write('</tr>\n')


        ofile.write('<tr>\n')
        ofile.write('<th></th>\n')
        ofile.write('<th></th>\n')
        ofile.write('<th></th>\n')
        ofile.write('<th></th>\n')
        ofile.write('<th>%g</th>\n'%(sum(values)))
        ofile.write('<th>%g</th>\n'%(sum(gas_prices)))
        ofile.write('<th>{:,}</th>\n'.format(sum(gas_limits)))
        ofile.write('<th>{:,}</th>\n'.format(sum(gas_used_list)))
        ofile.write('<th>%g</th>\n'%(sum(eth_spent_on_gas_list)))
        ofile.write('<th></th>\n')
        ofile.write('<th></th>\n')
        ofile.write('</tr>\n')


        # print(len(txs))

        ofile.write('''</table>\n''')


    ofile.write('''
</body>
</html>''')

    bar.finish()

if __name__ == '__main__':
    __main__()
