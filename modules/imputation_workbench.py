import pandas as pd
from sklearn.impute import KNNImputer


def analyze_missingness(df: pd.DataFrame) -> pd.DataFrame:
    """Generates a summary of missing values and missingness proportions per variable."""
    missing_count = df.isnull().sum()
    missing_pct = (missing_count / len(df)) * 100

    summary = pd.DataFrame(
        {
            "column": df.columns,
            "missing_count": missing_count.values,
            "missing_percentage": missing_pct.round(2).values,
        }
    )
    return summary.sort_values(by="missing_count", ascending=False)


def impute_missing_data(
    df: pd.DataFrame, strategy: str = "knn", n_neighbors: int = 5
) -> pd.DataFrame:
    """Imputes missing values using K-Nearest Neighbors (KNN) or Median/Mode baseline strategy."""
    imputed_df = df.copy()
    numeric_cols = imputed_df.select_dtypes(include=["number"]).columns

    if strategy == "knn" and len(numeric_cols) > 0:
        imputer = KNNImputer(n_neighbors=n_neighbors)
        imputed_df[numeric_cols] = imputer.fit_transform(
            imputed_df[numeric_cols]
        )
    elif strategy == "median_mode":
        for col in imputed_df.columns:
            if col in numeric_cols:
                imputed_df[col] = imputed_df[col].fillna(
                    imputed_df[col].median()
                )
            else:
                mode_val = imputed_df[col].mode()
                if not mode_val.empty:
                    imputed_df[col] = imputed_df[col].fillna(mode_val[0])

    return imputed_df