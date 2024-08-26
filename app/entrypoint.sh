#!/bin/sh
set -e

if [ "$#" -eq 0 ]; then
    python main.py
else
    exec "$@"
fi
