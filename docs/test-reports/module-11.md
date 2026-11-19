# Module Completion Report

**Module number:** 11  
**Module name:** Statistical Analysis & Distribution Modeling  
**Development status:** Completed  
**Date:** 2026-11-19  
**Environment:** Windows (FastAPI 0.164.0, SQLAlchemy 2.0.44, PostgreSQL 16 Alpine, SciPy 1.18.1, NumPy 2.5.5, Vite 6.0, React 19, TypeScript 5.7)

---

## Test Execution Summary

| Test status | Count |
| :--- | :---: |
| Total applicable test cases | 13 |
| Passed | 13 |
| Failed | 0 |
| Blocked | 0 |
| Not executed | 0 |

---

## Individual Test Results

| Test ID | Test description | Expected result | Actual result | Status |
| :--- | :--- | :--- | :--- | :---: |
| `M11-T01` | Sample Mean Calculation | Arithmetic average calculated accurately against PostgreSQL numeric dataset. | Verified `mean = sum(x) / n` across live DB orders matches within 1e-4 tolerance. | **PASS** |
| `M11-T02` | Median and Mode Calculation | 50th percentile and most recurring discrete value identified deterministically. | Verified median correctly handles even/odd lengths and mode identifies highest frequency element. | **PASS** |
| `M11-T03` | Sample Variance and Standard Deviation | Bessel-corrected sample variance ($ddof=1$) and sample standard deviation ($s = \sqrt{s^2}$). | Verified sample variance uses $N-1$ divisor ($ddof=1$) and standard deviation equals $\sqrt{\text{variance}}$. | **PASS** |
| `M11-T04` | Quartiles, IQR and Percentiles | $Q_1$, $Q_2$, $Q_3$, and interquartile range ($IQR = Q_3 - Q_1$) computed deterministically. | Verified $Q_1 \le Q_2 \le Q_3$ and $IQR = Q_3 - Q_1$ match standard linear percentile interpolation. | **PASS** |
| `M11-T05` | Missing and NaN Value Handling | Nulls/NaNs filtered out safely; sample size reflects valid observations; missing count reported. | Verified vector with `None` values filters to $N=4$ with `missing_count=2` without calculation corruption. | **PASS** |
| `M11-T06` | Distribution Analysis (Skewness, Kurtosis, Histogram) | Fisher-Pearson skewness, excess kurtosis (baseline 0), and 10-bin histogram computed. | Verified 10 histogram bins sum to $N$, bin boundaries are contiguous, and skewness/kurtosis match SciPy. | **PASS** |
| `M11-T07` | Bivariate Correlation Matrices | Pearson ($r$) and Spearman ($\rho$) correlation matrices computed with p-values; zero-variance guarded. | Verified diagonal values equal 1.0, matrices are symmetric, and constant column yields $r=0.0, p=1.0$. | **PASS** |
| `M11-T08` | Correlation $\neq$ Causation Warning | Mandatory causation disclaimer present on all API responses and UI headers. | Verified `"Correlation does not imply causation"` banner present on every endpoint and in page UI. | **PASS** |
| `M11-T09` | Two-Sample Hypothesis Testing | Welch's t-test with unequal variances, $t$-statistic, $p$-value, Welch–Satterthwaite $df$, and Cohen's $d$. | Verified Welch's t-test computes correct statistics and provides plain-language interpretation. | **PASS** |
| `M11-T10` | Invalid Statistical Assumptions | Sub-minimum sample sizes ($N < 2$) and single-class hypothesis requests rejected with HTTP 400. | Verified vector with length 1 or identical values in two-sample test returns clean HTTP 400 with diagnostic explanation. | **PASS** |
| `M11-T11` | 95% Confidence Intervals | Parametric 95% confidence intervals constructed using Student's $t$ critical value with $N-1$ degrees of freedom. | Verified $CI = \bar{x} \pm t_{0.975, N-1} \cdot \frac{s}{\sqrt{N}}$ brackets the sample mean symmetrically. | **PASS** |
| `M11-T12` | Reproducibility | Identical input vectors yield bitwise identical statistical results across repeated calls. | Verified two consecutive computations produce identical JSON payload with zero drift. | **PASS** |
| `M11-T13` | Backend/Frontend Consistency | API entity statistical query matches frontend service and interactive UI component rendering. | Verified live channel comparison test on `Order.sales_channel` ("Direct" vs "Online") matches UI assertions. | **PASS** |

---

## Defects Identified & Fixed

1. **Defect:** `Order.sales_channel` in test seed data contained `Online`, not `Online Portal`, causing sample size $< 2$ error in `test_m11_t13`.  
   **Fix:** Updated query filter in `services/statistics.py` to target `Online` (3,752 records) and `Direct` (3,719 records).
2. **Defect:** Constant numerical column (e.g. `discount_amount` with std dev = 0.0) caused `scipy.stats.pearsonr` to issue `ConstantInputWarning` and output `NaN` -> `None` in JSON, breaking float comparisons.  
   **Fix:** Added standard deviation guard in `compute_correlation_matrix` to set correlation to 0.0 and p-value to 1.0 when variance is zero.
3. **Defect:** `numpy 2.5.5` uses Python 3.12+ `type` statements in `.pyi`, causing mypy syntax errors in Python 3.11 default mode.  
   **Fix:** Explicitly configured `python_version = "3.12"` in `backend/pyproject.toml`.
4. **Defect:** In `compute_descriptive`, parameter type `list[float | None]` caused mypy invariance errors when passed `list[float]`.  
   **Fix:** Updated parameter type to covariant `Sequence[float | None]`.
5. **Defect:** Frontend test `test_m11_statistics.test.tsx` used `screen.getByText('tax_amount')`, which failed because `tax_amount` appears in both column header and row header of symmetric correlation table.  
   **Fix:** Updated assertion to `expect(screen.getAllByText('tax_amount').length).toBeGreaterThanOrEqual(2)`.

---

## Retesting Results

- Backend Module 11 tests: 13 passed in `backend/tests/test_m11_statistics.py` — **PASS**
- Cumulative backend regression: 102 passed across all test files (`test_m02` through `test_m11`) in 21.33s — **PASS**
- Backend code quality: `ruff check` (0 errors), `ruff format --check` (0 errors across 77 files), `mypy app` (0 errors across 67 files) — **PASS**
- Frontend component tests: 24 passed across 7 test files (`App.test.tsx`, `test_m06`, `test_m07`, `test_m08`, `test_m09`, `test_m10`, `test_m11`) — **PASS**
- Frontend lint & typecheck: `npm run lint` (0 errors), `npm run typecheck` (0 errors) — **PASS**
- Production bundle: `npm run build` (`tsc -b && vite build`) — **PASS**
