import requests
import json

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
