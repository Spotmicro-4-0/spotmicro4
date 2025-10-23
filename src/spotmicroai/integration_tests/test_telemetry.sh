#!/bin/bash
# Test script for telemetry display

cd ~/spotmicroai || exit
export PYTHONPATH=.
venv/bin/python3 integration_tests/test_telemetry/test_telemetry.py
