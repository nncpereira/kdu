# KDU API Contract — v1

**Base URL:** `/api/v1/`
**Auth:** JWT Bearer (except where noted)
**Content-Type:** `application/json`
**Charset:** UTF-8

---

## Global conventions

### Authentication
All endpoints require `Authorization: Bearer <access_token>` unless marked **Public**.
Access tokens expire in **15 minutes**. Refresh with `POST /auth/token/refresh/`.

### Error format
Every error response uses this shape:

```json
{
  "detail": "Human-readable message",
  "code": "MACHINE_READABLE_CODE"
}
```

Validation errors may include a `fields` object:

```json
{
  "detail": "Validation failed",
  "fields": { "amount": ["This field is required."] }
}
```

### HTTP status codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 204 | Deleted / no content |
| 400 | Validation error / domain error |
| 401 | Missing or invalid token |
| 403 | Authenticated but wrong role |
| 404 | Resource not found |
| 409 | Conflict (e.g., concurrent withdrawal) |
| 500 | Server error |

### Pagination
List endpoints accept `?page=1&page_size=50` (max 200).
Response shape:

```json
{
  "count": 128,
  "next": "http://host/api/v1/members/?page=2",
  "previous": null,
  "results": [ ... ]
}
```

### Money
All monetary amounts are strings with exactly 2 decimal places:
`"1000.00"`, `"0.01"`, `"-50.00"`.

### Dates
ISO 8601: `"2026-06-30"`. Timestamps are UTC ISO 8601.

---

## Role matrix

| Role | Capabilities |
|------|--------------|
| **MAKER** | Create/initiate financial mutations |
| **CHECKER** | Review & approve Maker's submissions; read-only reports |
| **CERTIFIER** | Final approval; triggers ledger posting |
| **SUPERADMIN** | Configure system, trigger jobs, all read access |
| **MEMBER** | Read own profile, savings, loans, SHU statement |
| **BOARD** | Read-only access to everything |
| **AUDITOR** | Read-only, PII masked unless case reference |

Any financial mutation **requires the full Maker → Checker → Certifier pipeline**.
No user may perform more than one role on the same transaction.

---

## 1. Authentication

### POST `/api/v1/auth/token/` — Public
Obtain a JWT pair.

**Request:**
```json
{ "username": "maker1", "password": "changeme123" }
```

**Response 200:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Errors:** `401 INVALID_CREDENTIALS`

---

### POST `/api/v1/auth/token/refresh/` — Public
Refresh an access token.

**Request:**
```json
{ "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..." }
```

**Response 200:**
```json
{ "access": "eyJ0eXAiOiJKV1QiLCJhbGc..." }
```

---

### POST `/api/v1/auth/token/verify/` — Public
Verify a token.

**Request:**
```json
{ "token": "eyJ0eXAiOiJKV1QiLCJhbGc..." }
```

**Response 200:** `{}`

---

## 2. Users

### GET `/api/v1/users/me/`
Return the current user's profile.

**Response 200:**
```json
{
  "id": "f3e1b2a4-...-9c8d",
  "username": "maker1",
  "email": "maker@example.com",
  "role": "MAKER",
  "must_change_password": false,
  "created_at": "2026-01-15T08:00:00Z"
}
```

---

### POST `/api/v1/users/me/change-password/`
Change the current user's password.

**Request:**
```json
{
  "old_password": "changeme123",
  "new_password": "MyNewPassword!2026"
}
```

**Response 200:**
```json
{ "detail": "Password updated." }
```

**Errors:**
- `400 OLD_PASSWORD_INCORRECT`
- `400 PASSWORD_TOO_SHORT`

---

## 3. Members

### GET `/api/v1/members/` — BOARD, CHECKER, SUPERADMIN
List members. Query params:
- `?status=Active` filter by status
- `?page=1&page_size=50`

**Response 200:**
```json
{
  "count": 3,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "11111111-...-111111111111",
      "membership_number": "KDU-000001",
      "salutation": "Ms",
      "first_name": "Maria",
      "middle_name": "",
      "last_name": "Test",
      "full_name": "Maria Test",
      "national_id": "N1",
      "phone_number": "77000001",
      "email": "maria@example.com",
      "date_of_birth": "1990-05-10",
      "aldeia": "A1", "suco": "S1", "posto": "P1", "municipio": "Dili",
      "profession": "Vendor",
      "status": "Active",
      "kapital_sosial_balance": "70.00",
      "date_joined": "2024-05-10",
      "last_transaction_at": "2026-06-15",
      "created_at": "2024-05-10T08:00:00Z"
    }
  ]
}
```

---

### POST `/api/v1/members/` — MAKER
Onboard a new member. Creates a PENDING member with `kapital_sosial_balance = 0`.

**Request:**
```json
{
  "first_name": "João",
  "middle_name": "",
  "last_name": "Silva",
  "salutation": "Mr",
  "national_id": "N999",
  "phone_number": "77000123",
  "email": "joao@example.com",
  "date_of_birth": "1985-03-20",
  "aldeia": "A", "suco": "S", "posto": "P", "municipio": "Dili",
  "profession": "Farmer"
}
```

**Response 201:** the created member object.

**Errors:** `400 VALIDATION_ERROR`

---

### GET `/api/v1/members/{id}/` — BOARD, CHECKER, SUPERADMIN
Member detail. Same shape as list item.

---

### POST `/api/v1/members/{id}/initial-capital/` — MAKER
Pay initial capital for a PENDING member. Enforces the $50 minimum (DL 76/2022).

**Request:**
```json
{ "amount": "50.00" }
```

**Response 201:**
```json
{
  "onboarding_id": "aaaa-bbbb-cccc",
  "pipeline_actor_id": "dddd-eeee-ffff"
}
```

**Errors:**
- `400 MIN_CAPITAL_50_USD_REQUIRED`
- `400 MEMBER_NOT_PENDING`

---

### POST `/api/v1/members/{id}/exit/` — MAKER
Request member exit (refund of capital). Blocked if outstanding loans.

**Request:**
```json
{ "reason": "relocation" }
```

**Response 201:**
```json
{
  "exit_request_id": "aaaa-bbbb-cccc",
  "pipeline_actor_id": "dddd-eeee-ffff"
}
```

**Errors:**
- `400 MEMBER_HAS_OUTSTANDING_OBLIGATIONS`
- `400 MEMBER_NO_CAPITAL`

---

## 4. Savings

### POST `/api/v1/savings/deposit/` — MAKER
Record a cash deposit. Splits into obligatory (up to monthly cap) + voluntary.

**Request:**
```json
{ "member": "11111111-...-111111111111", "amount": "1000.00" }
```

**Response 201:**
```json
{
  "id": "aaaa-bbbb-cccc",
  "member": "11111111-...-111111111111",
  "member_number": "KDU-000001",
  "transaction_type": "DEPOSIT",
  "requested_amount": "1000.00",
  "obligatory_portion": "20.00",
  "voluntary_portion": "980.00",
  "status": "PENDING_CHECK",
  "pipeline_actor": "pppp-qqqq-rrrr",
  "journal_entry": "jjjj-kkkk-llll",
  "created_at": "2026-06-15T10:00:00Z"
}
```

---

### POST `/api/v1/savings/withdraw/` — MAKER
Withdraw from voluntary deposits. Places an escrow hold immediately.

**Request:**
```json
{ "member": "11111111-...", "amount": "200.00" }
```

**Response 201:** same shape as deposit, `transaction_type: "WITHDRAWAL"`.

**Errors:**
- `400 INSUFFICIENT_VOLUNTARY_BALANCE`
- `409 PIPELINE_HOLD_ACTIVE` (if available balance is already held)

---

### GET `/api/v1/savings/transactions/` — BOARD, CHECKER, SUPERADMIN
List savings transactions. Query:
- `?member=<uuid>`
- `?type=DEPOSIT|WITHDRAWAL`
- `?page=1&page_size=50`

**Response 200:** paginated list of transaction objects.

---

### GET `/api/v1/savings/members/{member_id}/voluntary/` — BOARD, CHECKER, SUPERADMIN
Get a member's voluntary deposit balance.

**Response 200:**
```json
{
  "member": "11111111-...",
  "balance_available": "780.00",
  "balance_held_pipeline": "0.00",
  "updated_at": "2026-06-15T10:05:00Z"
}
```

---

## 5. Loans

### GET `/api/v1/loans/` — BOARD, CHECKER, SUPERADMIN
List loans. Query: `?member=<uuid>&status=DISBURSED`.

**Response 200:**
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "llll-1111-2222",
      "member": "11111111-...",
      "member_number": "KDU-000001",
      "principal_original": "9000.00",
      "principal_outstanding": "8300.00",
      "monthly_rate": "0.0200",
      "term_months": 12,
      "purpose": "working capital",
      "disbursed_date": "2026-06-01",
      "status": "DISBURSED",
      "created_at": "2026-06-01T08:00:00Z"
    }
  ]
}
```

---

### POST `/api/v1/loans/` — MAKER
Originate a loan (DRAFT, awaiting pipeline approval).

**Request:**
```json
{
  "member": "11111111-...",
  "principal": "9000.00",
  "term_months": 12,
  "monthly_rate": "0.0200",
  "purpose": "working capital"
}
```

**Response 201:** loan object.

**Errors:**
- `400 RATE_OUTSIDE_APPROVED_RANGE`
- `400 MEMBER_NOT_ACTIVE`

---

### GET `/api/v1/loans/{id}/` — BOARD, CHECKER, SUPERADMIN
Loan detail. Same shape as list item.

---

### POST `/api/v1/loans/{id}/repay/manual/` — MAKER
Record a variable manual repayment (for irregular income). No automated interest check.

**Request:**
```json
{
  "principal_paid": "500.00",
  "interest_paid": "90.00",
  "payment_date": "2026-07-15"
}
```

**Response 201:**
```json
{
  "id": "rrrr-1111-2222",
  "loan": "llll-1111-2222",
  "principal_paid": "500.00",
  "interest_paid": "90.00",
  "payment_date": "2026-07-15",
  "mode": "MANUAL",
  "status": "PENDING_CHECK",
  "created_at": "2026-07-15T10:00:00Z"
}
```

**Errors:** `400 AMOUNTS_ZERO`, `400 PRINCIPAL_EXCEEDS_OUTSTANDING`

---

### POST `/api/v1/loans/{id}/repay/scheduled/` — MAKER
Scheduled installment with waterfall (interest → principal → obligatory → voluntary).

**Request:**
```json
{
  "cash_amount": "1000.00",
  "scheduled_principal": "700.00",
  "payment_date": "2026-07-15"
}
```

**Response 201:** repayment object.

**Errors:**
- `400 INSUFFICIENT_FOR_INTEREST_DUE`

---

### GET `/api/v1/loans/{id}/repayments/` — BOARD, CHECKER, SUPERADMIN
List repayment history for a loan.

---

## 6. Expenses

### GET `/api/v1/expenses/` — BOARD, CHECKER, SUPERADMIN
List expenses. Query: `?expense_account_code=5101`.

---

### POST `/api/v1/expenses/` — MAKER
Record an expense.

**Request:**
```json
{
  "description": "AGM venue",
  "amount": "500.00",
  "expense_account_code": "5101",
  "payment_date": "2026-06-30"
}
```

**Response 201:** expense object.

**Errors:**
- `400 ACCOUNT_NOT_FOUND`
- `400 NOT_AN_EXPENSE_ACCOUNT`

---

### GET `/api/v1/expenses/{id}/` — BOARD, CHECKER, SUPERADMIN
Expense detail.

---

## 7. SHU (Sisa Hasil Usaha)

### POST `/api/v1/shu/calculate/` — MAKER
Run SHU calculation for a fiscal year. Creates a `PENDING_CHECK` calculation.

**Request:**
```json
{ "fy_id": "ffff-1111-2222" }
```

**Response 201:**
```json
{
  "id": "cccc-3333-4444",
  "fy": "ffff-1111-2222",
  "net_surplus": "130461.20",
  "reserva_legal_pct": "10.00",
  "admin_fund_pct": "30.00",
  "jasa_simpanan_pct": "25.00",
  "jasa_bunga_pct": "35.00",
  "reserva_legal_amt": "13046.12",
  "admin_fund_amt": "39138.36",
  "jasa_simpanan_amt": "32615.30",
  "jasa_bunga_amt": "45661.42",
  "status": "PENDING_CHECK",
  "created_at": "2026-07-01T08:00:00Z"
}
```

**Errors:**
- `400 FY_NOT_OPEN`
- `400 ACTIVE_CALCULATION_EXISTS`
- `400 NO_ACTIVE_SHU_SPLIT`
- `400 RESERVA_LEGAL_VIOLATION`

---

### GET `/api/v1/shu/{calc_id}/` — BOARD, CHECKER, SUPERADMIN
Calculation detail. Same shape as create response.

---

### GET `/api/v1/shu/{calc_id}/payouts/` — BOARD, CHECKER, SUPERADMIN
List per-member payouts.

**Response 200:**
```json
[
  {
    "id": "pppp-5555-6666",
    "member": "11111111-...",
    "member_number": "KDU-000001",
    "full_name": "Maria Test",
    "jasa_simpanan_gross": "20352.35",
    "jasa_bunga_gross": "608.82",
    "net_payout": "20961.17",
    "status": "DRAFT"
  }
]
```

---

### POST `/api/v1/shu/snapshot/` — SUPERADMIN
Trigger a monthly snapshot manually (otherwise runs on the last day of each month).

**Response 200:**
```json
{ "rows_created": 155 }
```

---

### POST `/api/v1/shu/aggregate/` — SUPERADMIN
Trigger annual aggregation for a fiscal year.

**Request:**
```json
{ "fy_id": "ffff-1111-2222" }
```

**Response 200:**
```json
{ "rows_created": 155 }
```

---

## 8. Governance

### GET `/api/v1/governance/config/` — BOARD, CHECKER, SUPERADMIN
List active configuration values.

**Response 200:**
```json
[
  {
    "id": "gggg-1111",
    "parameter_key": "shu_split",
    "parameter_value": {
      "reserva_legal_pct": 10,
      "admin_fund_pct": 30,
      "jasa_simpanan_pct": 25,
      "jasa_bunga_pct": 35
    },
    "effective_from": "2025-01-01",
    "status": "ACTIVE"
  }
]
```

---

### POST `/api/v1/governance/config/propose/` — MAKER
Propose a config change. Creates a `PENDING_CHECK` change.

**Request:**
```json
{
  "parameter_key": "obligatory_savings_monthly_cap",
  "proposed_value": { "value": 25 },
  "effective_from": "2027-01-01"
}
```

**Response 201:** change object.

**Errors:**
- `400 UNKNOWN_PARAMETER`
- `400 LEGAL_RESERVE_VIOLATION` (for `shu_split`)
- `400 PERCENTAGES_NOT_100`

---

### POST `/api/v1/governance/config/certify/{change_id}/` — CERTIFIER
Certify a proposed change. Writes it to `global_config`.

**Response 200:** certified change object.

**Errors:** `400 CHANGE_NOT_PENDING_CERTIFY`

---

### GET `/api/v1/governance/changes/` — BOARD, CHECKER, SUPERADMIN
List all config changes (history).

---

## 9. Reports

### GET `/api/v1/reports/trial-balance/?as_of=2026-06-30` — BOARD, CHECKER, SUPERADMIN

**Response 200:**
```json
[
  {
    "account_code": "1001",
    "account_name": "Cash on Hand",
    "account_type": "ASSET",
    "debit": "15000.00",
    "credit": "2000.00",
    "net": "13000.00"
  }
]
```

---

### GET `/api/v1/reports/income-statement/?start=2025-07-01&end=2026-06-30` — BOARD, CHECKER, SUPERADMIN

**Response 200:**
```json
{
  "revenue": [ ... ],
  "expenses": [ ... ],
  "total_revenue": "45661.42",
  "total_expenses": "1200.00",
  "net_surplus": "44461.42"
}
```

---

### GET `/api/v1/reports/balance-sheet/?as_of=2026-06-30` — BOARD, CHECKER, SUPERADMIN

**Response 200:**
```json
{
  "assets": [ ... ],
  "liabilities": [ ... ],
  "equity": [ ... ],
  "total_assets": "13000.00",
  "total_liabilities": "980.00",
  "total_equity": "12020.00",
  "balanced": true
}
```

---

### GET `/api/v1/reports/surplus-distribution/{fy_id}/` — BOARD, CHECKER, SUPERADMIN

**Response 200:**
```json
{
  "reserva_legal_amt": "13046.12",
  "admin_fund_amt": "39138.36",
  "jasa_simpanan_amt": "32615.30",
  "jasa_bunga_amt": "45661.42",
  "status": "PAYOUT_COMPLETE"
}
```

---

## 10. Pipeline

### GET `/api/v1/pipeline/pending-check/` — CHECKER
List pipeline actors awaiting the Checker's approval.

**Response 200:**
```json
[
  {
    "id": "pppp-1111",
    "transaction_type": "DEPOSIT",
    "target_record_id": "aaaa-bbbb-cccc",
    "maker": "mmmm-1111",
    "maker_username": "maker1",
    "checker": null,
    "checker_username": null,
    "certifier": null,
    "certifier_username": null,
    "status": "PENDING_CHECK",
    "updated_at": "2026-06-15T10:00:00Z"
  }
]
```

---

### GET `/api/v1/pipeline/pending-certify/` — CERTIFIER
Same shape, `status: "PENDING_CERTIFY"`.

---

### POST `/api/v1/pipeline/{actor_id}/check/` — CHECKER
Approve at the Checker stage.

**Response 200:**
```json
{ "id": "pppp-1111", "status": "PENDING_CERTIFY", ... }
```

**Errors:**
- `400 ACTOR_NOT_PENDING_CHECK`
- `400 MAKER_CANNOT_BE_CHECKER`

---

### POST `/api/v1/pipeline/{actor_id}/certify/` — CERTIFIER
Final approval. **This is the moment the ledger posts and balances update.**

**Response 200:**
```json
{ "id": "pppp-1111", "status": "COMPLETED", ... }
```

**Errors:**
- `400 ACTOR_NOT_PENDING_CERTIFY`
- `400 CERTIFIER_MUST_BE_DISTINCT`

---

### POST `/api/v1/pipeline/{actor_id}/reject/` — CHECKER
Reject a pending actor.

**Request:**
```json
{ "reason": "documentation missing" }
```

**Response 200:**
```json
{ "id": "pppp-1111", "status": "REJECTED", "rejection_reason": "documentation missing" }
```

---

## 11. Dashboard (aggregate)

### GET `/api/v1/dashboard/` — any authenticated staff
High-level counts + recent activity (implementation coming next).

**Response 200:**
```json
{
  "members": { "active": 155, "pending": 3, "dormant": 8 },
  "savings": { "voluntary_total": "1259361.74" },
  "loans": { "disbursed": 42, "outstanding_total": "1032964.00" },
  "pipeline": { "pending_check": 4, "pending_certify": 2 },
  "recent_activity": [
    { "type": "DEPOSIT", "amount": "1000.00", "member_number": "KDU-000001", "created_at": "..." }
  ]
}
```

---

## 12. Health check

### GET `/health/` — Public

**Response 200:**
```json
{ "status": "ok", "database": "ok", "version": "1.0.0" }
```

---

## Appendix — Complete endpoint map

| # | Method | Path | Role |
|---|--------|------|------|
| 1 | POST | `/auth/token/` | Public |
| 2 | POST | `/auth/token/refresh/` | Public |
| 3 | POST | `/auth/token/verify/` | Public |
| 4 | GET | `/users/me/` | Auth |
| 5 | POST | `/users/me/change-password/` | Auth |
| 6 | GET | `/members/` | BOARD/CHECKER |
| 7 | POST | `/members/` | MAKER |
| 8 | GET | `/members/{id}/` | BOARD/CHECKER |
| 9 | POST | `/members/{id}/initial-capital/` | MAKER |
| 10 | POST | `/members/{id}/exit/` | MAKER |
| 11 | POST | `/savings/deposit/` | MAKER |
| 12 | POST | `/savings/withdraw/` | MAKER |
| 13 | GET | `/savings/transactions/` | BOARD/CHECKER |
| 14 | GET | `/savings/members/{id}/voluntary/` | BOARD/CHECKER |
| 15 | GET | `/loans/` | BOARD/CHECKER |
| 16 | POST | `/loans/` | MAKER |
| 17 | GET | `/loans/{id}/` | BOARD/CHECKER |
| 18 | POST | `/loans/{id}/repay/manual/` | MAKER |
| 19 | POST | `/loans/{id}/repay/scheduled/` | MAKER |
| 20 | GET | `/loans/{id}/repayments/` | BOARD/CHECKER |
| 21 | GET | `/expenses/` | BOARD/CHECKER |
| 22 | POST | `/expenses/` | MAKER |
| 23 | GET | `/expenses/{id}/` | BOARD/CHECKER |
| 24 | POST | `/shu/calculate/` | MAKER |
| 25 | GET | `/shu/{id}/` | BOARD/CHECKER |
| 26 | GET | `/shu/{id}/payouts/` | BOARD/CHECKER |
| 27 | POST | `/shu/snapshot/` | SUPERADMIN |
| 28 | POST | `/shu/aggregate/` | SUPERADMIN |
| 29 | GET | `/governance/config/` | BOARD/CHECKER |
| 30 | POST | `/governance/config/propose/` | MAKER |
| 31 | POST | `/governance/config/certify/{id}/` | CERTIFIER |
| 32 | GET | `/governance/changes/` | BOARD/CHECKER |
| 33 | GET | `/reports/trial-balance/` | BOARD/CHECKER |
| 34 | GET | `/reports/income-statement/` | BOARD/CHECKER |
| 35 | GET | `/reports/balance-sheet/` | BOARD/CHECKER |
| 36 | GET | `/reports/surplus-distribution/{fy_id}/` | BOARD/CHECKER |
| 37 | GET | `/pipeline/pending-check/` | CHECKER |
| 38 | GET | `/pipeline/pending-certify/` | CERTIFIER |
| 39 | POST | `/pipeline/{id}/check/` | CHECKER |
| 40 | POST | `/pipeline/{id}/certify/` | CERTIFIER |
| 41 | POST | `/pipeline/{id}/reject/` | CHECKER |
| 42 | GET | `/dashboard/` | Auth |
| 43 | GET | `/health/` | Public |