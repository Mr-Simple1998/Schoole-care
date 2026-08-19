# Task 2 Report

Implemented request parameter normalization in both clients.

- Added local `cleanParams` helpers that remove only `undefined`, `null`, and empty-string values.
- Preserved `false`, `0`, arrays, and all non-empty values.
- Applied normalization to Axios query params and mini-program GET data only; POST/PUT/DELETE payloads are unchanged.
- Existing auth injection, response passthrough, and 401/403/400 handling remain unchanged.

Checks: Both builds were attempted with local dependencies. Vite could not write its temporary config under `frontend/node_modules/.vite-temp` (`EPERM`), and the mini-program command was blocked by the PowerShell execution policy/toolchain environment.
