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