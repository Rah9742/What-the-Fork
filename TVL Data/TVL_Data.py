import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np

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

def compute_tvl_car(chain_df, benchmark_df, event_date):
    """
    Compute TVL-based cumulative abnormal return (TVL-CAR) for a chain
    relative to the global TVL benchmark over the post-event window.
    """
    merged = pd.merge_asof(
        chain_df.sort_values("date"),
        benchmark_df.sort_values("date"),
        on="date",
        direction="nearest"
    )

    merged["tvl_ret"] = merged["tvl_norm"].pct_change()
    merged["bench_ret"] = merged["bench_norm"].pct_change()

    merged["AR_TVL"] = merged["tvl_ret"] - merged["bench_ret"]

    post_event = merged[merged["date"] >= event_date]

    return post_event["AR_TVL"].sum(skipna=True)


def fetch_tvl_api(chain):
    """
    Fetches TVL data from the DefiLlama API.
    If chain is None, returns global TVL.
    If chain is provided, returns per-chain TVL.
    """
    if chain:
        url = f"https://api.llama.fi/v2/historicalChainTvl/{chain.lower()}"
    else:
        url = "https://api.llama.fi/v2/historicalChainTvl"

    print("Full URL:", url)

    response = requests.get(url)
    data = response.json()

    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"], unit="s")
    df = df.sort_values("date").reset_index(drop=True)

    return df


def plot_tvl_series(df, title, event_date, tvl_all_chains, end_date_cutoff, normalise_at_event=True):
    fig, ax = plt.subplots(figsize=(8, 4))
    event_date = pd.to_datetime(event_date).normalize()
    end_date_cutoff = pd.to_datetime(end_date_cutoff).normalize()

    # ------------------------------------------------------------
    # Determine 120-day event window and restrict data
    # ------------------------------------------------------------
    full_min = df["date"].min()
    full_max = df["date"].max()

    desired_left = event_date - pd.Timedelta(days=30)
    desired_right = min(event_date + pd.Timedelta(days=120), end_date_cutoff)

    left_lim = max(full_min, desired_left)
    right_lim = min(full_max, desired_right)

    mask = (df["date"] >= left_lim) & (df["date"] <= right_lim)
    df_win = df.loc[mask].copy()

    # fallback: use all data
    if df_win.empty:
        df_win = df.copy()

    # Ensure sorted and normalised timestamps
    df_win = df_win.sort_values("date").reset_index(drop=True)
    df_win["date"] = df_win["date"].dt.normalize()

    left_lim = df_win["date"].iloc[0]
    right_lim = df_win["date"].iloc[-1]

    # ------------------------------------------------------------
    # Benchmark: Global TVL normalised to 100 at event_date or graph start
    # ------------------------------------------------------------
    mb = tvl_all_chains.copy()
    mb["date"] = mb["date"].dt.normalize()
    mb = mb[(mb["date"] >= left_lim) & (mb["date"] <= right_lim)].copy()
    mb = mb[mb["date"] <= end_date_cutoff].copy()

    if not mb.empty:
        if normalise_at_event:
            event_idx = (mb["date"] - event_date).abs().idxmin()
            bm_base = mb.loc[event_idx, "tvl"]
        else:
            # baseline at graph start
            closest_idx = (mb["date"] - left_lim).abs().idxmin()
            bm_base = mb.loc[closest_idx, "tvl"]
        mb["bench_norm"] = 100.0 * mb["tvl"] / bm_base
        bench_df = mb[["date", "bench_norm"]]

    # ------------------------------------------------------------
    # Plot TVL + Benchmark
    # ------------------------------------------------------------
    if normalise_at_event:
        # Baseline at event date
        event_idx_chain = (df_win["date"] - event_date).abs().idxmin()
        tvl_base = df_win.loc[event_idx_chain, "tvl"]
    else:
        # Baseline at graph start (left_lim)
        tvl_base = df_win["tvl"].iloc[0]
    df_win["tvl_norm"] = 100.0 * df_win["tvl"] / tvl_base
    chain_df = df_win[["date", "tvl_norm"]]

    if not mb.empty:
        TVL_CAR = compute_tvl_car(chain_df, bench_df, event_date)
        print(f"TVL CAR for {title} from {event_date.date()} to {right_lim.date()}: {TVL_CAR:.4f}")

    ax.plot(df_win["date"], df_win["tvl_norm"], color="blue", label=f"{title} TVL (%)")

    if not mb.empty:
        ax.plot(mb["date"], mb["bench_norm"], color="black", linestyle="--",
                label="Global TVL Benchmark (%)")

    ax.set_xlabel("Date", size=12)
    ax.set_ylabel("Normalised TVL (%)", size=12)
    ax.set_title(f"{title} Total Value Locked Data", size=14)

    # Event vertical line
    ax.axvline(event_date, linestyle=":", color="red", linewidth=1.2, label="Attack Date")

    # ------------------------------------------------------------
    # Set x-limits and generate 5 evenly spaced ticks
    # ------------------------------------------------------------
    ax.set_xlim(left_lim, right_lim)
    left_ts = pd.Timestamp(left_lim)
    right_ts = pd.Timestamp(right_lim)
    ticks = pd.to_datetime(
        np.linspace(left_ts.value, right_ts.value, 5)
    ).normalize().tolist()

    ax.set_xticks(ticks)
    ax.set_xticklabels([t.strftime("%Y-%m-%d") for t in ticks], ha="center")

    # ------------------------------------------------------------
    # Legend (below plot)
    # ------------------------------------------------------------
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(
        handles,
        labels,
        facecolor="white",
        framealpha=1.0,
        frameon=True,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.12),
        ncol=3
    )

    fig.subplots_adjust(top=0.88, left=0.12, right=0.90, bottom=0.22)
    fig.tight_layout()

    # ------------------------------------------------------------
    # Save to PNG
    # ------------------------------------------------------------
    safe_title = title.replace(" ", "_")
    plt.savefig(f"{safe_title}_TVL_Data.png", dpi=600)

    plt.show()


# ------------------------------------------------------------
# Fetch data and plot graph
# ------------------------------------------------------------

# You may place these CSVs in the same directory as the script
CHAIN_EVENTS = {
    "BSC": datetime(2022, 10, 6),
    "Berachain": datetime(2025, 12, 1),
    "Solana": datetime(2022, 2, 2)
}

END_DATE_CUTOFF = datetime(2025, 12, 6)

def main(chains, date_cutoff):
    tvl_all_chains = fetch_tvl_api(None)

    for chain in chains:
        print(f"\nFetching {chain}...")
        event_date = chains[chain]
        df = fetch_tvl_api(chain)
        plot_tvl_series(df, chain, event_date, tvl_all_chains, date_cutoff, normalise_at_event=True)

if __name__ == "__main__":
    main(CHAIN_EVENTS, END_DATE_CUTOFF)