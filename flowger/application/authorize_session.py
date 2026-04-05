from flowger.application.banking import BankProvider
from flowger.application.repositories import AccountRepository
from flowger.application.session_repository import SessionRepository
from flowger.domain.account import Account
from flowger.domain.bank_session import BankSession


class AuthorizeSessionUseCase:
    """Use case to exchange an OAuth code for a session and persist it locally."""

    def __init__(
        self,
        provider: BankProvider,
        session_repository: SessionRepository,
        account_repository: AccountRepository,
    ) -> None:
        self.__provider = provider
        self.__session_repository = session_repository
        self.__account_repository = account_repository

    def execute(self, code: str, bank_name: str, country: str) -> tuple[BankSession, list[Account]]:
        """
        Exchange the redirect code for a session, persist it alongside the accounts,
        and return both so callers can display or further use them.
        """
        session, accounts = self.__provider.authorize_session(
            code=code, bank_name=bank_name, country=country
        )

        for account in accounts:
            account.bank_name = bank_name
            account.country = country

        self.__session_repository.save_session(session)
        self.__account_repository.save_accounts(accounts)
        return session, accounts
