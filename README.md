# 🩺 Public Health Data Suite & Governance Workbench

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21968342.svg)](https://doi.org/10.5281/zenodo.21968342)
[![Digital Public Good](https://img.shields.io/badge/DPG-Candidate%20(Under%20Review)--GID0094074-blue.svg)](https://digitalpublicgoods.net/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Streamlit-1.30%2B-FF4B4B.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An open-source, zero-knowledge health data governance and anonymization engine engineered for public health agencies, academic researchers, IRBs, and international NGOs. The platform transforms raw, non-standard clinical data into de-identified, privacy-compliant, and interoperable digital health assets without persisting data to disk or cloud storage.

---

## 🏛️ Lead Architect & Engineering Credit

* **Lead System Architect:** Engr. Tasaddaque Hussain Arain [![ORCID](https://img.shields.io/badge/ORCID-0009--0002--6550--013X-green.svg)](https://orcid.org/0009-0002-6550-013X)
* **Professional Credentials:** Registered Professional Engineer (Pakistan Engineering Council - PEC Reg: `COMP/7479`)
* **Professional Profile:** [LinkedIn Profile](https://www.linkedin.com/in/tassaduqarain/)

> **Ethical Foundation:**
> *"Do you presume that you are a small entity, when within you the greater universe is folded?"*
> — **Imam Ali ibn Abi Talib (AS)**
> 
> *In health data governance, every individual data record reflects the sacred complexity of human life and well-being. This platform is built upon a strict duty of care, zero-knowledge privacy preservation, and public utility.*

---

## 🌟 Capabilities & Feature Matrix

| Category | Workbench Module | Technical Capabilities | Compliance & Interoperability |
| :--- | :--- | :--- | :--- |
| **Core Governance** | **Privacy Pre-Flight Scanner** | Audits $k$-anonymity across Quasi-Identifiers; automated age-binning generalization. | HIPAA / UK GDPR De-identification |
| **Core Governance** | **UK NHS Engine** | Modulus 11 NHS Number checksum validation; outward postcode masking (`M144PX` $\rightarrow$ `M14`). | NHS DSPT / OpenSAFELY Standard |
| **Core Governance** | **PPRL Record Linkage** | Multi-site deterministic record linkage using delimited HMAC SHA-256 tokens. | Cross-Trust De-duplication |
| **Core Governance** | **Quality Firewall & Triage** | Automated triage of physiological BP anomalies, invalid age ranges, and type mismatches. | WHO Clinical Data Quality Standards |
| **Core Governance** | **Schema Transformer** | One-click column alignment to DHIS2 Tracker and WHO disease surveillance schemas. | DHIS2 / WHO Surveillance |
| **Advanced Research** | **Differential Privacy** | Synthetic data generation via configurable Laplace noise injection ($\epsilon$ budget). | Mathematical Privacy Guarantees |
| **Advanced Research** | **Privacy Audit ($l, t$)** | Equivalence class scanning for $l$-diversity and $t$-closeness (Total Variation Distance). | Homogeneity & Disclosure Shield |
| **Advanced Research** | **HL7 FHIR Interoperability Bridge** | Bi-directional JSON Bundle $\leftrightarrow$ DataFrame parser (`Patient` & LOINC `85354-9` Vitals). | HL7 FHIR Release 4 (R4) |
| **Advanced Research** | **Spatial Privacy Engine** | Gaussian GPS displacement jittering and bounding-box spatial grid cell binning. | Geospatial De-identification |
| **Advanced Research** | **Imputation Workbench** | Missingness rate profiling with K-Nearest Neighbors (KNN) and median/mode imputation. | Epidemiological Data Prep |

---

## 🔒 Security & Zero-Knowledge Architecture

1. **Volatile RAM Execution:** All uploaded datasets are processed exclusively in volatile session memory. Data is never persisted to disk, databases, or cloud storage.
2. **Session Isolation:** Terminating or refreshing the browser tab instantly purges all data structures from memory.
3. **Local Deployment Ready:** Designed to run in air-gapped clinical environments without external network dependencies.

---

## 🚀 Installation & Local Execution

### Option A: Non-Technical One-Click Launcher (Windows)
1. Download or unzip the repository.
2. Double-click **`Launch_Suite.bat`**.
3. The script automatically initializes the virtual environment, installs requirements, and launches the browser interface.

### Option B: Terminal Command Line
```bash
git clone [https://github.com/araintasaddaque-ai/Public_Health_Data_Suite.git](https://github.com/araintasaddaque-ai/Public_Health_Data_Suite.git)
cd Public_Health_Data_Suite

python -m venv venv
source venv/bin/activate  # Windows PowerShell: venv\Scripts\activate

pip install -r requirements.txt
streamlit run main.py