import pandas as pd

from agent.agent import AccountPrioritizationAgent
from monitoring.monitor import check_prediction_distribution, fire_alert

agent = AccountPrioritizationAgent("model/model.pkl")

accounts = pd.read_csv("data/accounts_to_score.csv")

# Score and prioritize
results = agent.run(accounts)

monitoring = check_prediction_distribution(
    results["conversion_probability"]
)

fire_alert(monitoring)

print("\nPrediction monitoring:", monitoring)

high_priority = results[
    results["priority"] == "HIGH"
]

print(f"Total accounts: {len(accounts)}")
print(f"High-priority accounts: {len(high_priority)}")

# Run agent for high-priority accounts
for _, account in high_priority.head(5).iterrows():
    explanation = agent.explain_score(account)

    # The agent decides whether it needs CRM history,
    # external context, both, or neither.
    decision = agent.decide_action(
        account=account,
        explanation=explanation,
    )

    print("\nAccount:", account["account_id"])
    print(
        "Score:",
        round(account["conversion_probability"], 4)
    )

    print("Model explanation:", explanation)

    print("Tools used:", decision["tools_used"])

    print("Decision:", decision)

    # Execute the recommended action in Salesforce
    task = agent.create_salesforce_task(
        account_id=account["account_id"],
        action=decision["action"],
        reason=decision["reason"],
    )

    print("Salesforce task:", task)