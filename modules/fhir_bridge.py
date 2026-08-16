import json
import pandas as pd


def dataframe_to_fhir_patient_bundle(df: pd.DataFrame) -> dict:
    """Converts a tabular DataFrame with patient demographic and vital sign fields

    into an HL7 FHIR JSON Bundle with Patient and Observation resources.
    """
    entries = []

    for _, row in df.iterrows():
        patient_id = str(
            row.get("patient_id", row.get("client_ref", "P-UNKNOWN"))
        )

        # 1. Build Patient Resource
        patient_resource = {
            "resourceType": "Patient",
            "id": patient_id,
            "name": [
                {
                    "use": "official",
                    "family": str(
                        row.get("last_name", row.get("full_name", ""))
                    ),
                    "given": [str(row.get("first_name", ""))],
                }
            ],
            "gender": str(
                row.get("gender", row.get("gender_code", "unknown"))
            ).lower(),
            "birthDate": str(row.get("date_of_birth", row.get("dob", ""))),
            "address": [
                {
                    "postalCode": str(
                        row.get("uk_postcode", row.get("zip_code", ""))
                    )
                }
            ],
        }

        # Add NHS Number identifier if present
        nhs_num = row.get("nhs_number", row.get("nhs_id", None))
        if pd.notna(nhs_num):
            clean_nhs = str(nhs_num).split(".")[0].strip()
            patient_resource["identifier"] = [
                {
                    "system": "https://fhir.nhs.uk/Id/nhs-number",
                    "value": clean_nhs,
                }
            ]

        entries.append(
            {
                "fullUrl": f"urn:uuid:{patient_id}",
                "resource": patient_resource,
            }
        )

        # 2. Build Blood Pressure FHIR Observation Resource (if vitals exist)
        sys_val = row.get("sys_bp", row.get("blood_pressure_sys", None))
        dia_val = row.get("dia_bp", row.get("blood_pressure_dia", None))

        if pd.notna(sys_val) and pd.notna(dia_val):
            try:
                sys_float = float(sys_val)
                dia_float = float(dia_val)
                bp_observation = {
                    "resourceType": "Observation",
                    "id": f"obs-bp-{patient_id}",
                    "status": "final",
                    "category": [
                        {
                            "coding": [
                                {
                                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                    "code": "vital-signs",
                                    "display": "Vital Signs",
                                }
                            ]
                        }
                    ],
                    "code": {
                        "coding": [
                            {
                                "system": "http://loinc.org",
                                "code": "85354-9",
                                "display": "Blood pressure panel with systolic and diastolic",
                            }
                        ]
                    },
                    "subject": {"reference": f"Patient/{patient_id}"},
                    "component": [
                        {
                            "code": {
                                "coding": [
                                    {
                                        "system": "http://loinc.org",
                                        "code": "8480-6",
                                        "display": "Systolic blood pressure",
                                    }
                                ]
                            },
                            "valueQuantity": {
                                "value": sys_float,
                                "unit": "mmHg",
                                "system": "http://unitsofmeasure.org",
                                "code": "mm[Hg]",
                            },
                        },
                        {
                            "code": {
                                "coding": [
                                    {
                                        "system": "http://loinc.org",
                                        "code": "8462-4",
                                        "display": "Diastolic blood pressure",
                                    }
                                ]
                            },
                            "valueQuantity": {
                                "value": dia_float,
                                "unit": "mmHg",
                                "system": "http://unitsofmeasure.org",
                                "code": "mm[Hg]",
                            },
                        },
                    ],
                }

                entries.append(
                    {
                        "fullUrl": f"urn:uuid:obs-bp-{patient_id}",
                        "resource": bp_observation,
                    }
                )
            except (ValueError, TypeError):
                pass

    return {"resourceType": "Bundle", "type": "collection", "entry": entries}


def fhir_bundle_to_dataframe(fhir_json: dict) -> pd.DataFrame:
    """Flattens an HL7 FHIR Bundle JSON into a clean DataFrame with Null/None safe checking."""
    patient_map = {}
    entries = fhir_json.get("entry", [])

    # First pass: Extract Patient demographics safely
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        resource = entry.get("resource", {})
        if resource.get("resourceType") == "Patient":
            p_id = resource.get("id")
            name_data = (
                resource.get("name", [{}])[0]
                if isinstance(resource.get("name"), list)
                and len(resource.get("name")) > 0
                else {}
            )
            address_data = (
                resource.get("address", [{}])[0]
                if isinstance(resource.get("address"), list)
                and len(resource.get("address")) > 0
                else {}
            )
            identifiers = resource.get("identifier", []) or []

            # AUD-06 Fix: Guard against system being None or null
            nhs_val = next(
                (
                    i.get("value")
                    for i in identifiers
                    if isinstance(i, dict)
                    and i.get("system") is not None
                    and "nhs-number" in str(i.get("system"))
                ),
                None,
            )

            patient_map[p_id] = {
                "patient_id": p_id,
                "first_name": (
                    name_data.get("given", [""])[0]
                    if isinstance(name_data.get("given"), list)
                    and len(name_data.get("given")) > 0
                    else ""
                ),
                "last_name": name_data.get("family", ""),
                "gender": resource.get("gender"),
                "date_of_birth": resource.get("birthDate"),
                "uk_postcode": address_data.get("postalCode"),
                "nhs_number": nhs_val,
                "sys_bp": None,
                "dia_bp": None,
            }

    # Second pass: Link Observation Vitals to Patients
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        resource = entry.get("resource", {})
        if resource.get("resourceType") == "Observation":
            ref = resource.get("subject", {}).get("reference", "") or ""
            p_id = ref.replace("Patient/", "") if "Patient/" in ref else ref

            if p_id in patient_map:
                for comp in resource.get("component", []) or []:
                    if not isinstance(comp, dict):
                        continue
                    coding = comp.get("code", {}).get("coding", [{}])
                    code = (
                        coding[0].get("code", "")
                        if isinstance(coding, list) and len(coding) > 0
                        else ""
                    )
                    val = comp.get("valueQuantity", {}).get("value")
                    if code == "8480-6":
                        patient_map[p_id]["sys_bp"] = val
                    elif code == "8462-4":
                        patient_map[p_id]["dia_bp"] = val

    return pd.DataFrame(list(patient_map.values()))