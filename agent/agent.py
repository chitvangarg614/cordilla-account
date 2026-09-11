import pandas as pd
import joblib
import shap

from .tools import get_account_history
from .external_context import build_external_context


class AccountPrioritizationAgent:

    def __init__(self, model_path: str):
        self.model = joblib.load(model_path)

        # Tools available to the agent.
        # The agent decides which tool(s) to use.
        self.tools = {
            "crm_history": self.get_history,
            "external_context": self.get_external_context,
        }

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

        feature_cols = preprocessor.feature_names_in_

        X = pd.DataFrame([account])
        X = X[feature_cols]

        # Apply the same preprocessing used by the trained model.
        X_transformed = preprocessor.transform(X)

        # Explain the fitted GradientBoostingClassifier.
        explainer = shap.TreeExplainer(classifier)
        shap_values = explainer.shap_values(X_transformed)

        feature_names = preprocessor.get_feature_names_out()

        values = shap_values[0]

        explanations = pd.DataFrame({
            "feature": feature_names,
            "shap_value": values,
            "abs_shap_value": abs(values),
        })

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

        # Highest probability gets rank 1.
        result["rank"] = (
            result["conversion_probability"]
            .rank(
                method="first",
                ascending=False
            )
            .astype(int)
        )

        # Top 20% become the high-priority sales queue.
        threshold = result["conversion_probability"].quantile(0.80)

        result["priority"] = result["conversion_probability"].apply(
            lambda score: (
                "HIGH"
                if score >= threshold
                else "LOW"
            )
        )

        return result

    # AGENT TOOLS
  

    def get_history(self, account: pd.Series) -> dict:
        """Get CRM history for an account."""

        return get_account_history(account["account_id"])

    def get_external_context(self, account: pd.Series) -> dict:
        """Get external company context for an account."""

        return build_external_context(account["account_id"])

    # AGENT DECISION LOOP


    def decide_action(
        self,
        account: pd.Series,
        explanation: list[dict],
    ) -> dict:
        """
        Agentic decision loop.

        The agent starts with the account and model explanation.
        It decides which context tool it needs, evaluates the result,
        and can request another tool before making the final action.
        """

        system_prompt = """
You are an AI sales prioritization agent.

Your job is to help a sales representative decide the next best
action for a high-priority account.

The account has already been ranked highly by a machine-learning model.

The model score represents the estimated probability that the account
will convert within 90 days. It is a prioritization signal, not a guarantee.

You have access to two information tools:

1. crm_history
   Use this when you need information about:
   - previous customer relationship
   - previous sales interactions
   - last contact
   - contact outcome
   - open opportunities

2. external_context
   Use this when you need information about:
   - recent company activity
   - company news
   - hiring
   - business expansion
   - other current company signals

You decide which tool is useful based on the information already available.

You may:
- call one tool
- call both tools if the first result is insufficient
- stop without calling another tool if you already have enough information

Allowed final actions:

CONTACT_NOW
- Enough evidence exists to justify immediate outreach.

REENGAGE
- The account is a former customer and available signals suggest
  that re-engagement is appropriate.

RESEARCH_FIRST
- The account is high priority, but there is not enough reliable
  context to confidently recommend immediate outreach or re-engagement.

Important rules:

- Do not rely on the model score alone.
- Do not invent information.
- Treat missing information as unknown.
- SHAP explanations describe model behavior, not causal effects.
- Consider CRM and external context when relevant.
- If evidence conflicts or is too weak, choose RESEARCH_FIRST.

Return a tool request when additional information is required.

Return a final decision when enough information is available.
"""

        messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": {
                    "account": {
                        "account_id": account["account_id"],
                        "account_type": account["account_type"],
                        "conversion_probability": float(
                            account["conversion_probability"]
                        ),
                    },
                    "model_explanation": explanation,
                },
            },
        ]

        tools_used = []
        context = {}

       
        # Agent loop
    

        for _ in range(3):
            decision = self._mock_llm_decision(
                account=account,
                explanation=explanation,
                context=context,
            )

            # Agent wants another tool.
            if decision["type"] == "tool_call":

                tool_name = decision["tool"]

                if tool_name not in self.tools:
                    return {
                        "action": "RESEARCH_FIRST",
                        "reason": "Agent requested an unavailable tool.",
                        "tools_used": tools_used,
                    }

                result = self.tools[tool_name](account)

                tools_used.append(tool_name)
                context[tool_name] = result

                # In a real implementation, the tool result would be
                # appended to the LLM conversation here.
                messages.append({
                    "role": "tool",
                    "name": tool_name,
                    "content": result,
                })

                continue

            # Agent has enough information and makes final decision.
            if decision["type"] == "final":
                return {
                    "action": decision["action"],
                    "reason": decision["reason"],
                    "tools_used": tools_used,
                }

        # Safety fallback if the agent keeps requesting tools.
        return {
            "action": "RESEARCH_FIRST",
            "reason": (
                "The agent could not reach a confident decision "
                "within the allowed tool-call limit."
            ),
            "tools_used": tools_used,
        }

    def _mock_llm_decision(
        self,
        account: pd.Series,
        explanation: list[dict],
        context: dict,
    ) -> dict:
        """
        Mock the LLM's tool-calling behavior.

        This represents what a real LLM with native function calling
        would decide. The actual tool implementations are real/mocked
        independently.

        Replace this method with an actual LLM call in production.
        """

        account_type = account["account_type"]

        crm = context.get("crm_history")
        external = context.get("external_context")

       
        # First decision: choose the most useful tool.
        

        if not crm and not external:

            # Former customers need CRM history first because the
            # previous relationship is important for deciding whether
            # to re-engage.
            if account_type == "Former Customer":
                return {
                    "type": "tool_call",
                    "tool": "crm_history",
                }

            # For prospects/suspects, current company activity can
            # provide useful evidence for outreach.
            return {
                "type": "tool_call",
                "tool": "external_context",
            }


        # CRM information is available.


        if crm and not external:

            previous_customer = crm.get("previous_customer", False)
            open_opportunities = crm.get("open_opportunities", 0)
            last_contact_outcome = crm.get("last_contact_outcome")

            # Former customer + CRM history is usually enough to
            # determine whether re-engagement is appropriate.
            if previous_customer:

                if (
                    last_contact_outcome == "No response"
                    and open_opportunities == 0
                ):
                    return {
                        "type": "tool_call",
                        "tool": "external_context",
                    }

                return {
                    "type": "final",
                    "action": "REENGAGE",
                    "reason": (
                        "CRM history shows a previous customer relationship "
                        "and provides sufficient evidence to consider "
                        "re-engagement."
                    ),
                }

            # Active opportunity or positive engagement is strong
            # evidence for immediate contact.
            if (
                open_opportunities > 0
                or last_contact_outcome == "Positive response"
            ):
                return {
                    "type": "final",
                    "action": "CONTACT_NOW",
                    "reason": (
                        "CRM history shows active or positive sales "
                        "engagement, supporting immediate outreach."
                    ),
                }

            # CRM did not provide enough evidence.
            return {
                "type": "tool_call",
                "tool": "external_context",
            }

      
        # External information is available.
     

        if external and not crm:

            recent_news = external.get("recent_news", [])
            open_roles = external.get("open_roles")

            # Current company activity gives enough evidence to contact.
            if recent_news or (
                open_roles is not None and open_roles > 0
            ):
                return {
                    "type": "final",
                    "action": "CONTACT_NOW",
                    "reason": (
                        "External company context shows current business "
                        "activity, providing a relevant reason for outreach."
                    ),
                }

            # We don't know enough about the account's sales history.
            return {
                "type": "tool_call",
                "tool": "crm_history",
            }

      
        # Both tools are available.
       

        if crm and external:

            previous_customer = crm.get("previous_customer", False)
            last_contact_outcome = crm.get("last_contact_outcome")
            open_opportunities = crm.get("open_opportunities", 0)

            if previous_customer:
                return {
                    "type": "final",
                    "action": "REENGAGE",
                    "reason": (
                        "CRM history confirms a previous customer relationship "
                        "and external context provides additional current "
                        "company signals for re-engagement."
                    ),
                }

            if (
                open_opportunities > 0
                or last_contact_outcome == "Positive response"
            ):
                return {
                    "type": "final",
                    "action": "CONTACT_NOW",
                    "reason": (
                        "CRM history shows active or positive engagement, "
                        "supported by current external company context."
                    ),
                }

            return {
                "type": "final",
                "action": "CONTACT_NOW",
                "reason": (
                    "The account is high priority and both CRM and external "
                    "context provide sufficient evidence for outreach."
                ),
            }

        return {
            "type": "final",
            "action": "RESEARCH_FIRST",
            "reason": (
                "There is insufficient context to confidently recommend "
                "an immediate sales action."
            ),
        }


    def create_salesforce_task(
        self,
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