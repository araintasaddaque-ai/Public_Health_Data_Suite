import io
import json
import numpy as np
import pandas as pd
import streamlit as st

# --- Module Imports ---
try:
    from modules.differential_privacy import generate_differentially_private_df
    from modules.fhir_bridge import (
        dataframe_to_fhir_patient_bundle,
        fhir_bundle_to_dataframe,
    )
    from modules.imputation_workbench import (
        analyze_missingness,
        impute_missing_data,
    )
    from modules.privacy_audit import evaluate_l_diversity, evaluate_t_closeness
    from modules.spatial_privacy import (
        apply_spatial_jitter,
        create_spatial_grid_bins,
    )
except ImportError as e:
    st.error(
        f"Module import error: {e}. Ensure the `modules/` folder contains all 5 module files."
    )

# --- Synthetic Demo Datasets ---
SITE_A_CSV = """patient_id,first_name,last_name,date_of_birth,age,gender,sys_bp,dia_bp,uk_postcode,nhs_number,latitude,longitude,visit_date
P001,John,Smith,1985-05-12,41,M,120,80,M14 4PX,9434765919,53.4808,-2.2426,2026-02-10
P002,Sarah,Connor,1992-11-03,33,F,310,40,SW1A 1AA,6543219874,51.5074,-0.1278,2026-03-01
P003,Mohammed,Khan,1970-01-15,56,M,135,85,LS1 4AP,1234567890,53.7997,-1.5492,2026-01-15
P004,Elena,Rostova,2001-08-24,25,F,118,78,EC1A 1BB,9434765919,51.5173,-0.1032,2029-12-31
P005,David,Wilson,1948-03-30,145,M,140,90,BT7 1NN,6543219874,54.5973,-5.9301,2026-02-28"""

SITE_B_CSV = """client_ref,full_name,dob,age_yrs,gender_code,blood_pressure_sys,blood_pressure_dia,zip_code,nhs_id,lat,lng,encounter_date
CL-901,Jon Smith,1985-05-12,41,Male,122,82,M14 4PX,9434765919,53.4810,-2.2430,2026-04-12
CL-902,Sarah Conner,1992-11-03,33,Female,115,75,SW1A 1AA,6543219874,51.5070,-0.1275,2026-04-15
CL-903,Mo Khan,1970-01-15,-5,Male,135,85,LS1 4AP,99999,53.7990,-1.5490,2026-02-01
CL-904,Alice Vane,1999-12-01,26,Female,110,70,EH1 1YZ,9434765919,55.9533,-3.1883,2026-03-10
CL-905,David Wilson,1948-03-30,78,Male,142,88,BT7 1NN,6543219874,54.5970,-5.9300,2026-04-01"""


# --- Page Config & Theme ---
st.set_page_config(
    page_title="Public Health Data Suite & Research Workbench",
    page_icon="🩺",
    layout="wide",
)

# --- Session State Initialization ---
if "df_active" not in st.session_state:
    st.session_state["df_active"] = pd.read_csv(io.StringIO(SITE_A_CSV))
    st.session_state["active_dataset_name"] = "Site A (Hospital Registry Sample)"


# --- Sidebar Setup & Data Loader ---
st.sidebar.title("🩺 Health Data Suite")
st.sidebar.caption("Zero-Knowledge Public Health Governance Engine")

st.sidebar.markdown("---")
st.sidebar.markdown("### 📥 Load Data")

uploaded_file = st.sidebar.file_uploader("Upload CSV Dataset", type=["csv"])
if uploaded_file is not None:
    st.session_state["df_active"] = pd.read_csv(uploaded_file)
    st.session_state["active_dataset_name"] = uploaded_file.name
    st.sidebar.success(f"Loaded {uploaded_file.name}")

st.sidebar.markdown("#### 🧪 Quick Demo Datasets")
col_a, col_b = st.sidebar.columns(2)

if col_a.button("Site A (Hospital)", help="Primary Hospital Registry"):
    st.session_state["df_active"] = pd.read_csv(io.StringIO(SITE_A_CSV))
    st.session_state["active_dataset_name"] = "Site A (Hospital Registry)"
    st.sidebar.success("Loaded Site A")

if col_b.button("Site B (Clinic)", help="Regional Community Clinic"):
    st.session_state["df_active"] = pd.read_csv(io.StringIO(SITE_B_CSV))
    st.session_state["active_dataset_name"] = "Site B (Community Clinic)"
    st.sidebar.success("Loaded Site B")

st.sidebar.markdown("---")
st.sidebar.info(
    "🔒 **Privacy Notice**: Zero-knowledge architecture. All uploaded data is processed in volatile RAM and is never persisted to server storage."
)


# --- Main Header ---
st.title("Public Health Data Suite & Research Workbench")
st.markdown(
    f"Active Dataset: **`{st.session_state['active_dataset_name']}`** | Records: **`{len(st.session_state['df_active'])}`** | Variables: **`{len(st.session_state['df_active'].columns)}`**"
)

# --- Active Dataset Preview ---
with st.expander("👁️ View Active Dataset Preview", expanded=False):
    st.dataframe(st.session_state["df_active"], use_container_width=True)

df = st.session_state["df_active"]

# --- Research Workbench Navigation Tabs ---
tab_dp, tab_audit, tab_fhir, tab_spatial, tab_impute = st.tabs(
    [
        "🛡️ Differential Privacy",
        "🔍 l-Diversity & t-Closeness",
        "🔥 HL7 FHIR Bridge",
        "🗺️ Spatial Privacy",
        "🩹 Imputation Workbench",
    ]
)

# ==========================================
# TAB 1: DIFFERENTIAL PRIVACY GENERATOR
# ==========================================
with tab_dp:
    st.subheader("Differential Privacy Generator")
    st.caption(
        "Injects Laplace noise into numerical fields and performs noisy categorical resampling based on privacy budget (ε)."
    )

    col1, col2 = st.columns([1, 2])

    with col1:
        epsilon = st.slider(
            "Privacy Budget (ε)",
            min_value=0.1,
            max_value=5.0,
            value=1.0,
            step=0.1,
            help="Lower ε = stronger privacy (more noise). Higher ε = higher utility (less noise).",
        )

        num_cols = st.multiselect(
            "Numerical Columns to Anonymize",
            df.select_dtypes(include=["number"]).columns.tolist(),
            default=[
                c
                for c in ["age", "sys_bp", "dia_bp", "age_yrs"]
                if c in df.columns
            ],
        )

        cat_cols = st.multiselect(
            "Categorical Columns to Resample",
            df.select_dtypes(include=["object", "category"]).columns.tolist(),
            default=[c for c in ["gender", "gender_code"] if c in df.columns],
        )

        generate_btn = st.button("Generate DP Synthetic Data", type="primary")

    with col2:
        if generate_btn:
            if not num_cols and not cat_cols:
                st.warning("Select at least one variable to anonymize.")
            else:
                dp_result = generate_differentially_private_df(
                    df,
                    numeric_cols=num_cols,
                    categorical_cols=cat_cols,
                    epsilon=epsilon,
                )
                st.success("Differentially Private Synthetic Dataset Generated!")
                st.dataframe(dp_result, use_container_width=True)
                st.download_button(
                    "Download Private CSV",
                    dp_result.to_csv(index=False),
                    "dp_synthetic_dataset.csv",
                    "text/csv",
                )


# ==========================================
# TAB 2: ADVANCED PRIVACY AUDITING
# ==========================================
with tab_audit:
    st.subheader("Attribute Disclosure Risk Scanner")
    st.caption(
        "Evaluates l-diversity (minimum distinct sensitive values) and t-closeness (distributional similarity) across equivalence classes."
    )

    qis = st.multiselect(
        "Quasi-Identifiers (Equivalence Class Keys)",
        df.columns.tolist(),
        default=[
            c
            for c in [
                "gender",
                "gender_code",
                "uk_postcode",
                "zip_code",
                "date_of_birth",
            ]
            if c in df.columns
        ],
    )

    sensitive_col = st.selectbox(
        "Sensitive Health Attribute",
        [c for c in df.columns if c not in qis],
        index=0 if len([c for c in df.columns if c not in qis]) > 0 else 0,
    )

    if qis and sensitive_col:
        min_l, l_df = evaluate_l_diversity(df, qis, sensitive_col)
        max_t, t_df = evaluate_t_closeness(df, qis, sensitive_col)

        m1, m2 = st.columns(2)
        m1.metric("Minimum l-Diversity", min_l)
        m2.metric("Max t-Closeness Distance (TVD)", max_t)

        st.markdown("#### Equivalence Class Distribution Breakdown")
        st.dataframe(t_df, use_container_width=True)


# ==========================================
# TAB 3: HL7 FHIR INTEROPERABILITY BRIDGE
# ==========================================
with tab_fhir:
    st.subheader("HL7 FHIR Interoperability Bridge")
    st.caption(
        "Bi-directional transformation between tabular datasets and HL7 FHIR Patient Bundle JSON standards."
    )

    mode = st.radio(
        "Operation Mode",
        ["Tabular DataFrame ➔ FHIR JSON", "FHIR JSON ➔ Tabular DataFrame"],
        horizontal=True,
    )

    if mode == "Tabular DataFrame ➔ FHIR JSON":
        if st.button("Convert Dataset to FHIR Bundle", type="primary"):
            fhir_bundle = dataframe_to_fhir_patient_bundle(df)
            json_str = json.dumps(fhir_bundle, indent=2)

            st.json(fhir_bundle)
            st.download_button(
                "Download FHIR Patient Bundle (.json)",
                json_str,
                "fhir_patient_bundle.json",
                "application/json",
            )
    else:
        uploaded_json = st.file_uploader(
            "Upload HL7 FHIR Bundle JSON", type=["json"]
        )
        if uploaded_json:
            fhir_data = json.load(uploaded_json)
            parsed_df = fhir_bundle_to_dataframe(fhir_data)
            st.success("Successfully parsed FHIR Patient Bundle!")
            st.dataframe(parsed_df, use_container_width=True)


# ==========================================
# TAB 4: SPATIAL PRIVACY ENGINE
# ==========================================
with tab_spatial:
    st.subheader("Geospatial Anonymization Engine")
    st.caption(
        "Applies Gaussian spatial jittering or bounding-box grid binning to GPS coordinates."
    )

    lat_candidates = [
        c for c in df.columns if "lat" in c.lower()
    ] + df.columns.tolist()
    lon_candidates = [
        c for c in df.columns if "lon" in c.lower() or "lng" in c.lower()
    ] + df.columns.tolist()

    c1, c2 = st.columns(2)
    lat_col = c1.selectbox("Latitude Column", lat_candidates)
    lon_col = c2.selectbox("Longitude Column", lon_candidates)

    spatial_mode = st.radio(
        "Anonymization Method",
        ["Gaussian Spatial Jitter", "Bounding Box Grid Binning"],
        horizontal=True,
    )

    if spatial_mode == "Gaussian Spatial Jitter":
        radius = st.slider("Displacement Radius (meters)", 100, 2000, 500, 100)
        if st.button("Apply Spatial Jitter", type="primary"):
            jittered_df = apply_spatial_jitter(
                df, lat_col, lon_col, radius_meters=radius
            )
            st.success(f"Applied {radius}m spatial jittering!")
            st.dataframe(jittered_df, use_container_width=True)
    else:
        grid_deg = st.select_slider(
            "Grid Box Resolution (degrees)",
            options=[0.001, 0.005, 0.01, 0.05, 0.1],
            value=0.01,
        )
        if st.button("Apply Spatial Binning", type="primary"):
            binned_df = create_spatial_grid_bins(
                df, lat_col, lon_col, grid_size_degrees=grid_deg
            )
            st.success("Spatial grid binning complete!")
            st.dataframe(binned_df, use_container_width=True)


# ==========================================
# TAB 5: IMPUTATION WORKBENCH
# ==========================================
with tab_impute:
    st.subheader("Missingness Profiler & Imputation Workbench")
    st.caption(
        "Profile missing value rates across dataset columns and perform KNN or statistical imputation."
    )

    summary_df = analyze_missingness(df)
    st.markdown("#### Missing Value Summary")
    st.dataframe(summary_df, use_container_width=True)

    st.markdown("---")
    st.markdown("#### Run Imputation")

    imp_col1, imp_col2 = st.columns([1, 2])
    strategy = imp_col1.selectbox(
        "Imputation Strategy",
        ["knn", "median_mode"],
        format_func=lambda x: "K-Nearest Neighbors (KNN)"
        if x == "knn"
        else "Median / Mode Baseline",
    )

    if imp_col1.button("Impute Dataset", type="primary"):
        imputed_df = impute_missing_data(df, strategy=strategy)
        st.success("Dataset imputation complete!")
        st.dataframe(imputed_df, use_container_width=True)
        st.download_button(
            "Download Imputed CSV",
            imputed_df.to_csv(index=False),
            "imputed_health_dataset.csv",
            "text/csv",
        )