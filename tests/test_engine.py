import pandas as pd

from src.main import discover_patterns, detect_anomalies


def test_pattern_discovery_detects_decline():
    data = []

    for day in range(1, 8):
        data.append(
            {
                "user_id": "U_TEST",
                "date": f"2026-01-{day:02d}",
                "steps": 10000,
                "sleep_hours": 7,
                "screen_time_hours": 4,
                "deep_work_hours": 4,
                "exercise_minutes": 40,
            }
        )

    for day in range(8, 15):
        data.append(
            {
                "user_id": "U_TEST",
                "date": f"2026-01-{day:02d}",
                "steps": 5000,
                "sleep_hours": 7,
                "screen_time_hours": 4,
                "deep_work_hours": 4,
                "exercise_minutes": 40,
            }
        )

    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])

    insights = discover_patterns(df)

    assert any(
        item["type"] == "pattern"
        and item["domain"] == "Physical Activity"
        and "declined" in item["insight"]
        for item in insights
    )


def test_anomaly_detection_finds_unusual_value():
    data = []

    for day in range(1, 21):
        steps = 8000
        if day == 20:
            steps = 1000

        data.append(
            {
                "user_id": "U_TEST",
                "date": f"2026-01-{day:02d}",
                "steps": steps,
                "sleep_hours": 7,
                "screen_time_hours": 4,
                "deep_work_hours": 4,
                "exercise_minutes": 40,
            }
        )

    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])

    anomalies = detect_anomalies(df)

    assert any(
        item["type"] == "anomaly"
        and item["domain"] == "Physical Activity"
        for item in anomalies
    )


def test_insufficient_evidence_abstains():
    data = []

    for day in range(1, 4):
        data.append(
            {
                "user_id": "U_TEST",
                "date": f"2026-01-{day:02d}",
                "steps": 8000,
                "sleep_hours": 7,
                "screen_time_hours": 4,
                "deep_work_hours": 4,
                "exercise_minutes": 40,
            }
        )

    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])

    insights = discover_patterns(df)

    assert any(item["type"] == "abstention" for item in insights)


def test_outputs_do_not_use_judgment_words():
    data = []

    for day in range(1, 15):
        data.append(
            {
                "user_id": "U_TEST",
                "date": f"2026-01-{day:02d}",
                "steps": 8000,
                "sleep_hours": 7,
                "screen_time_hours": 4,
                "deep_work_hours": 4,
                "exercise_minutes": 40,
            }
        )

    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])

    insights = discover_patterns(df) + detect_anomalies(df)

    banned_words = ["lazy", "careless", "addicted", "undisciplined"]

    full_text = str(insights).lower()

    for word in banned_words:
        assert word not in full_text