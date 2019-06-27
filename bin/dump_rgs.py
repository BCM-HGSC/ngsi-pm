#! /usr/bin/env python3

import re
import sys


def main():
    run()


def run():
    for line in sys.stdin:
        linesplit = line.rstrip().split('\t')
        if linesplit[0] != '@RG':
            continue
        rg_dict = {}
        for item in linesplit[1:]:
            k, v = item.split(':', 1)
            assert k not in rg_dict, (k, rg_dict)
            assert ':' not in k
            rg_dict[k] = v
        pat = re.compile(r'PU:(?:[\w-]+_)?([\w-]+)')
        rg_bc = pat.search(line).group(1)
        rg_sm = rg_dict['SM']
        print(rg_bc, rg_sm, sep='\t')


if __name__ == "__main__":
    main()
