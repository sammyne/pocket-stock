# LLM 股票分析模块

该模块提供基于大语言模型（LLM）的股票分析功能，能够根据股票实时行情和相关新闻资讯，生成结构化的投资决策建议。

## 功能特性

- **智能分析**：基于股票实时行情和多维度新闻资讯进行综合分析
- **结构化输出**：返回包含股票名称、核心结论、持仓建议、狙击点位、检查清单的结构化结果
- **灵活配置**：支持任意兼容 OpenAI API 的 LLM 服务（如阿里云通义千问、OpenAI GPT 等）
- **错误处理**：完善的异常处理机制，覆盖超时、认证、网络、解析等各种错误场景

## 安装依赖

该模块依赖 `langchain-openai`，已在项目依赖中配置：

```bash
pip install langchain-openai
```

## 配置说明

在使用前，需要在项目根目录创建 `.env` 文件，配置以下环境变量：

```bash
# OpenAI 兼容的模型名称
OPENAI_MODEL=qwen-max

# OpenAI 兼容的 API 服务地址
OPENAI_API_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# 访问 API 服务所需的密钥
OPENAI_API_KEY=your-api-key-here
```

参考 `.env.example` 文件获取配置模板。

## 使用方法

### 基本用法

```python
from pocket_stock.llm import analyse_stock
from pocket_stock.data_provider import StockQuote
from pocket_stock.search import StockSearchResponse

# 准备股票行情数据
stock_quote = StockQuote(
    stock_code="sh600519",
    name="贵州茅台",
    current_price=1800.00,
    change=10.00,
    change_percent=0.56,
    volume=10000,
    turnover=18000000.00,
    open_price=1790.00,
    close_price=1795.00,
    high_price=1805.00,
    low_price=1788.00,
)

# 准备新闻资讯数据
stock_news = StockSearchResponse(
    stock_name="贵州茅台",
    dimensions={
        StockSearchDimension.LATEST_NEWS: news_response,
        StockSearchDimension.RISK_ANALYSIS: risk_response,
    },
    total_time=0.8,
)

# 执行分析
result = analyse_stock(stock_quote, stock_news)

# 查看结果
print(f"股票名称: {result.stock_name}")
print(f"核心结论: {result.conclusion}")
print(f"空仓者建议: {result.position_suggestion.no_position}")
print(f"持仓者建议: {result.position_suggestion.has_position}")
print(f"买入价: {result.target_prices.buy_price}")
print(f"止损价: {result.target_prices.stop_loss_price}")
print(f"目标价: {result.target_prices.target_price}")
print("检查清单:")
for item in result.checklist:
    print(f"  {item.status} {item.content}")
```

### 高级用法

```python
from pocket_stock.llm import LLMStockAnalyser
from pocket_stock.llm.config import LLMConfig

# 自定义配置
config = LLMConfig(
    openai_model="gpt-4",
    openai_api_base_url="https://api.openai.com/v1",
    openai_api_key="sk-xxx",
)

# 创建分析器实例
analyser = LLMStockAnalyser(config)

# 执行分析
result = analyser.analyse(stock_quote, stock_news)
```

## 输出格式

`analyse_stock` 函数返回 `StockAnalysisResult` 对象，包含以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `stock_name` | `str` | 股票名称（中文全称） |
| `conclusion` | `str` | 核心结论，一句话概括（该买/该卖/该等） |
| `position_suggestion` | `PositionSuggestion` | 持仓分类建议 |
| `position_suggestion.no_position` | `str` | 空仓者的操作建议 |
| `position_suggestion.has_position` | `str` | 持仓者的操作建议 |
| `target_prices` | `TargetPrices` | 具体狙击点位 |
| `target_prices.buy_price` | `float \| None` | 买入价（精确到分） |
| `target_prices.stop_loss_price` | `float \| None` | 止损价（精确到分） |
| `target_prices.target_price` | `float \| None` | 目标价（精确到分） |
| `checklist` | `list[ChecklistItem]` | 检查清单（5-10项） |
| `checklist[].content` | `str` | 检查项内容 |
| `checklist[].status` | `str` | 检查项状态（✅/⚠️/❌） |

## 异常处理

该模块定义了以下异常类型：

| 异常类 | 说明 |
|--------|------|
| `ConfigurationError` | 配置错误（缺少必需配置或配置无效） |
| `LLMApiTimeoutError` | LLM API 调用超时 |
| `LLMAuthenticationError` | API 密钥无效或认证失败 |
| `LLMServiceError` | LLM 服务返回错误 |
| `NetworkConnectionError` | 网络连接失败 |
| `LLMResponseParseError` | 响应解析失败或格式不符合预期 |

### 异常处理示例

```python
from pocket_stock.llm import analyse_stock
from pocket_stock.llm.exceptions import (
    ConfigurationError,
    LLMApiTimeoutError,
    LLMAuthenticationError,
    LLMServiceError,
    NetworkConnectionError,
    LLMResponseParseError,
)

try:
    result = analyse_stock(stock_quote, stock_news)
except ConfigurationError as e:
    print(f"配置错误: {e}")
except LLMApiTimeoutError as e:
    print(f"API 调用超时: {e}")
except LLMAuthenticationError as e:
    print(f"认证失败: {e}")
except LLMServiceError as e:
    print(f"服务错误: {e}")
except NetworkConnectionError as e:
    print(f"网络连接失败: {e}")
except LLMResponseParseError as e:
    print(f"响应解析失败: {e}")
```

## 支持的 LLM 服务

该模块支持任何兼容 OpenAI API 的 LLM 服务，包括但不限于：

- **阿里云通义千问**：https://dashscope.aliyuncs.com/compatible-mode/v1
- **OpenAI GPT**：https://api.openai.com/v1
- **其他兼容 OpenAI API 的服务**

配置时只需设置正确的 `OPENAI_MODEL` 和 `OPENAI_API_BASE_URL` 即可。

## 测试

运行单元测试：

```bash
pytest tests/test_llm_*.py -v
```

运行集成测试：

```bash
pytest tests/test_llm_integration.py -v -m integration
```

运行所有测试并检查覆盖率：

```bash
pytest tests/ -v --cov=src/pocket_stock/llm --cov-report=html
```

## 注意事项

1. 确保 `.env` 文件中的 API 密钥正确
2. 根据选择的 LLM 服务设置正确的 `OPENAI_API_BASE_URL`
3. API 调用可能产生费用，请注意使用量
4. 检查清单必须包含 5-10 个检查项
5. 所有价格必须精确到分（保留两位小数）
6. 股票名称必须是中文全称，不包含股票代码
