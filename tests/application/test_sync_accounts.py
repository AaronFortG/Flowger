from flowger.application.sync_accounts import SyncAccountsUseCase
from flowger.domain.account import Account
from flowger.domain.transaction import Transaction


class FakeBankProvider:
    """Mock provider to verify use case interaction."""

    def __init__(self, accounts_to_return: list[Account]) -> None:
        self.__accounts_to_return = accounts_to_return
        self.__called = False

    def fetch_accounts(self, session_id: str) -> list[Account]:
        self.__called = True
        return self.__accounts_to_return

    def fetch_transactions(self, session_id: str, account_id: str) -> list[Transaction]:
        return []

    @property
    def called(self) -> bool:
        return self.__called


class FakeAccountRepository:
    """Mock repository to verify use case interaction."""

    def __init__(self) -> None:
        self.__saved_accounts: list[Account] = []

    def save_accounts(self, accounts: list[Account]) -> None:
        self.__saved_accounts.extend(accounts)

    def get_accounts(self) -> list[Account]:
        return self.__saved_accounts

    @property
    def saved_accounts(self) -> list[Account]:
        return self.__saved_accounts


def test_sync_accounts_use_case() -> None:
    """Verify that SyncAccountsUseCase fetches from provider and saves to repo."""
    # 1. Arrange
    mock_account = Account(id="fake_1", iban="TEST", name="Fake Account", currency="EUR")
    fake_provider = FakeBankProvider(accounts_to_return=[mock_account])
    fake_repo = FakeAccountRepository()

    use_case = SyncAccountsUseCase(provider=fake_provider, repository=fake_repo)

    # 2. Act
    use_case.execute(session_id="fake-session")

    # 3. Assert
    assert fake_provider.called is True
    assert len(fake_repo.saved_accounts) == 1
    assert fake_repo.saved_accounts[0].id == "fake_1"


def test_sync_accounts_use_case_empty_accounts() -> None:
    """Verify that save_accounts is called with an empty list when provider returns none."""
    fake_provider = FakeBankProvider(accounts_to_return=[])
    fake_repo = FakeAccountRepository()

    use_case = SyncAccountsUseCase(provider=fake_provider, repository=fake_repo)
    use_case.execute(session_id="fake-session")

    assert fake_provider.called is True
    assert fake_repo.saved_accounts == []
