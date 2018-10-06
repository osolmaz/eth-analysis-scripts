import copy
from hexbytes import HexBytes

seed_words = open('mnemonic_words.txt').read().split('\n')
seed_words.remove('')

seed_words_idx = {}

for n, w in enumerate(seed_words):
    seed_words_idx[w] = n

def number_to_addr(number):
    return "0x%0.40x"%number

def get_different_base_indices(x, base):
    'Get a list of indices of digits of x in a different base'

    if not isinstance(x, int):
        raise Exception('Input number must be of type int')
    if x < 0:
        raise Exception('Negative numbers not supported')
    elif x == 0:
        return [0]

    digits = []

    while x > 0:
        digits.append(x % base)
        x = x // base

    digits.reverse()

    return digits

# def get_different_base_indices(number, base):
#     'Alternative implementation'
#     n_idx = 0
#     number_ = copy.copy(number)
#     indices = []
#     while base**(n_idx+1) < number:
#         n_idx += 1
#     while n_idx >= 0:
#         current_idx = 0
#         digit_value = base**n_idx
#         while number_ - digit_value >= 0:
#             number_ -= digit_value
#             current_idx += 1
#         indices.append(current_idx)
#         n_idx -= 1
#     return indices


class Mnemonic:
    def __init__(self):
        pass
    def from_addr(addr):
        new_obj = Mnemonic()
        new_obj.addr = addr

        number = int(addr[2:], 16)
        indices = get_different_base_indices(number, 2048)
        new_obj.list_ = [seed_words[i] for i in indices]
        return new_obj

    def from_str(str_):
        list_ = str_.split()
        return Mnemonic.from_list(list_)

    def from_list(list_):
        new_obj = Mnemonic()
        new_obj.list_ = list_
        indices = [seed_words_idx[word] for word in list_]
        number = sum([i*2048**n for n,i in enumerate(reversed(indices))])
        new_obj.addr = number_to_addr(number)
        return new_obj

    def __repr__(self):
        return ' '.join(self.list_)

    def get_str(self):
        return ' '.join(self.list_)

    def get_trunc_str(self, trunc_level = 1):
        # result = self.list_[:trunc_level] + ['.'] + self.list_[-trunc_level:]
        # return '.'.join(result)
        return '.'.join(self.list_[:trunc_level]) + '..' + '.'.join(self.list_[-trunc_level:])

    def get_addr(self):
        return self.addr

if __name__ == '__main__':
    test_addr = '0xa62142888aba8370742be823c1782d17a0389da1'

    mnemonic = Mnemonic.from_addr(test_addr)
    print(mnemonic)
    print(mnemonic.get_trunc_str())

    mnemonic2 = Mnemonic.from_str(mnemonic.get_str())
    print(mnemonic2.get_addr())
    print(mnemonic2.get_addr()==test_addr)

    # number = int(test_addr[2:], 16)
    # print(get_different_base_indices(number, 2048))
