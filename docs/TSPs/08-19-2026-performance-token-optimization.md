# Performance and Token Optimization Technical Spec

> **For agentic workers:** REQUIRED SUB-SKILL: Use dmi-superpowers:subagent-driven-development (recommended) or dmi-superpowers:executing-plans to implement this TSP task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce list payloads, duplicate request work, initial PC bundle cost, and mobile memory while preserving business behavior and existing array responses.

**Architecture:** Add optional pagination at existing FastAPI list boundaries, retaining full-list defaults. Keep shared request utilities responsible for parameter normalization, token lookup, and stale-request protection; make PC routes and ECharts lazy through existing Vue/Vite primitives; keep uni-app pages structurally unchanged and replace page arrays rather than accumulating them.

**Tech Stack:** FastAPI, SQLAlchemy, Vue 3, Vite, Element Plus, ECharts, Pinia, uni-app.

## Global Constraints

- Target mainstream Chrome/Edge and the current stable WeChat Mini Program base library.
- Do not add dependencies.
- Do not change business semantics, permissions, error codes, required fields, or existing response array shapes.
- Paginated calls use optional `page` and `page_size`; a short page is the end marker.
- Existing calls without pagination parameters retain full-list behavior.
- No LLM chain exists; optimize only duplicate request parameters, redundant response work, and JWT lookup/header injection.

---

### Task 1: Add Backward-Compatible Backend Pagination

**Files:**
- Modify: `backend/app/routers/students.py`
- Modify: `backend/app/routers/income.py`
- Modify: `backend/app/routers/campuses.py`
- Modify: `backend/app/routers/commissions.py`
- Modify: `backend/app/routers/points.py`
- Modify: `backend/app/routers/platform.py`
- Modify: `backend/app/routers/subjects.py`
- Create: `backend/tests/test_pagination.py`

**Interfaces:**
- Consumes: existing list query functions and SQLAlchemy `Query` objects.
- Produces: optional `page: int | None = None`, `page_size: int = 10` parameters; unchanged list response models.

- [ ] **Step 1: Write failing tests** for omitted parameters, `page_size=10`, invalid values, empty pages, and exact-full-page boundaries. Assert response remains a JSON array.
- [ ] **Step 2: Run** `pytest backend/tests/test_pagination.py -q`; expect failures because list handlers do not accept pagination.
- [ ] **Step 3: Implement** validation with `Query(default=None, ge=1)` for `page` and `Query(default=10, ge=1, le=100)` for `page_size`; apply `offset((page - 1) * page_size).limit(page_size)` only when `page` is provided. Preserve existing `.all()` behavior otherwise and map related names only after the page is selected.
- [ ] **Step 4: Run** `pytest backend/tests/test_pagination.py -q`; expect PASS.
- [ ] **Step 5: Commit** `git add backend/app/routers backend/tests/test_pagination.py && git commit -m "perf: add compatible list pagination"`.

### Task 2: Normalize Shared Request Work

**Files:**
- Modify: `frontend/src/utils/request.js`
- Modify: `weapp/src/utils/request.js`
- Modify: `frontend/src/stores/user.js`
- Modify: `weapp/src/stores/user.js`
- Create: `backend/tests/test_request_contract.md` (manual contract checklist)

**Interfaces:**
- Consumes: existing request helpers and auth storage APIs.
- Produces: same exported request methods and error behavior, with normalized query data and one token read per request.

- [ ] **Step 1: Record** current request contract: exported method names, auth header format, status handling, and response passthrough.
- [ ] **Step 2: Implement** a small local `cleanParams` helper in each request utility that removes only `undefined`, `null`, and empty-string query values; never remove `false`, `0`, or non-empty arrays.
- [ ] **Step 3: Ensure** token is read once per request, the Authorization header is added only when non-empty, and existing 401/403/400 handling remains unchanged.
- [ ] **Step 4: Verify** with browser and mini-program request mocks or the contract checklist; assert serialized params and headers match the existing contract for valid values.
- [ ] **Step 5: Commit** `git add frontend/src/utils/request.js weapp/src/utils/request.js frontend/src/stores/user.js weapp/src/stores/user.js backend/tests/test_request_contract.md && git commit -m "perf: normalize client request overhead"`.

### Task 3: Reduce PC Initial Work

**Files:**
- Modify: `frontend/src/router/index.js`
- Modify: `frontend/src/main.js`
- Modify: `frontend/src/views/PlatformManage.vue`
- Modify: `frontend/src/views/Dashboard.vue`
- Modify: `frontend/src/views/StudentList.vue`
- Modify: `frontend/src/views/TeacherManage.vue`
- Modify: `frontend/src/views/IncomeManage.vue`

**Interfaces:**
- Consumes: existing routes, Element Plus components/icons, and ECharts chart lifecycle.
- Produces: identical route URLs and UI behavior with route-level chunks and on-demand chart/icon loading.

- [ ] **Step 1: Replace** static view imports in `frontend/src/router/index.js` with `() => import(...)`; keep route names, paths, guards, and metadata unchanged.
- [ ] **Step 2: Replace** `import * as ElementPlusIconsVue` registration in `frontend/src/main.js` with the exact icon components used by templates, preserving component names.
- [ ] **Step 3: Change** `PlatformManage.vue` chart setup to `await import('echarts')` inside the existing mount path, dispose the instance on unmount, and preserve options and resize behavior.
- [ ] **Step 4: Memoize** repeated filtered-table computations per reactive input where current templates call the same filter more than once; do not alter displayed rows.
- [ ] **Step 5: Run** `npm run build` from `frontend`; inspect `dist/assets` for route chunks and absence of a monolithic icon registration chunk.
- [ ] **Step 6: Commit** `git add frontend/src && git commit -m "perf: lazy load pc routes and charts"`.

### Task 4: Add 10-Row Mobile Paging

**Files:**
- Modify: `weapp/src/pages/student/list.vue`
- Modify: `weapp/src/pages/teachers/teachers.vue`
- Modify: `weapp/src/pages/income/income.vue`
- Modify: `weapp/src/pages/campus/transactions.vue`
- Modify: `weapp/src/pages/points/points.vue`
- Modify: `weapp/src/pages/platform/platform.vue`

**Interfaces:**
- Consumes: existing page data, request helpers, and unchanged array responses.
- Produces: page state `{ page, size: 10, loading, done }`, next/previous controls, and current-page-only arrays.

- [ ] **Step 1: Add** page state and a `loadPage(page = 1)` function per high-volume page; pass `page` and `page_size: 10` to existing list URLs.
- [ ] **Step 2: Reset** page to 1 on filter changes, replace the page array on success, and set `done = rows.length < 10`; retain prior rows on failure.
- [ ] **Step 3: Disable** next/previous actions while loading and ignore stale responses using a monotonically increasing request sequence number.
- [ ] **Step 4: Add** compact responsive controls using existing styles/components; do not change the surrounding responsive layout.
- [ ] **Step 5: Run** `npm run build:mp-weixin` from `weapp`; smoke-test empty, 1-9, 10, and 11-row datasets in the mini-program preview.
- [ ] **Step 6: Commit** `git add weapp/src && git commit -m "perf: page mobile list data"`.

### Task 5: Verification and Regression Checks

**Files:**
- Create: `docs/verification/performance-token-optimization.md`

- [ ] **Step 1: Run** `pytest` from `backend`; record pass/fail and any environment-only skips.
- [ ] **Step 2: Run** `npm run build` from `frontend` and `npm run build:mp-weixin` from `weapp`.
- [ ] **Step 3: Verify** old no-pagination calls return arrays, paginated calls never exceed 10 rows, and exact multiples continue to request the next page.
- [ ] **Step 4: Verify** PC route chunks, dynamic ECharts loading, mobile current-page memory, stale-request handling, and auth header behavior with network/devtools traces.
- [ ] **Step 5: Write** measured results and known gaps in `docs/verification/performance-token-optimization.md`.
- [ ] **Step 6: Commit** `git add docs/verification/performance-token-optimization.md && git commit -m "test: record performance optimization verification"`.
