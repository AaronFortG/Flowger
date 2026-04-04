from flowger.application.sync_accounts import SyncAccountsUseCase
from flowger.domain.account import Account


class FakeBankProvider:
    """Mock provider to verify use case interaction."""

    def __init__(self, accounts_to_return: list[Account]) -> None:
        self.accounts_to_return = accounts_to_return
        self.called = False

    def fetch_accounts(self) -> list[Account]:
        self.called = True
        return self.accounts_to_return


class FakeAccountRepository:
    """Mock repository to verify use case interaction."""

    def __init__(self) -> None:
        self.saved_accounts: list[Account] = []

    def save_accounts(self, accounts: list[Account]) -> None:
        self.saved_accounts.extend(accounts)


def test_sync_accounts_use_case() -> None:
    """Verify that SyncAccountsUseCase fetches from provider and saves to repo."""
    # 1. Arrange
    mock_account = Account(id="fake_1", iban="TEST", name="Fake Account", currency="EUR")
    fake_provider = FakeBankProvider(accounts_to_return=[mock_account])
    fake_repo = FakeAccountRepository()

    use_case = SyncAccountsUseCase(provider=fake_provider, repository=fake_repo)

    # 2. Act
    use_case.execute()

    # 3. Assert
    assert fake_provider.called is True
    assert len(fake_repo.saved_accounts) == 1
    assert fake_repo.saved_accounts[0].id == "fake_1"
