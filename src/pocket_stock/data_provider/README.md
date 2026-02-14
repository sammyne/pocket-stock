# 数据提供者模块 (data_provider)

## 简介

`data_provider` 是一个金融数据获取模块，用于从腾讯财经获取股票的实时行情数据。该模块提供了异步接口，支持配置自定义请求参数，并包含完善的错误处理和日志记录功能。

**主要特性：**
- 使用 `pydantic` 进行数据建模和验证
- 异步接口，基于 `aiohttp` 实现
- 从腾讯财经获取实时股票行情
- 支持自定义请求超时
- 完善的错误处理和自定义异常类型
- 数据验证和清洗
- 详细的日志记录
- 支持依赖注入，便于测试
- 完整的类型注解和中文文档

## 特性

- ✅ 使用 `pydantic BaseModel` 进行数据建模，自动验证数据类型和约束
- ✅ 异步接口，基于 `aiohttp` 实现
- ✅ 从腾讯财经获取实时股票行情
- ✅ 支持自定义请求超时
- ✅ 完善的错误处理和自定义异常类型
- ✅ 数据验证和清洗
- ✅ 详细的日志记录
- ✅ 支持依赖注入，便于测试
- ✅ 完整的类型注解和中文文档

## 安装

```bash
# 确保安装了必要的依赖
pip install aiohttp pydantic pytest pytest-asyncio pytest-mock

# 或使用 uv
uv pip install aiohttp pydantic pytest pytest-asyncio pytest-mock
```

## 快速开始

### 基本使用

```python
import asyncio
from pocket_stock.data_provider import (
    ProviderConfig,
    StockDataProvider,
)

async def main():
    # 创建配置
    config = ProviderConfig(timeout=10.0)

    # 创建数据提供者
    async with StockDataProvider(config) as provider:
        # 获取股票行情
        quote = await provider.get_stock_quote("sh600000")

        # 打印结果
        print(f"股票名称: {quote.name}")
        print(f"当前价格: {quote.current_price}")
        print(f"涨跌额: {quote.change}")
        print(f"涨跌幅: {quote.change_percent}%")
        print(f"成交量: {quote.volume}")
        print(f"成交额: {quote.turnover}")

# 运行
asyncio.run(main())
```

### 高级配置

```python
import asyncio
from pocket_stock.data_provider import ProviderConfig, StockDataProvider

async def main():
    # 创建自定义配置
    config = ProviderConfig(
        timeout=15.0,
    )

    # 使用自定义配置
    async with StockDataProvider(config) as provider:
        quote = await provider.get_stock_quote("sz000001")
        print(f"{quote.name}: {quote.current_price}")

asyncio.run(main())
```

### 股票代码格式

支持的股票代码格式：
- 上海市场：`sh` + 6 位数字（如 `sh600000`）
- 深圳市场：`sz` + 6 位数字（如 `sz000001`）

示例：
- `sh600000` - 浦发银行
- `sh000001` - 上证指数
- `sz000001` - 平安银行
- `sz399001` - 深证成指

## API 文档

### 配置类

#### `ProviderConfig`

数据提供者配置类，基于 `pydantic.BaseModel`，提供自动数据验证。

**参数：**
- `timeout` (float): 异步请求超时时间（秒），默认 10.0，必须 > 0

**Pydantic 验证规则：**
- `timeout`: 必须 > 0

**类方法：**
- `from_dict(config_dict: Mapping[str, Any]) -> ProviderConfig`: 从字典创建配置对象

**示例：**
```python
from pocket_stock.data_provider import ProviderConfig

# 创建默认配置
config = ProviderConfig()

# 创建自定义配置
config = ProviderConfig(timeout=15.0)

# 从字典创建配置
config = ProviderConfig.from_dict({
    "timeout": 15.0
})

# 无效数据会引发 ValidationError
try:
    invalid_config = ProviderConfig(timeout=-1.0)  # 负数会验证失败
except ValidationError as e:
    print(f"验证失败: {e}")
```

### 数据提供者

#### `StockDataProvider`

股票数据提供者类，提供异步获取股票行情的接口。

**构造函数：**
```python
StockDataProvider(
    config: ProviderConfig,
    session: aiohttp.ClientSession | None = None
)
```

**方法：**

##### `async get_stock_quote(stock_code: str) -> StockQuote`

获取指定股票的实时行情。

**参数：**
- `stock_code` (str): 股票代码

**返回：**
- `StockQuote`: 股票行情数据对象

**异常：**
- `InvalidStockCodeError`: 当股票代码无效时
- `NetworkError`: 当网络连接失败或超时时
- `ProviderServiceError`: 当数据提供者返回错误状态码时

### 数据模型

#### `StockQuote`

股票行情数据模型，基于 `pydantic.BaseModel`，提供自动数据验证。

**属性：**
- `stock_code` (str): 股票代码（必填，非空）
- `name` (str): 股票名称（必填，非空）
- `current_price` (float): 当前价格（必填，>= 0）
- `change` (float): 涨跌额（默认 0.0）
- `change_percent` (float): 涨跌幅（百分比，默认 0.0）
- `volume` (int): 成交量（默认 0，>= 0）
- `turnover` (float): 成交额（默认 0.0，>= 0）
- `open_price` (float | None): 开盘价（可选，>= 0）
- `close_price` (float | None): 收盘价（可选，>= 0）
- `high_price` (float | None): 最高价（可选，>= 0）
- `low_price` (float | None): 最低价（可选，>= 0）
- `timestamp` (datetime | None): 数据时间戳（可选）

**Pydantic 验证规则：**
- `stock_code`: 必填，不能为空
- `name`: 必填，不能为空
- `current_price`: 必填，必须 >= 0
- 所有数值字段：必须 >= 0
- 创建实例时会自动进行数据验证

**示例：**
```python
from pocket_stock.data_provider import StockQuote

# 创建有效实例
quote = StockQuote(
    stock_code="sh600000",
    name="浦发银行",
    current_price=10.25,
    volume=1000000
)

# 无效数据会引发 ValidationError
try:
    invalid_quote = StockQuote(
        stock_code="",  # 空值会验证失败
        name="浦发银行",
        current_price=10.25
    )
except ValidationError as e:
    print(f"验证失败: {e}")
```

**序列化：**
```python
# 转换为字典
data = quote.model_dump()

# 转换为 JSON 字符串
json_str = quote.model_dump_json()
```

### 验证函数

#### `validate_stock_code_format(stock_code: str) -> bool`

验证股票代码格式是否正确。

**参数：**
- `stock_code` (str): 股票代码

**返回：**
- `bool`: 格式正确返回 True，否则返回 False

#### `validate_stock_quote(quote: StockQuote) -> None`

验证股票行情数据的完整性和正确性。

**参数：**
- `quote` (StockQuote): 待验证的股票行情对象

**异常：**
- `DataValidationError`: 当数据验证失败时

### 异常类

所有异常都继承自 `DataProviderError`。

- `InvalidStockCodeError`: 股票代码无效异常
- `NetworkError`: 网络错误异常
- `ProviderServiceError`: 数据提供者服务错误异常
- `DataParseError`: 数据解析错误异常
- `DataValidationError`: 数据验证错误异常

**注意：** 当使用 `pydantic` 进行数据验证时，无效的数据会引发 `pydantic.ValidationError`，解析器会将其转换为 `DataParseError`。

## 错误处理

```python
import asyncio
from pocket_stock.data_provider import (
    ProviderConfig,
    StockDataProvider,
    InvalidStockCodeException,
    NetworkErrorException,
    ProviderServiceErrorException,
)
from pydantic import ValidationError

async def main():
    config = ProviderConfig(timeout=10.0)

    async with StockDataProvider(config) as provider:
        try:
            quote = await provider.get_stock_quote("sh600000")
            print(f"股票名称: {quote.name}, 价格: {quote.current_price}")

        except InvalidStockCodeException as e:
            print(f"股票代码错误: {e}")

        except NetworkErrorException as e:
            print(f"网络错误: {e}")

        except ProviderServiceErrorException as e:
            print(f"服务错误: {e}")

        except ValidationError as e:
            # 直接使用 StockQuote 时可能遇到此异常
            print(f"数据验证错误: {e}")

asyncio.run(main())
```

### Pydantic 验证

使用 `pydantic` 进行数据验证时，以下情况会自动引发 `ValidationError`：

1. **必填字段缺失**：`stock_code` 或 `name` 为空
2. **数值范围错误**：价格、成交量等字段为负数
3. **类型错误**：字段类型不匹配

所有验证错误都会在创建实例时自动检测，无需手动调用验证函数。

## 日志

模块使用 Python 标准库 `logging` 模块记录日志。日志级别固定为 INFO。

日志记录以下内容：
- 请求开始（股票代码和超时时间）
- 响应成功（股票代码和耗时）
- 错误信息（异常详情）

日志级别：
- `INFO`: 请求和响应的一般信息
- `ERROR`: 错误信息

## 测试

### 运行单元测试

```bash
# 运行所有单元测试
pytest tests/

# 运行特定测试文件
pytest tests/test_provider.py

# 运行测试并生成覆盖率报告
pytest tests/ --cov=src/pocket_stock/data_provider --cov-report=html
```

### 运行集成测试

集成测试会实际访问腾讯财经 API，需要网络连接。

```bash
# 运行集成测试
pytest tests/ -v --integration

# 只运行集成测试
pytest tests/test_integration.py -v --integration
```

## 开发规范

本项目遵循以下开发规范：

- Python >= 3.13
- PEP 8 代码规范
- 4 空格缩进
- 120 字符行长度
- 类型注解（Type Hints）
- 中文文档字符串
- 使用 `pytest` 测试框架
- 测试覆盖率 >= 80%

详见 [AGENTS.md](/Users/xiangminli/Workspaces/gitcode.com/sammyne/pocket-stock/AGENTS.md)。

## 注意事项

1. 本模块不包含重试机制，网络错误会直接抛出异常
2. 所有接口都是异步的，需要在异步上下文中使用
3. 推荐使用 `async with` 语句管理资源
4. 腾讯财经 API 可能有访问频率限制，请合理使用
5. 本模块仅供学习和个人使用，请勿用于商业用途

## 许可证

本项目遵循项目主许可证。

## 贡献

欢迎提交 Issue 和 Pull Request。
