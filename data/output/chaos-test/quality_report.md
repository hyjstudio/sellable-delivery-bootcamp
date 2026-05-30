# Data Quality Report

## Summary
- Input rows: 10
- Kept rows: 8
- Invalid rows: 2
- Invalid row ratio: 20.00%
- Dropped duplicate rows: 0
- Negative amount rows: 0

## File Quality Details
| File | Input Rows | Kept Rows | Invalid Rows | Invalid Date | Invalid Amount | Negative Amount | Duplicate Order IDs | Duplicate Order Rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| sample_sales.csv | 10 | 8 | 2 | 0 | 2 | 0 | 0 | 0.00% |

### 错误样例行：sample_sales.csv
| Row | Date | Order ID | Amount | Reasons |
| --- | --- | --- | --- | --- |
| 6 | 2026-05-23 | ORD-1005 | None | invalid_amount |
| 10 | 2026-05-26 | ORD-1009 | None | invalid_amount |
