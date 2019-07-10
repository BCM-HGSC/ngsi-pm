#!/bin/bash

set -ex

mkdir -p $PREFIX/bin

for f in $(ls bin); do
    (
        echo "#!$PREFIX/bin/bash"
        echo "export PATH=$PREFIX/bin"
        cat bin/$f
    ) > $PREFIX/bin/$f
done