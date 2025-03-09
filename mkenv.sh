#!/usr/bin/env nix-shell
#! nix-shell -i bash -p python3
set -e
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip3 install pe_tools
pip3 install json5