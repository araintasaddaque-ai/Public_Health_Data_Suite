import numpy as np
import pandas as pd


def generate_differentially_private_df(
    df: pd.DataFrame,
    numeric_cols: list[str],
    categorical_cols: list[str],
    epsilon: float = 1.0,
) -> pd.DataFrame:
    """Generates a differentially private synthetic dataset using Laplace mechanism for numeric fields

    and noisy categorical sampling.
    """
    dp_df = df.copy()
    num_cols_count = len(numeric_cols)
    cat_cols_count = len(categorical_cols)
    total_vars = max(1, num_cols_count + cat_cols_count)

    # Allocate privacy budget across variables
    eps_per_var = epsilon / total_vars

    # 1. Numeric Fields: Apply Laplace Noise
    for col in numeric_cols:
        if col in dp_df.columns and pd.api.types.is_numeric_dtype(dp_df[col]):
            col_min, col_max = dp_df[col].min(), dp_df[col].max()
            sensitivity = (
                float(col_max - col_min) if col_max != col_min else 1.0
            )
            scale = sensitivity / eps_per_var

            noise = np.random.laplace(0, scale, size=len(dp_df))
            dp_df[col] = np.clip(dp_df[col] + noise, col_min, col_max)
            if pd.api.types.is_integer_dtype(df[col]):
                dp_df[col] = dp_df[col].round().astype(int)

    # 2. Categorical Fields: Noisy Distribution Resampling
    for col in categorical_cols:
        if col in dp_df.columns:
            counts = dp_df[col].value_counts()
            categories = counts.index.tolist()
            sensitivity = 2.0
            scale = sensitivity / eps_per_var

            noisy_counts = counts.values + np.random.laplace(
                0, scale, size=len(counts)
            )
            noisy_counts = np.maximum(noisy_counts, 0.001)
            probs = noisy_counts / noisy_counts.sum()

            dp_df[col] = np.random.choice(categories, size=len(dp_df), p=probs)

    return dp_df