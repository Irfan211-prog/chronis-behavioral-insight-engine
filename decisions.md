# Chronis Behavioral Insight Engine — Decisions

## Overview

This document explains the main decisions behind the **Chronis Task A — Behavioral Insight Engine** project.

The goal of this project is simple: take daily behavioral data and convert it into useful, explainable insights. The system does not try to make personal judgments about a user. It only reports what the data supports.

The project focuses on four main things:

- Finding meaningful behavior patterns
- Detecting unusual changes
- Giving evidence for every insight
- Refusing to make a claim when the evidence is weak

---

## 1. Data Used

The given dataset contains daily behavior records for multiple users.

The main columns used are:

| Column | Meaning |
|--------|---------|
| `user_id` | Unique user identifier |
| `date` | Date of the behavior record |
| `steps` | Daily physical activity |
| `sleep_hours` | Sleep duration |
| `screen_time_hours` | Daily screen time |
| `deep_work_hours` | Focused work duration |
| `exercise_minutes` | Exercise duration |

These metrics were selected because they represent common daily behavior areas: activity, sleep, digital habits, productivity, and exercise.

---

## 2. Pattern Discovery Method

For pattern discovery, the system compares two time windows:

```text
Recent 7 days vs Previous 7 days
```

For every user and every metric, the system calculates:

```text
average value in recent 7 days
average value in previous 7 days
percentage change
```

If the change is large enough, the system generates an insight.

### Example

```text
Previous 7 days average steps: 8,100
Recent 7 days average steps: 5,400
```

Generated insight:

```text
Physical Activity declined in the recent period.
```

### Why this method was chosen

This method is simple, explainable, and easy to verify. Since Chronis values reasoning and explainability more than model complexity, a clear statistical comparison is a better choice than using a black-box model.

---

## 3. Meaningful Change Boundary

The system only creates a pattern insight if the change is at least:

```text
15%
```

This avoids generating insights for very small changes.

### Example

If sleep changes from 7.0 hours to 7.1 hours, the system does not generate an insight because the difference is too small.

If steps change from 8,000 to 5,500, the system generates an insight because the difference is meaningful.

---

## 4. Anomaly Detection Method

For anomaly detection, the system uses a z-score based method.

For each user and each metric, the system calculates:

```text
user average
standard deviation
z-score for each daily value
```

A value is treated as unusual if:

```text
absolute z-score >= 2.5
```

### Example

If a user normally sleeps around 7 hours, but one day they sleep only 3 hours, the system may flag it as unusual.

Generated insight:

```text
Unusual Sleep Duration detected.
```

### Why this method was chosen

Z-score is easy to explain. It checks how far one value is from the user's normal behavior. This makes anomaly detection understandable for reviewers.

---

## 5. Confidence Score

Each generated insight gets a confidence score.

The confidence score is based on:

1. How large the behavioral change is
2. How much data is available

Large changes with enough data receive higher confidence. Small changes or limited data receive lower confidence.

### Example

```text
A 35% drop in steps with enough records = higher confidence
A 16% change with fewer records = lower confidence
```

The confidence score helps the user understand how strongly the data supports the insight.

---

## 6. Evidence for Every Insight

Every insight includes evidence.

The system does not simply say:

```text
Activity declined.
```

Instead, it explains why:

```text
Average steps changed from 8,100 steps to 5,400 steps.
```

This makes the output transparent and easy to check.

---

## 7. Evidence Sufficiency and Abstention

The system does not force an insight when the data is not enough.

For pattern discovery, the system requires at least:

```text
5 recent values
5 previous values
```

For anomaly detection, the system requires at least:

```text
10 historical values
```

If the data is not enough, the system returns an abstention.

### Example

```text
Insufficient evidence for Sleep Duration.
Reason: Need at least 5 recent and 5 previous values.
```

### Why abstention is important

A weak claim can mislead the user. So the system is designed to stay silent when the evidence is not strong enough. This makes the project safer and more reliable.

---

## 8. Output Safety

The system only talks about behavior data. It does not judge the person.

The system avoids words like:

- lazy
- careless
- addicted
- undisciplined

Bad output:

```text
The user is lazy.
```

Good output:

```text
Physical Activity declined in the recent period.
```

This keeps the system professional and safe.

---

## 9. Assumptions

The project uses the following assumptions:

| Metric | Assumption |
|--------|------------|
| `steps` | Higher steps usually indicate more physical activity |
| `sleep_hours` | Higher sleep duration is generally better within a normal range |
| `screen_time_hours` | Higher screen time is treated as a negative change |
| `deep_work_hours` | Higher deep work usually indicates stronger focused work |
| `exercise_minutes` | Higher exercise minutes usually indicate stronger exercise behavior |

These assumptions are simple and practical for this assessment. They can be changed later based on domain requirements.

---

## 10. Failure Modes

This system is useful, but it is not perfect.

Possible failure cases:

1. **It may miss long-term patterns**
   - The current method compares recent 7 days with previous 7 days. Very slow changes over months may not be captured.

2. **It does not explain the reason behind a behavior**
   - The system can say that sleep declined, but it cannot know why it declined.

3. **Z-score may not work well for all behavior types**
   - Some behaviors are naturally irregular, so z-score may sometimes flag too much or too little.

4. **The system depends on data quality**
   - Missing or incorrect data can affect the final insights.

5. **The assumptions may not fit every user**
   - For example, high screen time may be negative for one user but work-related for another user.

---

## 11. Why I Did Not Use a Complex ML Model

I did not use a complex machine learning model because the assessment values clarity, reasoning, explainability, and practical engineering judgment.

A complex model may produce results, but it can be hard to explain why the result was generated.

For this task, a simple rule-based and statistics-based system is better because:

- Every insight is easy to verify
- Every decision has clear evidence
- The logic is easy to test
- The system can abstain when data is weak
- The output is understandable for both technical and non-technical reviewers

---

## 12. Testing Decisions

The test suite checks the most important parts of the system:

- Pattern discovery detects a clear decline
- Anomaly detection finds an unusual value
- The system abstains when evidence is insufficient
- The output does not use judgmental language

These tests prove that the system is not only producing output, but also following the core requirements of the task.

---

## 13. Dashboard Decision

I added a Streamlit dashboard to make the generated insights easier to understand.

The JSON report is useful for technical review, but the dashboard makes the project more user-friendly.

The dashboard shows:

- Overall behavior records
- User-level trends
- Metric charts
- Generated insights
- Confidence scores
- Evidence for each insight
- Abstention cases

This helps reviewers understand the project quickly without manually reading the JSON file.

---

## 14. Final Design Choice

The final design is intentionally simple:

```text
CSV data → Python insight engine → JSON report → Streamlit dashboard
```

This flow keeps the project easy to run, easy to test, and easy to review.

The main focus is not model complexity. The main focus is building a reliable system that gives useful, explainable, and evidence-backed behavioral insights.
