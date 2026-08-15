import numpy as np
import pandas as pd


def apply_spatial_jitter(
    df: pd.DataFrame,
    lat_col: str,
    lon_col: str,
    radius_meters: float = 500.0,
) -> pd.DataFrame:
    """Applies random Gaussian spatial displacement to coordinates within a specified radius (in meters)."""
    jittered_df = df.copy()

    # Convert radius from meters to approximate degrees (~111,000m per degree)
    deg_offset = radius_meters / 111000.0

    lat_noise = np.random.normal(0, deg_offset / 2, size=len(jittered_df))
    lon_noise = np.random.normal(0, deg_offset / 2, size=len(jittered_df))

    jittered_df[lat_col] = (jittered_df[lat_col] + lat_noise).round(6)
    jittered_df[lon_col] = (jittered_df[lon_col] + lon_noise).round(6)

    return jittered_df


def create_spatial_grid_bins(
    df: pd.DataFrame,
    lat_col: str,
    lon_col: str,
    grid_size_degrees: float = 0.01,
) -> pd.DataFrame:
    """Bins GPS coordinates into uniform spatial grid bounding boxes (~1km at 0.01 degree resolution)."""
    binned_df = df.copy()

    binned_df["grid_lat_bin"] = (
        np.floor(binned_df[lat_col] / grid_size_degrees) * grid_size_degrees
    ).round(4)
    binned_df["grid_lon_bin"] = (
        np.floor(binned_df[lon_col] / grid_size_degrees) * grid_size_degrees
    ).round(4)
    binned_df["spatial_cell_id"] = (
        "GRID_"
        + binned_df["grid_lat_bin"].astype(str)
        + "_"
        + binned_df["grid_lon_bin"].astype(str)
    )

    return binned_df