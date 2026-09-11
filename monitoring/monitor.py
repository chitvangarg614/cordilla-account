import pandas as pd


def check_prediction_distribution(
    predictions: pd.Series,
    baseline_mean: float = 0.0655,
) -> dict:
    """Check for unusual changes in the model prediction distribution."""

    mean_prediction = predictions.mean()
    min_prediction = predictions.min()
    max_prediction = predictions.max()

    mean_shift = (
        abs(mean_prediction - baseline_mean) / baseline_mean
    )

    status = "OK" if mean_shift <= 0.50 else "INVESTIGATE"

    return {
        "status": status,
        "mean_prediction": round(mean_prediction, 4),
        "min_prediction": round(min_prediction, 4),
        "max_prediction": round(max_prediction, 4),
        "baseline_mean": baseline_mean,
        "mean_shift_pct": round(mean_shift * 100, 2),
    }


def fire_alert(monitoring_result: dict):
    if monitoring_result["status"] == "INVESTIGATE":
        print(
            "🚨 ALERT: Prediction distribution has shifted. "
            f"Mean={monitoring_result['mean_prediction']}, "
            f"Baseline={monitoring_result['baseline_mean']}, "
            f"Shift={monitoring_result['mean_shift_pct']}%"
        )