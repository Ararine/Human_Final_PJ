from services import report


def test_risk_score():
    result = report.analyze_posts([
        "죽고싶다",
        "010-1234-5678"
    ])

    assert result["score"] > 50