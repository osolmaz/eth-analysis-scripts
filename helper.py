import requests
import sys
import json

from web3.utils.events import get_event_data

ABI_REQUEST_ENDPOINT = 'https://api.etherscan.io/api?module=contract&action=getabi&address='

def etherscan_fetch_abi(addr):

    response = requests.get('%s%s'%(ABI_REQUEST_ENDPOINT, addr))
    response_json = response.json()
    abi = json.loads(response_json['result'])

    return abi

def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]

def fill_data(X, Y, start, end):
    X_ = list(range(start, end+1))
    Y_ = [ 0 for i in X_ ]

    for x, y in zip(X, Y):
        Y_[x-start] = y

    return X_, Y_

def diversity(txs):
    unique_addresses = set()

    for tx in txs:
        if tx['to']:
            unique_addresses.add(tx['to'].lower())
        if tx['from']:
            unique_addresses.add(tx['from'].lower())

    if len(txs) > 0:
        result = len(unique_addresses)/len(txs)/2
    else:
        result = 1

    return result

import sys

def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")

def get_abi_fn_from_tx(contract, tx):
    if tx['input'] == '0x':
        fn_name = '0x'
    else:
        fn_name = contract.decode_function_input(tx['input'])[0].fn_name

    return fn_name

def get_events_from_receipt(contract, tx_receipt):
    result = {}

    for i in contract.events._events:

        name = i['name']

        matching_abi = contract._find_matching_event_abi(name)

        # n_matches = len(contract.events.__dict__[name]().processReceipt(tx_receipt))
        # print(i['name'], len(contract.events.__dict__[name]().processReceipt(tx_receipt)))

        for log in tx_receipt['logs']:

            try:
                get_event_data(matching_abi, log)
                abi_matches = True
            except:
                abi_matches = False

            if log['address'] == contract.address and abi_matches:
                if not name in result:
                    result[name] = 0

                result[name] += 1

    return result
