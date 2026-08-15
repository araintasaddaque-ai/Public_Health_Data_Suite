import numpy as np
import pandas as pd


def evaluate_l_diversity(
    df: pd.DataFrame, quasi_identifiers: list[str], sensitive_column: str
) -> tuple[int, pd.DataFrame]:
    """Calculates the minimum distinct sensitive values across equivalence classes (l-diversity)."""
    groups = (
        df.groupby(quasi_identifiers)[sensitive_column]
        .nunique()
        .reset_index(name="distinct_sensitive_count")
    )
    min_l = int(groups["distinct_sensitive_count"].min())
    return min_l, groups


def evaluate_t_closeness(
    df: pd.DataFrame, quasi_identifiers: list[str], sensitive_column: str
) -> tuple[float, pd.DataFrame]:
    """Calculates max distance between equivalence class distributions and global population distribution (t-closeness)."""
    global_dist = df[sensitive_column].value_counts(normalize=True)

    max_t = 0.0
    records = []

    grouped = df.groupby(quasi_identifiers)
    for name, group in grouped:
        group_dist = group[sensitive_column].value_counts(normalize=True)

        # Total Variation Distance (TVD)
        all_categories = global_dist.index.union(group_dist.index)
        tvd = (
            0.5
            * sum(
                abs(group_dist.get(cat, 0.0) - global_dist.get(cat, 0.0))
                for cat in all_categories
            )
        )

        max_t = max(max_t, tvd)
        records.append(
            {
                "group": str(name),
                "group_size": len(group),
                "t_distance": round(tvd, 4),
            }
        )

    return round(max_t, 4), pd.DataFrame(records)