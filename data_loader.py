"""
Loads and validates the CDC provisional natality CSV.

Cached with st.cache_data so the file is only read/parsed once per session
(re-runs on every widget interaction otherwise).
"""

from pathlib import Path

import pandas as pd
import streamlit as st

from state_utils import MONTH_ORDER

EXPECTED_COLUMNS = {
    "state_of_residence", "month", "month_code",
    "year_code", "sex_of_infant", "births",
}

# Resolved relative to this file, not the working directory, so the app
# finds the CSV whether it's launched locally (`streamlit run app.py` from
# anywhere) or on Streamlit Community Cloud.
DATA_PATH = Path(__file__).parent / "data" / "Provisional_Natality_2025_CDC1.csv"


class DataValidationError(Exception):
    """Raised when the CSV doesn't match the shape the dashboard expects."""


def _validate(df: pd.DataFrame) -> list[str]:
    """Return a list of human-readable validation problems (empty = clean)."""
    problems = []

    missing_cols = EXPECTED_COLUMNS - set(df.columns)
    if missing_cols:
        problems.append(f"Missing expected column(s): {', '.join(sorted(missing_cols))}")
        return problems  # can't check anything else safely

    if df["births"].isna().any():
        problems.append("Some 'births' values are missing (null).")
    if (df["births"] < 0).any():
        problems.append("Some 'births' values are negative.")

    bad_months = set(df["month"].unique()) - set(MONTH_ORDER)
    if bad_months:
        problems.append(f"Unrecognized month name(s): {', '.join(sorted(bad_months))}")

    bad_sex = set(df["sex_of_infant"].unique()) - {"Female", "Male"}
    if bad_sex:
        problems.append(f"Unrecognized sex_of_infant value(s): {', '.join(sorted(bad_sex))}")

    if df.duplicated(subset=["state_of_residence", "month", "sex_of_infant"]).any():
        problems.append("Duplicate rows found for the same state/month/sex combination.")

    return problems


@st.cache_data
def load_data() -> pd.DataFrame:
    """Load the natality CSV, validate it, and return a cleaned DataFrame.

    Validation problems are non-fatal (data-quality caveats are common with
    provisional data) but are surfaced to the user via st.warning rather
    than silently ignored.
    """
    if not DATA_PATH.exists():
        raise DataValidationError(
            f"Data file not found at {DATA_PATH}. Make sure the CSV is in the "
            "'data/' folder alongside app.py."
        )

    df = pd.read_csv(DATA_PATH)
    problems = _validate(df)

    if "month" in df.columns:
        df["month"] = pd.Categorical(df["month"], categories=MONTH_ORDER, ordered=True)

    df.attrs["validation_problems"] = problems
    return df
