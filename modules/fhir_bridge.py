import json
import pandas as pd


def dataframe_to_fhir_patient_bundle(df: pd.DataFrame) -> dict:
    """Converts a tabular DataFrame with patient fields into an HL7 FHIR JSON Bundle."""
    entries = []

    for _, row in df.iterrows():
        patient_resource = {
            "resourceType": "Patient",
            "id": str(row.get("patient_id", row.get("client_ref", "P-UNKNOWN"))),
            "name": [
                {
                    "use": "official",
                    "family": str(row.get("last_name", "")),
                    "given": [str(row.get("first_name", ""))],
                }
            ],
            "gender": str(row.get("gender", "unknown")).lower(),
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
            patient_resource["identifier"] = [
                {
                    "system": "https://fhir.nhs.uk/Id/nhs-number",
                    "value": str(nhs_num),
                }
            ]

        entries.append(
            {
                "fullUrl": f"urn:uuid:{patient_resource['id']}",
                "resource": patient_resource,
            }
        )

    return {"resourceType": "Bundle", "type": "collection", "entry": entries}


def fhir_bundle_to_dataframe(fhir_json: dict) -> pd.DataFrame:
    """Flattens an HL7 FHIR Patient Bundle JSON into a clean tabular DataFrame."""
    rows = []
    entries = fhir_json.get("entry", [])

    for entry in entries:
        resource = entry.get("resource", {})
        if resource.get("resourceType") == "Patient":
            name_data = resource.get("name", [{}])[0]
            address_data = resource.get("address", [{}])[0]
            identifiers = resource.get("identifier", [])

            nhs_val = None
            for ident in identifiers:
                if "nhs-number" in ident.get("system", ""):
                    nhs_val = ident.get("value")

            rows.append(
                {
                    "patient_id": resource.get("id"),
                    "first_name": (
                        name_data.get("given", [""])[0]
                        if name_data.get("given")
                        else ""
                    ),
                    "last_name": name_data.get("family", ""),
                    "gender": resource.get("gender"),
                    "date_of_birth": resource.get("birthDate"),
                    "uk_postcode": address_data.get("postalCode"),
                    "nhs_number": nhs_val,
                }
            )

    return pd.DataFrame(rows)