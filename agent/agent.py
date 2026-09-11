import pandas as pd
import joblib
import shap


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

    def explain_score(
        self,
        account: pd.Series,
        top_k: int = 3
    ) -> list[dict]:
        """
        Return the top local features contributing to an account's
        model prediction using SHAP.
        """

        preprocessor = self.model.named_steps["pre"]
        classifier = self.model.named_steps["clf"]

        # Select the model's expected input features
        feature_cols = preprocessor.feature_names_in_

        X = pd.DataFrame([account])
        X = X[feature_cols]

        # Apply the same preprocessing used by the trained model
        X_transformed = preprocessor.transform(X)

        # Explain the fitted GradientBoostingClassifier
        explainer = shap.TreeExplainer(classifier)
        shap_values = explainer.shap_values(X_transformed)

        # Get feature names after preprocessing
        feature_names = preprocessor.get_feature_names_out()

        # SHAP values for this account
        values = shap_values[0]

        explanations = pd.DataFrame({
            "feature": feature_names,
            "shap_value": values,
            "abs_shap_value": abs(values),
        })

        # Select the top contributors by absolute SHAP value
        explanations = (
            explanations
            .sort_values("abs_shap_value", ascending=False)
            .head(top_k)
        )

        return [
            {
                "feature": row["feature"]
                    .replace("num__", "")
                    .replace("cat__", ""),
                "impact": (
                    "positive"
                    if row["shap_value"] > 0
                    else "negative"
                ),
                "shap_value": float(row["shap_value"]),
            }
            for _, row in explanations.iterrows()
        ]

    def prioritize(self, accounts: pd.DataFrame) -> pd.DataFrame:
        """Rank accounts and assign priority tiers."""

        result = accounts.copy()

        # Highest probability gets rank 1
        result["rank"] = (
            result["conversion_probability"]
            .rank(
                method="first",
                ascending=False
            )
            .astype(int)
        )

        # Top 20% become the high-touch SDR queue
        threshold = result["conversion_probability"].quantile(0.80)

        result["priority"] = result["conversion_probability"].apply(
            lambda score: (
                "HIGH"
                if score >= threshold
                else "LOW"
            )
        )

        return result

    def run(self, accounts: pd.DataFrame) -> pd.DataFrame:
        """Run the complete prioritization flow."""

        result = self.get_scores(accounts)
        result = self.prioritize(result)

        return result