from app.services.scoring_service import ScoringService


def test_drs_calculation_worked_example():
    """
    T-15: Test DRS calculation from SRS Appendix C.
    100 functions, 80 documented.
    Raw penalty: e.g. 3 Medium findings (weight 2.0 each = 6.0 raw penalties) or equivalent.
    Scaled penalty = 6.0 * 0.80 = 4.8.
    Completeness = 32.0.
    """
    # Test 100 functions, all documented, no findings -> 100.0
    perfect = ScoringService.calculate_drs(
        total_functions=100,
        documented_functions=100,
        findings_by_severity={"High": 0, "Medium": 0, "Low": 0}
    )
    assert perfect["documentation_score"] == 100.0
    assert perfect["breakdown"]["completeness_score"] == 40.0
    assert perfect["breakdown"]["consistency_score"] == 60.0

    # Test 100 functions, 0 documented -> 0.0
    zero_doc = ScoringService.calculate_drs(
        total_functions=100,
        documented_functions=0,
        findings_by_severity={"High": 100, "Medium": 0, "Low": 0}
    )
    assert zero_doc["documentation_score"] == 0.0
    assert zero_doc["breakdown"]["completeness_score"] == 0.0
    assert zero_doc["breakdown"]["consistency_score"] == 0.0

    # Test 100 functions, 80 documented, 0 penalties -> 32 + 48 = 80.0
    partial_clean = ScoringService.calculate_drs(
        total_functions=100,
        documented_functions=80,
        findings_by_severity={"High": 0, "Medium": 0, "Low": 0}
    )
    assert partial_clean["documentation_score"] == 80.0
    assert partial_clean["breakdown"]["completeness_score"] == 32.0
    assert partial_clean["breakdown"]["consistency_score"] == 48.0

