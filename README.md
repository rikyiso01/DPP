# Data Protection and Privacy

-   Isola S4943369
-   Cattaneo S4944382

## Requirements

-   python>=3.12

## Installation

Create a virtual environment and install the dependencies into it:

```bash
python3 -m venv .env
source .env/bin/python3
python3 -m pip install .
```

## Data Generation

To generate data run:

```bash
python3 generator.py --seed=42 --n=10000 data.json
```

any script supports the `--help` flag

## Graph visualization

```bash
python3 generator.py --seed=42 --n=100 plot.json
python3 plot.py --k 0.1 plot.json
```

if for any reason the image doesn't show you can output an image using

```bash
python3 plot.py --k 0.1 --out plot.svg plot.json
```

## Anonymize graph

with uniform lists

```bash
python3 paper.py uniform_list data.json anonymized.json --m 10 --k 10
```

with partitioning

```bash
python3 paper.py partitioning data.json anonymized2.json --m 10
```

## Analysis of the results

Open the notebook using

```bash
jupyter notebook paper.ipynb
```

## Run scripts

### Generalization

```bash
python3 -m scripts.generalization data.json scripts/generalization.csv
```

### KMeans

```bash
python3 -m scripts.kmeans --k 3 --seed 42 data.json scripts/kmeans.svg
```

### Graph

```bash
python3 -m scripts.graph
```

### Analysis

An analysis of the results can be found in the notebook which can be opened using

```bash
jupyter notebook scripts/notebook.ipynb
```
