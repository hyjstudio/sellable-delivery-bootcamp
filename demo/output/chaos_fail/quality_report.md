# Data Quality Report

## Summary
- Input rows: 8
- Kept rows: 7
- Invalid rows: 1
- Invalid row ratio: 12.50%
- Dropped duplicate rows: 0
- Negative amount rows: 1

## File Quality Details
| File | Input Rows | Kept Rows | Invalid Rows | Invalid Date | Invalid Amount | Negative Amount | Duplicate Order IDs | Duplicate Order Rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| sample_chaos_sales.csv | 8 | 7 | 1 | 0 | 1 | 1 | 0 | 0.00% |

### 错误样例行：sample_chaos_sales.csv
| Row | Date | Order ID | Amount | Reasons |
| --- | --- | --- | --- | --- |
| 5 | 2026-05-23 | ORD-3003 | None | invalid_amount |
