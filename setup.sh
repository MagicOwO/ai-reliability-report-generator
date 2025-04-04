#!/bin/bash

echo "Setting up the report generator project..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed or not in PATH. Please install Python 3 and try again."
    exit 1
fi

# Run the setup script
python3 setup.py

if [ $? -ne 0 ]; then
    echo ""
    echo "There was an error during the setup process."
    exit 1
fi

echo ""
echo "Setup completed! Now activating the virtual environment..."

# Activate the virtual environment and run the report generator
if [ -f .venv/bin/activate ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
    
    echo ""
    echo "Virtual environment activated. You can now run:"
    echo "python -m src.report_generator"
    
    read -p "Would you like to run the report generator now? (y/n): " run_now
    if [[ $run_now == "y" || $run_now == "Y" ]]; then
        echo ""
        echo "Running report generator..."
        python -m src.report_generator
    fi
else
    echo "Could not find the virtual environment activation script."
    echo "Please try running: source .venv/bin/activate"
fi 