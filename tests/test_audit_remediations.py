import pandas as pd
from main import mask_outward_postcode, validate_nhs_number
from modules.fhir_bridge import fhir_bundle_to_dataframe


def test_aud_01_unspaced_postcode_masking():
    assert mask_outward_postcode("M144PX") == "M14"
    assert mask_outward_postcode("SW1A 1AA") == "SW1A"
    assert mask_outward_postcode("LS14AP") == "LS1"


def test_aud_02_float_coerced_nhs_validation():
    # Test integer float string representation from Pandas
    assert validate_nhs_number("9434765919.0") is True
    assert validate_nhs_number(9434765919.0) is True
    assert validate_nhs_number("1234567890") is False


def test_aud_06_fhir_null_system_handling():
    # FHIR bundle with null system key inside identifier
    malformed_bundle = {
        "resourceType": "Bundle",
        "entry": [
            {
                "resource": {
                    "resourceType": "Patient",
                    "id": "P99",
                    "identifier": [{"system": None, "value": "12345"}],
                }
            }
        ],
    }
    df = fhir_bundle_to_dataframe(malformed_bundle)
    assert len(df) == 1
    assert df.loc[0, "patient_id"] == "P99"