"""腾讯财经数据解析器。"""

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
        >>> data = 'v_sh600000="1~浦发银行~600000~10.18~..."'
        >>> quote = await parser.parse(data, "sh600000")
    """

    async def parse(self, raw_data: str, stock_code: str) -> StockQuote:
        """异步解析腾讯财经返回的数据。

        腾讯财经 API 返回的数据格式为（以 ~ 分隔的66个字段）：
        v_sh600000="1~浦发银行~600000~10.18~10.12~10.11~611715~..."

        数据结构样例：

        | 字段索引 | 字段名称 | 说明 | 示例值 |
        |----------|----------|------|--------|
        | 0 | 未知 | 固定为1 | 1 |
        | 1 | 股票名称 | 中文名称 | 贵州茅台 |
        | 2 | 股票代码 | 数字代码 | 600519 |
        | 3 | 当前价格 | 最新成交价 | 1670.00 |
        | 4 | 昨日收盘价 | 前收盘 | 1680.00 |
        | 5 | 今日开盘价 | 开盘价 | 1675.00 |
        | 6 | 成交量(手) | 累计成交量 | 12345 |
        | 7 | 外盘 | 主动买入成交量 | 6789 |
        | 8 | 内盘 | 主动卖出成交量 | 5556 |
        | 9-28 | 买卖盘 | 买一~买五、卖一~卖五价格和数量 | - |
        | 29 | 最近逐笔成交 | 成交明细 | 15:00:03/1670.00/100/M |
        | 30 | 更新时间 | 时间戳 | 20250208150003 |
        | 31 | 涨跌 | 涨跌额 | -10.00 |
        | 32 | 涨跌幅% | 百分比 | -0.60 |
        | 33 | 最高价 | 今日最高 | 1685.00 |
        | 34 | 最低价 | 今日最低 | 1660.00 |
        | 35 | 价格/成交量/成交额 | 综合数据 | 1670.00/12345/20641500 |
        | 36 | 成交量(手) | 总成交量 | 12345 |
        | 37 | 成交额(万) | 总成交额(万元) | 20641.50 |
        | 38 | 换手率% | 换手率 | 0.10 |
        | 39 | 市盈率 | 动态市盈率 | 25.50 |
        | 40 | 未知 | 保留字段 | - |
        | 41 | 最高 | 重复字段 | 1685.00 |
        | 42 | 最低 | 重复字段 | 1660.00 |
        | 43 | 振幅% | 振幅 | 1.49 |
        | 44 | 流通市值 | 流通市值(亿) | 21000.50 |
        | 45 | 总市值 | 总市值(亿) | 21000.50 |
        | 46 | 市净率 | 市净率 | 8.50 |
        | 47 | 涨停价 | 涨停限制 | 1848.00 |
        | 48 | 跌停价 | 跌停限制 | 1512.00 |
        | 49 | 量比 | 量比 | 0.85 |
        | 50 | 委差 | 委买委卖差 | -500 |
        | 51 | 委比% | 委比 | -10.00 |
        | 52 | 均价 | 成交均价 | 1672.50 |
        | 53 | 52周最高 | 52周最高价 | 1900.00 |
        | 54 | 52周最低 | 52周最低价 | 1400.00 |
        | 55 | 历史最高 | 历史最高价 | 2600.00 |
        | 56 | 历史最低 | 历史最低价 | 20.00 |
        | 57 | 股息率% | 股息率 | 1.50 |
        | 58 | 股息(TTM) | 股息 | 25.00 |
        | 59 | 每股收益 | EPS | 65.00 |
        | 60 | 每股净资产 | BPS | 196.00 |
        | 61 | 总股本 | 总股本(亿) | 12.56 |
        | 62 | 流通股 | 流通股(亿) | 12.56 |
        | 63 | 行业 | 所属行业 | 白酒 |
        | 64 | 地区 | 所属地区 | 贵州 |
        | 65 | 上市日期 | IPO日期 | 20010827 |

        Args:
            raw_data: 腾讯财经返回的原始数据，格式：'v_sh600000="1~浦发银行~600000~..."'
            stock_code: 股票代码

        Returns:
            解析后的 StockQuote 对象

        Raises:
            DataParseException: 当数据解析失败或格式不符合预期时
            ValidationError: 当 pydantic 模型验证失败时

        Examples:
            >>> parser = TencentFinanceParser()
            >>> data = 'v_sh600000="1~浦发银行~600000~10.18~..."'
            >>> quote = await parser.parse(data, "sh600000")
        """
        return self._parse_var_format(raw_data, stock_code)

    def _parse_var_format(self, raw_data: str, stock_code: str) -> StockQuote:
        """解析腾讯财经的 v_code="..." 格式数据。

        腾讯财经 API 实际返回的格式是（以 ~ 分隔的66个字段）：
        v_sh600000="1~贵州茅台~600519~1670.00~1680.00~1675.00~12345~...~20641.50~..."

        Args:
            raw_data: 腾讯财经返回的原始数据
            stock_code: 股票代码

        Returns:
            解析后的 StockQuote 对象

        Raises:
            DataParseException: 当数据解析失败时
        """
        # 移除末尾的分号和换行符
        raw_data = raw_data.rstrip().rstrip(";")

        # 提取变量名和值部分
        # 格式：v_sh600000="1~浦发银行~600000~..."
        if not raw_data.startswith("v_") or "=" not in raw_data:
            raise DataParseException(stock_code, "数据格式错误：无法识别腾讯财经格式")

        # 提取引号中的数据部分
        try:
            _, value_part = raw_data.split("=", 1)
            value_part = value_part.strip()
            if not (value_part.startswith('"') and value_part.endswith('"')):
                raise DataParseException(stock_code, "数据格式错误：缺少引号")
            data_str = value_part[1:-1]  # 移除引号
        except ValueError as e:
            raise DataParseException(stock_code, f"数据格式错误：{e}") from e

        # 使用 ~ 分割字段
        fields = data_str.split("~")
        if len(fields) < 38:
            raise DataParseException(stock_code, f"数据格式错误：字段数量不足（{len(fields)}），需要至少38个字段")

        # 腾讯财经字段映射（根据实际返回的数据结构）
        # fields[0]: 未知（固定为1）
        # fields[1]: 股票名称
        # fields[2]: 股票代码（数字代码）
        # fields[3]: 当前价格
        # fields[4]: 昨日收盘价
        # fields[5]: 今日开盘价
        # fields[6]: 成交量（手）
        # fields[7]: 外盘
        # fields[8]: 内盘
        # fields[9-28]: 买一~买五、卖一~卖五价格和数量
        # fields[29]: 最近逐笔成交
        # fields[30]: 更新时间
        # fields[31]: 涨跌
        # fields[32]: 涨跌幅%
        # fields[33]: 最高价
        # fields[34]: 最低价
        # fields[35]: 价格/成交量/成交额（综合数据）
        # fields[36]: 成交量（手，重复）
        # fields[37]: 成交额（万元）
        # fields[38-65]: 更多扩展字段...

        try:
            stock_name = fields[1]
            current_price = float(fields[3])
            close_price = float(fields[4])
            open_price = float(fields[5])
            volume = int(float(fields[6])) if fields[6] else 0
            change = float(fields[31]) if fields[31] else 0.0
            change_percent = float(fields[32]) if fields[32] else 0.0
            high_price = float(fields[33]) if fields[33] else None
            low_price = float(fields[34]) if fields[34] else None
            turnover_wan = float(fields[37]) if fields[37] else 0.0

            # 构建数据字典
            cleaned_data = {
                "stock_code": stock_code,
                "name": stock_name,
                "current_price": current_price,
                "change": change,
                "change_percent": change_percent,
                "volume": volume,
                "turnover": turnover_wan * 10000,  # 腾讯财经返回的是万元，转换为元
                "open_price": open_price,
                "close_price": close_price,
                "high_price": high_price,
                "low_price": low_price,
                "timestamp": datetime.now(),
            }

            return self._to_stock_quote(cleaned_data, stock_code)
        except (ValueError, TypeError, IndexError) as e:
            raise DataParseException(stock_code, f"数据解析失败：{e}") from e

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
