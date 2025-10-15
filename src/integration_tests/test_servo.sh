#!/bin/bash

cd ~/spotmicroai
export PYTHONPATH=.

venv/bin/python3 integration_tests/test_servo/test_servo.py

