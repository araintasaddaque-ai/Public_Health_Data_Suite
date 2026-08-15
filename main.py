import hashlib
import hmac
import io
import json
import re
import numpy as np
import pandas as pd
import streamlit as st

# --- Research Module Imports ---
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


# --- Core Helper Functions ---
def validate_nhs_number(nhs_num: str) -> bool:
    """Validates a 10-digit UK NHS Number using the Modulus 11 checksum algorithm."""
    nhs_str = str(nhs_num).strip().replace(" ", "").replace("-", "")
    if len(nhs_str) != 10 or not nhs_str.isdigit():
        return False
    weights = [10, 9, 8, 7, 6, 5, 4, 3, 2]
    total = sum(int(nhs_str[i]) * weights[i] for i in range(9))
    remainder = total % 11
    check_digit = 11 - remainder
    if check_digit == 11:
        check_digit = 0
    elif check_digit == 10:
        return False
    return check_digit == int(nhs_str[9])


def mask_outward_postcode(postcode: str) -> str:
    """Truncates UK postcodes to outward code only (e.g., 'M14 4PX' -> 'M14')."""
    if pd.isna(postcode):
        return ""
    clean_pc = str(postcode).strip().upper()
    parts = clean_pc.split()
    return parts[0] if len(parts) > 0 else clean_pc


def hash_pprl_token(val: str, salt: str = "health_suite_secret_salt") -> str:
    """Generates a deterministic salted SHA-256 HMAC hash for PPRL record linkage."""
    if pd.isna(val) or not str(val).strip():
        return ""
    key = salt.encode("utf-8")
    msg = str(val).strip().lower().encode("utf-8")
    return hmac.new(key, msg, hashlib.sha256).hexdigest()[:16]


# --- Synthetic Demo Datasets ---
SITE_A_CSV = """patient_id,first_name,last_name,date_of_birth,age,gender,sys_bp,dia_bp,uk_postcode,nhs_number,latitude,longitude,visit_date
P001,John,Smith,1985-05-12,41,M,120,80,M14 4PX,9434765919,53.4808,-2.2426,2026-02-10
P002,Sarah,Connor,1992-11-03,33,F,310,40,SW1A 1AA,6543219874,51.5074,-0.1278,2026-03-01
P003,Mohammed,Khan,1970-01-15,56,M,135,85,LS1 4AP,1234567890,53.7997,-1.5492,2026-01-15
P004,Elena,Rostova,2001-08-24,-5,F,118,78,EC1A 1BB,9434765919,51.5173,-0.1032,2029-12-31
P005,David,Wilson,1948-03-30,145,M,140,90,BT7 1NN,6543219874,54.5973,-5.9301,2026-02-28"""

SITE_B_CSV = """client_ref,full_name,dob,age_yrs,gender_code,blood_pressure_sys,blood_pressure_dia,zip_code,nhs_id,lat,lng,encounter_date
CL-901,Jon Smith,1985-05-12,41,Male,122,82,M14 4PX,9434765919,53.4810,-2.2430,2026-04-12
CL-902,Sarah Conner,1992-11-03,33,Female,115,75,SW1A 1AA,6543219874,51.5070,-0.1275,2026-04-15
CL-903,Mo Khan,1970-01-15,56,Male,135,85,LS1 4AP,99999,53.7990,-1.5490,2026-02-01
CL-904,Alice Vane,1999-12-01,26,Female,110,70,EH1 1YZ,9434765919,55.9533,-3.1883,2026-03-10
CL-905,David Wilson,1948-03-30,78,Male,142,88,BT7 1NN,6543219874,54.5970,-5.9300,2026-04-01"""


# --- Page Config ---
st.set_page_config(
    page_title="Public Health Data Suite & Research Workbench",
    page_icon="🩺",
    layout="wide",
)

# --- Session State Initialization ---
if "df_active" not in st.session_state:
    st.session_state["df_active"] = pd.read_csv(io.StringIO(SITE_A_CSV))
    st.session_state["active_dataset_name"] = "Site A (Hospital Registry Sample)"

# --- Sidebar ---
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
if col_a.button("Site A (Hospital)"):
    st.session_state["df_active"] = pd.read_csv(io.StringIO(SITE_A_CSV))
    st.session_state["active_dataset_name"] = "Site A (Hospital Registry)"
    st.sidebar.success("Loaded Site A")

if col_b.button("Site B (Clinic)"):
    st.session_state["df_active"] = pd.read_csv(io.StringIO(SITE_B_CSV))
    st.session_state["active_dataset_name"] = "Site B (Community Clinic)"
    st.sidebar.success("Loaded Site B")

st.sidebar.markdown("---")
st.sidebar.info(
    "🔒 **Privacy Notice**: Zero-knowledge architecture. All uploaded data is processed in volatile RAM and is never persisted to server storage."
)


# --- Main Header ---
st.title("Public Health Data Suite & Governance Workbench")
st.markdown(
    f"Active Dataset: **`{st.session_state['active_dataset_name']}`** | Records: **`{len(st.session_state['df_active'])}`** | Variables: **`{len(st.session_state['df_active'].columns)}`**"
)

with st.expander("👁️ View Active Dataset Preview", expanded=False):
    st.dataframe(st.session_state["df_active"], use_container_width=True)

df = st.session_state["df_active"]


# --- Navigation Tabs ---
(
    tab_k,
    tab_nhs,
    tab_pprl,
    tab_firewall,
    tab_schema,
    tab_dp,
    tab_audit,
    tab_fhir,
    tab_spatial,
    tab_impute,
) = st.tabs(
    [
        "🛡️ Privacy Pre-Flight Scanner",
        "🇬🇧 UK NHS Engine",
        "🔗 PPRL & Linkage",
        "🚨 Quality Firewall",
        "🔄 Schema Transformer",
        "🎲 Differential Privacy",
        "🔍 l-Diversity / t-Closeness",
        "🔥 HL7 FHIR Bridge",
        "🗺️ Spatial Privacy",
        "🩹 Imputation Workbench",
    ]
)


# ==========================================
# TAB 1: PRIVACY PRE-FLIGHT SCANNER (k-ANONYMITY)
# ==========================================
with tab_k:
    st.subheader("Privacy Pre-Flight Scanner & k-Anonymity Audit")
    st.caption(
        "Audits mathematical k-anonymity across Quasi-Identifiers and applies automated age-binning generalization."
    )

    col1, col2 = st.columns([1, 2])
    with col1:
        qis = st.multiselect(
            "Select Quasi-Identifiers",
            df.columns.tolist(),
            default=[
                c
                for c in ["gender", "gender_code", "age", "age_yrs", "uk_postcode"]
                if c in df.columns
            ],
        )
        target_k = st.slider("Target k-Anonymity Threshold", 2, 10, 3)
        gen_age = st.checkbox("Apply 10-Year Age Group Generalization", value=True)

    with col2:
        scan_df = df.copy()
        age_col = "age" if "age" in scan_df.columns else "age_yrs" if "age_yrs" in scan_df.columns else None

        if gen_age and age_col and pd.api.types.is_numeric_dtype(scan_df[age_col]):
            scan_df["age_group"] = pd.cut(
                scan_df[age_col],
                bins=[-1, 17, 29, 39, 49, 59, 69, 120],
                labels=["<18", "18-29", "30-39", "40-49", "50-59", "60-69", "70+"],
            )
            if age_col in qis:
                qis = ["age_group" if x == age_col else x for x in qis]

        if qis:
            counts = scan_df.groupby(qis).size().reset_index(name="group_size")
            min_k = int(counts["group_size"].min()) if not counts.empty else 0

            if min_k >= target_k:
                st.success(f"Passed! Dataset meets k-Anonymity (Minimum k = {min_k} >= {target_k})")
            else:
                st.error(f"Violation Detected! Minimum k = {min_k} < Target {target_k}")

            st.markdown("#### Equivalence Classes Breakdown")
            st.dataframe(counts, use_container_width=True)


# ==========================================
# TAB 2: UK NHS COMPLIANCE ENGINE
# ==========================================
with tab_nhs:
    st.subheader("UK NHS Compliance & GDPR Engine")
    st.caption(
        "Validates 10-digit NHS Numbers using Modulus 11 and masks UK outward postcodes for GDPR compliance."
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Modulus 11 NHS Number Audit")
        nhs_col = st.selectbox(
            "Select NHS Number Field",
            [c for c in df.columns if "nhs" in c.lower()] + df.columns.tolist(),
        )

        if st.button("Run NHS Number Validation"):
            audit_df = df.copy()
            audit_df["nhs_valid"] = audit_df[nhs_col].apply(validate_nhs_number)
            st.dataframe(audit_df[[nhs_col, "nhs_valid"]], use_container_width=True)

    with col2:
        st.markdown("#### UK Outward Postcode Masking")
        pc_col = st.selectbox(
            "Select Postcode Field",
            [c for c in df.columns if "postcode" in c.lower() or "zip" in c.lower()] + df.columns.tolist(),
        )

        if st.button("Apply Outward Masking"):
            masked_df = df.copy()
            masked_df["outward_postcode"] = masked_df[pc_col].apply(mask_outward_postcode)
            st.dataframe(masked_df[[pc_col, "outward_postcode"]], use_container_width=True)


# ==========================================
# TAB 3: PRIVACY-PRESERVING RECORD LINKAGE (PPRL)
# ==========================================
with tab_pprl:
    st.subheader("Privacy-Preserving Record Linkage (PPRL)")
    st.caption("Generates deterministic HMAC SHA-256 tokens for multi-site patient de-duplication.")

    salt_key = st.text_input("Enter Secret Site Salt Key", "nhs_trust_alpha_secret")
    link_cols = st.multiselect(
        "Identifiers to Hash into PPRL Token",
        df.columns.tolist(),
        default=[c for c in ["first_name", "last_name", "date_of_birth", "dob"] if c in df.columns],
    )

    if st.button("Generate PPRL Tokens", type="primary"):
        pprl_df = df.copy()

        def compute_token(row):
            combined = "".join([str(row[c]) for c in link_cols])
            return hash_pprl_token(combined, salt=salt_key)

        pprl_df["pprl_token"] = pprl_df.apply(compute_token, axis=1)
        st.success("PPRL Tokens Created!")
        st.dataframe(pprl_df[["pprl_token"] + [c for c in df.columns if c not in link_cols]], use_container_width=True)


# ==========================================
# TAB 4: AUTOMATED QUALITY FIREWALL
# ==========================================
with tab_firewall:
    st.subheader("Automated Quality Firewall")
    st.caption("Triages impossible physiological anomalies, invalid ages, and invalid encounter dates.")

    if st.button("Run Quality Firewall Audit", type="primary"):
        firewall_df = df.copy()
        anomalies = []

        for idx, row in firewall_df.iterrows():
            reasons = []
            age_val = row.get("age", row.get("age_yrs", None))
            sys_val = row.get("sys_bp", row.get("blood_pressure_sys", None))

            if pd.notna(age_val) and (age_val < 0 or age_val > 120):
                reasons.append(f"Invalid Age: {age_val}")
            if pd.notna(sys_val) and (sys_val < 60 or sys_val > 250):
                reasons.append(f"Anomalous Systolic BP: {sys_val}")

            if reasons:
                anomalies.append({"row": idx + 1, "issues": "; ".join(reasons)})

        if anomalies:
            st.error(f"Detected {len(anomalies)} Quality Violations!")
            st.dataframe(pd.DataFrame(anomalies), use_container_width=True)
        else:
            st.success("No physiological or date quality violations detected.")


# ==========================================
# TAB 5: SCHEMA TRANSFORMER
# ==========================================
with tab_schema:
    st.subheader("DHIS2 & WHO Schema Transformer")
    st.caption("Standardizes heterogeneous column headers to DHIS2 / WHO surveillance schemas.")

    dhis2_mapping = {
        "patient_id": "trackedEntityInstance",
        "client_ref": "trackedEntityInstance",
        "date_of_birth": "dob",
        "gender": "sex",
        "gender_code": "sex",
        "uk_postcode": "postcode",
        "zip_code": "postcode",
    }

    if st.button("Transform to DHIS2 Standard Schema"):
        transformed_df = df.rename(columns=dhis2_mapping)
        st.success("Schema Transformed!")
        st.dataframe(transformed_df, use_container_width=True)


# ==========================================
# TAB 6: DIFFERENTIAL PRIVACY GENERATOR
# ==========================================
with tab_dp:
    st.subheader("Differential Privacy Generator")
    st.caption("Injects Laplace noise into numerical fields and performs noisy categorical resampling.")

    col1, col2 = st.columns([1, 2])
    with col1:
        epsilon = st.slider("Privacy Budget (ε)", 0.1, 5.0, 1.0, 0.1)
        num_cols = st.multiselect(
            "Numerical Columns",
            df.select_dtypes(include=["number"]).columns.tolist(),
            default=[c for c in ["age", "sys_bp", "dia_bp", "age_yrs"] if c in df.columns],
        )
        cat_cols = st.multiselect(
            "Categorical Columns",
            df.select_dtypes(include=["object", "category"]).columns.tolist(),
            default=[c for c in ["gender", "gender_code"] if c in df.columns],
        )
        generate_btn = st.button("Generate DP Synthetic Data", type="primary")

    with col2:
        if generate_btn:
            dp_result = generate_differentially_private_df(
                df, numeric_cols=num_cols, categorical_cols=cat_cols, epsilon=epsilon
            )
            st.success("Differentially Private Synthetic Dataset Generated!")
            st.dataframe(dp_result, use_container_width=True)


# ==========================================
# TAB 7: ADVANCED PRIVACY AUDITING (l-DIVERSITY & t-CLOSENESS)
# ==========================================
with tab_audit:
    st.subheader("Attribute Disclosure Risk Scanner")
    st.caption("Evaluates l-diversity and t-closeness across equivalence classes.")

    qis_audit = st.multiselect(
        "Quasi-Identifiers",
        df.columns.tolist(),
        default=[c for c in ["gender", "gender_code", "uk_postcode", "zip_code"] if c in df.columns],
    )
    sens_col = st.selectbox("Sensitive Health Variable", [c for c in df.columns if c not in qis_audit])

    if qis_audit and sens_col:
        min_l, l_df = evaluate_l_diversity(df, qis_audit, sens_col)
        max_t, t_df = evaluate_t_closeness(df, qis_audit, sens_col)

        m1, m2 = st.columns(2)
        m1.metric("Minimum l-Diversity", min_l)
        m2.metric("Max t-Closeness Distance (TVD)", max_t)

        st.dataframe(t_df, use_container_width=True)


# ==========================================
# TAB 8: HL7 FHIR INTEROPERABILITY BRIDGE
# ==========================================
with tab_fhir:
    st.subheader("HL7 FHIR Interoperability Bridge")
    st.caption("Bi-directional transformation between DataFrames and HL7 FHIR JSON Bundles.")

    mode = st.radio("Operation Mode", ["Tabular DataFrame ➔ FHIR JSON", "FHIR JSON ➔ Tabular DataFrame"], horizontal=True)

    if mode == "Tabular DataFrame ➔ FHIR JSON":
        if st.button("Convert Dataset to FHIR Bundle", type="primary"):
            fhir_bundle = dataframe_to_fhir_patient_bundle(df)
            st.json(fhir_bundle)
    else:
        uploaded_json = st.file_uploader("Upload HL7 FHIR Bundle JSON", type=["json"])
        if uploaded_json:
            fhir_data = json.load(uploaded_json)
            parsed_df = fhir_bundle_to_dataframe(fhir_data)
            st.success("Parsed FHIR Bundle!")
            st.dataframe(parsed_df, use_container_width=True)


# ==========================================
# TAB 9: SPATIAL PRIVACY ENGINE
# ==========================================
with tab_spatial:
    st.subheader("Geospatial Anonymization Engine")
    st.caption("Applies Gaussian spatial jittering or bounding-box grid binning to GPS coordinates.")

    c1, c2 = st.columns(2)
    lat_col = c1.selectbox("Latitude Column", [c for c in df.columns if "lat" in c.lower()] + df.columns.tolist())
    lon_col = c2.selectbox("Longitude Column", [c for c in df.columns if "lon" in c.lower() or "lng" in c.lower()] + df.columns.tolist())

    spatial_mode = st.radio("Method", ["Gaussian Spatial Jitter", "Bounding Box Grid Binning"], horizontal=True)

    if spatial_mode == "Gaussian Spatial Jitter":
        radius = st.slider("Displacement Radius (meters)", 100, 2000, 500, 100)
        if st.button("Apply Spatial Jitter", type="primary"):
            jittered_df = apply_spatial_jitter(df, lat_col, lon_col, radius_meters=radius)
            st.dataframe(jittered_df, use_container_width=True)
    else:
        grid_deg = st.select_slider("Grid Resolution (degrees)", options=[0.001, 0.005, 0.01, 0.05, 0.1], value=0.01)
        if st.button("Apply Spatial Binning", type="primary"):
            binned_df = create_spatial_grid_bins(df, lat_col, lon_col, grid_size_degrees=grid_deg)
            st.dataframe(binned_df, use_container_width=True)


# ==========================================
# TAB 10: IMPUTATION WORKBENCH
# ==========================================
with tab_impute:
    st.subheader("Missingness Profiler & Imputation Workbench")
    st.caption("Profiles missing values and performs KNN or statistical baseline imputation.")

    summary_df = analyze_missingness(df)
    st.dataframe(summary_df, use_container_width=True)

    strategy = st.selectbox("Imputation Strategy", ["knn", "median_mode"])
    if st.button("Impute Dataset", type="primary"):
        imputed_df = impute_missing_data(df, strategy=strategy)
        st.success("Imputation complete!")
        st.dataframe(imputed_df, use_container_width=True)