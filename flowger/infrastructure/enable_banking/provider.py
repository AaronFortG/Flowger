import datetime
import hashlib
from decimal import Decimal
from typing import Any

from flowger.domain.account import Account
from flowger.domain.bank_session import BankSession
from flowger.domain.payment_type import PaymentType
from flowger.domain.transaction import Transaction
from flowger.infrastructure.enable_banking.client import EnableBankingClient

_AUTH_ENDPOINT = "/auth"
_SESSIONS_ENDPOINT = "/sessions"
_TRANSACTIONS_ENDPOINT = "/accounts/{account_id}/transactions"

_ACCESS_VALID_DAYS = 180


class EnableBankingProvider:
    """Adapts EnableBanking HTTP API to the application's BankProvider port."""

    def __init__(
        self,
        app_id: str,
        private_key_path: str,
        client: EnableBankingClient | None = None,
    ) -> None:
        self.__client = (
            client
            if client is not None
            else EnableBankingClient(
                app_id=app_id,
                private_key_path=private_key_path,
            )
        )

    def __enter__(self) -> "EnableBankingProvider":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.__client.close()

    def start_authorization(
        self, bank_name: str, country: str, redirect_url: str, state: str, psu_type: str = ""
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
            "state": state,
            "redirect_url": redirect_url,
        }
        if len(psu_type) > 0:
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
        bank_service_provider = response.get("aspsp")
        bank_name_resp = (
            bank_service_provider if bank_service_provider is not None else {}
        ).get("name", bank_name)

        accounts: list[Account] = []
        for acc in raw_accounts:
            # IBAN is found inside the account_id object, but is optional
            # If IBAN is missing, we fall back to 'other' -> 'identification'
            account_id_obj = acc.get("account_id")
            if account_id_obj is None:
                account_id_obj = {}
            
            iban_val = account_id_obj.get("iban")
            if iban_val is None or (isinstance(iban_val, str) and len(iban_val.strip()) == 0):
                other_obj = account_id_obj.get("other")
                if other_obj is None:
                    other_obj = {}
                iban_val = other_obj.get("identification")

            iban = str(iban_val) if (iban_val is not None and len(str(iban_val).strip()) > 0) else ""

            # Name selection: Prefer 'name', then 'details' per the API response example
            name_candidates = [
                acc.get("name"),
                acc.get("details"),
            ]
            acc_name = "Account"
            for cand in name_candidates:
                if cand is not None and (not isinstance(cand, str) or len(str(cand).strip()) > 0):
                    acc_name = str(cand)
                    break

            full_name = f"{bank_name_resp} {acc_name}".strip()
            currency = acc.get("currency", "")

            accounts.append(
                Account(
                    id=acc["uid"],
                    iban=str(iban),
                    name=str(full_name),
                    currency=currency,
                    bank_name=bank_name,
                    country=country,
                )
            )

        return session, accounts

    def fetch_transactions(
        self, session_id: str, account_id: str, bank_name: str, country: str
    ) -> list[Transaction]:
        """Fetch all transactions for an account, following pagination via continuation_key."""
        endpoint = _TRANSACTIONS_ENDPOINT.format(account_id=account_id)
        raw_txs: list[dict[str, Any]] = []
        params: dict[str, str] = {"session_id": session_id}

        while True:
            response = self.__client.get(endpoint, params=params)
            raw_txs.extend(response.get("transactions", []))
            continuation_key = response.get("continuation_key")
            if continuation_key is None or len(continuation_key) == 0:
                break
            params = {"continuation_key": continuation_key, "session_id": session_id}

        return [_parse_transaction(tx, account_id, bank_name, country) for tx in raw_txs]


def _compute_valid_until(days: int = _ACCESS_VALID_DAYS) -> str:
    """Return an ISO-8601 UTC timestamp 'days' from now, as required by EnableBanking."""
    until = datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(days=days)
    return until.strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_transaction(
    tx: dict[str, Any], account_id: str, bank_name: str, country: str
) -> Transaction:
    return Transaction(
        id=_resolve_id(tx),
        account_id=account_id,
        bank_name=bank_name,
        country=country,
        date=_resolve_date(tx),
        amount=_resolve_amount(tx),
        currency=_resolve_currency(tx),
        payee=_resolve_payee(tx),
        notes=_resolve_notes(tx),
    )


def _resolve_id(tx: dict[str, Any]) -> str:
    """Return the unique identifier for a transaction."""
    tx_id = tx.get("entry_reference")
    if tx_id is None or len(str(tx_id)) == 0:
        amount_obj = tx.get("transaction_amount")
        if amount_obj is None:
            amount_obj = {}
        amount_str = str(amount_obj.get("amount", ""))
        
        booking_date = tx.get("booking_date")
        value_date = tx.get("value_date")
        booking_date_str = "" if booking_date is None else str(booking_date).strip()
        value_date_str = "" if value_date is None else str(value_date).strip()
        date_str = booking_date_str if len(booking_date_str) > 0 else value_date_str
        
        indicator = tx.get("credit_debit_indicator", "")
        remittance_info = tx.get("remittance_information", "")
        raw_str = f"{date_str}_{amount_str}_{indicator}_{remittance_info}"
        return hashlib.sha256(raw_str.encode()).hexdigest()
    return str(tx_id)


def _resolve_date(tx: dict[str, Any]) -> datetime.date:
    """Return the best available date — transaction_date > booking_date > value_date."""
    transaction_date = tx.get("transaction_date")
    booking_date = tx.get("booking_date")
    value_date = tx.get("value_date")
    
    raw = None
    for candidate in (transaction_date, booking_date, value_date):
        if candidate is not None and (not isinstance(candidate, str) or len(candidate.strip()) > 0):
            raw = candidate
            break
    if raw is None:
        raise ValueError(f"Transaction has no parseable date: {tx.get('entry_reference', '?')}")
    return datetime.date.fromisoformat(str(raw)[:10])


def _resolve_amount(tx: dict[str, Any]) -> Decimal:
    """Return the signed amount based on the credit/debit indicator."""
    indicator = str(tx.get("credit_debit_indicator", "")).upper()
 
    amount_obj = tx.get("transaction_amount")
    if amount_obj is None:
        amount_obj = {}
    raw_amount = amount_obj.get("amount", "0")
    amount = Decimal(str(raw_amount))

    if indicator == PaymentType.DEBIT.value:
        return -abs(amount)
    if indicator == PaymentType.CREDIT.value:
        return abs(amount)

    raise ValueError(
        f"Missing or unknown credit_debit_indicator: '{indicator}'. "
        f"Expected {PaymentType.CREDIT.value} or {PaymentType.DEBIT.value}."
    )


def _resolve_currency(tx: dict[str, Any]) -> str:
    amount_obj = tx.get("transaction_amount")
    if amount_obj is None:
        amount_obj = {}
    return str(amount_obj.get("currency", ""))


def _resolve_payee(tx: dict[str, Any]) -> str:
    """Return the best available payee for a transaction."""
    indicator = str(tx.get("credit_debit_indicator", "")).upper()

    # Try to extract a structured remittance string if available
    remittance = tx.get("remittance_information")
    if isinstance(remittance, list):
        remittance_str = " ".join(remittance)
    else:
        remittance_str = str(remittance) if remittance is not None else ""

    if indicator == PaymentType.DEBIT.value:
        # It's an expense, so the payee is the creditor
        creditor = tx.get("creditor")
        creditor_name = (creditor if creditor is not None else {}).get("name")
        if creditor_name is not None and len(str(creditor_name).strip()) > 0:
            return str(creditor_name)
        if len(remittance_str) > 0:
            return remittance_str
        return "Unknown Payee"
        
    # It's income, so the payee is the debtor
    debtor = tx.get("debtor")
    debtor_name = (debtor if debtor is not None else {}).get("name")
    if debtor_name is not None and len(str(debtor_name).strip()) > 0:
        return str(debtor_name)
    if len(remittance_str) > 0:
        return remittance_str
    return "Unknown Payee"


def _resolve_notes(tx: dict[str, Any]) -> str:
    """Return remittance information as a single string."""
    remittance = tx.get("remittance_information")
    if isinstance(remittance, list):
        return " ".join(remittance)
    return str(remittance) if remittance is not None else ""
