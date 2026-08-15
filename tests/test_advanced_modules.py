import numpy as np
import pandas as pd
import pytest

from modules.differential_privacy import generate_differentially_private_df
from modules.fhir_bridge import (
    dataframe_to_fhir_patient_bundle,
    fhir_bundle_to_dataframe,
)
from modules.imputation_workbench import analyze_missingness, impute_missing_data
from modules.privacy_audit import evaluate_l_diversity, evaluate_t_closeness
from modules.spatial_privacy import apply_spatial_jitter, create_spatial_grid_bins


def test_differential_privacy_generation():
    df = pd.DataFrame(
        {
            "age": [25, 30, 45, 50, 60],
            "sys_bp": [120, 130, 125, 140, 135],
            "condition": ["Flu", "Flu", "COVID", "COVID", "Flu"],
        }
    )
    dp_df = generate_differentially_private_df(
        df, numeric_cols=["age", "sys_bp"], categorical_cols=["condition"], epsilon=1.0
    )
    assert len(dp_df) == len(df)
    assert list(dp_df.columns) == list(df.columns)


def test_privacy_auditing_l_diversity_and_t_closeness():
    df = pd.DataFrame(
        {
            "age_group": ["20-29", "20-29", "20-29", "30-39", "30-39"],
            "gender": ["M", "M", "M", "F", "F"],
            "diagnosis": ["Flu", "Flu", "COVID", "Diabetes", "Diabetes"],
        }
    )
    min_l, l_df = evaluate_l_diversity(
        df, quasi_identifiers=["age_group", "gender"], sensitive_column="diagnosis"
    )
    max_t, t_df = evaluate_t_closeness(
        df, quasi_identifiers=["age_group", "gender"], sensitive_column="diagnosis"
    )
    assert min_l == 1
    assert 0.0 <= max_t <= 1.0


def test_fhir_bridge_bidirectional_conversion():
    original_df = pd.DataFrame(
        {
            "patient_id": ["P101", "P102"],
            "first_name": ["Alice", "Bob"],
            "last_name": ["Smith", "Jones"],
            "gender": ["female", "male"],
            "date_of_birth": ["1990-01-01", "1985-05-15"],
            "uk_postcode": ["M14 4PX", "SW1A 1AA"],
            "nhs_number": ["9434765919", "6543219874"],
        }
    )
    bundle = dataframe_to_fhir_patient_bundle(original_df)
    assert bundle["resourceType"] == "Bundle"

    parsed_df = fhir_bundle_to_dataframe(bundle)
    assert len(parsed_df) == 2


def test_spatial_jitter_and_grid_binning():
    df = pd.DataFrame(
        {
            "patient_id": ["P1", "P2"],
            "latitude": [53.4808, 51.5074],
            "longitude": [-2.2426, -0.1278],
        }
    )
    jittered = apply_spatial_jitter(df, "latitude", "longitude", radius_meters=1000.0)
    binned = create_spatial_grid_bins(df, "latitude", "longitude", grid_size_degrees=0.01)

    assert not jittered["latitude"].equals(df["latitude"])
    assert "spatial_cell_id" in binned.columns


def test_missingness_analysis_and_imputation():
    df = pd.DataFrame(
        {
            "age": [25.0, np.nan, 35.0, 40.0, 50.0],
            "bp": [120.0, 130.0, np.nan, 125.0, 140.0],
            "group": ["A", "A", "B", np.nan, "B"],
        }
    )
    summary = analyze_missingness(df)
    assert summary.loc[summary["column"] == "age", "missing_count"].values[0] == 1

    imputed_knn = impute_missing_data(df, strategy="knn", n_neighbors=2)
    assert imputed_knn["age"].isna().sum() == 0

    imputed_baseline = impute_missing_data(df, strategy="median_mode")
    assert imputed_baseline["group"].isna().sum() == 0