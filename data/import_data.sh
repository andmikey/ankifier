#!/bin/bash
set -eo pipefail

LANGUAGE=$1
FILEPATH=$2

mongoimport -d ankifier -c $LANGUAGE --file $FILEPATH