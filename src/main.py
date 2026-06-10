import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


METRICS = {
    "steps": {
        "name": "Physical Activity",
        "unit": "steps",
        "higher_is_better": True,
    },
    "sleep_hours": {
        "name": "Sleep Duration",
        "unit": "hours",
        "higher_is_better": True,
    },
    "screen_time_hours": {
        "name": "Screen Time",
        "unit": "hours",
        "higher_is_better": False,
    },
    "deep_work_hours": {
        "name": "Deep Work",
        "unit": "hours",
        "higher_is_better": True,
    },
    "exercise_minutes": {
        "name": "Exercise",
        "unit": "minutes",
        "higher_is_better": True,
    },
}


REQUIRED_COLUMNS = [
    "user_id",
    "date",
    "steps",
    "sleep_hours",
    "screen_time_hours",
    "deep_work_hours",
    "exercise_minutes",
]


def load_data(input_path: str) -> pd.DataFrame:
    df = pd.read_csv(input_path)

    missing_columns = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["user_id", "date"]).reset_index(drop=True)

    return df


def calculate_confidence(change_pct: float, min_points: int, available_points: int) -> float:
    """
    Confidence increases when:
    1. change is larger
    2. enough data points are available
    """
    change_strength = min(abs(change_pct), 0.50) / 0.50
    data_strength = min(available_points / min_points, 1.0)

    confidence = 0.50 + (0.35 * change_strength) + (0.10 * data_strength)
    return round(min(confidence, 0.95), 2)


def discover_patterns(df: pd.DataFrame) -> list:
    """
    Compares recent 7 days with previous 7 days.
    If the change is meaningful, generates an insight.
    If data is insufficient, abstains.
    """
    insights = []
    recent_days = 7
    previous_days = 7
    minimum_points = 5
    meaningful_change_threshold = 0.15

    for user_id, user_df in df.groupby("user_id"):
        user_df = user_df.sort_values("date")
        max_date = user_df["date"].max()

        recent_start = max_date - pd.Timedelta(days=recent_days - 1)
        previous_start = recent_start - pd.Timedelta(days=previous_days)

        recent_df = user_df[user_df["date"] >= recent_start]
        previous_df = user_df[
            (user_df["date"] >= previous_start) & (user_df["date"] < recent_start)
        ]

        for metric, config in METRICS.items():
            recent_values = recent_df[metric].dropna()
            previous_values = previous_df[metric].dropna()

            if len(recent_values) < minimum_points or len(previous_values) < minimum_points:
                insights.append(
                    {
                        "user_id": user_id,
                        "type": "abstention",
                        "domain": config["name"],
                        "message": f"Insufficient evidence for {config['name']}.",
                        "reason": f"Need at least {minimum_points} recent and {minimum_points} previous values.",
                        "confidence": 0.0,
                    }
                )
                continue

            recent_avg = recent_values.mean()
            previous_avg = previous_values.mean()

            if previous_avg == 0:
                continue

            change_pct = (recent_avg - previous_avg) / abs(previous_avg)

            if abs(change_pct) < meaningful_change_threshold:
                continue

            direction = "increased" if change_pct > 0 else "declined"

            if config["higher_is_better"]:
                interpretation = "positive change" if change_pct > 0 else "negative change"
            else:
                interpretation = "negative change" if change_pct > 0 else "positive change"

            confidence = calculate_confidence(
                change_pct=change_pct,
                min_points=minimum_points,
                available_points=min(len(recent_values), len(previous_values)),
            )

            insights.append(
                {
                    "user_id": user_id,
                    "type": "pattern",
                    "domain": config["name"],
                    "insight": f"{config['name']} {direction} in the recent period.",
                    "interpretation": interpretation,
                    "confidence": confidence,
                    "evidence": (
                        f"Average {metric} changed from "
                        f"{previous_avg:.2f} {config['unit']} to "
                        f"{recent_avg:.2f} {config['unit']}."
                    ),
                    "change_percentage": round(change_pct * 100, 2),
                }
            )

    return insights


def detect_anomalies(df: pd.DataFrame) -> list:
    """
    Uses z-score to detect unusual values.
    A value is anomalous if it is far from the user's normal behavior.
    """
    anomalies = []
    minimum_history = 10
    z_threshold = 2.5

    for user_id, user_df in df.groupby("user_id"):
        user_df = user_df.sort_values("date")

        for metric, config in METRICS.items():
            values = user_df[metric].dropna()

            if len(values) < minimum_history:
                anomalies.append(
                    {
                        "user_id": user_id,
                        "type": "abstention",
                        "domain": config["name"],
                        "message": f"Insufficient evidence for anomaly detection in {config['name']}.",
                        "reason": f"Need at least {minimum_history} historical values.",
                        "confidence": 0.0,
                    }
                )
                continue

            mean = values.mean()
            std = values.std()

            if std == 0 or np.isnan(std):
                continue

            for _, row in user_df.iterrows():
                value = row[metric]
                z_score = (value - mean) / std

                if abs(z_score) >= z_threshold:
                    direction = "higher than normal" if z_score > 0 else "lower than normal"
                    confidence = round(min(0.95, 0.60 + (abs(z_score) - z_threshold) * 0.15), 2)

                    anomalies.append(
                        {
                            "user_id": user_id,
                            "type": "anomaly",
                            "domain": config["name"],
                            "date": str(row["date"].date()),
                            "insight": f"Unusual {config['name']} detected.",
                            "confidence": confidence,
                            "evidence": (
                                f"On {row['date'].date()}, {metric} was {value:.2f} {config['unit']}, "
                                f"which is {direction}. User average is {mean:.2f} {config['unit']}."
                            ),
                            "z_score": round(z_score, 2),
                        }
                    )

    return anomalies


def generate_report(input_path: str, output_path: str) -> dict:
    df = load_data(input_path)

    patterns = discover_patterns(df)
    anomalies = detect_anomalies(df)

    report = {
        "project": "Chronis Task A - Behavioral Insight Engine",
        "dataset_summary": {
            "rows": len(df),
            "users": df["user_id"].nunique(),
            "start_date": str(df["date"].min().date()),
            "end_date": str(df["date"].max().date()),
            "metrics_used": list(METRICS.keys()),
        },
        "insights": patterns + anomalies,
    }

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)

    return report


def print_report(report: dict) -> None:
    print("\nCHRONIS BEHAVIORAL INSIGHT ENGINE")
    print("=" * 45)

    summary = report["dataset_summary"]
    print(f"Rows: {summary['rows']}")
    print(f"Users: {summary['users']}")
    print(f"Date Range: {summary['start_date']} to {summary['end_date']}")

    print("\nGenerated Insights:")
    print("-" * 45)

    for item in report["insights"]:
        if item["type"] == "abstention":
            print(f"[ABSTAIN] User {item['user_id']} | {item['domain']}")
            print(f"Reason: {item['reason']}\n")
        else:
            print(f"[{item['type'].upper()}] User {item['user_id']} | {item['domain']}")
            print(f"Insight: {item['insight']}")
            print(f"Confidence: {item['confidence']}")
            print(f"Evidence: {item['evidence']}\n")


def main():
    parser = argparse.ArgumentParser(description="Chronis Task A Behavioral Insight Engine")
    parser.add_argument(
        "--input",
        default="data/behavior.csv",
        help="Path to behavioral dataset CSV",
    )
    parser.add_argument(
        "--output",
        default="results/report.json",
        help="Path to save JSON report",
    )

    args = parser.parse_args()

    report = generate_report(args.input, args.output)
    print_report(report)


if __name__ == "__main__":
    main()