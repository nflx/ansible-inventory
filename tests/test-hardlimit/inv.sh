#!/bin/bash

SCRIPTPATH=$(dirname $0)
./inventory.py --file $SCRIPTPATH/inventory.yml --list --hardlimit 'docker' 
#./inventory.py --file $SCRIPTPATH/inventory.yml --list --hardlimit 'docker/site_b/alpha.*'
#./inventory.py --file $SCRIPTPATH/inventory.yml --list --hardlimit 'docker/site_b/alpha.*' --hardlimit 'docker/site_b/beta.*'
#./inventory.py --file $SCRIPTPATH/inventory.yml --list --hardlimit 'docker/site_a/.*' --hardlimit 'docker/site_b/alpha.*' --hardlimit 'docker/site_b/beta.*'
