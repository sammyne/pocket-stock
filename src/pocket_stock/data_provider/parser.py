"""腾讯财经数据解析器。"""

import json
from datetime import datetime
from typing import Any

from pydantic import ValidationError

from pocket_stock.data_provider.exceptions import DataParseException
from pocket_stock.data_provider.models import StockQuote


class TencentFinanceParser:
    """腾讯财经数据解析器。

    该类负责解析腾讯财经返回的股票数据，并将其转换为 StockQuote 对象。
    支持异步操作，包含数据清洗、转换和验证功能。

    Examples:
        >>> parser = TencentFinanceParser()
        >>> data = '{"sh600000": {"name": "浦发银行", "price": 10.25}}'
        >>> quote = await parser.parse(data, "sh600000")
    """

    # 腾讯财经 API 数据字段映射
    _FIELD_MAPPING = {
        "name": "name",
        "current_price": "price",
        "change": "change",
        "change_percent": "percent",
        "volume": "volume",
        "turnover": "turnover",
        "open_price": "open",
        "close_price": "close",
        "high_price": "high",
        "low_price": "low",
    }

    async def parse(self, raw_data: str, stock_code: str) -> StockQuote:
        """异步解析腾讯财经返回的数据。

        Args:
            raw_data: 腾讯财经返回的原始数据
                支持 JSON 格式：'{"sh600000": {"name": "浦发银行", "price": 10.25}}'
                或腾讯财经实际格式：'v_sh600000="1~浦发银行~600000~..."'
            stock_code: 股票代码

        Returns:
            解析后的 StockQuote 对象

        Raises:
            DataParseException: 当数据解析失败或格式不符合预期时
            ValidationError: 当 pydantic 模型验证失败时

        Examples:
            >>> parser = TencentFinanceParser()
            >>> data = '{"sh600000": {"name": "浦发银行", "price": 10.25}}'
            >>> quote = await parser.parse(data, "sh600000")
        """
        # 优先尝试解析为 JSON
        try:
            data_dict = json.loads(raw_data)
            stock_data, actual_stock_code = self._extract_stock_data(data_dict, stock_code)
            cleaned_data = self._clean_data(stock_data, actual_stock_code)
            return self._to_stock_quote(cleaned_data, actual_stock_code)
        except json.JSONDecodeError:
            # JSON 解析失败，尝试腾讯财经的 v_code="..." 格式
            pass
        except DataParseException:
            # JSON 解析成功但提取数据失败，直接抛出
            raise

        # 尝试解析腾讯财经的 var 格式
        try:
            return self._parse_var_format(raw_data, stock_code)
        except DataParseException:
            # 两种格式都失败，抛出 JSON 解析失败的错误（因为这是最可能的错误）
            raise DataParseException(stock_code, "JSON 解析失败: Expecting value")

    def _extract_stock_data(self, data_dict: dict[str, Any], stock_code: str) -> tuple[dict[str, Any], str]:
        """从返回数据中提取股票数据。

        Args:
            data_dict: 解析后的数据字典
            stock_code: 股票代码

        Returns:
            (股票数据字典, 实际股票代码) 的元组

        Raises:
            DataParseException: 当找不到对应股票数据时
        """
        # 尝试直接获取
        if stock_code in data_dict:
            return data_dict[stock_code], stock_code

        # 尝试不区分大小写获取
        for key in data_dict:
            if key.lower() == stock_code.lower():
                return data_dict[key], stock_code

        # 尝试获取第一个键（某些 API 格式）
        if data_dict:
            actual_code = next(iter(data_dict.keys()))
            return next(iter(data_dict.values())), actual_code

        raise DataParseException(stock_code, "未找到股票数据")

    def _parse_var_format(self, raw_data: str, stock_code: str) -> StockQuote:
        """解析腾讯财经的 v_code="..." 格式数据。

        腾讯财经 API 实际返回的格式是：
        v_sh600000="1~浦发银行~600000~10.18~10.12~10.11~611715~303022~308694~10.18~..."

        Args:
            raw_data: 腾讯财经返回的原始数据
            stock_code: 股票代码

        Returns:
            解析后的 StockQuote 对象

        Raises:
            DataParseException: 当数据解析失败时
        """
        # 移除末尾的分号和换行符
        raw_data = raw_data.rstrip().rstrip(';')

        # 提取变量名和值部分
        # 格式：v_sh600000="1~浦发银行~600000~..."
        if not raw_data.startswith('v_') or '=' not in raw_data:
            raise DataParseException(stock_code, "数据格式错误：无法识别腾讯财经格式")

        # 提取引号中的数据部分
        try:
            _, value_part = raw_data.split('=', 1)
            value_part = value_part.strip()
            if not (value_part.startswith('"') and value_part.endswith('"')):
                raise DataParseException(stock_code, "数据格式错误：缺少引号")
            data_str = value_part[1:-1]  # 移除引号
        except ValueError as e:
            raise DataParseException(stock_code, f"数据格式错误：{e}") from e

        # 使用 ~ 分割字段
        fields = data_str.split('~')
        if len(fields) < 4:
            raise DataParseException(stock_code, f"数据格式错误：字段数量不足（{len(fields)}）")

        # 腾讯财经字段映射（根据实际返回的数据结构）
        # fields[0]: 未知（可能是状态）
        # fields[1]: 股票名称
        # fields[2]: 股票代码
        # fields[3]: 当前价
        # fields[4]: 昨收
        # fields[5]: 今开
        # fields[6]: 成交量（手）
        # fields[7]: 外盘
        # fields[8]: 内盘
        # fields[9]: 昨收（重复）
        # ... 更多字段

        try:
            stock_name = fields[1]
            current_price = float(fields[3])
            close_price = float(fields[4])
            open_price = float(fields[5])
            volume = int(float(fields[6])) if fields[6] else 0

            # 计算涨跌额和涨跌幅
            change = current_price - close_price if close_price > 0 else 0.0
            change_percent = (change / close_price * 100) if close_price > 0 else 0.0

            # 构建数据字典
            cleaned_data = {
                "stock_code": stock_code,
                "name": stock_name,
                "current_price": current_price,
                "change": change,
                "change_percent": change_percent,
                "volume": volume,
                "turnover": 0.0,
                "open_price": open_price,
                "close_price": close_price,
                "high_price": None,
                "low_price": None,
                "timestamp": datetime.now(),
            }

            return self._to_stock_quote(cleaned_data, stock_code)
        except (ValueError, TypeError, IndexError) as e:
            raise DataParseException(stock_code, f"数据解析失败：{e}") from e

    def _clean_data(self, raw_data: dict[str, Any], stock_code: str) -> dict[str, Any]:
        """清洗和转换数据。

        Args:
            raw_data: 原始股票数据
            stock_code: 股票代码

        Returns:
            清洗后的数据字典
        """
        cleaned: dict[str, Any] = {}

        for target_field, source_field in self._FIELD_MAPPING.items():
            value = raw_data.get(source_field)

            # 转换数值类型
            if value is not None and value != "":
                try:
                    if target_field in (
                        "current_price",
                        "change",
                        "change_percent",
                        "turnover",
                        "open_price",
                        "close_price",
                        "high_price",
                        "low_price",
                    ):
                        cleaned[target_field] = float(value)
                    elif target_field == "volume":
                        cleaned[target_field] = int(float(value))
                    else:
                        cleaned[target_field] = str(value)
                except (ValueError, TypeError):
                    # 转换失败，使用默认值（pydantic 会进行验证）
                    cleaned[target_field] = None
            else:
                cleaned[target_field] = None

        # 确保必填字段存在
        cleaned["stock_code"] = stock_code

        # 添加时间戳
        cleaned["timestamp"] = datetime.now()

        return cleaned

    def _to_stock_quote(self, data: dict[str, Any], stock_code: str) -> StockQuote:
        """将清洗后的数据转换为 StockQuote 对象。

        使用 pydantic BaseModel，会自动进行数据验证。

        Args:
            data: 清洗后的数据
            stock_code: 股票代码

        Returns:
            StockQuote 对象

        Raises:
            ValidationError: 当 pydantic 模型验证失败时
        """
        try:
            return StockQuote(**data)
        except ValidationError as e:
            # 将 pydantic 的 ValidationError 转换为 DataParseException
            error_details = "; ".join(f"{err['loc'][0]}: {err['msg']}" for err in e.errors())
            raise DataParseException(stock_code, f"数据验证失败: {error_details}") from e
