from cv_optimiser.local_ai import _language_problem


def test_language_check_directions():
    assert _language_problem("Wdrożyłem politykę oraz dla zespołu", "en-GB")
    assert not _language_problem("Managed Łódź office", "en-GB")
    assert _language_problem("Wdrożyłem the policy and the process", "pl")
    assert not _language_problem("Wdrożyłem politykę bezpieczeństwa NIST", "pl")
    assert not _language_problem("Praca „Autonomous Security Software for Companies” została wyróżniona", "pl")
