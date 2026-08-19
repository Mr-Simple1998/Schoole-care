# ADR 0001: Backward-Compatible Array Pagination

## Status

Accepted

## Context

Existing list endpoints return arrays and are consumed by both the PC Vue app and the uni-app client. Large responses are expensive on weak networks, but changing the response envelope would break existing consumers.

## Decision

Add optional `page` and `page_size` query parameters. Paginated calls return the same array shape as existing calls; a response shorter than `page_size` marks the last page. Calls without pagination parameters retain historical full-list behavior.

## Consequences

Consumers remain compatible and response parsing stays small. Paginated clients do not receive an exact total count and must infer the end from page length. Exact totals can be added later only through a backward-compatible metadata channel if the product requires it.
