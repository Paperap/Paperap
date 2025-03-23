

from __future__ import annotations

from paperap.models.abstract import StandardModel


class ListResponse(StandardModel):
    """
    Not currently used, but kept for documentation or future expansion.

    The structure of an api response from paperless ngx for a list of models.
    """

    count: int
    next: str | None
    previous: str | None
    all: list[int]
    results: list[StandardModel]
