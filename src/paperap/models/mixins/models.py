"""




 ----------------------------------------------------------------------------

    METADATA:

        File:    models.py
        Project: paperap
        Created: 2025-03-09
        Version: 0.0.4
        Author:  Jess Mann
        Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

 ----------------------------------------------------------------------------

    LAST MODIFIED:

        2025-03-09     By Jess Mann

"""
class MatcherMixin:
    match: str | None = None
    matching_algorithm: int | None = None
    is_insensitive: bool