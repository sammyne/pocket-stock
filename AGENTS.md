# AGENTS.md

## 项目概述

**项目名称**：pocket-stock  
**项目版本**：0.1.0  
**开发语言**：Python  
**最低 Python 版本**：>= 3.13  

本项目是一个股票相关工具，旨在为用户提供便捷的股票信息管理和分析功能。

## 技术栈

### 核心技术
- **Python**：>= 3.13
- **包管理工具**：基于 pyproject.toml 的现代 Python 项目管理

### 主要依赖库

- aiohttp 提供一步 HTTP 接口
- pydantic 用于数据建模和配置定义

## 开发规范

需要以下库或 API 文档、代码生成、设置或配置步骤时，始终使用 Context7 MCP，无需等待我的明确要求
- duckdb-python

### 代码风格
- 遵循 PEP 8 规范
- 使用 4 空格缩进，不使用 Tab
- 行长度限制为 120 字符
- 使用类型注解（Type Hints）提高代码可读性

### 类型注解规范
- **优先使用 PEP 585**：Python 3.9+ 支持使用内置类型作为泛型类型
  - `typing.List` -> `list`
  - `typing.Dict` -> `dict`
  - `typing.Tuple` -> `tuple`
  - `typing.Set` -> `set`
  - `typing.FrozenSet` -> `frozenset`
  - `typing.Type` -> `type`
  - `typing.NoReturn` -> `types.NoneType`（Python 3.11+）
  - 对于抽象基类，使用 `collections.abc`：
    - `typing.Iterable` -> `collections.abc.Iterable`
    - `typing.Iterator` -> `collections.abc.Iterator`
    - `typing.Sequence` -> `collections.abc.Sequence`
    - `typing.MutableSequence` -> `collections.abc.MutableSequence`
- **优先使用 PEP 604**：Python 3.10+ 支持使用 `|` 操作符作为 Union 的语法糖
  - `typing.Optional[str]` -> `str | None`
  - `typing.Union[int, str]` -> `int | str`
  - `typing.Union[bool, int, str]` -> `bool | int | str`
- **仅在必要时从 typing 导入**：如 `Optional`、`Union`、`Protocol`、`TypedDict` 等特殊类型
- 示例：
  ```python
  # 推荐
  def process_items(items: list[str]) -> dict[str, int]:
      ...

  # 推荐（使用 | 操作符）
  def get_data(value: str | None) -> dict[str, int] | None:
      ...

  # 不推荐
  from typing import List, Dict, Optional
  def process_items(items: List[str]) -> Optional[Dict[str, int]]:
      ...
  ```

### 命名规范
- **文件名**：使用小写字母和下划线，如 `stock_helper.py`
- **变量名**：使用小写字母和下划线，如 `current_price`
- **常量名**：使用大写字母和下划线，如 `MAX_RETRIES`
- **函数名**：使用小写字母和下划线，如 `get_stock_data()`
- **类名**：使用大驼峰命名法，如 `StockAnalyzer`

### 文档规范
- 所有模块、类、函数必须添加 docstring
- 优先使用中文编写文档和注释
- 在 Markdown 文档中，中文字符与英文字符、数字之间添加空格
- 示例：`这是一个 Python 项目`、`版本 0.1.0`

## 测试要求

### 测试框架
- 使用 `pytest` 作为测试框架
- 测试覆盖率目标：>= 80%

### 测试文件组织
- 测试文件命名为 `test_*.py`
- 测试类命名为 `Test*`
- 测试函数命名为 `test_*`

### 测试运行
```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_main.py

# 生成覆盖率报告
pytest --cov=. --cov-report=html
```

## 错误处理原则

### 异常处理
- 使用具体的异常类型，避免使用裸 `except:` 语句
- 对可预见的错误情况进行捕获和处理
- 记录错误日志，包含足够的上下文信息
- 向用户提供清晰的错误提示

### 日志规范
- 使用 Python 标准库 `logging` 模块
- 日志级别：DEBUG < INFO < WARNING < ERROR < CRITICAL
- 生产环境使用 INFO 级别，开发环境使用 DEBUG 级别

示例：
```python
import logging

logger = logging.getLogger(__name__)

def get_stock_price(symbol: str) -> float:
    try:
        # 业务逻辑
        price = fetch_price(symbol)
        logger.info(f"获取股票 {symbol} 价格成功: {price}")
        return price
    except NetworkError as e:
        logger.error(f"网络错误，无法获取 {symbol} 价格: {e}")
        raise
    except ValueError as e:
        logger.warning(f"股票代码 {symbol} 无效: {e}")
        raise
```

## 开发工作流

### 新功能开发
1. 在相应分支进行开发
2. 编写代码并添加注释和文档
3. 编写单元测试
4. 确保所有测试通过
5. 运行代码检查工具（如有）
6. 提交代码并推送

### 代码审查要点
- 代码风格是否符合规范
- 是否有充分的测试覆盖
- 异常处理是否合理
- 文档是否完整清晰

## 版本管理

### 版本号规则
遵循语义化版本（Semantic Versioning）：
- 主版本号：不兼容的 API 修改
- 次版本号：向下兼容的功能性新增
- 修订号：向下兼容的问题修正

### 提交信息规范
- 使用清晰的提交信息
- 格式：`<type>: <subject>`
  - `feat`: 新功能
  - `fix`: 修复 bug
  - `docs`: 文档更新
  - `style`: 代码格式调整
  - `refactor`: 重构
  - `test`: 测试相关
  - `chore`: 构建/工具相关

示例：
```
feat: 添加股票价格查询功能
fix: 修复日期格式解析错误
docs: 更新 README 文档
```

## 安全规范

### 敏感信息
- 不在代码中硬编码密码、API 密钥等敏感信息
- 使用环境变量存储敏感配置
- 将敏感配置文件加入 `.gitignore`

### 依赖管理
- 定期更新依赖包到安全版本
- 使用 `pip-audit` 等工具检查安全漏洞
- 添加依赖时评估其安全性和维护状态

## 性能优化

### 优化原则
- 避免过早优化
- 优先优化瓶颈部分
- 使用性能分析工具定位问题
- 考虑使用缓存减少重复计算

### 性能监控
- 关键函数添加性能日志
- 监控内存使用情况
- 定期进行性能测试

## 贡献指南

1. Fork 本项目
2. 创建特性分支（`git checkout -b feature/AmazingFeature`）
3. 提交更改（`git commit -m 'feat: 添加某个功能'`）
4. 推送到分支（`git push origin feature/AmazingFeature`）
5. 开启 Pull Request

## 联系方式

如有问题或建议，请通过以下方式联系：
- 提交 Issue
- 发起 Pull Request

---

**文档最后更新时间**：2026-02-09
