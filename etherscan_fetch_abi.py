#!/usr/bin/python
import argparse
import json

from helper import etherscan_fetch_abi

# Exports contract ABI in JSON

ABI_REQUEST_ENDPOINT = 'https://api.etherscan.io/api?module=contract&action=getabi&address='

parser = argparse.ArgumentParser()
parser.add_argument('addr', type=str, help='Contract address')
parser.add_argument('-o', '--output', type=str, help="Path to the output JSON file", required=True)

def __main__():

    args = parser.parse_args()

    abi = etherscan_fetch_abi(args.addr)
    result = json.dumps({"abi":abi}, indent=4, sort_keys=True)

    open(args.output, 'w').write(result)
    # import ipdb; ipdb.set_trace()

if __name__ == '__main__':
    __main__()

