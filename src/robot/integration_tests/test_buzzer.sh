#!/bin/bash

cd ~/spotmicroai
export PYTHONPATH=.

venv/bin/python3 integration_tests/test_buzzer/test_buzzer.py

