# Robot Review Bot — Test Report

## 1. Case Selection

### Issue Dataset (`issues.csv`)

Issues are collected from `triton-lang/triton-ascend` via the GitHub API using
**state-based stratified sampling** to ensure balanced representation:

| State | Target | Collected | Meaning |
| ----- | ------ | --------- | ------- |
| `open` | 35 | 35 | Still open |
| `solved` | 35 | 13 | Closed with `state_reason: completed` |
| `closed` | 30 | 3 | Closed with `state_reason: not_planned` or null |

**Total: 51 issues** (actual closed/solved counts limited by repo history —
triton-ascend is a relatively young fork with fewer resolved issues).

Prefix distribution:

| Prefix | Count |
| ------ | ----- |
| `[Misc]` | 32 |
| `[Feature]` | 5 |
| `[ssbuffer]` | 4 |
| `[Doc]` | 3 |
| `[Performance]` | 1 |
| `[Bug]` | 1 |
| Others (`[Feature request]`, `[Docs]`, `[Feat]`, `[SSBUFER]`, `[packaging]`) | 1 each |

Note: The heavy skew toward `[Misc]` reflects that triton-ascend does not
enforce the `[Bug]:` / `[Feature]:` prefix convention on issue titles, unlike
vllm-ascend. Most issues use free-form titles.

### PR Dataset (`prs.csv`)

PRs collected via time-based stratified sampling across 400 PRs (4 pages of 100):

| Stratum | Pool | Picked |
| ------- | ---- | ------ |
| Newest 100 (indices 0–99) | 100 | 40 |
| Next 100 (indices 100–199) | 100 | 10 |
| Older 200 (indices 200–399) | 200 | 10 |

**Total: 60 PRs** across all states:

| State | Count |
| ----- | ----- |
| `merged` | 28 |
| `open` | 21 |
| `closed` | 4 |

Prefix distribution (top 10):

| Prefix | Count |
| ------ | ----- |
| `[ssbuffer]` | 15 |
| `[Misc]` | 10 |
| `[docs]` | 6 |
| `[CI]` | 6 |
| `[Docs]` | 5 |
| `[TritonToLinalg]` | 2 |
| `[API]` | 2 |
| Others (14 unique prefixes) | 1 each |

---

## 2. Evaluation Process (GitHub Actions Pipeline)

Each case is evaluated using the **same pipeline** as the production
`bot_issue_review.yaml` and `bot_pr_review.yaml` workflows:

```text
Title + Body → System Prompt → LLM (deepseek-v4-flash) → JSON Result
     │              │                                          │
     │    ┌────────┘                                   ┌──────┘
     ▼    ▼                                            ▼
  Load issue/PR template,         Parse JSON into:
  type key from prefix_map.py     ┌───────────────┐
                                  │ ok: true/false│
                                  │ score: 0-100  │
                                  │ reasoning     │
                                  │ missing_items │
                                  │ suggestions   │
                                  └───────────────┘
```

The LLM produces a structured JSON assessment with:

- `ok` — whether the description is sufficient (true) or insufficient (false)
- `score` — quality score 0–100
- `reasoning` — explanation of the judgment
- `missing_items` — what required fields are missing
- `suggestions` — actionable improvement suggestions

Results are stored in `deepseek_v4_flash_output` (raw) and
`expected_ok_dsv4` (parsed boolean).

---

## 3. Judgment Process

Each evaluation is then judged by the same LLM with a dedicated **judge system
prompt** that audits the evaluation across four dimensions:

| Dimension | Question |
| --------- | -------- |
| `ok_reasonable` | Is the ok=true/false judgment consistent with the actual content quality? |
| `reasoning_valid` | Is the reasoning self-consistent with the ok/score decision? |
| `suggestions_valid` | Are suggestions specific, actionable, and free of mandatory language? |
| `missing_items` accuracy | Do listed missing items genuinely correspond to missing required information? |

Judge output stored in columns: `judge_raw_output`, `ok_reasonable`,
`reasoning_valid`, `suggestions_valid`, `judge_reasoning`.

Rows with malformed or truncated evaluation output (7 rows total across both
datasets) were regenerated via `--retry-errors` before judging to ensure clean
input data. A few edge cases (empty LLM output) remain unresolvable and were
excluded from judge analysis.

---

## 4. Results Summary

### Issue Evaluation Accuracy

| Metric | Value |
| ------ | ----- |
| Cases evaluated | 48 |
| Evaluated ok=true | 44 |
| Evaluated ok=false | 4 |
| Average score | 83.8 |
| Cases judged | 46 (2 had no evaluation output) |

### Issue Judge Results

| | Count |
| --- | --- |
| ok_reasonable=true | 45 |
| ok_reasonable=false | 1 |

| | Count |
| --- | --- |
| reasoning_valid=true | 45 |
| reasoning_valid=false | 1 |

| | Count |
| --- | --- |
| suggestions_valid=true | 45 |
| suggestions_valid=false | 1 |

**Confusion matrix (judge vs eval):**

| | Judge: reasonable | Judge: not reasonable |
| --- | --- | --- |
| **Eval: ok=true** | TN=41 | FP=1 |
| **Eval: ok=false** | TP=4 | FN=0 |

- **Accuracy**: 97.8%
- **Precision**: 80.0%
- **Recall**: 100.0%

Precision is lower due to the single false positive (see below). With only 4
ok=false evaluations in the dataset, a single misjudgment has a disproportionate
impact on precision.

#### False Positives (eval said ok but judge disagreed)

| # | Title | Issue |
| - | ----- | ----- |
| 6 | Tracking of Items for out-of-tree approval | Eval marked ok=true (score 70) but the description is a tracking issue with minimal actionable detail — the judge found ok=true unreasonable for a tracking/stub issue |

### PR Evaluation Accuracy

| Metric | Value |
| ------ | ----- |
| Cases evaluated | 53 |
| Evaluated ok=true | 24 |
| Evaluated ok=false | 29 |
| Average score | 56.5 |
| Cases judged | 52 (1 had no evaluation output) |

The lower average score (56.5 vs 83.8 for issues) reflects the nature of PR
descriptions in this repo: many are terse technical fixes (ssbuffer, CI) that
provide code changes but minimal prose description, causing the bot to flag them
as insufficient.

### PR Judge Results

| | Count |
| --- | --- |
| ok_reasonable=true | 52 |
| ok_reasonable=false | 0 |
| reasoning_valid=true | 52 |
| suggestions_valid=true | 52 |

**Confusion matrix:**

| | Judge: reasonable | Judge: not reasonable |
| --- | --- | --- |
| **Eval: ok=true** | TN=23 | FP=0 |
| **Eval: ok=false** | TP=29 | FN=0 |

- **Accuracy**: 100.0%
- **Precision**: 100.0%
- **Recall**: 100.0%

Perfect agreement on PR evaluations — zero false positives, zero false
negatives. The judge consistently agreed that the bot's ok=false flags for
terse PR descriptions were justified.

---

## Conclusion

The review bot pipeline achieves **97.8–100% accuracy** on description
completeness judgments for triton-lang/triton-ascend. The LLM evaluation is
reliable:

- **Issues**: 1 false positive out of 46 judged (2.2%) — a tracking/stub issue
  with minimal content that the bot optimistically marked as sufficient.
- **PRs**: Perfect agreement — all 52 judged evaluations matched the judge's
  assessment with no false positives or false negatives.
- Reasoning and suggestions are valid in **97.8–100%** of cases.

The bot correctly identifies that most triton-ascend PRs have sparse
descriptions (24 true / 29 false for ok) — many are ssbuffer/compiler fixes
with minimal prose. The judge confirms these flags are reasonable: maintainers
would benefit from more detailed PR descriptions for non-trivial changes.

Compared to the vllm-ascend baseline (93–98% accuracy), the triton-ascend
results are comparable or better, though the smaller and less-prefix-structured
issue dataset means precision metrics are sensitive to individual edge cases.
