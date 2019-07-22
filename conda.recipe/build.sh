#!/bin/bash

set -ex

$PYTHON setup.py install --single-version-externally-managed --record=record.txt

mkdir -p $PREFIX/bin

for f in $(ls bin); do
    (
        echo "#!$PREFIX/bin/bash"
        echo "export PATH=$PREFIX/bin:/usr/bin"
        cat bin/$f
    ) > $PREFIX/bin/$f
done
