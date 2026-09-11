import pandas as pd
import joblib


class AccountPrioritizationAgent:

    def __init__(self, model_path: str):
        self.model = joblib.load(model_path)

    def get_scores(self, accounts: pd.DataFrame) -> pd.DataFrame:
        """Score all accounts using the provided model."""

        feature_cols = self.model.named_steps["pre"].feature_names_in_

        X = accounts[feature_cols]

        probabilities = self.model.predict_proba(X)

        result = accounts.copy()
        result["conversion_probability"] = probabilities[:, 1]

        return result

    def prioritize(self, accounts: pd.DataFrame) -> pd.DataFrame:
        """Rank accounts and assign priority tiers."""

        result = accounts.copy()

        # Highest probability gets rank 1
        result["rank"] = (
            result["conversion_probability"]
            .rank(method="first", ascending=False)
            .astype(int)
        )

        # Top 20% become the high-touch SDR queue
        threshold = result["conversion_probability"].quantile(0.80)

        result["priority"] = result["conversion_probability"].apply(
            lambda score: "HIGH"
            if score >= threshold
            else "LOW"
        )

        return result

    def run(self, accounts: pd.DataFrame) -> pd.DataFrame:
        """Run the complete prioritization flow."""

        result = self.get_scores(accounts)
        result = self.prioritize(result)

        return result