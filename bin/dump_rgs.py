#! /usr/bin/env python3

import re
import sys


def main():
    run()


def run():
    # read file, get rg_bc, rg_sm
    # filename = '20_rg.txt'
    # with open(filename) as fin:
    for line in sys.stdin:
        linesplit = line.rstrip().split('\t')
        if linesplit[0] != '@RG':
            continue
        # print (linesplit)
        rg_dict = {}
        for item in linesplit[1:]:
            k, v = item.split(':', 1)
            assert k not in rg_dict, (k, rg_dict)
            assert ':' not in k
            rg_dict[k] = v
        # print(rg_dict.items())
        # update rg_bc for new HgV 17.5
        pat = re.compile(r'PU:(?:[\w-]+_)?([\w-]+)')
        rg_bc = pat.search(line).group(1)
        # rg_bc = rg_dict['PU']
        rg_sm = rg_dict['SM']
        #  print('PU: %s SM: %s' % (rg_bc, rg_sm))
        print(rg_bc, rg_sm, sep='\t')


if __name__ == "__main__":
    main()
