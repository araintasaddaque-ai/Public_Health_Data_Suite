from datetime import datetime
import hashlib
import json
import re
import pandas as pd
import recordlinkage
from recordlinkage.index import Block
import streamlit as st

# Page Setup
st.set_page_config(
    page_title="Public Health Data Suite | Enterprise Governance",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# GOOGLE MATERIAL DESIGN 3 (MATERIAL YOU) CSS
# ==========================================
st.markdown("""
<style>
    /* Import Google Sans & Roboto Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&family=Roboto:wght@300;400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'Google Sans', 'Roboto', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #1f1f1f;
    }

    /* Main Container Padding & Material Background */
    .stApp {
        background-color: #f8f9fa;
    }

    /* Material Design 3 Cards */
    div[data-testid="stForm"], div[data-testid="stContainer"] {
        background-color: #ffffff;
        border-radius: 16px !important;
        border: 1px solid #e0e0e0 !important;
        padding: 20px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05), 0 1px 2px rgba(0,0,0,0.1);
    }

    /* Primary Google Blue Buttons */
    .stButton > button {
        background-color: #0b57d0 !important;
        color: #ffffff !important;
        border-radius: 24px !important;
        padding: 10px 24px !important;
        font-weight: 500 !important;
        font-size: 14px !important;
        border: none !important;
        box-shadow: 0 1px 3px rgba(11,87,208,0.3) !important;
        transition: all 0.2s ease-in-out !important;
    }
    .stButton > button:hover {
        background-color: #0842a0 !important;
        box-shadow: 0 4px 8px rgba(11,87,208,0.4) !important;
        transform: translateY(-1px);
    }

    /* Sidebar Material Styling */
    section[data-testid="stSidebar"] {
        background-color: #f0f4f9 !important;
        border-right: 1px solid #e1e3e1 !important;
    }

    /* Metric Card Styling */
    div[data-testid="stMetric"] {
        background-color: #f0f4f9;
        border-radius: 12px;
        padding: 16px;
        border: 1px solid #e1e3e1;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 13px !important;
        color: #444746 !important;
        font-weight: 500 !important;
    }
    div[data-testid="stMetricValue"] {
        font-size: 24px !important;
        color: #0b57d0 !important;
        font-weight: 700 !important;
    }

    /* Input & Slider Styling */
    .stTextInput input, .stSelectbox select {
        border-radius: 8px !important;
        border: 1px solid #747775 !important;
    }

    /* Custom Header Pills */
    .material-pill {
        display: inline-block;
        background-color: #c2e7ff;
        color: #001d35;
        padding: 4px 12px;
        border-radius: 8px;
        font-size: 12px;
        font-weight: 500;
        margin-bottom: 12px;
    }
    
    .author-card {
        background: linear-gradient(135deg, #0b57d0 0%, #0842a0 100%);
        color: white;
        border-radius: 16px;
        padding: 16px;
        margin-top: 10px;
    }
    .author-card a {
        color: #c2e7ff !important;
        text-decoration: underline;
    }
</style>
""", unsafe_allow_html=True)


# ==========================================
# HELPER FUNCTIONS & COMPLIANCE ENGINES
# ==========================================
def validate_nhs_number(nhs_str: str) -> bool:
    clean_nhs = re.sub(r'\D', '', str(nhs_str or ''))
    if len(clean_nhs) != 10:
        return False
    digits = [int(d) for d in clean_nhs]
    weights = [10, 9, 8, 7, 6, 5, 4, 3, 2]
    total = sum(d * w for d, w in zip(digits[:9], weights))
    remainder = total % 11
    check_digit = 11 - remainder
    if check_digit == 11:
        check_digit = 0
    return check_digit == digits[9]

def anonymize_uk_postcode(postcode_str: str) -> str:
    if pd.isna(postcode_str) or not str(postcode_str).strip():
        return "UNKNOWN"
    clean_pc = str(postcode_str).strip().upper()
    parts = clean_pc.split()
    if len(parts) > 1:
        return parts[0]
    elif len(clean_pc) > 3:
        return clean_pc[:-3].strip()
    return clean_pc


# ==========================================
# SIDEBAR NAVIGATION & CREDIT CARD
# ==========================================
with st.sidebar:
    st.markdown('<div class="material-pill">Google Material 3 v2.5</div>', unsafe_allow_html=True)
    st.title("🏥 Health Data Suite")
    st.caption("Open-Source Digital Public Good for Epidemiologists & Public Health Teams")

    menu_choice = st.radio(
        "Navigation Module:",
        [
            "1. Record Linkage (PPRL)",
            "2. Data Quality Engine",
            "3. Schema Transformer",
            "4. Privacy Scanner (k-Anonymity)",
            "5. UK NHS Compliance & Research Converter"
        ],
        help="Select the health data processing tool you wish to run."
    )

    st.divider()

    # Material Credit Card
    st.markdown("""
    <div class="author-card">
        <div style="font-size:11px; text-transform:uppercase; letter-spacing:0.5px; opacity:0.8;">Platform Architect</div>
        <div style="font-size:15px; font-weight:700; margin-top:2px;">Engr. Tasaddaque Hussain Arain</div>
        <div style="font-size:12px; opacity:0.9; margin-top:2px;">Enterprise Solution Architect<br>PEC Registered Engineer</div>
        <div style="margin-top:10px;">
            <a href="https://www.linkedin.com/in/tasaddaque" target="_blank" style="font-size:12px; font-weight:500;">
                Connect on LinkedIn ➔
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ==========================================
# MODULE 1: PRIVACY-PRESERVING RECORD LINKAGE
# ==========================================
def render_tool1():
    st.markdown('<div class="material-pill">Module 01 • Cryptographic Linking</div>', unsafe_allow_html=True)
    st.title("Privacy-Preserving Record Linkage (PPRL)")
    st.caption("De-duplicate patient records across fragmented registries using salted SHA-256 hashes and probabilistic matching without exposing raw PII.")

    with st.container(border=True):
        st.subheader("1. Data Source Selection")
        c_up1, c_up2 = st.columns(2)
        with c_up1:
            file_a = st.file_uploader("Upload Registry A (CSV)", type=["csv"], key="t1_file_a", help="Upload your first health registry CSV file.")
        with c_up2:
            file_b = st.file_uploader("Upload Registry B (CSV)", type=["csv"], key="t1_file_b", help="Upload your second health registry or vaccination log CSV file.")

        if file_a is not None and file_b is not None:
            raw_df_a = pd.read_csv(file_a)
            raw_df_b = pd.read_csv(file_b)
            st.success("Custom datasets loaded successfully.")
        else:
            st.info("💡 Using built-in demo datasets (Upload custom CSVs above anytime).")
            raw_df_a = pd.DataFrame({
                'id': [101, 102, 103, 104],
                'first_name': ['Tasaddaque', 'Muhammad', 'Fatima', 'Ali'],
                'last_name': ['Arain', 'Khan', 'Memon', 'Raza'],
                'dob': ['1986-08-14', '1990-03-12', '1995-11-05', '1980-01-01'],
                'gender': ['M', 'M', 'F', 'M']
            })
            raw_df_b = pd.DataFrame({
                'id': [501, 502, 503, 504],
                'first_name': ['Tasaduk', 'Mohammad', 'Zainab', 'Ali'],
                'last_name': ['Hussain', 'Khan', 'Baloch', 'Raza'],
                'dob': ['1986-08-14', '1990-03-12', '2001-01-20', '1980-01-01'],
                'gender': ['M', 'M', 'F', 'M']
            })

    with st.container(border=True):
        st.subheader("2. Cryptographic & Matching Parameters")
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            salt_key = st.text_input("HMAC Secret Salt Phrase", value="SindhHealth2026", type="password", key="t1_salt", help="Secret salt phrase used to generate irreversible SHA-256 hashes.")
        with col_s2:
            match_threshold = st.slider("Probabilistic Confidence Score Threshold", 1.0, 3.0, 2.0, 0.5, key="t1_thresh", help="Minimum required probabilistic score to classify two patient records as duplicates.")

    def hash_pii(val: str, salt: str) -> str:
        if pd.isna(val) or not str(val).strip():
            return ""
        clean_val = str(val).strip().lower()
        return hashlib.sha256(f"{clean_val}:{salt}".encode('utf-8')).hexdigest()[:16]

    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            st.write("**Registry A Preview**")
            st.dataframe(raw_df_a, width="stretch")
    with c2:
        with st.container(border=True):
            st.write("**Registry B Preview**")
            st.dataframe(raw_df_b, width="stretch")

    if st.button("Run Privacy-Preserving Linkage Engine", type="primary", key="t1_run", help="Execute SHA-256 hashing and probabilistic string matching across datasets."):
        id_col_a = raw_df_a.columns[0]
        id_col_b = raw_df_b.columns[0]
        
        df_a = raw_df_a.copy().set_index(id_col_a)
        df_b = raw_df_b.copy().set_index(id_col_b)

        fn_a = 'first_name' if 'first_name' in df_a.columns else df_a.columns[0]
        fn_b = 'first_name' if 'first_name' in df_b.columns else df_b.columns[0]
        ln_a = 'last_name' if 'last_name' in df_a.columns else df_a.columns[min(1, len(df_a.columns)-1)]
        ln_b = 'last_name' if 'last_name' in df_b.columns else df_b.columns[min(1, len(df_b.columns)-1)]

        df_a['hash_fn'] = df_a[fn_a].apply(lambda x: hash_pii(x, salt_key))
        df_b['hash_fn'] = df_b[fn_b].apply(lambda x: hash_pii(x, salt_key))

        if 'gender' in df_a.columns and 'gender' in df_b.columns:
            indexer = Block('gender')
            candidate_links = indexer.index(df_a, df_b)
        else:
            indexer = recordlinkage.Index()
            indexer.full()
            candidate_links = indexer.index(df_a, df_b)

        compare = recordlinkage.Compare()
        compare.string(fn_a, fn_b, method='jarowinkler', threshold=0.7, label='fn_score')
        compare.string(ln_a, ln_b, method='jarowinkler', threshold=0.7, label='ln_score')

        features = compare.compute(candidate_links, df_a, df_b)
        matches = features[features.sum(axis=1) >= match_threshold]

        with st.container(border=True):
            st.subheader("Match Results & Verification")
            if not matches.empty:
                st.success(f"Successfully identified {len(matches)} duplicate record pair(s).")
                st.dataframe(matches, width="stretch")
                
                for id_a, id_b in matches.index:
                    rec_a = raw_df_a[raw_df_a[id_col_a] == id_a].iloc[0].to_dict()
                    rec_b = raw_df_b[raw_df_b[id_col_b] == id_b].iloc[0].to_dict()
                    st.info(f"Duplicate Pair Detected: Registry A ({id_a}) <===> Registry B ({id_b})")
                    st.table(pd.DataFrame([rec_a, rec_b], index=[f"Reg A ({id_a})", f"Reg B ({id_b})"]))
            else:
                st.warning("No duplicate records found meeting the current match threshold.")


# ==========================================
# MODULE 2: AUTOMATED DATA QUALITY ENGINE
# ==========================================
def render_tool2():
    st.markdown('<div class="material-pill">Module 02 • Data Firewall</div>', unsafe_allow_html=True)
    st.title("Automated Data Quality & Expectation Engine")
    st.caption("Automated triage firewall for health datasets. Detects physiological errors, out-of-bounds vitals, and missing field entries.")

    with st.container(border=True):
        st.subheader("1. Upload Facility Dataset")
        uploaded_file = st.file_uploader("Upload Raw Facility Register (CSV)", type=["csv"], key="t2_upload", help="Upload a CSV dataset containing patient clinical entries and vitals.")

        if uploaded_file is not None:
            raw_df = pd.read_csv(uploaded_file)
            st.success("Custom dataset loaded.")
        else:
            st.info("💡 Using built-in demo facility dataset.")
            raw_df = pd.DataFrame({
                'record_id': [1001, 1002, 1003, 1004, 1005, 1006, 1007],
                'patient_name': ['Tasaddaque Hussain', 'Fatima Memon', 'Muhammad Ali', 'Zainab Bibi', 'Rashid Khan', 'Khadija Soomro', 'Unassigned'],
                'age': [39, 145, 28, -5, 52, 44, 31],
                'sys_bp': [120, 135, 110, 80, 240, 90, 118],
                'dia_bp': [80, 85, 70, 110, 115, 60, 78],
                'visit_date': ['2026-08-10', '2026-08-12', '2028-11-01', '2026-08-14', '2026-08-15', None, '2026-08-15'],
                'district': ['Karachi', 'Hyderabad', 'Sukkur', 'Larkana', 'Mirpurkhas', 'Badin', None]
            })

    with st.container(border=True):
        st.subheader("2. Validation Rule Parameters")
        c1, c2, c3 = st.columns(3)
        with c1:
            min_age, max_age = st.slider("Valid Age Range (Years)", 0, 120, (0, 100), key="t2_age", help="Set the acceptable range for age entries.")
        with c2:
            min_sys, max_sys = st.slider("Valid Systolic BP Range", 50, 250, (70, 200), key="t2_sys", help="Physiological range for systolic blood pressure.")
        with c3:
            min_dia, max_dia = st.slider("Valid Diastolic BP Range", 30, 150, (40, 120), key="t2_dia", help="Physiological range for diastolic blood pressure.")

    flags = []
    for idx, row in raw_df.iterrows():
        row_flags = []
        if 'age' in row and (pd.isna(row['age']) or row['age'] < min_age or row['age'] > max_age):
            row_flags.append(f"Invalid Age ({row.get('age')})")
        if 'sys_bp' in row and (pd.isna(row['sys_bp']) or row['sys_bp'] < min_sys or row['sys_bp'] > max_sys):
            row_flags.append(f"Abnormal Sys BP ({row.get('sys_bp')})")
        if 'dia_bp' in row and (pd.isna(row['dia_bp']) or row['dia_bp'] < min_dia or row['dia_bp'] > max_dia):
            row_flags.append(f"Abnormal Dia BP ({row.get('dia_bp')})")
        if 'sys_bp' in row and 'dia_bp' in row and pd.notna(row['sys_bp']) and pd.notna(row['dia_bp']) and row['sys_bp'] <= row['dia_bp']:
            row_flags.append("Physiological Anomaly (Sys <= Dia)")
        if 'visit_date' in row and (pd.isna(row['visit_date']) or str(row['visit_date']).strip() == ""):
            row_flags.append("Missing Visit Date")
        if 'visit_date' in row and pd.notna(row['visit_date']):
            try:
                if datetime.strptime(str(row['visit_date']), "%Y-%m-%d") > datetime.now():
                    row_flags.append(f"Future Date ({row['visit_date']})")
            except ValueError:
                pass
        flags.append("; ".join(row_flags) if row_flags else "CLEAN")

    audited_df = raw_df.copy()
    audited_df['Quality_Status'] = flags
    clean_records = audited_df[audited_df['Quality_Status'] == "CLEAN"]
    flagged_records = audited_df[audited_df['Quality_Status'] != "CLEAN"]

    st.subheader("Executive Health Scorecard")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Rows Evaluated", len(audited_df), help="Number of patient rows scanned.")
    m2.metric("Clean Records", len(clean_records), help="Rows passing all physiological rules.")
    m3.metric("Flagged Violations", len(flagged_records), help="Rows containing errors or invalid dates.")
    m4.metric("Data Health Index", f"{round((len(clean_records)/len(audited_df))*100, 1)}%", help="Percentage of usable, clean data.")

    t1, t2 = st.columns(2)
    with t1:
        with st.container(border=True):
            st.subheader("Flagged Violations Log")
            st.dataframe(flagged_records, width="stretch")
    with t2:
        with st.container(border=True):
            st.subheader("Cleaned Dataset (Export Ready)")
            st.dataframe(clean_records, width="stretch")
            st.download_button(
                label="Download Sanitized Dataset (CSV)",
                data=clean_records.to_csv(index=False),
                file_name="sanitized_health_data.csv",
                mime="text/csv"
            )


# ==========================================
# MODULE 3: REUSABLE SCHEMA TRANSFORMER
# ==========================================
def render_tool3():
    st.markdown('<div class="material-pill">Module 03 • Schema Standardization</div>', unsafe_allow_html=True)
    st.title("Reusable Schema & Template Transformer")
    st.caption("Map unstandardized field registers (KoboToolbox, ODK, Excel) to standardized international schemas (DHIS2, WHO).")

    with st.container(border=True):
        st.subheader("1. Upload Source Register")
        uploaded_file = st.file_uploader("Upload Raw Field CSV", type=["csv"], key="t3_upload", help="Upload a raw field register CSV file.")

        if uploaded_file is not None:
            raw_df = pd.read_csv(uploaded_file)
            st.success("Loaded uploaded dataset.")
        else:
            st.info("💡 Using built-in demo dataset.")
            raw_df = pd.DataFrame({
                'p_id': [201, 202, 203],
                'p_name': ['Tasaddaque Hussain', 'Fatima Memon', 'Muhammad Ali'],
                'age_yr': [39, 28, 52],
                'gender_raw': ['Male', 'Female', 'Male'],
                'loc': ['Karachi', 'Hyderabad', 'Sukkur'],
                'v_date': ['2026-08-10', '2026-08-12', '2026-08-15']
            })

    TARGET_SCHEMAS = {
        "DHIS2 Individual Immunization Template": ["Patient_Full_Name", "Age_Years", "Gender_Code", "Facility_District", "Report_Date"],
        "WHO Disease Surveillance Schema": ["Case_Identifier", "Subject_Name", "Age", "Sex", "Reporting_Location"]
    }

    selected_schema_name = st.selectbox("Select Target International Schema", list(TARGET_SCHEMAS.keys()), key="t3_schema", help="Select the target schema format required by your funding body or national system.")
    target_fields = TARGET_SCHEMAS[selected_schema_name]

    with st.container(border=True):
        st.subheader("2. Interactive Visual Column Mapping")
        source_cols = ["-- Unmapped --"] + list(raw_df.columns)
        mapping = {}

        col_layout = st.columns(min(len(target_fields), 4))
        for i, target_field in enumerate(target_fields):
            with col_layout[i % len(col_layout)]:
                default_index = 0
                for idx, src_col in enumerate(source_cols):
                    if target_field.lower().replace("_", "") in src_col.lower().replace("_", ""):
                        default_index = idx
                        break
                mapping[target_field] = st.selectbox(f"`{target_field}`", options=source_cols, index=default_index, key=f"t3_m_{target_field}")

    if st.button("Transform & Standardize Dataset", type="primary", key="t3_trans"):
        transformed_data = {t_field: raw_df[s_col] if s_col != "-- Unmapped --" else None for t_field, s_col in mapping.items()}
        transformed_df = pd.DataFrame(transformed_data)
        
        with st.container(border=True):
            st.subheader("Standardized Output Preview")
            st.dataframe(transformed_df, width="stretch")
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                st.download_button(
                    label="Download Standardized CSV",
                    data=transformed_df.to_csv(index=False),
                    file_name="standardized_export.csv",
                    mime="text/csv"
                )
            with col_d2:
                st.download_button(
                    label="Export Mapping Config (JSON)",
                    data=json.dumps(mapping, indent=2),
                    file_name="schema_mapping_rules.json",
                    mime="application/json",
                    help="Save column alignment rules to automatically transform future datasets."
                )


# ==========================================
# MODULE 4: PRIVACY SCANNER (K-ANONYMITY)
# ==========================================
def render_tool4():
    st.markdown('<div class="material-pill">Module 04 • Risk Audit & Mitigation</div>', unsafe_allow_html=True)
    st.title("Automated k-Anonymity & Privacy Pre-Flight Scanner")
    st.caption("Calculates k-anonymity scores, flags re-identification risks, and applies automated age-binning generalization before public dataset release.")

    with st.container(border=True):
        st.subheader("1. Upload Research Dataset")
        uploaded_file = st.file_uploader("Upload Dataset (CSV)", type=["csv"], key="t4_upload", help="Upload a dataset to audit before sharing with research partners or publishing.")

        if uploaded_file is not None:
            raw_df = pd.read_csv(uploaded_file)
            st.success("Loaded uploaded dataset.")
        else:
            st.info("💡 Using built-in demo research dataset.")
            raw_df = pd.DataFrame({
                'patient_id': [3001, 3002, 3003, 3004, 3005, 3006, 3007, 3008],
                'age': [39, 38, 25, 25, 72, 39, 25, 50],
                'gender': ['M', 'M', 'F', 'F', 'F', 'M', 'F', 'M'],
                'district': ['Karachi', 'Karachi', 'Hyderabad', 'Hyderabad', 'Badin', 'Karachi', 'Hyderabad', 'Sukkur'],
                'diagnosis': ['Asthma', 'Diabetes', 'Malaria', 'Malaria', 'Hypertension', 'Asthma', 'Dengue', 'Diabetes']
            })

    target_k = st.slider("Target k-Anonymity Threshold", 2, 5, 3, key="t4_k", help="Minimum required group size (equivalence class) for identical quasi-identifiers.")

    avail_qis = [c for c in raw_df.columns if c.lower() not in ['patient_id', 'id', 'name']]
    selected_qis = st.multiselect("Selected Quasi-Identifiers (QIs):", options=avail_qis, default=avail_qis[:min(3, len(avail_qis))], key="t4_qis", help="Attributes that could re-identify patients when linked with external data.")

    if selected_qis:
        group_sizes = raw_df.groupby(selected_qis, observed=False).size().reset_index(name='k_count')
        audited_df = pd.merge(raw_df, group_sizes, on=selected_qis, how='left')
        current_k = int(group_sizes['k_count'].min()) if not group_sizes.empty else 0
        at_risk = audited_df[audited_df['k_count'] < target_k]

        st.subheader("Privacy Risk Metrics")
        c1, c2, c3 = st.columns(3)
        c1.metric("Current k-Score", f"k = {current_k}", help="Smallest group size in current dataset.")
        c2.metric("Target Threshold", f"k >= {target_k}", help="Desired compliance target.")
        c3.metric("At-Risk Patient Rows", len(at_risk), help="Rows failing the k-anonymity threshold.")

        if st.button("Apply Age Binning Generalization & Suppress Direct IDs", type="primary", key="t4_mitigate"):
            mitigated_df = raw_df.drop(columns=[c for c in ['patient_id', 'id'] if c in raw_df.columns])
            if 'age' in mitigated_df.columns:
                bins = [0, 18, 30, 40, 50, 60, 70, 100]
                labels = ['0-17', '18-29', '30-39', '40-49', '50-59', '60-69', '70+']
                mitigated_df['age'] = pd.cut(mitigated_df['age'], bins=bins, labels=labels, right=False)

            remap_qis = [c for c in selected_qis if c in mitigated_df.columns]
            post_groups = mitigated_df.groupby(remap_qis, observed=False).size().reset_index(name='k_count')
            post_df = pd.merge(mitigated_df, post_groups, on=remap_qis, how='left')
            post_k = int(post_groups['k_count'].min())

            with st.container(border=True):
                st.success(f"Anonymization Applied! New Score: k = {post_k}")
                st.dataframe(post_df, width="stretch")
                st.download_button(
                    label="Download Anonymized Dataset (CSV)",
                    data=post_df.to_csv(index=False),
                    file_name=f"anonymized_data_k{post_k}.csv",
                    mime="text/csv"
                )


# ==========================================
# MODULE 5: UK NHS COMPLIANCE & RESEARCH CONVERTER
# ==========================================
def render_tool5():
    st.markdown('<div class="material-pill">Module 05 • UK NHS Governance</div>', unsafe_allow_html=True)
    st.title("UK NHS Compliance & Research Data Converter")
    st.caption("Transforms datasets to meet UK NHS Data Security & Protection Toolkit (DSPT), UK GDPR, and CPRD/OpenSAFELY academic research standards.")

    with st.container(border=True):
        st.subheader("1. Upload UK Research Dataset")
        uploaded_file = st.file_uploader("Upload Dataset for UK NHS Conversion (CSV)", type=["csv"], key="t5_upload", help="Upload a raw research dataset containing UK NHS patient fields.")

        if uploaded_file is not None:
            raw_df = pd.read_csv(uploaded_file)
            st.success("Loaded uploaded CSV dataset.")
        else:
            st.info("💡 Using built-in UK sample dataset.")
            raw_df = pd.DataFrame({
                'nhs_number': ['9434765919', '9434765920', '1234567890', '9876543210'],
                'patient_name': ['Dr. Jane Smith', 'Arthur Pendelton', 'Clara Oswald', 'John Watson'],
                'uk_postcode': ['M14 4PX', 'M1 7ED', 'LS1 3EX', 'B1 1AA'],
                'ethnicity_code': ['A', 'C', 'H', 'M'],
                'age': [34, 62, 29, 45],
                'primary_diagnosis_icd10': ['J45.9', 'E11.9', 'I10', 'J45.0']
            })

    with st.container(border=True):
        st.subheader("2. Governance Actions")
        col_opt1, col_opt2, col_opt3 = st.columns(3)
        with col_opt1:
            do_nhs_val = st.checkbox("Validate NHS Numbers (Modulus 11)", value=True, help="Validate 10-digit NHS numbers using the official Modulus 11 algorithm.")
        with col_opt2:
            do_postcode_mask = st.checkbox("Mask Postcodes to Outward Code", value=True, help="Truncate UK postcodes (e.g. M14 4PX -> M14) for UK GDPR geographic privacy.")
        with col_opt3:
            do_pseudonymize = st.checkbox("Generate NHS Salted Pseudo-IDs", value=True, help="Replace direct patient names with irreversible SHA-256 research IDs.")

        salt_phrase = st.text_input("UK Research Salt Phrase", value="GreaterManchesterNHS2026", type="password", help="Salt phrase for generating research pseudonyms.")

    if st.button("Execute UK Compliance Transformation", type="primary", key="t5_run", help="Apply UK NHS information governance transformations."):
        transformed_df = raw_df.copy()

        if do_nhs_val and 'nhs_number' in transformed_df.columns:
            transformed_df['nhs_validity'] = transformed_df['nhs_number'].apply(
                lambda x: "VALID" if validate_nhs_number(x) else "INVALID_NHS_NO"
            )

        if do_postcode_mask and 'uk_postcode' in transformed_df.columns:
            transformed_df['uk_postcode_district'] = transformed_df['uk_postcode'].apply(anonymize_uk_postcode)
            transformed_df = transformed_df.drop(columns=['uk_postcode'])

        if do_pseudonymize:
            id_source = 'nhs_number' if 'nhs_number' in transformed_df.columns else transformed_df.columns[0]
            transformed_df['pseudo_research_id'] = transformed_df[id_source].apply(
                lambda val: "NHS_PID_" + hashlib.sha256(f"{val}:{salt_phrase}".encode('utf-8')).hexdigest()[:12].upper()
            )
            if 'patient_name' in transformed_df.columns:
                transformed_df = transformed_df.drop(columns=['patient_name'])

        with st.container(border=True):
            st.subheader("UK NHS Compliant Dataset Output")
            st.dataframe(transformed_df, width="stretch")

            col_d1, col_d2 = st.columns(2)
            with col_d1:
                st.download_button(
                    label="Download NHS Compliant Research CSV",
                    data=transformed_df.to_csv(index=False),
                    file_name="nhs_dspt_compliant_research_data.csv",
                    mime="text/csv"
                )
            with col_d2:
                compliance_manifest = {
                    "governance_standard": "UK NHS DSPT & UK GDPR",
                    "anonymization_level": "Pseudonymised with Salted Outward-Code Postcode",
                    "nhs_modulus11_checked": do_nhs_val,
                    "timestamp": datetime.now().isoformat(),
                    "author": "Engr. Tasaddaque Hussain Arain"
                }
                st.download_button(
                    label="Download Governance Manifest (JSON)",
                    data=json.dumps(compliance_manifest, indent=2),
                    file_name="nhs_compliance_manifest.json",
                    mime="application/json",
                    help="Official compliance log for university ethics boards and IRBs."
                )


# ROUTER
if "1. Record Linkage" in menu_choice:
    render_tool1()
elif "2. Data Quality" in menu_choice:
    render_tool2()
elif "3. Schema Transformer" in menu_choice:
    render_tool3()
elif "4. Privacy Scanner" in menu_choice:
    render_tool4()
elif "5. UK NHS Compliance" in menu_choice:
    render_tool5()