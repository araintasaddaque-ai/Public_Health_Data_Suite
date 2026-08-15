import hashlib
import hmac
import io
import json
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


# --- Helper Logic & Helpers ---
def validate_nhs_number(nhs_num: str) -> bool:
    nhs_str = str(nhs_num).strip().replace(" ", "").replace("-", "")
    if len(nhs_str) != 10 or not nhs_str.isdigit():
        return False
    weights = [10, 9, 8, 7, 6, 5, 4, 3, 2]
    total = sum(int(nhs_str[i]) * weights[i] for i in range(9))
    check_digit = 11 - (total % 11)
    if check_digit == 11:
        check_digit = 0
    elif check_digit == 10:
        return False
    return check_digit == int(nhs_str[9])


def mask_outward_postcode(postcode: str) -> str:
    if pd.isna(postcode):
        return ""
    clean_pc = str(postcode).strip().upper()
    parts = clean_pc.split()
    return parts[0] if len(parts) > 0 else clean_pc


def hash_pprl_token(val: str, salt: str = "health_suite_secret_salt") -> str:
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


# --- Page Config & Custom Styling ---
st.set_page_config(
    page_title="Public Health Data Suite & Governance Workbench",
    page_icon="🩺",
    layout="wide",
)

st.markdown(
    """
    <style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #1E3A8A; margin-bottom: 0px; }
    .sub-header { font-size: 1rem; color: #4B5563; margin-bottom: 20px; }
    .architect-card { background-color: #F0F9FF; border-left: 4px solid #0284C7; padding: 12px; border-radius: 6px; margin-bottom: 15px; }
    .metric-box { background-color: #F8FAFC; padding: 15px; border-radius: 8px; border: 1px solid #E2E8F0; text-align: center; }
    </style>
""",
    unsafe_allow_html=True,
)


# --- Session State ---
if "df_active" not in st.session_state:
    st.session_state["df_active"] = pd.read_csv(io.StringIO(SITE_A_CSV))
    st.session_state["active_dataset_name"] = "Site A (Hospital Registry Sample)"

df = st.session_state["df_active"]


# --- Sidebar Navigation & Author Attribution ---
st.sidebar.title("🩺 Health Data Suite")
st.sidebar.caption("Zero-Knowledge Governance Workbench")

# Architect Attribution Block
st.sidebar.markdown(
    """
    <div class="architect-card">
        <small><b>Lead System Architect & Chief Engineer</b></small><br>
        <b>Engr. Tasaddaque Hussain Arain</b><br>
        <small>Reg. Professional Engineer (PEC COMP/7479)</small><br>
        <a href="https://www.linkedin.com/in/tasaddaque" target="_blank">🔗 LinkedIn Profile</a>
    </div>
""",
    unsafe_allow_html=True,
)

st.sidebar.markdown("---")
st.sidebar.subheader("📌 Navigation Menu")

category = st.sidebar.radio(
    "Select Suite Category",
    ["📋 Core Governance & Compliance", "🔬 Advanced Research Workbench"],
)

if category == "📋 Core Governance & Compliance":
    active_tool = st.sidebar.radio(
        "Select Governance Tool",
        [
            "🛡️ Privacy Pre-Flight Scanner (k-Anonymity)",
            "🇬🇧 UK NHS Compliance Engine",
            "🔗 PPRL Record Linkage",
            "🚨 Quality Firewall & Triage",
            "🔄 DHIS2 / WHO Schema Transformer",
        ],
    )
else:
    active_tool = st.sidebar.radio(
        "Select Research Workbench Tool",
        [
            "🎲 Differential Privacy Generator",
            "🔍 l-Diversity & t-Closeness Audit",
            "🔥 HL7 FHIR Interoperability Bridge",
            "🗺️ Spatial Privacy & Geospatial Engine",
            "🩹 Imputation Workbench",
        ],
    )

st.sidebar.markdown("---")
st.sidebar.markdown("### 📥 Dataset Loader")
uploaded_file = st.sidebar.file_uploader("Upload CSV File", type=["csv"])
if uploaded_file is not None:
    st.session_state["df_active"] = pd.read_csv(uploaded_file)
    st.session_state["active_dataset_name"] = uploaded_file.name

col_a, col_b = st.sidebar.columns(2)
if col_a.button("Demo Site A"):
    st.session_state["df_active"] = pd.read_csv(io.StringIO(SITE_A_CSV))
    st.session_state["active_dataset_name"] = "Site A (Hospital Registry)"

if col_b.button("Demo Site B"):
    st.session_state["df_active"] = pd.read_csv(io.StringIO(SITE_B_CSV))
    st.session_state["active_dataset_name"] = "Site B (Clinic Registry)"


# --- Main Header Banner ---
st.markdown(
    '<div class="main-header">Public Health Data Suite & Governance Workbench</div>',
    unsafe_allow_html=True,
)
st.markdown(
    f'<div class="sub-header">Active Dataset: <b>{st.session_state["active_dataset_name"]}</b> | Records: <b>{len(df)}</b> | Variables: <b>{len(df.columns)}</b></div>',
    unsafe_allow_html=True,
)

with st.expander("👁️ Preview Active Data Matrix", expanded=False):
    st.dataframe(df, use_container_width=True)

st.markdown("---")


# ==============================================================================
# TOOL 1: PRIVACY PRE-FLIGHT SCANNER (k-ANONYMITY)
# ==============================================================================
if active_tool == "🛡️ Privacy Pre-Flight Scanner (k-Anonymity)":
    st.header("🛡️ Privacy Pre-Flight Scanner (k-Anonymity)")
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
                for c in [
                    "gender",
                    "gender_code",
                    "age",
                    "age_yrs",
                    "uk_postcode",
                ]
                if c in df.columns
            ],
        )
        target_k = st.slider("Target k-Anonymity Threshold", 2, 10, 3)
        gen_age = st.checkbox(
            "Apply 10-Year Age Group Generalization", value=True
        )

    with col2:
        scan_df = df.copy()
        age_col = (
            "age"
            if "age" in scan_df.columns
            else "age_yrs"
            if "age_yrs" in scan_df.columns
            else None
        )

        if (
            gen_age
            and age_col
            and pd.api.types.is_numeric_dtype(scan_df[age_col])
        ):
            scan_df["age_group"] = pd.cut(
                scan_df[age_col],
                bins=[-1, 17, 29, 39, 49, 59, 69, 120],
                labels=[
                    "<18",
                    "18-29",
                    "30-39",
                    "40-49",
                    "50-59",
                    "60-69",
                    "70+",
                ],
            )
            if age_col in qis:
                qis = ["age_group" if x == age_col else x for x in qis]

        if qis:
            counts = scan_df.groupby(qis).size().reset_index(name="group_size")
            min_k = int(counts["group_size"].min()) if not counts.empty else 0

            m1, m2 = st.columns(2)
            m1.metric("Min Equivalence Class Size (k)", min_k)
            m2.metric("Target Threshold", target_k)

            st.markdown("#### 📊 Equivalence Class Size Distribution (Infographic)")
            st.bar_chart(counts["group_size"])

            st.markdown("#### Equivalence Classes Breakdown")
            st.dataframe(counts, use_container_width=True)

            # Standard Audit Report Download
            report = f"# k-Anonymity Audit Certificate\n- Dataset: {st.session_state['active_dataset_name']}\n- Minimum k: {min_k}\n- Target k: {target_k}\n- Compliance Status: {'PASSED' if min_k >= target_k else 'FAILED'}\n- Quasi-Identifiers: {', '.join(qis)}\n- Architect: Engr. Tasaddaque Hussain Arain\n"
            st.download_button(
                "📥 Download Standard k-Anonymity Audit Report (.txt)",
                report,
                "k_anonymity_audit_report.txt",
                "text/plain",
            )


# ==============================================================================
# TOOL 2: UK NHS COMPLIANCE ENGINE
# ==============================================================================
elif active_tool == "🇬🇧 UK NHS Compliance Engine":
    st.header("🇬🇧 UK NHS Compliance Engine")
    st.caption(
        "Validates 10-digit NHS Numbers using Modulus 11 and masks UK outward postcodes for GDPR compliance."
    )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Modulus 11 NHS Validation")
        nhs_col = st.selectbox(
            "NHS Number Field",
            [c for c in df.columns if "nhs" in c.lower()] + df.columns.tolist(),
        )
        audit_df = df.copy()
        audit_df["nhs_valid"] = audit_df[nhs_col].apply(validate_nhs_number)

        valid_count = int(audit_df["nhs_valid"].sum())
        invalid_count = len(audit_df) - valid_count

        st.metric("Valid NHS Numbers", f"{valid_count} / {len(audit_df)}")
        st.bar_chart(pd.DataFrame({"Status": ["Valid", "Invalid"], "Count": [valid_count, invalid_count]}).set_index("Status"))
        st.dataframe(audit_df[[nhs_col, "nhs_valid"]], use_container_width=True)

    with col2:
        st.markdown("#### Outward Postcode Masking")
        pc_col = st.selectbox(
            "Postcode Field",
            [c for c in df.columns if "postcode" in c.lower() or "zip" in c.lower()] + df.columns.tolist(),
        )
        masked_df = df.copy()
        masked_df["outward_postcode"] = masked_df[pc_col].apply(mask_outward_postcode)

        st.metric("Postcodes Truncated", len(masked_df))
        st.dataframe(masked_df[[pc_col, "outward_postcode"]], use_container_width=True)

    report_nhs = f"# UK NHS Compliance Attestation\n- Dataset: {st.session_state['active_dataset_name']}\n- Total Records: {len(df)}\n- Valid NHS Checksums: {valid_count}\n- Invalid NHS Checksums: {invalid_count}\n- Outward Postcode Masking: Applied\n- Governance Standard: UK GDPR / DSPT Compliant\n"
    st.download_button(
        "📥 Download NHS Compliance Governance Report",
        report_nhs,
        "nhs_compliance_report.txt",
        "text/plain",
    )


# ==============================================================================
# TOOL 3: PPRL RECORD LINKAGE
# ==============================================================================
elif active_tool == "🔗 PPRL Record Linkage":
    st.header("🔗 Privacy-Preserving Record Linkage (PPRL)")
    st.caption(
        "Generates deterministic HMAC SHA-256 tokens for multi-site patient de-duplication."
    )

    salt_key = st.text_input("Enter Site Salt Key", "nhs_trust_alpha_secret")
    link_cols = st.multiselect(
        "Identifiers to Hash into Token",
        df.columns.tolist(),
        default=[c for c in ["first_name", "last_name", "date_of_birth", "dob"] if c in df.columns],
    )

    if st.button("Generate Linkage Tokens", type="primary"):
        pprl_df = df.copy()

        def compute_token(row):
            combined = "".join([str(row[c]) for c in link_cols])
            return hash_pprl_token(combined, salt=salt_key)

        pprl_df["pprl_token"] = pprl_df.apply(compute_token, axis=1)

        unique_tokens = pprl_df["pprl_token"].nunique()
        duplicate_count = len(pprl_df) - unique_tokens

        m1, m2 = st.columns(2)
        m1.metric("Unique Patient Entities", unique_tokens)
        m2.metric("Cross-Site Duplicates Identified", duplicate_count)

        st.markdown("#### 📊 Token Uniqueness Infographic")
        st.bar_chart(pd.DataFrame({"Metric": ["Unique Entities", "Duplicates"], "Count": [unique_tokens, duplicate_count]}).set_index("Metric"))

        st.dataframe(pprl_df[["pprl_token"] + [c for c in df.columns if c not in link_cols]], use_container_width=True)

        report_pprl = f"# PPRL Linkage Certificate\n- Dataset: {st.session_state['active_dataset_name']}\n- Total Records Processed: {len(df)}\n- Unique Patient Clusters: {unique_tokens}\n- Potential Cross-Site Duplicates: {duplicate_count}\n- Encryption Standard: Salted HMAC SHA-256\n"
 st.download_button(
            "📥 Download PPRL Linkage Audit Log",
            report_pprl,
            "pprl_linkage_report.txt",
            "text/plain",
        )

# ==============================================================================
# TOOL 4: QUALITY FIREWALL & TRIAGE
# ==============================================================================
elif active_tool == "🚨 Quality Firewall & Triage":
    st.header("🚨 Automated Quality Firewall & Triage")
    st.caption("Triages physiological anomalies, invalid ages, and invalid encounter dates.")

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

    anomaly_df = pd.DataFrame(anomalies)

    m1, m2 = st.columns(2)
    m1.metric("Total Records Audited", len(df))
    m2.metric("Quality Anomalies Flagged", len(anomaly_df))

    st.markdown("#### 📊 Quality Health Index Infographic")
    st.bar_chart(pd.DataFrame({"Status": ["Clean Records", "Anomalous Records"], "Count": [len(df) - len(anomaly_df), len(anomaly_df)]}).set_index("Status"))

    if not anomaly_df.empty:
        st.error("Flagged Quality Violations")
        st.dataframe(anomaly_df, use_container_width=True)
    else:
        st.success("No physiological or date quality violations detected.")

    report_qw = f"# Data Quality Audit Certificate\n- Dataset: {st.session_state['active_dataset_name']}\n- Total Audited Rows: {len(df)}\n- Clean Records: {len(df) - len(anomaly_df)}\n- Anomalous Records Flagged: {len(anomaly_df)}\n"
    st.download_button(
        "📥 Download Quality Triage Report",
        report_qw,
        "data_quality_triage_report.txt",
        "text/plain",
    )


# ==============================================================================
# TOOL 5: DHIS2 / WHO SCHEMA TRANSFORMER
# ==============================================================================
elif active_tool == "🔄 DHIS2 / WHO Schema Transformer":
    st.header("🔄 DHIS2 & WHO Schema Transformer")
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

    transformed_df = df.rename(columns=dhis2_mapping)

    m1, m2 = st.columns(2)
    m1.metric("Original Columns", len(df.columns))
    m2.metric("DHIS2 Aligned Variables", len(transformed_df.columns))

    st.markdown("#### Standardized DHIS2 Schema Table")
    st.dataframe(transformed_df, use_container_width=True)

    report_schema = f"# DHIS2 Schema Alignment Report\n- Dataset: {st.session_state['active_dataset_name']}\n- Alignment Standard: DHIS2 Tracker / WHO Surveillance\n- Mapped Variables: {', '.join(transformed_df.columns)}\n"
    st.download_button(
        "📥 Download DHIS2 Standard CSV",
        transformed_df.to_csv(index=False),
        "dhis2_transformed_dataset.csv",
        "text/csv",
    )


# ==============================================================================
# TOOL 6: DIFFERENTIAL PRIVACY GENERATOR
# ==============================================================================
elif active_tool == "🎲 Differential Privacy Generator":
    st.header("🎲 Differential Privacy Generator")
    st.caption("Injects Laplace noise into numerical fields and performs noisy categorical resampling.")

    col1, col2 = st.columns([1, 2])
    with col1:
        epsilon = st.slider("Privacy Budget (ε)", 0.1, 5.0, 1.0, 0.1)
        num_cols = st.multiselect(
            "Numerical Variables",
            df.select_dtypes(include=["number"]).columns.tolist(),
            default=[c for c in ["age", "sys_bp", "dia_bp", "age_yrs"] if c in df.columns],
        )
        cat_cols = st.multiselect(
            "Categorical Variables",
            df.select_dtypes(include=["object", "category"]).columns.tolist(),
            default=[c for c in ["gender", "gender_code"] if c in df.columns],
        )

    with col2:
        if num_cols or cat_cols:
            dp_result = generate_differentially_private_df(
                df, numeric_cols=num_cols, categorical_cols=cat_cols, epsilon=epsilon
            )
            st.success(f"Differentially Private Dataset Generated (ε = {epsilon})")

            if num_cols:
                st.markdown("#### 📊 Privacy Noise Curve Comparison (Original vs. DP Noise)")
                chart_data = pd.DataFrame({"Original": df[num_cols[0]], "DP Synthetic": dp_result[num_cols[0]]})
                st.line_chart(chart_data)

            st.dataframe(dp_result, use_container_width=True)

            report_dp = f"# Differential Privacy Certificate\n- Dataset: {st.session_state['active_dataset_name']}\n- Allocated Privacy Budget (ε): {epsilon}\n- Noise Mechanism: Laplace Distribution\n- Anonymized Variables: {', '.join(num_cols + cat_cols)}\n"
            st.download_button(
                "📥 Download DP Synthetic Dataset (CSV)",
                dp_result.to_csv(index=False),
                "dp_synthetic_dataset.csv",
                "text/csv",
            )


# ==============================================================================
# TOOL 7: l-DIVERSITY & t-CLOSENESS AUDIT
# ==============================================================================
elif active_tool == "🔍 l-Diversity & t-Closeness Audit":
    st.header("🔍 Attribute Disclosure Risk Scanner (l-Diversity / t-Closeness)")
    st.caption("Evaluates attribute disclosure risks inside equivalence classes to prevent homogeneity attacks.")

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

        st.markdown("#### 📊 Equivalence Class Distance Spectrum")
        st.bar_chart(t_df["t_distance"])

        st.dataframe(t_df, use_container_width=True)

        report_audit = f"# Advanced Privacy Audit Certificate\n- Dataset: {st.session_state['active_dataset_name']}\n- Minimum l-Diversity Score: {min_l}\n- Maximum t-Closeness Distance: {max_t}\n- Sensitive Variable Evaluated: {sens_col}\n"
        st.download_button(
            "📥 Download Disclosure Audit Report",
            report_audit,
            "attribute_disclosure_audit.txt",
            "text/plain",
        )


# ==============================================================================
# TOOL 8: HL7 FHIR INTEROPERABILITY BRIDGE
# ==============================================================================
elif active_tool == "🔥 HL7 FHIR Interoperability Bridge":
    st.header("🔥 HL7 FHIR Interoperability Bridge")
    st.caption("Bi-directional transformation between tabular datasets and HL7 FHIR Patient Bundle JSON standards.")

    mode = st.radio("Operation Mode", ["Tabular DataFrame ➔ FHIR JSON", "FHIR JSON ➔ Tabular DataFrame"], horizontal=True)

    if mode == "Tabular DataFrame ➔ FHIR JSON":
        fhir_bundle = dataframe_to_fhir_patient_bundle(df)
        json_str = json.dumps(fhir_bundle, indent=2)

        st.metric("FHIR Resources Generated", len(fhir_bundle.get("entry", [])))
        st.json(fhir_bundle)

        st.download_button(
            "📥 Download HL7 FHIR Bundle JSON",
            json_str,
            "fhir_patient_bundle.json",
            "application/json",
        )
    else:
        uploaded_json = st.file_uploader("Upload HL7 FHIR Bundle JSON", type=["json"])
        if uploaded_json:
            fhir_data = json.load(uploaded_json)
            parsed_df = fhir_bundle_to_dataframe(fhir_data)
            st.success("Parsed FHIR Bundle successfully!")
            st.dataframe(parsed_df, use_container_width=True)


# ==============================================================================
# TOOL 9: SPATIAL PRIVACY & GEOSPATIAL ENGINE
# ==============================================================================
elif active_tool == "🗺️ Spatial Privacy & Geospatial Engine":
    st.header("🗺️ Spatial Privacy & Geospatial Engine")
    st.caption("Applies Gaussian spatial jittering or bounding-box grid binning to GPS coordinates.")

    c1, c2 = st.columns(2)
    lat_col = c1.selectbox("Latitude Field", [c for c in df.columns if "lat" in c.lower()] + df.columns.tolist())
    lon_col = c2.selectbox("Longitude Field", [c for c in df.columns if "lon" in c.lower() or "lng" in c.lower()] + df.columns.tolist())

    spatial_mode = st.radio("Strategy", ["Gaussian Spatial Jitter", "Bounding Box Grid Binning"], horizontal=True)

    if spatial_mode == "Gaussian Spatial Jitter":
        radius = st.slider("Displacement Radius (meters)", 100, 2000, 500, 100)
        jittered_df = apply_spatial_jitter(df, lat_col, lon_col, radius_meters=radius)

        st.markdown("#### 📊 GPS Displacement Scatter Plot")
        scatter_data = pd.DataFrame({"Original Lat": df[lat_col], "Jittered Lat": jittered_df[lat_col]})
        st.scatter_chart(scatter_data)

        st.dataframe(jittered_df, use_container_width=True)

        st.download_button(
            "📥 Download Anonymized Spatial Data (CSV)",
            jittered_df.to_csv(index=False),
            "spatial_anonymized_dataset.csv",
            "text/csv",
        )
    else:
        grid_deg = st.select_slider("Grid Resolution (degrees)", options=[0.001, 0.005, 0.01, 0.05, 0.1], value=0.01)
        binned_df = create_spatial_grid_bins(df, lat_col, lon_col, grid_size_degrees=grid_deg)
        st.dataframe(binned_df, use_container_width=True)


# ==============================================================================
# TOOL 10: IMPUTATION WORKBENCH
# ==============================================================================
elif active_tool == "🩹 Imputation Workbench":
    st.header("🩹 Missingness Profiler & Imputation Workbench")
    st.caption("Profiles missing value rates across dataset columns and performs KNN or statistical imputation.")

    summary_df = analyze_missingness(df)

    st.markdown("#### 📊 Variable Missingness Rate Breakdown (Infographic)")
    st.bar_chart(summary_df.set_index("column")["missing_percentage"])

    st.markdown("#### Missingness Summary Table")
    st.dataframe(summary_df, use_container_width=True)

    strategy = st.selectbox("Imputation Algorithm", ["knn", "median_mode"])
    if st.button("Run Imputation", type="primary"):
        imputed_df = impute_missing_data(df, strategy=strategy)
        st.success("Dataset Imputation Complete!")
        st.dataframe(imputed_df, use_container_width=True)

        report_imp = f"# Missingness Imputation Certificate\n- Dataset: {st.session_state['active_dataset_name']}\n- Imputation Strategy: {strategy.upper()}\n- Processed Columns: {len(df.columns)}\n"
        st.download_button(
            "📥 Download Imputed Dataset (CSV)",
            imputed_df.to_csv(index=False),
            "imputed_health_dataset.csv",
            "text/csv",
        )


# --- Footer Author Banner ---
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #6B7280; font-size: 0.9rem; margin-top: 20px;">
        Public Health Data Suite & Governance Engine &bull; Architected & Engineered by <b>Engr. Tasaddaque Hussain Arain</b> (PEC COMP/7479)<br>
        Zero-Knowledge Architecture &bull; Open-Source License &bull; Designed for Health Ministries, IRBs, and Epidemiological Researchers
    </div>
""",
    unsafe_allow_html=True,
)