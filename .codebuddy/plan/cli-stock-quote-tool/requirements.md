# 需求文档

## 引言
本功能旨在提供一个极简的命令行工具，允许用户通过命令行输入股票代码，调用 `data_provider` 模块查询该股票的实时行情信息，并将结果以可读格式输出到标准输出。该工具面向需要快速查询股票行情的用户，提供简单、直观的使用体验。

## 需求

### 需求 1：命令行参数解析

**用户故事：** 作为一名普通用户，我希望能够通过命令行参数指定股票代码，以便快速查询股票行情。

#### 验收标准

1. WHEN 用户执行命令并提供股票代码参数 THEN 系统 SHALL 接受并解析该股票代码
2. WHEN 用户未提供股票代码参数 THEN 系统 SHALL 显示使用帮助信息并退出
3. WHEN 用户提供的股票代码格式不符合要求（如长度不足8位或不以sh/sz开头）THEN 系统 SHALL 显示错误提示信息

### 需求 2：股票行情数据查询

**用户故事：** 作为一名普通用户，我希望系统能够调用 `data_provider` 模块获取股票的实时行情数据，以便查看最新信息。

#### 验收标准

1. WHEN 用户输入有效的股票代码 THEN 系统 SHALL 使用 `StockDataProvider` 异步获取股票行情数据
2. IF 数据提供者返回网络错误 THEN 系统 SHALL 捕获 `NetworkErrorException` 并显示友好的错误提示
3. IF 数据提供者返回服务错误 THEN 系统 SHALL 捕获 `ProviderServiceErrorException` 并显示友好的错误提示
4. IF 股票代码无效 THEN 系统 SHALL 捕获 `InvalidStockCodeException` 并显示友好的错误提示

### 需求 3：行情信息格式化输出

**用户故事：** 作为一名普通用户，我希望查询结果以清晰易读的格式输出，以便快速获取关键信息。

#### 验收标准

1. WHEN 成功获取股票行情数据 THEN 系统 SHALL 以表格形式输出股票信息，包含以下字段：
   - 股票代码（stock_code）
   - 股票名称（name）
   - 当前价格（current_price）
   - 涨跌额（change）
   - 涨跌幅（change_percent）
   - 成交量（volume）
   - 成交额（turnover）
   - 开盘价（open_price）
   - 收盘价（close_price）
   - 最高价（high_price）
   - 最低价（low_price）
2. WHEN 涨跌幅为正数 THEN 系统 SHALL 使用绿色标记（或"+"符号前缀）
3. WHEN 涨跌幅为负数 THEN 系统 SHALL 使用红色标记（或"-"符号前缀）
4. WHEN 输出结果 THEN 系统 SHALL 确保所有价格字段保留两位小数

### 需求 4：错误处理和退出码

**用户故事：** 作为一名普通用户，我希望程序在遇到错误时能够正确处理并返回合适的退出码，以便在脚本中使用。

#### 验收标准

1. WHEN 查询成功 THEN 系统 SHALL 返回退出码 0
2. WHEN 发生网络错误 THEN 系统 SHALL 返回退出码 1
3. WHEN 发生服务错误 THEN 系统 SHALL 返回退出码 2
4. WHEN 发生无效参数错误 THEN 系统 SHALL 返回退出码 3
5. WHEN 发生未知错误 THEN 系统 SHALL 返回退出码 99

### 需求 5：异步运行支持

**用户故事：** 作为一名开发人员，我希望命令行工具能够正确处理异步操作，以便充分利用异步 I/O 的优势。

#### 验收标准

1. WHEN 命令启动 THEN 系统 SHALL 使用 `asyncio.run()` 启动异步主函数
2. WHEN 使用 `StockDataProvider` THEN 系统 SHALL 通过 `async with` 语句正确管理资源生命周期
3. WHEN 查询完成后 THEN 系统 SHALL 确保所有资源（如 HTTP 会话）被正确关闭
