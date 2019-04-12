#!/bin/sh
# Simple script that will enter the documentation directory and build it.

target="${1:-html}"

cd doc
make "$target"
