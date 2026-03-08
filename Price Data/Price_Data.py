import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

plt.rcParams.update({
    # Font
    "font.size": 11,
    "font.family": "Times New Roman",

    # Figure sizing
    "figure.figsize": (6, 4),
    "figure.dpi": 120,

    # Line styles
    "lines.linewidth": 1.2,
    "lines.markersize": 4,

    # Axes
    "axes.grid": False,
    "axes.spines.top": False,
    "axes.spines.right": True,
    "axes.labelsize": 11,
    "axes.titlesize": 12,

    # Ticks
    "xtick.direction": "in",
    "ytick.direction": "in",
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,

    # Legends
    "legend.frameon": False,
    "legend.fontsize": 10,
    "legend.facecolor": "white",
    "legend.framealpha": 1.0,

    # Saving
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.1,
})

# ------------------------------------------------------------
# Load Local CSV Price Data and Plot
# ------------------------------------------------------------
def load_cmc_csv(path):
    """
    Load a CoinMarketCap-style CSV and return a cleaned dataframe.
    Uses daily open prices (timeOpen, open) to align with benchmark series
    anchored at 00:00 UTC.
    """
    df = pd.read_csv(path, sep=';')

    # Standardise column names just in case
    df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]

    # Ensure date parsing and remove timezone info
    if 'timeopen' not in df.columns:
        raise ValueError(f"CSV {path} missing 'timeOpen' column.")
    df['time'] = pd.to_datetime(df['timeopen']).dt.tz_localize(None)

    # Require opening price, rename to close
    if 'open' not in df.columns:
        raise ValueError(f"CSV {path} missing 'Open' column.")
    df['price'] = df['open']

    # Require volume
    if 'volume' not in df.columns:
        raise ValueError(f"CSV {path} missing 'Volume' column.")

    # print(df.head())

    return df[['time', 'price', 'volume']]


def load_market_cap_csv(path):
    """
    Load global crypto market cap (CoinGecko format):
    snapped_at (unix ms), market_cap, total_volume
    """
    df = pd.read_csv(path)

    # Convert unix-ms timestamp to naive datetime
    df['time'] = pd.to_datetime(df['snapped_at'], unit='ms').dt.tz_localize(None)

    # Keep only timestamp + market cap
    df = df[['time', 'market_cap']]

    # Sort chronologically
    df = df.sort_values('time').reset_index(drop=True)

    return df


def compute_car(asset_df, benchmark_df, event_date):
    """
    Compute cumulative abnormal return (CAR) for an asset relative to a benchmark
    over the post-event window.
    """
    # Align timestamps
    merged = pd.merge_asof(
        asset_df.sort_values('time'),
        benchmark_df.sort_values('time'),
        on='time',
        direction='nearest'
    )

    # Compute returns
    merged['asset_ret'] = merged['asset_norm'].pct_change()
    merged['bench_ret'] = merged['bench_norm'].pct_change()

    # Abnormal return
    merged['AR'] = merged['asset_ret'] - merged['bench_ret']

    # Restrict to post-event window
    post_event = merged[merged['time'] >= event_date]

    post_event["CAR_cum"] = post_event["AR"].cumsum()
    print(post_event[["time", "AR", "CAR_cum"]].head(10))
    print(post_event[["time", "AR", "CAR_cum"]].tail(10))

    return post_event['AR'].sum(skipna=True)


def plot_price_series(df, benchmark_df, title, event_date, normalise_at_event=True):
    fig, ax1 = plt.subplots(figsize=(8, 4))
    event_date = pd.to_datetime(event_date).normalize()

    # ------------------------------------------------------------
    # Determine up to 120-day event window and restrict asset data
    # ------------------------------------------------------------
    full_min = df['time'].min()
    full_max = df['time'].max()

    desired_left = event_date - pd.Timedelta(days=30)
    desired_right = event_date + pd.Timedelta(days=120)

    # Clamp to available data
    left_lim = max(full_min, desired_left)
    right_lim = min(full_max, desired_right)

    window_mask = (df['time'] >= left_lim) & (df['time'] <= right_lim)
    df_win = df.loc[window_mask].copy()

    # Fallback: if window is empty, use all data
    if df_win.empty:
        df_win = df.copy()
        left_lim = df_win['time'].min()
        right_lim = df_win['time'].max()

    # Ensure left_lim/right_lim match the visible data window
    df_win = df_win.sort_values('time').reset_index(drop=True)
    left_lim = df_win['time'].iloc[0]
    right_lim = df_win['time'].iloc[-1]

    # Normalise asset price
    if normalise_at_event:
        idx_evt = (df_win['time'] - event_date).abs().idxmin()
        asset_base = df_win.loc[idx_evt, 'price']
    else:
        asset_base = df_win['price'].iloc[0]
    df_win['asset_norm'] = 100.0 * df_win['price'] / asset_base
    asset_df = df_win[['time', 'asset_norm']]

    # Price line (left axis) in % of start
    ax1.plot(df_win['time'], df_win['asset_norm'],
             label=f"{title} (%)", color='blue')
    ax1.set_xlabel("Date", size=12)
    ax1.set_ylabel("Normalised Price (%)", size=12)

    # Volume bar plot (right axis) using same window
    ax2 = ax1.twinx()
    ax2.bar(df_win['time'], df_win['volume'],
            alpha=0.25, color='grey', label=f"{title} Volume")
    ax2.set_ylabel("Volume ($)")

    # Event line
    ax1.axvline(event_date, linestyle=':', color='red',
                linewidth=1.2, label="Attack Date")

    # ----- Benchmark normalised returns (left axis, dashed black) -----
    mb = benchmark_df[
        (benchmark_df['time'] >= left_lim) &
        (benchmark_df['time'] <= right_lim)
    ].copy()

    if not mb.empty:
        # Normalise benchmark
        if normalise_at_event:
            evt_idx = (mb['time'] - event_date).abs().idxmin()
            bm_base = mb.loc[evt_idx, 'market_cap']
        else:
            closest_idx = (mb['time'] - left_lim).abs().idxmin()
            bm_base = mb.loc[closest_idx, 'market_cap']
        mb['bench_norm'] = 100.0 * mb['market_cap'] / bm_base

        # Prepare benchmark for CAR computation
        bench_df = mb[['time', 'bench_norm']]

        # Plot benchmark on left axis
        ax1.plot(mb['time'], mb['bench_norm'],
                 color='black', linestyle='--', label='Total Crypto Market Cap Benchmark (%)')

        CAR = compute_car(asset_df, bench_df, event_date)
        print(f"CAR for {title} from {event_date.date()} to {right_lim.date()}: {CAR:.4f}")

    # Title
    ax1.set_title(title + " Price Data", size=14)

    left_ts = pd.Timestamp(left_lim)
    right_ts = pd.Timestamp(right_lim)
    total_days = (right_ts - left_ts).days

    if total_days <= 2:
        # Very small window: fallback ticks
        ticks = [left_ts, event_date, right_ts]
        while len(ticks) < 5:
            ticks.insert(0, left_ts)
        ticks = ticks[:5]
    else:
        # Normal case: evenly spaced ticks
        ticks = pd.to_datetime(
            np.linspace(left_ts.value, right_ts.value, 5)
        ).normalize().tolist()
        # ticks[2] = event_date

    # Axis formatting
    ax1.set_xlim(left_lim, right_lim)
    ax1.set_xticks(ticks)
    ax1.set_xticklabels(
        [t.strftime("%Y-%m-%d") for t in ticks],
        rotation=0,
        ha='center'
    )
    ax2.tick_params(axis='y', pad=6)
    ax1.tick_params(axis='x', pad=4)
    handles1, labels1 = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()

    # Place legend centered below the plot
    ax1.legend(
        handles1 + handles2,
        labels1 + labels2,
        facecolor="white",
        framealpha=1.0,
        frameon=True,
        loc='upper center',
        bbox_to_anchor=(0.5, -0.12),
        fancybox=True,
        shadow=False,
        ncol=4
    )

    fig.subplots_adjust(top=0.88, left=0.12, right=0.90, bottom=0.22)
    fig.tight_layout()

    # Save plot to file
    safe_title = title.replace(" ", "_")
    plt.savefig(f"{safe_title}_Price_Data.png", dpi=600)
    plt.show()


# ------------------------------------------------------------
# Load all local datasets
# ------------------------------------------------------------

# Load global market cap benchmark
BENCHMARK_PATH = "CoinGecko-GlobalCryptoMktCap-2025-12-07.csv"

# Tokens to plot with CSV file in the same directory as the script
TOKENS_EVENT = {
    "Ethereum": {
        "csv_file": "Ethereum_01_01_2016-31_12_2016_historical_data_coinmarketcap.csv",
        "event_date": datetime(2016, 6, 17)
    },
    # "BNB": {
    #     "csv_file": "BNB_01_04_2022-31_03_2023_historical_data_coinmarketcap.csv",
    #     "event_date": datetime(2022, 10, 6)
    # },
    # "Berachain": {
    #     "csv_file": "Berachain_07_12_2024-07_12_2025_historical_data_coinmarketcap.csv",
    #     "event_date": datetime(2025, 12, 1)
    # },
    # "Solana": {
    #     "csv_file": "Solana_01_09_2021-31_08_2022_historical_data_coinmarketcap.csv",
    #     "event_date": datetime(2022, 2, 2)
    # }
}

def main(benchmark_path, tokens):
    benchmark_df = load_market_cap_csv(benchmark_path)

    for token in tokens:
        print(f"\nLoading {token}...")

        file_path = tokens[token]["csv_file"]
        if not os.path.exists(file_path):
            print("No CSV file found. Ensure it is placed in the correct directory.")
        else:
            print("Found CSV files:", file_path)

        df_prices = load_cmc_csv(file_path)

        event_date = tokens.get(token).get("event_date", df_prices['time'].min()).replace(tzinfo=None)

        plot_price_series(df_prices, benchmark_df, token, event_date, normalise_at_event=True)

if __name__ == "__main__":
    main(BENCHMARK_PATH, TOKENS_EVENT)