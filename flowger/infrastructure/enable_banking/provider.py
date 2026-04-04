import datetime
import uuid
from decimal import Decimal
from typing import Any

from flowger.domain.account import Account
from flowger.domain.bank_session import BankSession
from flowger.domain.payment_type import PaymentType
from flowger.domain.transaction import Transaction
from flowger.infrastructure.enable_banking.client import EnableBankingClient

_AUTH_ENDPOINT = "/auth"
_SESSIONS_ENDPOINT = "/sessions"
_ACCOUNTS_ENDPOINT = "/accounts"
_TRANSACTIONS_ENDPOINT = "/accounts/{account_id}/transactions"
_AUTH_STATE = "flowger_sync"
_ACCESS_VALID_DAYS = 180


class EnableBankingProvider:
    """Adapts EnableBanking HTTP API to the application's BankProvider port."""

    def __init__(
        self,
        app_id: str,
        private_key_path: str,
        environment: str,
        client: EnableBankingClient | None = None,
    ) -> None:
        self.__client = client or EnableBankingClient(
            app_id=app_id,
            private_key_path=private_key_path,
            environment=environment,
        )

    def start_authorization(
        self, bank_name: str, country: str, redirect_url: str, psu_type: str = ""
    ) -> str:
        """
        Initiate an authorization flow.
        Returns the authorization URL that the user must visit in their browser.
        """
        payload: dict[str, Any] = {
            "access": {
                "valid_until": _compute_valid_until(),
            },
            "aspsp": {
                "name": bank_name,
                "country": country,
            },
            "state": _AUTH_STATE,
            "redirect_url": redirect_url,
        }
        if psu_type:
            payload["psu_type"] = psu_type
        response = self.__client.post(_AUTH_ENDPOINT, json=payload)
        url: str = response.get("url", "")
        return url

    def authorize_session(
        self, code: str, bank_name: str, country: str
    ) -> tuple[BankSession, list[Account]]:
        """
        Exchange the redirect authorization code for a session_id.
        Returns a tuple of (BankSession, list[Account]) ready to be persisted.
        """
        response = self.__client.post(_SESSIONS_ENDPOINT, json={"code": code})
        session_id: str = response["session_id"]

        session = BankSession(
            session_id=session_id,
            bank_name=bank_name,
            country=country,
            created_at=datetime.datetime.now(tz=datetime.timezone.utc),
        )

        raw_accounts: list[dict[str, Any]] = response.get("accounts", [])
        bank_name_resp = (response.get("aspsp") or {}).get("name", bank_name)

        accounts = []
        for acc in raw_accounts:
            iban = acc.get("iban") or (acc.get("account_id") or {}).get("iban", "")
            acc_name = acc.get("product") or acc.get("name") or acc.get("details") or "Account"
            full_name = f"{bank_name_resp} {acc_name}".strip()
            currency = acc.get("currency", "")

            accounts.append(
                Account(
                    id=acc["uid"],
                    iban=str(iban),
                    name=str(full_name),
                    currency=currency,
                )
            )

        return session, accounts

    def fetch_transactions(self, session_id: str, account_id: str) -> list[Transaction]:
        """Fetch all transactions for an account, following pagination via continuation_key."""
        endpoint = _TRANSACTIONS_ENDPOINT.format(account_id=account_id)
        raw_txs: list[dict[str, Any]] = []
        params: dict[str, str] = {"session_id": session_id}

        while True:
            query = "&".join(f"{k}={v}" for k, v in params.items())
            response = self.__client.get(f"{endpoint}?{query}")
            raw_txs.extend(response.get("transactions", []))
            continuation_key = response.get("continuation_key")
            if not continuation_key:
                break
            params = {"continuation_key": continuation_key}

        return [_parse_transaction(tx, account_id) for tx in raw_txs]


def _compute_valid_until(days: int = _ACCESS_VALID_DAYS) -> str:
    """Return an ISO-8601 UTC timestamp 'days' from now, as required by EnableBanking."""
    until = datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(days=days)
    return until.strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_transaction(tx: dict[str, Any], account_id: str) -> Transaction:
    return Transaction(
        id=_resolve_id(tx),
        account_id=account_id,
        date=_resolve_date(tx),
        amount=_resolve_amount(tx),
        currency=_resolve_currency(tx),
        payee=_resolve_payee(tx),
        notes=_resolve_notes(tx),
    )


def _resolve_id(tx: dict[str, Any]) -> str:
    """Return the unique identifier for a transaction."""
    tx_id = tx.get("entry_reference")
    if not tx_id:
        return str(uuid.uuid4())
    return str(tx_id)


def _resolve_date(tx: dict[str, Any]) -> datetime.date:
    """Return the best available date — transaction_date > booking_date > value_date."""
    raw = tx.get("booking_date") or tx.get("value_date")
    if not raw:
        raise ValueError(f"Transaction has no parseable date: {tx.get('entry_reference', '?')}")
    return datetime.date.fromisoformat(str(raw)[:10])


def _resolve_amount(tx: dict[str, Any]) -> Decimal:
    """Return the signed amount based on the credit/debit indicator."""
    indicator = str(tx.get("credit_debit_indicator", "")).upper()

    amount_obj = tx.get("transaction_amount") or {}
    raw_amount = amount_obj.get("amount", "0")
    amount = Decimal(str(raw_amount))

    if indicator == PaymentType.DEBIT:
        return -abs(amount)
    return abs(amount)


def _resolve_currency(tx: dict[str, Any]) -> str:
    amount_obj = tx.get("transaction_amount") or {}
    return str(amount_obj.get("currency", "0"))


def _resolve_payee(tx: dict[str, Any]) -> str:
    """Return the best available payee for a transaction."""
    indicator = str(tx.get("credit_debit_indicator", "")).upper()
    if indicator == PaymentType.DEBIT:
        # It's an expense, so the payee is the creditor
        return (
            (tx.get("creditor") or {}).get("name")
            or tx.get("remittance_information_unstructured")
            or "Unknown Payee"
        )
    # It's income, so the payee is the debtor
    return (
        (tx.get("debtor") or {}).get("name")
        or tx.get("remittance_information_unstructured")
        or "Unknown Payee"
    )


def _resolve_notes(tx: dict[str, Any]) -> str:
    """Return remittance information as a single string."""
    unstructured = tx.get("remittance_information_unstructured")
    if unstructured:
        return str(unstructured)
    structured = tx.get("remittance_information")
    if isinstance(structured, list):
        return " ".join(structured)
    return ""
