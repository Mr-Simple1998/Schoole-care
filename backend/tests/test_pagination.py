"""Static contract checks for backward-compatible list pagination."""

from pathlib import Path


ROUTERS = Path(__file__).parents[1] / "app" / "routers"


def _route_sources():
    return "\n".join(
        path.read_text(encoding="utf-8")
        for path in ROUTERS.glob("*.py")
        if path.name != "__init__.py"
    )


def test_pagination_bounds_and_conditional_slice():
    source = _route_sources()
    assert "page_size: int = Query(default=10, ge=1, le=100)" in source
    assert ".offset((page - 1) * page_size).limit(page_size).all()" in source
    assert "if page is not None else q.all()" in source


def test_paginated_timestamp_queries_are_deterministic():
    source = _route_sources()
    assert "PointRecord.created_at.desc(), PointRecord.id.desc()" in source
    assert "Redemption.created_at.desc(), Redemption.id.desc()" in source
    assert "Organization.created_at.desc(), Organization.id.desc()" in source
