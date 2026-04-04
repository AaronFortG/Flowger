from flowger.infrastructure.config import Settings
from flowger.infrastructure.enable_banking.provider import EnableBankingProvider


def create_bank_provider(settings: Settings) -> EnableBankingProvider:
    """Helper to instantiate the BankProvider with current settings."""
    return EnableBankingProvider(
        app_id=settings.enablebanking_app_id,
        private_key_path=settings.enablebanking_key_path,
        environment=settings.enablebanking_environment,
    )
