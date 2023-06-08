from typing import Union
from decimal import Decimal


class CurrencyMixin:

    def to_decimal(self, value: Union[int, str, Decimal]) -> Decimal:
        return self.round(Decimal(value).scaleb(-self.decimals))

    def round(self, d: Decimal) -> Decimal:
        return Decimal(round(d, self.decimals))

    def decimal_string(self, value: Decimal) -> str:
        return f'{value:.{self.decimals}f}'.rstrip('0').rstrip('.')

    def int_value(self, value: Decimal) -> int:
        value = Decimal(value)
        return int(value.scaleb(self.decimals))

    def human_string(self, value) -> str:
        return f'{self.decimal_string(value)} {self.name}'