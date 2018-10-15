import copy
from hexbytes import HexBytes

# seed_words = open('mnemonic_words_shuffled.txt').read().split('\n')
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
    # test_addr = '0xa62142888aba8370742be823c1782d17a0389da1'
    test_addr = '0xa62142888aba8370742be823c1782d17a0389da1'

    test_addrs = [
        '0x85b463314d8177fdb2a590c6af321699e2d718cc',
        '0x16b0c89b6c987fc1687c6c5d5f19f9f0543f2ba7',
        '0xf054e6f785cbf6ca764d0bad1dcf47e12c070484',
        '0xbfdfaef8656a810adb72d9ee2b30bd0e15aa0d5f',
        '0x570436a62b6e5d1b54ec3d3ab9c21a979bf8dc2b',
        '0xba6cf19a5fc9277f4e976b41a7789adc8cd1fefd',
        '0x466b5222d47b8533f15a32ef9f82a3a9fd6f8b2f',
        '0xbfdfaef8656a810adb72d9ee2b30bd0e15aa0d5f',
        '0x077be25134037a10160e6f4bded4c17a4765508a',
        '0x65ab6b69c47815b6bd89327ab67e19675212ad4a',
        '0x16b0c89b6c987fc1687c6c5d5f19f9f0543f2ba7',
        '0x20f81043f12dde4440ecc0b35156a1275f181653',
        '0xba6cf19a5fc9277f4e976b41a7789adc8cd1fefd',
        '0x077be25134037a10160e6f4bded4c17a4765508a',
        '0x65ab6b69c47815b6bd89327ab67e19675212ad4a',
        '0xbfdfaef8656a810adb72d9ee2b30bd0e15aa0d5f',
    ]

    mnemonic = Mnemonic.from_addr(test_addr)
    print(mnemonic)
    print(mnemonic.get_trunc_str())

    mnemonic2 = Mnemonic.from_str(mnemonic.get_str())
    print(mnemonic2.get_addr())
    print(mnemonic2.get_addr()==test_addr)


    for addr in test_addrs:
        mnemonic = Mnemonic.from_addr(addr)
        print(mnemonic.get_trunc_str())


    # number = int(test_addr[2:], 16)
    # print(get_different_base_indices(number, 2048))
    # import ipdb; ipdb.set_trace()
