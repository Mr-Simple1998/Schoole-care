# Task 1: Add Backward-Compatible Backend Pagination

**Files:** Modify `backend/app/routers/students.py`, `backend/app/routers/income.py`, `backend/app/routers/campuses.py`, `backend/app/routers/commissions.py`, `backend/app/routers/points.py`, `backend/app/routers/platform.py`, `backend/app/routers/subjects.py`; create `backend/tests/test_pagination.py`.

**Interfaces:** Add optional `page: int | None = None`, `page_size: int = 10` parameters; keep list response models unchanged.

**Global constraints:** Target mainstream Chrome/Edge and current stable WeChat Mini Program base library. Do not add dependencies. Do not change business semantics, permissions, error codes, required fields, or response array shapes. Paginated calls use optional `page` and `page_size`; short page is the end marker. Calls without pagination retain full-list behavior.

Write failing tests for omitted parameters, `page_size=10`, invalid values, empty pages, and exact-full-page boundaries. Apply `offset((page - 1) * page_size).limit(page_size)` only when `page` is provided. Preserve existing `.all()` otherwise and map related names only after selecting the page. Run `pytest backend/tests/test_pagination.py -q`, then full backend tests before committing. Report implementation, tests, files, concerns to `.superpowers/sdd/task-1-report.md` and commit the task.
