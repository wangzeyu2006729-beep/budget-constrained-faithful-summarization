#!/bin/bash
set -e

# Uses the correct virtual environment for the summarization project
PYTHON="/path/to/NLP_generatesummary/.venv/bin/python"

echo "Running LNS..."
$PYTHON run.py --method lns --tri-metric --num-samples -1

echo "Running ILP..."
$PYTHON run.py --method ilp --tri-metric --num-samples -1

echo "Running MMR..."
$PYTHON run.py --method mmr --tri-metric --num-samples -1

echo "Running DPP..."
$PYTHON run.py --method dpp --tri-metric --num-samples -1

echo "All methods finished!"
