#!/bin/bash
# Wrapper script to ensure virtual environment is activated
# Usage: ./scripts/run_pipeline.sh [arguments]

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Activate virtual environment
cd "$PROJECT_ROOT"
source venv/bin/activate

# Run the pipeline script with all arguments
python scripts/run_pipeline.py "$@"
