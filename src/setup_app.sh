#!/bin/bash

cd ~/spotmicroai || exit

export PYTHONPATH=.

venv/bin/python3 -m setup_app
