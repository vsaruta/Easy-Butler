#!/bin/bash

# Check if the script is sourced
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "Error: Bot runs in a virtual environment. This setup script must be sourced. Run it as:"
    echo "source setup.sh"
    exit 1
fi

# Create a virtual environment named "env"
python3 -m venv env

# Activate the virtual environment
source env/bin/activate

# Install dependencies from requirements.txt
env/bin/python3 -m pip install -r requirements.txt

echo "Virtual environment activated. Ready to use!"
