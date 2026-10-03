# Auth / Dashboard v2.5 Historical Delivery Archive

The recovered `AxProtocol.zip` contains a cluster of v2.5 auth/dashboard delivery documents. They are preserved here as an **inventory of historical project material**, not as current verified production claims.

Several of the documents repeatedly describe the code as `PRODUCTION HARDENED`, `PRODUCTION READY`, `enterprise-grade`, or attach speculative ROI/business-value figures. Those phrases reflect how the work was being presented at the time. The 2026 repository reconciliation does not independently validate those claims and therefore does not repeat them as current facts in the canonical README.

The source code that those documents discuss (`auth.py`, `dashboard.py`) is present in the repository, and the most useful executive summary from the ZIP is preserved alongside this index as `EXECUTIVE_SUMMARY.md`.

## Files present in the recovered ZIP

| Historical file | Size | Main subject |
|---|---:|---|
| `AUTH_V2.5_DOCUMENTATION.md` | 24,822 B | Detailed auth/security upgrade notes: secret enforcement, JWT claims/refresh rotation, UTC handling, DB rate limiting, bearer tokens, constant-time API-key comparison, and threat rules |
| `QUICK_START.md` | 6,097 B | Auth v2.5 deployment/test quick-start |
| `DELIVERY_SUMMARY.md` | 10,593 B | Auth v2.5 delivery summary and before/after claims |
| `DASHBOARD_V2.5_DOCUMENTATION.md` | 20,522 B | Dashboard changes: Kaleido handling, dead-code cleanup, chunked CSV loading, missing-column/no-data handling |
| `DASHBOARD_QUICK_START.md` | 6,383 B | Dashboard v2.5 deployment/test quick-start |
| `DASHBOARD_DELIVERY.md` | 8,896 B | Dashboard delivery summary and performance/value claims |
| `MASTER_DELIVERY.md` | 9,932 B | Combined auth + dashboard delivery narrative |
| `EXECUTIVE_SUMMARY.md` | 3,323 B | Compact combined summary; restored verbatim from the ZIP |

## Why the long delivery documents were not promoted into canonical docs

The objective of the reconciliation is to make the repository a better and more accurate explanation of the project, not to preserve every duplicated generated sentence at equal prominence.

These files are heavily overlapping delivery collateral. Their useful technical subjects are represented by the actual source, the restored executive summary, the current README, and the reconciliation/history documents. Keeping this inventory preserves the historical record that the documents existed while avoiding a large block of repeated assertions that could be mistaken for current verification.

The original archive is identified permanently by SHA-256 in [`../ZIP_RECONCILIATION_2026-10-03.md`](../ZIP_RECONCILIATION_2026-10-03.md), so this editorial decision is explicit rather than silent data loss.
