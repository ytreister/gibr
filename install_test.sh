#!/bin/bash

# Can use this script to test the instance deployed to test.pypi

python -m venv venv_test_gibr
source venv_test_gibr/Scripts/activate
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple gibr
