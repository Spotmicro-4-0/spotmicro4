#!/bin/bash

cd ~/spotmicroai/calibration || exit
export PYTHONPATH=~/spotmicroai/calibration:$PYTHONPATH

../venv/bin/python3 calibration.py
