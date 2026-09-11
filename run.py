import pandas as pd

from agent import AccountPrioritizationAgent


def main():

    accounts = pd.read_csv("data/accounts_to_score.csv")

    agent = AccountPrioritizationAgent(
        model_path="model/model.pkl"
    )

    results = agent.run(accounts)

    results = results.sort_values(
        "conversion_probability",
        ascending=False
    )

    print("\nTop 20 accounts:\n")

    print(
        results[
            [
                "account_id",
                "account_type",
                "conversion_probability",
                "rank",
                "priority",
            ]
        ].head(20).to_string(index=False)
    )

    # Save complete ranked output
    results.to_csv(
        "data/prioritized_accounts.csv",
        index=False
    )

    print("\nSaved: agent/prioritized_accounts.csv")


if __name__ == "__main__":
    main()