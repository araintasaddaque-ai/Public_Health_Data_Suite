# 🏥 Public Health Data Suite & UK Compliance Engine
[![Public Health Data Suite CI](https://github.com/tasaddaque/Public_Health_Data_Suite/actions/workflows/pytest.yml/badge.svg?branch=main)](https://github.com/tasaddaque/Public_Health_Data_Suite/actions/workflows/pytest.yml)
# Public Health Data Suite & UK Compliance Engine

[![Public Health Data Suite CI](https://github.com/tasaddaque/Public_Health_Data_Suite/actions/workflows/pytest.yml/badge.svg?branch=main)](https://github.com/tasaddaque/Public_Health_Data_Suite/actions/workflows/pytest.yml)
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://publichealthdatasuite-hqgog7csa3stt8tcujxd8k.streamlit.app/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/tasaddaque/Public_Health_Data_Suite/blob/main/LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

[![Live App](https://img.shields.io/badge/Streamlit_Cloud-Live_Demo-00D46A?style=for-the-badge&logo=streamlit)](https://publichealthdatasuite-hqgog7csa3stt8tcujxd8k.streamlit.app/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](LICENSE)
[![Design](https://img.shields.io/badge/UI-Google_Material_3-0B57D0?style=for-the-badge)](https://m3.material.io/)

An open-source, privacy-preserving, enterprise-grade data management suite designed for public health researchers, epidemiologists, and clinical data managers. This platform resolves critical data bottlenecks—from offline probabilistic record de-duplication and automated data quality triage to international schema transformation and UK NHS governance compliance.

---

## 🌐 Live Application
Access the production-ready, zero-install interactive deployment here:  
👉 **[https://publichealthdatasuite-hqgog7csa3stt8tcujxd8k.streamlit.app/](https://publichealthdatasuite-hqgog7csa3stt8tcujxd8k.streamlit.app/)**

---

## 👤 Architect & Developer

**Engr. Tasaddaque Hussain Arain**  
*Enterprise Solution Architect | PEC Registered Engineer*  
* Specialized in Large-Scale Digital Public Goods, Health IT Infrastructure, and Privacy-Preserving Systems.  
* 🔗 **LinkedIn:** [linkedin.com/in/tasaddaque](https://www.linkedin.com/in/tassaduqarain)

---

## 🚀 Key Modules & Functional Overview

| Module | Core Capability | Governance & Technical Highlights |
| :--- | :--- | :--- |
| **1. Privacy-Preserving Record Linkage (PPRL)** | Probabilistic patient record de-duplication across registries | Salted SHA-256 HMAC cryptographic hashing, Jaro-Winkler string distance scoring, memory-only linkage. |
| **2. Automated Data Quality Engine** | Automated physiological & logical data firewall | Real-time triage, systolic/diastolic anomaly detection, future date checks, automated Health Scorecard generation. |
| **3. Reusable Schema Transformer** | Dynamic field register alignment | Drag-and-drop mapping to **DHIS2** and **WHO** standards with reusable `.json` rule exports. |
| **4. Privacy Pre-Flight Scanner** | $k$-Anonymity re-identification risk audit | Computes $k$-scores across quasi-identifiers, offers 1-click age-binning generalization and ID suppression. |
| **5. UK NHS Compliance Engine** | UK Health Research Governance converter | Modulus 11 NHS Number validation, UK GDPR outward postcode masking (`M14 4PX` $\rightarrow$ `M14`), OpenSAFELY/CPRD readiness. |

---
@software{Arain_Public_Health_Data_Suite_2026,
  author       = {Arain, Engr. Tasaddaque Hussain},
  title        = {Public Health Data Suite \& UK Compliance Engine},
  month        = aug,
  year         = {2026},
  publisher    = {GitHub},
  version      = {v1.0.0},
  url          = {https://publichealthdatasuite-hqgog7csa3stt8tcujxd8k.streamlit.app/},
  howpublished = {\url{https://github.com/your-username/Public_Health_Data_Suite}}
}