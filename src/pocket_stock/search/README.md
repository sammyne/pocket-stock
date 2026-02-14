# 搜索模块

基于 Tavily 的搜索服务模块，为 pocket-stock 项目提供强大的网络搜索能力。

## 功能特性

- 统一的搜索接口：提供一致的 API，支持同步和异步搜索
- 可配置的搜索选项：支持搜索深度、结果数量、时间范围等配置
- 异步支持：支持并发搜索请求，提高性能
- 完整的数据模型：使用 Pydantic 进行数据验证
- 错误处理：完善的异常处理和日志记录
- 安全配置：通过环境变量管理 API key

## 安装

### 依赖要求

- Python >= 3.13
- tavily-python >= 0.3.0
- pydantic >= 2.0.0
- pydantic-settings >= 2.0.0
- aiohttp >= 3.9.0

### 安装依赖

```bash
pip install -e .
```

## 配置

### 环境变量

模块使用 `pydantic-settings` 自动加载配置，支持从环境变量和 `.env` 文件中读取配置。

在项目根目录创建 `.env` 文件，配置 Tavily API key：

```env
TAVILY_API_KEY=your_api_key_here
```

`pydantic-settings` 会自动从以下位置读取配置（按优先级从高到低）：
1. 环境变量
2. `.env` 文件（项目根目录）

### 获取 API Key

访问 [Tavily](https://tavily.com/) 注册账号并获取 API key。

## 使用方法

### 基本使用

```python
from pocket_stock.search import SearchService, SearchOptions, SearchDepth, SearchTimeRange

# 初始化搜索服务
service = SearchService()

# 执行搜索
response = service.search("苹果公司 股价")

# 遍历搜索结果
for result in response.results:
    print(f"标题: {result.title}")
    print(f"内容: {result.content}")
    print(f"来源: {result.source}")
    print(f"URL: {result.url}")
    print(f"评分: {result.score}")
    print()
```

### 使用配置

```python
from pocket_stock.search import SearchService, SearchOptions, SearchDepth, SearchTimeRange

# 创建搜索配置
config = SearchOptions(
    max_results=10,
    search_depth=SearchDepth.ADVANCED,
    time_range=SearchTimeRange.WEEK,
    include_answer=True,
)

# 使用配置搜索
service = SearchService()
response = service.search("特斯拉 财报", config=config)

# 获取 AI 生成的答案
if response.answer:
    print(f"AI 答案: {response.answer}")
```

### 异步搜索

```python
import asyncio
from pocket_stock.search import SearchService, SearchOptions

async def main():
    # 初始化搜索服务
    service = SearchService()

    # 执行异步搜索
    response = await service.search_async("英伟达 股票")

    print(f"找到 {response.result_count} 条结果")
    for result in response.results:
        print(f"- {result.title}")

# 运行异步函数
asyncio.run(main())
```

### 并发搜索

```python
import asyncio
from pocket_stock.search import SearchService

async def main():
    service = SearchService()

    # 并发搜索多个查询
    queries = ["苹果股票", "特斯拉股票", "英伟达股票"]
    responses = await service.search_multiple_async(queries)

    # 处理结果
    for query, response in zip(queries, responses):
        print(f"查询: {query}")
        print(f"结果数量: {response.result_count}")
        print()

asyncio.run(main())
```

### 自定义 API Key

```python
from pocket_stock.search import SearchService

# 直接传入 API key（不推荐生产环境使用）
service = SearchService(api_key="your_api_key_here")
```

## API 文档

### SearchService

搜索服务类，提供统一的搜索接口。

#### 方法

- `search(query: str, config: Optional[SearchOptions] = None) -> SearchResponse`
  - 执行同步搜索
  - 参数：
    - `query`: 搜索查询字符串
    - `config`: 可选的搜索配置
  - 返回：搜索响应对象

- `async search_async(query: str, config: Optional[SearchOptions] = None) -> SearchResponse`
  - 执行异步搜索
  - 参数同上
  - 返回：搜索响应对象

- `async search_multiple_async(queries: list[str], config: Optional[SearchOptions] = None) -> list[SearchResponse]`
  - 并发执行多个搜索查询
  - 参数：
    - `queries`: 查询字符串列表
    - `config`: 可选的搜索配置
  - 返回：搜索响应列表

### SearchOptions

搜索配置类，定义搜索的各种选项。

#### 字段

- `max_results`: 最大结果数量（1-20），默认 5
- `search_depth`: 搜索深度（`basic` 或 `advanced`），默认 `basic`
- `time_range`: 搜索时间范围（`day`、`week`、`month`、`year`），默认 None
- `include_domains`: 包含的域名列表
- `exclude_domains`: 排除的域名列表
- `include_answer`: 是否包含 AI 生成的答案，默认 False
- `include_raw_content`: 是否包含原始内容，默认 False
- `include_images`: 是否包含图片，默认 False

### SearchResult

搜索结果模型。

#### 字段

- `title`: 搜索结果标题
- `content`: 搜索结果内容摘要
- `url`: 来源 URL
- `source`: 来源网站名称
- `published_date`: 发布时间（可选）
- `score`: 相关性评分（0-1）

### SearchResponse

搜索响应模型。

#### 字段

- `query`: 搜索查询字符串
- `results`: 搜索结果列表
- `answer`: AI 生成的答案（可选）
- `images`: 图片 URL 列表（可选）
- `response_time`: 响应时间（秒）
- `result_count`: 结果数量（只读属性）

## 异常处理

```python
from pocket_stock.search import SearchService
from pocket_stock.search.exceptions import (
    MissingAPIKeyError,
    ValidationError,
    NetworkError,
    ServiceError,
)

try:
    service = SearchService()
    response = service.search("搜索内容")
except MissingAPIKeyError:
    print("请配置 TAVILY_API_KEY 环境变量")
except ValidationError as e:
    print(f"参数验证失败: {e.message}")
except NetworkError as e:
    print(f"网络错误: {e.message}")
except ServiceError as e:
    print(f"服务错误: {e.message}")
```

## 日志记录

模块使用 Python 的 `logging` 模块记录日志，包括：

- API 调用请求参数（不包含敏感信息）
- 响应状态和结果数量
- 响应时间
- 错误详情和上下文信息

配置日志级别：

```python
import logging

logging.basicConfig(level=logging.INFO)
```

## 项目结构

```
src/pocket_stock/search/
├── __init__.py      # 模块导出
├── client.py        # Tavily 客户端实现
├── config.py        # 配置管理
├── exceptions.py    # 异常定义
├── models.py        # 数据模型
├── service.py       # 搜索服务
└── README.md        # 本文档
```

## 开发注意事项

1. 遵循项目编码规范（`AGENTS.md`）：
   - Python >= 3.13
   - 遵循 PEP 8 规范
   - 使用 PEP 585 和 PEP 604 的类型注解
   - 4 空格缩进，行长度限制为 120 字符
   - 使用中文编写文档和注释

2. 安全要求：
   - 使用 HTTPS 传输 API 请求
   - 日志中不记录敏感的 API key 信息
   - 对用户输入进行基本验证

## 许可证

MIT
