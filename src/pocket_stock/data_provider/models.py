"""股票行情数据模型。"""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class StockQuote(BaseModel):
    """股票行情数据模型。

    该类用于封装股票的实时行情信息，包括股票名称、当前价格、
    涨跌幅、成交量等字段。

    Attributes:
        stock_code: 股票代码（如 "sh600000"）
        name: 股票名称
        current_price: 当前价格
        change: 涨跌额（正数表示上涨，负数表示下跌）
        change_percent: 涨跌幅（百分比，如 3.5 表示 3.5%）
        volume: 成交量
        turnover: 成交额
        open_price: 开盘价
        close_price: 收盘价
        high_price: 最高价
        low_price: 最低价
        timestamp: 数据时间戳

    Examples:
        >>> quote = StockQuote(
        ...     stock_code="sh600000",
        ...     name="浦发银行",
        ...     current_price=10.25,
        ...     change=0.15,
        ...     change_percent=1.48,
        ...     volume=1000000,
        ...     turnover=10250000.0
        ... )
    """

    stock_code: str = Field(..., min_length=1, description="股票代码")
    name: str = Field(..., min_length=1, description="股票名称")
    current_price: float = Field(..., ge=0, description="当前价格")
    change: float | None = Field(default=0.0, description="涨跌额")
    change_percent: float | None = Field(default=0.0, description="涨跌幅")
    volume: int | None = Field(default=0, description="成交量")
    turnover: float | None = Field(default=0.0, description="成交额")
    open_price: float | None = Field(default=None, ge=0, description="开盘价")
    close_price: float | None = Field(default=None, ge=0, description="收盘价")
    high_price: float | None = Field(default=None, ge=0, description="最高价")
    low_price: float | None = Field(default=None, ge=0, description="最低价")
    timestamp: datetime | None = Field(default=None, description="数据时间戳")

    model_config = {"json_encoders": {datetime: lambda v: v.isoformat() if v else None}}

    @field_validator("stock_code")
    @classmethod
    def validate_stock_code_format(cls, v: str) -> str:
        """验证股票代码格式。

        支持的格式：
        - 上海市场：sh + 6位数字（如 sh600000）
        - 深圳市场：sz + 6位数字（如 sz000001）

        Args:
            v: 待验证的股票代码

        Returns:
            验证通过的股票代码（保持原始大小写）

        Raises:
            ValueError: 当股票代码格式不正确时抛出

        Examples:
            >>> StockQuote.model_validate({"stock_code": "sh600000", ...})
        """
        if not v or len(v) != 8:
            raise ValueError(f'股票代码格式错误: "{v}"，应为8位字符（如 sh600000 或 sz000001）')

        prefix = v[:2].lower()
        suffix = v[2:]

        if prefix not in ("sh", "sz"):
            raise ValueError(f'股票代码前缀错误: "{v}"，应以 "sh" 或 "sz" 开头')

        if not suffix.isdigit():
            raise ValueError(f'股票代码后缀错误: "{v}"，后6位应为数字')

        return v

    @field_validator("name")
    @classmethod
    def validate_non_empty_str(cls, v: str) -> str:
        """验证字符串非空。"""
        if not v or not v.strip():
            raise ValueError("股票名称不能为空")
        return v.strip()

    @field_validator("change", "change_percent", "turnover")
    @classmethod
    def convert_none_to_default_float(cls, v: float | None) -> float:
        """将 None 转换为 0.0。"""
        return 0.0 if v is None else v

    @field_validator("volume")
    @classmethod
    def convert_none_to_default_int(cls, v: int | None) -> int:
        """将 None 转换为 0，但拒绝负值。"""
        if v is None:
            return 0
        if v < 0:
            raise ValueError("成交量不能为负数")
        return v
