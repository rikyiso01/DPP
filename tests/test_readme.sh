#!/usr/bin/env bash

set -euo pipefail

rm -rf .env
rm -f data.json plot.json plot.svg scripts/generalization.csv scripts/kmeans.svg anonymized.json
python3 -m venv .env
source .env/bin/activate
python3 -m pip install .
python3 generator.py --seed=42 --n=10000 data.json
python3 generator.py --seed=42 --n=100 plot.json
python3 plot.py --k 0.1 plot.json
python3 plot.py --k 0.1 --out plot.svg plot.json
python3 paper.py uniform_list data.json anonymized.json --m 10 --k 10
python3 paper.py partitioning data.json anonymized2.json --m 10
python3 -m scripts.generalization data.json scripts/generalization.csv
python3 -m scripts.kmeans --k 3 --seed 42 data.json scripts/kmeans.svg
python3 -m scripts.graph
rm -r .env
rm data.json plot.json plot.svg scripts/generalization.csv scripts/kmeans.svg anonymized.json
