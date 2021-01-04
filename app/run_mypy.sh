#!/bin/bash

export MYPYPATH="$(pwd)/application:$(pwd)/pythonmodules:$(pwd)/test"
mypy application/app.py
mypy application/checksample.py
mypy capture/capture.py

