#!/bin/bash

# Check virtual environment, deleting it if it's there already.
if [ -d "./venv" ]; then
	rm -rf venv
fi

# Provision fresh virtual environment.
python3 -m venv venv

# Enter virtual environment.
. venv/bin/activate

# Install depenencies.
pip install --upgrade pip # Upgrade pip first.
pip install -r requirements.txt
