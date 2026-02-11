"""数据模型模块。

定义股票分析结果的结构化数据模型。
"""

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ChecklistItem(BaseModel):
    """检查清单项模型。

    表示投资分析中的单个检查项。

    Attributes:
        content: 检查项的内容描述。
        status: 检查项的状态符号，使用 ✅/⚠️/❌ 表示。
    """

    content: str = Field(..., description="检查项的内容描述")
    status: Literal["✅", "⚠️", "❌"] = Field(..., description="检查项的状态符号")

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        """验证状态符号。

        Args:
            value: 状态符号。

        Returns:
            验证通过的状态符号。

        Raises:
            ValueError: 当状态符号不在允许范围内时抛出。
        """
        if value not in {"✅", "⚠️", "❌"}:
            raise ValueError("状态符号必须是 ✅、⚠️ 或 ❌")
        return value


class PositionSuggestion(BaseModel):
    """持仓分类建议模型。

    表示针对不同持仓状态的操作建议。

    Attributes:
        no_position: 空仓者的操作建议。
        has_position: 持仓者的操作建议。
    """

    no_position: str = Field(..., description="空仓者的操作建议")
    has_position: str = Field(..., description="持仓者的操作建议")


class TargetPrices(BaseModel):
    """具体狙击点位模型。

    表示买入价、止损价和目标价。

    Attributes:
        buy_price: 买入价，精确到分（保留两位小数）。
        stop_loss_price: 止损价，精确到分（保留两位小数）。
        target_price: 目标价，精确到分（保留两位小数），卖出建议时为 None。
    """

    buy_price: float | None = Field(None, description="买入价，精确到分")
    stop_loss_price: float | None = Field(None, description="止损价，精确到分")
    target_price: float | None = Field(None, description="目标价，精确到分")

    @field_validator("buy_price", "stop_loss_price", "target_price", mode="before")
    @classmethod
    def validate_price_precision(cls, value: float | None) -> float | None:
        """验证价格精度。

        确保价格保留两位小数。

        Args:
            value: 价格值。

        Returns:
            保留两位小数的价格值。

        Raises:
            ValueError: 当价格精度不符合要求时抛出。
        """
        if value is None:
            return None
        # 保留两位小数
        rounded_value = round(value, 2)
        # 验证原始值与四舍五入后的值是否一致
        if abs(value - rounded_value) > 0.001:
            raise ValueError("价格必须精确到分（保留两位小数）")
        return rounded_value


class StockAnalysisResult(BaseModel):
    """股票分析结果模型。

    表示 LLM 生成的完整股票分析结果。

    Attributes:
        stock_name: 股票名称，必须为正确的中文全称。
        conclusion: 核心结论，一句话概括投资建议（该买/该卖/该等）。
        position_suggestion: 持仓分类建议。
        target_prices: 具体狙击点位。
        checklist: 检查清单，包含多个检查项。
    """

    stock_name: str = Field(..., description="股票名称，中文全称")
    conclusion: str = Field(..., description="核心结论，一句话概括投资建议")
    position_suggestion: PositionSuggestion = Field(..., description="持仓分类建议")
    target_prices: TargetPrices = Field(..., description="具体狙击点位")
    checklist: list[ChecklistItem] = Field(..., description="检查清单")

    @field_validator("checklist")
    @classmethod
    def validate_checklist_length(cls, value: list[ChecklistItem]) -> list[ChecklistItem]:
        """验证检查清单长度。

        Args:
            value: 检查清单列表。

        Returns:
            验证通过的检查清单。

        Raises:
            ValueError: 当检查清单长度不在 5-10 范围内时抛出。
        """
        if len(value) < 5 or len(value) > 10:
            raise ValueError("检查清单必须包含 5-10 个检查项")
        return value
