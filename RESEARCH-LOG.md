### Entry 1 - Intent Score Coverage

- Training data:
  - Missing: **40.2%**
  - Available: **59.8%**
- Fresh data:
  - Missing: **38.67%**
  - Available: **61.33%**

The missingness is very similar:

| | Training | Fresh |
|---|---:|---:|
| Missing | 40.2% | 38.7% |
| Available | 59.8% | 61.3% |

**Finding:** Fresh data has slightly better intent-score coverage, so there is currently **no evidence of a major intent-coverage shift**.

**Production consideration:** Continue monitoring intent-score availability because this could change if the upstream data source or process changes.




## Entry 2 — Model Scoring

### What I wanted to check

I wanted to understand how the provided model behaves on the fresh 300 accounts and whether the scores give enough separation to prioritize accounts.

### What I found

- Average predicted conversion probability: **6.55%**
- Minimum: **3.81%**
- Maximum: **20.94%**
- Median: **5.40%**
- Top 20%: **60 accounts**
- Top 20% score threshold: **8.74%**


### Decision

Use the model as a ranking signal and initially prioritize the **top 20% (60 accounts)** for higher-touch sales activity.

The 20% cutoff is an initial business assumption based on limited sales capacity, not a proven optimal threshold.

### AI tool question

**Asked:** Should I use an absolute probability threshold or rank the accounts?

**Answer:** Since there is no predefined business threshold, ranking is more appropriate. The cutoff can later be adjusted based on actual sales capacity and outcomes.



## Entry: Prediction monitoring

### Hypothesis
A change in the model prediction distribution can indicate an upstream
data change, population shift, or model degradation, but it does not by
itself mean that the model has failed.

### Decision
Added prediction-distribution monitoring using the current mean, minimum,
and maximum predicted conversion probability compared with the baseline
mean of 6.55%.

A large shift is treated as an `INVESTIGATE` signal rather than an automatic
model-failure alert. For example, higher predictions could be legitimate if
lead quality or conversion rates improve.

### Follow-up validation
The stronger model-health check will compare predictions with delayed actual
90-day conversion outcomes. The key question is whether higher-ranked
accounts continue to have higher observed conversion rates.

If ranking/lift deteriorates, investigate upstream data changes, population
shift, vendor changes, or model decay before deciding whether to recalibrate,
retrain, or roll back.



Sure — here is the exact `.md` content:

## Next Steps — Agent Observability

### Hypothesis

A model can be healthy while the agent workflow is failing. Operational failures such as tool errors, high latency, failed LLM responses, or unsuccessful Salesforce actions could prevent good model predictions from turning into useful sales actions.

### What I plan to monitor

For each agent/tool execution:

- Tool name and account ID
- Success or failure
- Execution time
- Error details

At the workflow level:

- Agent success/failure rate
- Tool failure rate and p95 latency
- End-to-end execution time
- Salesforce action success rate
- Invalid or failed LLM responses
- Number of tool calls per account

### Decision

Keep **model monitoring** and **agent observability** as separate layers.

Model monitoring answers **"Is the model still performing as expected?"**, while agent observability answers **"Is the system executing the workflow reliably?"**

### Next

Implement structured logs for these signals and surface the key metrics in a simple operational dashboard.

Then add outcome monitoring to determine whether actions such as `CONTACT_NOW`, `REENGAGE`, and `RESEARCH_FIRST` lead to productive sales outcomes.



## Final Synthesis

### What I would stand behind

- The fresh dataset contains 300 accounts.
- Mean predicted conversion probability is 6.55%.
- The top 20% contains 60 accounts.
- Intent-score missingness is 38.67% in fresh data versus 40.2% in training.
- Ranking is preferable to an absolute probability cutoff because no business threshold was provided.
- The 20% prioritization level is a sales-capacity assumption, not a proven optimal threshold.
- Model predictions should be treated as prioritization signals, not guarantees or causal estimates.
- The agent adds context and converts the ranking into an actionable sales decision.
- Operational monitoring and business-outcome monitoring are separate from model monitoring.
- Actual 90-day conversion outcomes will be needed to validate whether the ranking continues to provide useful lift.

### Key assumptions

- Sales capacity supports a high-touch queue of approximately 20% of scored accounts.
- CRM and external context are available when needed.
- Salesforce actions can be represented by the mocked integration in the prototype.
- Actual conversion outcomes will become available after the 90-day outcome window.

### Main risks

- Upstream feature quality or missingness changes.
- Population changes over time.
- Model ranking/lift deteriorates.
- Agent tools fail or become slow.
- Agent recommendations do not translate into productive sales activity.