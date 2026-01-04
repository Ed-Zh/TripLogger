#!/bin/bash
# Move to the directory where this script is located
cd "$(dirname "$0")" || exit

# Run the app
python3 -m streamlit run app.py
