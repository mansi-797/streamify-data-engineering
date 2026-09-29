#!/bin/bash

cd ~/streamify-main

source .venv-dashboard/bin/activate

export STREAMIFY_PG_PASSWORD=streamify

docker start streamify-postgres

PYTHONPATH=. streamlit run dashboard/app.py
