import pandas as pd
import pytest


# --- Modulus 11 NHS Number Validation Function & Tests ---
def validate_nhs_number(nhs_num: str) -> bool:
    """Validates 10-digit UK NHS Number using Modulus 11 Checksum."""
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
        return False  # Invalid Checksum

    return check_digit == int(nhs_str[9])


def test_nhs_modulus11_validation():
    # Valid NHS Numbers
    assert validate_nhs_number("9434765919") is True
    assert validate_nhs_number("654-321-9874") is True

    # Invalid Checksums or Formats
    assert validate_nhs_number("1234567890") is False
    assert validate_nhs_number("99999") is False
    assert validate_nhs_number("ABC1234567") is False


# --- Jaro-Winkler Similarity Function & Tests ---
def jaro_winkler_similarity(s1: str, s2: str) -> float:
    """Calculates basic character-level Jaro-Winkler distance between two strings."""
    s1, s2 = s1.lower().strip(), s2.lower().strip()
    if s1 == s2:
        return 1.0
    if not s1 or not s2:
        return 0.0

    match_distance = (max(len(s1), len(s2)) // 2) - 1
    match_distance = max(0, match_distance)

    s1_matches = [False] * len(s1)
    s2_matches = [False] * len(s2)
    matches = 0

    for i in range(len(s1)):
        start = max(0, i - match_distance)
        end = min(i + match_distance + 1, len(s2))
        for j in range(start, end):
            if not s2_matches[j] and s1[i] == s2[j]:
                s1_matches[i] = True
                s2_matches[j] = True
                matches += 1
                break

    if matches == 0:
        return 0.0

    t = 0
    k = 0
    for i in range(len(s1)):
        if s1_matches[i]:
            while not s2_matches[k]:
                k += 1
            if s1[i] != s2[k]:
                t += 1
            k += 1

    transpositions = t / 2.0
    m = matches
    jaro = (m / len(s1) + m / len(s2) + (m - transpositions) / m) / 3.0

    # Winkler prefix bonus
    prefix = 0
    for i in range(min(4, min(len(s1), len(s2)))):
        if s1[i] == s2[i]:
            prefix += 1
        else:
            break

    return jaro + (prefix * 0.1 * (1 - jaro))


def test_jaro_winkler_logic():
    # Exact Match
    assert jaro_winkler_similarity("John", "John") == 1.0

    # High Similarity (Typos)
    sim_john = jaro_winkler_similarity("John", "Jon")
    assert sim_john > 0.85

    sim_connor = jaro_winkler_similarity("Connor", "Conner")
    assert sim_connor > 0.90

    # Disparate Strings
    assert jaro_winkler_similarity("John", "Alexander") < 0.50


# --- k-Anonymity Math & Equivalence Class Tests ---
def calculate_k_anonymity(
    df: pd.DataFrame, quasi_identifiers: list[str]
) -> int:
    """Returns the minimum equivalence class size (k) across specified quasi-identifiers."""
    if df.empty or not quasi_identifiers:
        return 0
    group_sizes = df.groupby(quasi_identifiers).size()
    return int(group_sizes.min())


def test_k_anonymity_math():
    sample_data = pd.DataFrame(
        {
            "age_group": ["20-29", "20-29", "20-29", "30-39", "30-39"],
            "gender": ["M", "M", "M", "F", "F"],
            "outward_postcode": ["M14", "M14", "M14", "SW1A", "SW1A"],
        }
    )

    # All combinations have at least 2 identical records (k=2)
    k_min = calculate_k_anonymity(
        sample_data, ["age_group", "gender", "outward_postcode"]
    )
    assert k_min == 2

    # Append a unique individual (violates k >= 2)
    sample_data.loc[len(sample_data)] = ["40-49", "M", "EC1A"]
    k_min_violator = calculate_k_anonymity(
        sample_data, ["age_group", "gender", "outward_postcode"]
    )
    assert k_min_violator == 1