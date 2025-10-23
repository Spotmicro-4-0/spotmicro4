#!/bin/bash

cd ~/spotmicroai
export PYTHONPATH=.

venv/bin/python3 integration_tests/test_kenimatics/test_kenimatics.py

