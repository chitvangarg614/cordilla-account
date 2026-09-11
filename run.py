import pandas as pd

from agent.agent import AccountPrioritizationAgent


agent = AccountPrioritizationAgent("model/model.pkl")

accounts = pd.read_csv("data/accounts_to_score.csv")

# Score and prioritize
results = agent.run(accounts)

high_priority = results[
    results["priority"] == "HIGH"
]

print(f"Total accounts: {len(accounts)}")
print(f"High-priority accounts: {len(high_priority)}")

# Run agent for high-priority accounts
for _, account in high_priority.head(5).iterrows():

    explanation = agent.explain_score(account)
    history = agent.get_history(account)
    external_context = agent.get_external_context(account)

    decision = agent.decide_action(
        account,
        history,
        explanation,
        external_context,
    )

    print("\nAccount:", account["account_id"])
    print("Score:", round(account["conversion_probability"], 4))
    print("Decision:", decision)

    # Execute the recommended action in Salesforce
    task = agent.create_salesforce_task(
        account_id=account["account_id"],
        action=decision["action"],
        reason=decision["reason"],
    )

    print("Salesforce task:", task)