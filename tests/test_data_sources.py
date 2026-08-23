from __future__ import annotations

from typing import Any

from saude_brasil_insights.data_sources import fetch_paginated


class FakeResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return self.payload


class FakeSession:
    def __init__(self) -> None:
        self.pages = {
            0: {"items": [{"id": 1}, {"id": 2}]},
            2: {"items": [{"id": 3}]},
        }
        self.requested_pages: list[int] = []

    def get(self, _url: str, *, params: dict[str, Any], timeout: int) -> FakeResponse:
        assert timeout == 120
        offset = params["offset"]
        self.requested_pages.append(offset)
        return FakeResponse(self.pages[offset])


def test_fetch_paginated_advances_offset_by_page_size() -> None:
    session = FakeSession()

    result = fetch_paginated(
        "/example",
        "items",
        limit=2,
        session=session,  # type: ignore[arg-type]
    )

    assert result["id"].tolist() == [1, 2, 3]
    assert session.requested_pages == [0, 2]
