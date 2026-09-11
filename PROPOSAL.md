# Sales Account Prioritization Agent

## Executive Summary

**The problem:** Sales representatives have more accounts than they can meaningfully contact. Today, they need to decide which accounts deserve their attention and what action to take.

**The recommendation:** Use the existing conversion model to rank accounts, then have an AI agent investigate the highest-priority accounts and recommend the next sales action.

From the **300 accounts** provided:

* **60 accounts** are in the initial high-priority queue.
* Their predicted conversion score is approximately **8.74% or higher**.
* The average predicted score across all accounts is **6.55%**.
* Scores range from **3.81% to 20.94%**.

This does **not** mean the 60 accounts will convert. The score is a prioritization signal. The goal is to help the sales team spend limited outreach capacity where it is most likely to matter.

---

## What the Sales Representative Gets

Instead of giving a representative a spreadsheet of 300 scores:

```text
Account → Score → Rank
```

the system produces an actionable recommendation:

```text
Account
   ↓
Why is this account worth attention?
   ↓
Check relevant CRM / company context
   ↓
Recommended action
   ↓
Salesforce task
```

The agent can recommend:

* **CONTACT_NOW** — evidence supports immediate outreach.
* **REENGAGE** — previous customer with signals worth revisiting.
* **RESEARCH_FIRST** — account looks promising, but more information is needed before contacting.

The representative therefore receives a **prioritized account plus a suggested next step**, rather than having to interpret a model score themselves.

---

## Why 60 Accounts?

The model scores all 300 accounts, but sales capacity is limited.

I selected the **top 20% (60 accounts)** as an initial high-touch queue. The approximately **8.74% score** is therefore a capacity-based cutoff, not a universal definition of a "good" account.

If the team can handle 30 accounts, the queue can be reduced. If it can handle 100, it can be expanded.

The important principle is:

> **Rank the accounts first, then match the high-touch queue to actual sales capacity.**

Actual conversion outcomes should eventually determine whether 20% is the right operating point.

---

## What We Learned From the Data

### Intent data is useful but incomplete

Intent score is missing for approximately:

* **40.2%** of historical training accounts.
* **38.67%** of fresh accounts.

The missingness is therefore broadly similar between historical and fresh data. This is encouraging, but it should continue to be monitored because changes in upstream data coverage could affect the model.

### The model relies heavily on a few signals

The three largest global feature importance values are:

| Signal          | Importance |
| --------------- | ---------: |
| Intent score    |      27.1% |
| Web touchpoints |      21.4% |
| Sales contacts  |      20.9% |

Together, these account for approximately **69% of the model's feature importance**.

These values explain what the model relies on; they should not be interpreted as causal drivers of conversion.

---

## How the Agent Works

The model and agent have different responsibilities.

### Model

The model answers:

> **"Which accounts should receive more attention?"**

It scores and ranks the accounts.

### Agent

The agent answers:

> **"Given that this account is important, what should the sales representative do next?"**

For a high-priority account, the agent can decide what additional context it needs.

For example:

**CRM history may show:**

* Recent contact
* Previous response
* Existing opportunity
* Former customer relationship

**External context may show:**

* Company expansion
* Hiring activity
* Other relevant business signals

The agent evaluates the evidence and chooses the next action.

It does not have to call every tool for every account. If the available evidence is already sufficient, it can act. If evidence is weak or conflicting, it can gather additional context.

---

## What Happens When the System Is Wrong?

There are four important outcomes:

| Model decision                | Business outcome                         |
| ----------------------------- | ---------------------------------------- |
| High priority + converts      | Sales capacity was well spent            |
| High priority + no conversion | Outreach capacity was potentially wasted |
| Low priority + converts       | Potential opportunity was missed         |
| Low priority + no conversion  | Deprioritization was appropriate         |

This is why model accuracy alone is not enough.

The system should ultimately be evaluated on **sales outcomes per unit of outreach capacity**.

---

## Monitoring

Monitoring is designed to catch both model degradation and operational failures.

### Model monitoring

Track:

* Prediction distribution
* Feature missingness
* Population/feature drift
* Score-bucket performance
* Calibration
* Actual 90-day conversion and lift

The prototype includes a prediction-distribution check. A significant shift from the current **6.55% baseline mean** raises an `INVESTIGATE` alert.

An alert does not automatically mean the model is broken. The team should first check data quality, population changes, and newly available outcomes.

### Agent monitoring

Track:

* Agent success/failure
* Tool failures
* Tool latency
* Number of tool calls
* LLM failures
* Salesforce execution failures

A healthy model is not enough if the agent cannot reliably execute its work.

### Business monitoring

Once outcomes become available, measure:

* Responses
* Meetings
* Opportunities
* Conversions
* Productive sales activity

These should be compared across score ranges and recommended actions.

---

## Implementation

The prototype uses **lightweight Python with a tool-based agent loop**.

The ML scoring and ranking remain deterministic. The agentic behavior starts after prioritization, where the agent decides what context it needs and what action to recommend.

The prototype uses mocked LLM/tool integrations so it can run without external credentials. In production, these interfaces can connect to the actual CRM, external data sources, and Salesforce using native LLM tool/function calling.

I intentionally did not introduce LangGraph because the current use case has limited tools and branching. A more complex implementation could introduce it later if persistent state, human approval, or complex retries become necessary.

---

## Assumptions and Next Steps

The initial solution assumes:

* Sales capacity can support a 20% high-priority queue.
* CRM and external context are available.
* Salesforce actions can be executed reliably.
* Actual conversion outcomes will become available for validation.

The most important next step is to **measure what happens after representatives act on these recommendations**.

If the top-ranked accounts consistently produce better sales outcomes, the approach is working. If not, investigate whether the issue comes from the model, data, agent decisions, or sales execution.

**The objective is not to build another scoring dashboard. It is to turn model predictions into better sales decisions and measurable sales outcomes.**
