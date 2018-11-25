#!/bin/bash

SCRIPTS=~/.scripts
if [ ! -e $SCRIPTS ]; then
    mkdir $SCRIPTS
fi

for filename in edit_*.py
do
    ln -s $(realpath $filename) $SCRIPTS
    echo $filename
done
