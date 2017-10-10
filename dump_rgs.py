#! /usr/bin/env python3

import sys

# read file, get rg_bc, rg_sm
# filename = '20_rg.txt'
# with open(filename) as f:
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
    # print (rg_dict.items())
    rg_pu = rg_dict['PU']
    rg_bc = rg_pu.split('_')[2]
    rg_sm = rg_dict["SM"]
    #  print('PU: %s SM: %s' % (rg_bc, rg_sm))
    print(rg_bc, rg_sm, sep='\t')
