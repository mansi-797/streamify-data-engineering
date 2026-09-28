#!/bin/bash

cd ~/streamify-main

# Start Streamify PostgreSQL
docker start streamify-postgres >/dev/null 2>&1 || true

# Activate dashboard environment
source .venv-dashboard/bin/activate

# Start Streamlit
streamlit run dashboard/app.py
