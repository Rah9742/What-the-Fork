"""Module to plot Ethereum and Ethereum Classic mining difficulty over a specified historical window.

Data Source:
- Assumes CSV input with columns including 'Date', 'Ethereum - Difficulty', and 'Ethereum Classic - Difficulty'.

This script visualizes the mining difficulty trends around key events in 2016,
specifically the attack and fork dates, producing a publication-ready figure.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

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


def plot_difficulty_series(csv_path):
    # ------------------------------------------------------------
    # Load and prepare data
    # ------------------------------------------------------------
    df = pd.read_csv(csv_path)

    # Parse dates and normalize to midnight
    df["Date"] = pd.to_datetime(df["Date"]).dt.normalize()

    # Event window defined by module constants
    mask = (df["Date"] >= START_DATE) & (df["Date"] <= END_DATE)
    df_win = df.loc[mask].copy()

    if df_win.empty:
        raise ValueError(f"No data in the requested window {START_DATE.date()} to {END_DATE.date()}")

    # Ensure sorted and clean index
    df_win = df_win.sort_values("Date").reset_index(drop=True)
    df_win["Date"] = df_win["Date"].dt.normalize()

    left_lim = df_win["Date"].iloc[0]
    right_lim = df_win["Date"].iloc[-1]

    # ------------------------------------------------------------
    # Plot difficulties
    # ------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8, 4))

    ax.plot(
        df_win["Date"],
        df_win["Ethereum - Difficulty"],
        label="Ethereum Difficulty",
        linewidth=1.5,
    )
    ax.plot(
        df_win["Date"],
        df_win["Ethereum Classic - Difficulty"],
        label="Ethereum Classic Difficulty",
        linewidth=1.5,
    )
    # Event vertical lines
    ax.axvline(ATTACK_DATE, linestyle=":", color="red", linewidth=1.2, label="Attack Date")
    ax.axvline(FORK_DATE, linestyle=":", color="purple", linewidth=1.2, label="Fork Date")

    ax.set_xlabel("Date", size=12)
    ax.set_ylabel("Mining Difficulty (Hashes)", size=12)
    ax.set_title("Ethereum vs Ethereum Classic Mining Difficulty", size=14)

    # ------------------------------------------------------------
    # X limits and evenly spaced ticks (same style as TVL plot)
    # ------------------------------------------------------------
    ax.set_xlim(left_lim, right_lim)

    left_ts = pd.Timestamp(left_lim)
    right_ts = pd.Timestamp(right_lim)

    ticks = (
        pd.to_datetime(
            np.linspace(left_ts.value, right_ts.value, 5)
        )
        .normalize()
        .tolist()
    )

    ax.set_xticks(ticks)
    ax.set_xticklabels(
        [t.strftime("%Y-%m-%d") for t in ticks],
        ha="center",
    )
    ax.tick_params(axis="x", pad=5)
    plt.ylim(bottom=0)

    # ------------------------------------------------------------
    # Legend below the plot (matching your TVL styling)
    # ------------------------------------------------------------
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(
        handles,
        labels,
        facecolor="white",
        framealpha=1.0,
        frameon=True,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.15),
        ncol=4,
    )

    # Margins similar to your TVL function
    fig.subplots_adjust(top=0.88, left=0.12, right=0.90, bottom=0.25)
    fig.tight_layout()

    # Save and show
    plt.savefig(OUTPUT_FIGURE, dpi=600)
    plt.show()


# Module-level constants for key dates and output filename
START_DATE = pd.Timestamp("2016-05-19")
END_DATE = pd.Timestamp("2016-10-14")
ATTACK_DATE = pd.Timestamp("2016-06-17")
FORK_DATE = pd.Timestamp("2016-07-20")

OUTPUT_FIGURE = "ETH_ETC_Difficulty.png"


def main():
    plot_difficulty_series("ETH_ETC_Difficulty.csv")


if __name__ == "__main__":
    main()