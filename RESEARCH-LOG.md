### Intent Score Coverage

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