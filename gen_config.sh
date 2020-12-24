# Little script to simplify configuration file generating template.
python3 -c "import os; print(os.getcwd())"
python3 -c "import sys, os; sys.path.append(os.getcwd())"
python3 utils/generate_config_file.py
