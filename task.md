# Task List - Optimasi Laporan Monitoring Saldo Subkontrak

- `[x]` Update backend `monitoring_saldo_subkontrak.py`
  - `[x]` Add vendor/partner filter logic matching `tabENTITAS`
  - `[x]` Replace `LIMIT 1` query with `SUM` aggregation to support partial subcontract returns
- `[x]` Update frontend `monitoring_saldo_subkontrak.js`
  - `[x]` Implement rich CSS-styled visual formatter for `status` column
  - `[x]` Implement dynamic color coloring for `aging` column
- `[x]` Verify changes and create walkthrough
