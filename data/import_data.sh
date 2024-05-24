#!/bin/bash
set -eo pipefail

DATABASE=$1 # MongoDB database you're using for Ankifier
COLLECTION=$2 # Collection for this language
FILEPATH=$3 # Path to Kaikki export

mongoimport -d $DATABASE -c $COLLECTION --file $FILEPATH