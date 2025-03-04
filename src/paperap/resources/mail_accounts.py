"""




----------------------------------------------------------------------------

   METADATA:

       File:    mail_accounts.py
       Project: paperap
       Created: 2025-03-04
       Version: 0.0.1
       Author:  Jess Mann
       Email:   jess@jmann.me
       Copyright (c) 2025 Jess Mann

----------------------------------------------------------------------------

   LAST MODIFIED:

       2025-03-04     By Jess Mann

"""

from __future__ import annotations

from paperap.models.mail_accounts import MailAccounts
from paperap.resources.base import PaperlessResource


class MailAccountsResource(PaperlessResource[MailAccounts]):
    """Resource for managing mail accounts."""

    model_class = MailAccounts
