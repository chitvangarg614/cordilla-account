import pandas as pd
import joblib
import shap

from .tools import get_account_history
from .external_context import build_external_context

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

    def get_history(self, account: pd.Series) -> dict:
        """Get CRM history for an account."""
        return get_account_history(account["account_id"])

    def get_high_priority_context(self, accounts: pd.DataFrame) -> list[dict]:
        """Get explanations and CRM history only for high-priority accounts."""

        results = self.run(accounts)

        high_priority = results[results["priority"] == "HIGH"]

        context = []

        for _, account in high_priority.iterrows():
            context.append({
                "account_id": account["account_id"],
                "score": account["conversion_probability"],
                "explanation": self.explain_score(account),
                "history": self.get_history(account),
            })

        return context

    def get_external_context(self, account: pd.Series) -> dict:
        """Get external company context for an account."""
        return build_external_context(account["account_id"])


    def decide_action(
        self,
        account: pd.Series,
        history: dict,
        explanation: list[dict],
        external_context: dict,
    ) -> dict:
        """Use an LLM to decide the next sales action."""

        system_prompt = """
    You are an AI sales prioritization agent.

    Your job is to help a sales representative decide the next best action
    for a high-priority account.

    The account has already been ranked highly by a machine-learning model.
    The model score represents the estimated probability that the account
    will convert within 90 days. It is a prioritization signal, not a guarantee.

    You will receive:
    - account information
    - model conversion probability
    - model explanation
    - CRM/account history
    - external company context

    Your responsibility is to synthesize these signals and recommend the
    most appropriate next action for the sales representative.

    Allowed actions:

    CONTACT_NOW
    - The account has enough evidence to justify immediate outreach.

    REENGAGE
    - The account is a former customer and the available signals suggest
    that re-engagement is appropriate.

    RESEARCH_FIRST
    - The account is high priority, but there is not enough reliable context
    to confidently recommend immediate outreach or re-engagement.

    Decision guidelines:

    - Consider all available signals together.
    - Do not rely on the model score alone.
    - Use the model explanation to understand which features contributed to
    the prediction. Do not interpret model explanations as causal effects.
    - Use CRM history to understand previous interactions, opportunities,
    contact outcomes, and customer history.
    - Use external context to understand what is happening at the company.
    - Do not invent information that is not provided.
    - Treat missing or None values as unknown.
    - Missing information does not automatically require RESEARCH_FIRST.
    - For former customers, consider REENGAGE when there are meaningful
    current signals; otherwise choose RESEARCH_FIRST.
    - For engaged prospects/accounts with strong evidence, prefer CONTACT_NOW.
    - If the available evidence conflicts substantially or is too weak,
    choose RESEARCH_FIRST.

    The recommendation should be actionable for a sales representative.

    Return ONLY valid JSON:

    {
        "action": "CONTACT_NOW | REENGAGE | RESEARCH_FIRST",
        "reason": "Brief explanation grounded in the provided evidence."
    }
    """

        user_prompt = {
            "account": {
                "account_id": account["account_id"],
                "account_type": account["account_type"],
                "conversion_probability": float(
                    account["conversion_probability"]
                ),
            },
            "model_explanation": explanation,
            "crm_history": history,
            "external_context": external_context,
        }

        # Mock LLM response for the take-home.
        # Replace this with the actual LLM call later.
        #
        # Recommended production parameters:
        # temperature=0.0 for deterministic decisions
        # max_tokens=300 to keep the response concise
        # response_format=json_object for structured output
        mock_response = {
            "action": "CONTACT_NOW",
            "reason": (
                "The account has a high predicted conversion probability, "
                "recent positive CRM engagement, and external signals that "
                "indicate potential business activity."
            ),
        }

        return mock_response



 

    def create_salesforce_task(self,
        account_id: str,
        action: str,
        reason: str,
    ) -> dict:
        """Create a mock Salesforce task for the sales representative."""

        return {
            "status": "created",
            "account_id": account_id,
            "task": action,
            "reason": reason,
        }
    
    def run(self, accounts: pd.DataFrame) -> pd.DataFrame:
        """Run the complete prioritization flow."""

        result = self.get_scores(accounts)
        result = self.prioritize(result)

        return result