# What the Fork

## Overview
This repository contains a collection of data analysis scripts used to examine how major security incidents and protocol forks affect blockchain ecosystems. The analysis focuses on three core dimensions of blockchain activity:

- Mining difficulty
- Token price behaviour
- Total Value Locked (TVL)

The scripts generate event-study style visualisations around key historical attack or exploit dates. Each analysis normalises the series around the event window to allow comparison of behaviour before and after the event.

The outputs are publication-quality figures designed for clear interpretation of how markets and network fundamentals respond to critical protocol-level events.

## Repository Structure

### Mining Difficulty Data
Examines how mining difficulty evolves around major blockchain events.

Files:
- `Difficulty_Data.py` – plots Ethereum and Ethereum Classic mining difficulty around the 2016 fork.
- `ETH_ETC_Difficulty.csv` – processed dataset used for plotting.
- `ETC_Difficulty.json` – raw difficulty data.
- `ETH_ETC_Difficulty.png` – generated figure.

Purpose:
The analysis highlights how mining power redistributed between Ethereum and Ethereum Classic after the fork event.

### Price Data
Performs an event study on token price behaviour relative to the broader crypto market.

Files:
- `Price_Data.py` – loads token price datasets and generates event-window plots.
- Token CSV files containing historical price and volume data.
- Generated PNG figures for each token.

Assets analysed include:
- Ethereum
- BNB
- Solana
- Berachain

Key features:
- Prices normalised to 100 at the event date.
- Volume plotted alongside price movements.
- Benchmark comparison using global crypto market capitalisation.
- Computation of **Cumulative Abnormal Return (CAR)** relative to the market benchmark.

### TVL Data
Analyses changes in ecosystem capital allocation using Total Value Locked.

Files:
- `TVL_Data.py` – retrieves historical TVL data using the DefiLlama API and produces event-window plots.
- Generated PNG figures for each chain.

Chains analysed include:
- BSC
- Solana
- Berachain

Key features:
- TVL normalised to event date.
- Comparison against global DeFi TVL.
- Computation of **TVL-based Cumulative Abnormal Return (TVL-CAR)**.

## Methodology

### Event Window
Each analysis uses a consistent window:

- 30 days before the event
- 120 days after the event

This allows visual inspection of both anticipation effects and post-event adjustment.

### Normalisation
Series are normalised to **100 at the event date** to make cross-chain comparisons easier.

### Benchmarking
Two benchmarks are used depending on the dataset:

Price analysis:
- Global crypto market capitalisation (CoinGecko)

TVL analysis:
- Global DeFi TVL (DefiLlama)

Abnormal returns are computed as:

AR = Asset Return − Benchmark Return

The cumulative abnormal return over the post-event window is then calculated.

## Dependencies

Python packages required:

- pandas
- numpy
- matplotlib
- requests

Install with:

pip install pandas numpy matplotlib requests

## Running the Scripts

### Price Event Study

python Price_Data.py

This will:
- Load token CSV datasets
- Load the global crypto market cap benchmark
- Generate price and volume plots for each token

### Mining Difficulty Analysis

python Difficulty_Data.py

Produces the Ethereum vs Ethereum Classic difficulty comparison plot.

### TVL Event Study

python TVL_Data.py

This script:
- Retrieves TVL data from the DefiLlama API
- Generates event-window TVL plots for each chain

## Data Sources

- CoinMarketCap historical price datasets
- CoinGecko global crypto market capitalisation data
- DefiLlama TVL API
- Historical mining difficulty datasets

## Output
Each script generates high-resolution PNG figures suitable for reports or publications.

Figures include:
- Normalised price trajectories
- Trading volume overlays
- Benchmark comparisons
- Event markers indicating the attack date