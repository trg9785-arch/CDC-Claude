"""Computes the five header KPIs from whatever slice of data is currently selected."""

import pandas as pd


def compute_kpis(filtered_df: pd.DataFrame) -> dict:
    """Return the KPI values for the current filter selection.

    Returns None-valued fields if filtered_df is empty; callers should check
    for that and show a friendly message instead of rendering blank cards.
    """
    if filtered_df.empty:
        return {
            "total_births": None,
            "n_geographies": None,
            "avg_births_per_month": None,
            "top_geography": None,
            "top_month": None,
        }

    total_births = int(filtered_df["births"].sum())
    n_geographies = filtered_df["state_of_residence"].nunique()

    by_month = filtered_df.groupby("month", observed=True)["births"].sum()
    avg_births_per_month = float(by_month.mean()) if not by_month.empty else 0.0
    top_month = by_month.idxmax() if not by_month.empty else None

    by_state = filtered_df.groupby("state_of_residence", observed=True)["births"].sum()
    top_geography = by_state.idxmax() if not by_state.empty else None

    return {
        "total_births": total_births,
        "n_geographies": n_geographies,
        "avg_births_per_month": avg_births_per_month,
        "top_geography": top_geography,
        "top_month": top_month,
    }
