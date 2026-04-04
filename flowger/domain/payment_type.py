from enum import Enum


class PaymentType(str, Enum):
    """Indicates the direction of a payment (income vs expense)"""
    DEBIT = "DBIT"  # Expense
    CREDIT = "CRDT" # Income
