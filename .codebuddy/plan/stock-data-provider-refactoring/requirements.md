# 需求文档

## 引言

本功能旨在重构现有的股票数据提供者模块，引入面向对象的设计模式，将 `StockDataProvider` 重构为基于继承的模块化架构。通过抽象出 `BaseStockDataProvider` 基类，定义统一的接口规范和数据获取流程，使得未来可以轻松添加其他数据源（如新浪财经、东方财富等）而无需修改核心逻辑。

为了更好的模块化和可扩展性，本设计采用子模块结构：
- `data_provider` 模块：包含基类、通用组件（异常、模型、配置等）
- `data_provider.tencent` 子模块：专门封装腾讯财经相关的数据提供者实现和解析器

## 需求

### 需求 1：创建 data_provider.tencent 子模块

**用户故事：** 作为一名【开发者】，我希望【创建一个独立的 data_provider.tencent 子模块】，以便【将腾讯财经相关的代码集中管理，保持清晰的模块边界】。

#### 验收标准

1. WHEN 【创建项目结构】 THEN 【系统】 SHALL 【在 data_provider 目录下创建 tencent 子目录】
2. WHEN 【创建 tencent 子模块】 THEN 【系统】 SHALL 【在 tencent 子目录中创建 __init__.py 文件】
3. WHEN 【创建 tencent 子模块】 THEN 【系统】 SHALL 【在 tencent 子目录中创建 provider.py 文件用于存放腾讯财经数据提供者】
4. WHEN 【创建 tencent 子模块】 THEN 【系统】 SHALL 【在 tencent 子目录中创建 parser.py 文件用于存放腾讯财经数据解析器】
5. WHEN 【创建 tencent 子模块】 THEN 【系统】 SHALL 【保持 data_provider 主模块包含通用的异常类、数据模型、配置等组件】

### 需求 2：创建 BaseStockDataProvider 抽象基类

**用户故事：** 作为一名【开发者】，我希望【定义一个 BaseStockDataProvider 抽象基类】，以便【为所有股票数据提供者子类提供统一的接口规范和通用的验证逻辑】。

#### 验收标准

1. WHEN 【用户尝试实例化 BaseStockDataProvider】 THEN 【系统】 SHALL 【抛出 TypeError 异常，提示该类是抽象类】
2. WHEN 【定义 BaseStockDataProvider 类】 THEN 【系统】 SHALL 【将类定义在 data_provider/provider.py 文件中】
3. WHEN 【定义 BaseStockDataProvider 类】 THEN 【系统】 SHALL 【使用 abc.ABC 作为元类或使用 abc.ABC 作为基类】
4. WHEN 【定义 BaseStockDataProvider 类】 THEN 【系统】 SHALL 【定义一个名为 get 的公共方法】
5. WHEN 【调用 get 方法】 THEN 【系统】 SHALL 【首先调用股票代码验证方法检查股票代码合法性】
6. WHEN 【股票代码验证通过】 THEN 【系统】 SHALL 【调用抽象方法 _get 获取原始数据】
7. WHEN 【调用 get 方法】 THEN 【系统】 SHALL 【返回解析后的 StockQuote 对象】
8. WHEN 【定义 BaseStockDataProvider 类】 THEN 【系统】 SHALL 【定义一个抽象方法 _get】
9. IF 【股票代码验证失败】 THEN 【系统】 SHALL 【抛出 InvalidStockCodeException 异常】
10. WHEN 【定义 BaseStockDataProvider 类】 THEN 【系统】 SHALL 【接受 ProviderConfig 配置对象作为初始化参数】

### 需求 3：实现腾讯财经数据提供者子类

**用户故事：** 作为一名【开发者】，我希望【在 tencent 子模块中实现 TencentStockDataProvider 子类】，以便【从腾讯财经 API 获取股票实时行情数据并保持模块化】。

#### 验收标准

1. WHEN 【定义 TencentStockDataProvider 类】 THEN 【系统】 SHALL 【将类定义在 data_provider/tencent/provider.py 文件中】
2. WHEN 【定义 TencentStockDataProvider 类】 THEN 【系统】 SHALL 【继承自 BaseStockDataProvider】
3. WHEN 【实现 TencentStockDataProvider 类】 THEN 【系统】 SHALL 【实现抽象方法 _get】
4. WHEN 【调用 _get 方法】 THEN 【系统】 SHALL 【向腾讯财经 API URL 发起 HTTP GET 请求】
5. WHEN 【调用 _get 方法】 THEN 【系统】 SHALL 【返回原始响应文本数据】
6. WHEN 【腾讯财经 API 返回非 200 状态码】 THEN 【系统】 SHALL 【抛出 ProviderServiceErrorException 异常】
7. WHEN 【网络请求失败或超时】 THEN 【系统】 SHALL 【抛出 NetworkErrorException 异常】
8. WHEN 【腾讯财经 API 返回空响应】 THEN 【系统】 SHALL 【抛出 NetworkErrorException 异常】
9. WHEN 【初始化 TencentStockDataProvider】 THEN 【系统】 SHALL 【创建腾讯财经专用的解析器实例用于数据解析】
10. WHEN 【定义腾讯财经 API URL】 THEN 【系统】 SHALL 【使用 "https://qt.gtimg.cn/q={stock_code}" 格式】

### 需求 4：迁移腾讯财经解析器到 tencent 子模块

**用户故事：** 作为一名【开发者】，我希望【将 TencentFinanceParser 移动到 data_provider/tencent 子模块】，以便【将腾讯财经相关的所有代码集中管理】。

#### 验收标准

1. WHEN 【迁移 TencentFinanceParser】 THEN 【系统】 SHALL 【将类从 data_provider/parser.py 移动到 data_provider/tencent/parser.py】
2. WHEN 【迁移 TencentFinanceParser】 THEN 【系统】 SHALL 【更新所有导入该类的代码路径】
3. WHEN 【创建 tencent 子模块的 __init__.py】 THEN 【系统】 SHALL 【导出 TencentStockDataProvider 和 TencentFinanceParser】

### 需求 5：统一异常处理和日志记录

**用户故事：** 作为一名【开发者】，我希望【数据获取过程中的异常和日志记录保持一致】，以便【便于调试和问题追踪】。

#### 验收标准

1. WHEN 【在 get 方法中捕获异常】 THEN 【系统】 SHALL 【记录错误日志】
2. WHEN 【记录错误日志】 THEN 【系统】 SHALL 【包含股票代码和异常详情】
3. WHEN 【调用 _get 方法前】 THEN 【系统】 SHALL 【记录请求日志】
4. WHEN 【_get 方法成功返回】 THEN 【系统】 SHALL 【记录响应日志和耗时信息】

### 需求 6：保持异步接口和上下文管理器支持

**用户故事：** 作为一名【开发者】，我希望【重构后的类保持异步接口和上下文管理器支持】，以便【与现有异步代码架构保持一致】。

#### 验收标准

1. WHEN 【定义 BaseStockDataProvider 和 TencentStockDataProvider】 THEN 【系统】 SHALL 【支持 async with 上下文管理器语法】
2. WHEN 【进入上下文管理器】 THEN 【系统】 SHALL 【创建或复用 aiohttp.ClientSession 会话】
3. WHEN 【退出上下文管理器】 THEN 【系统】 SHALL 【关闭拥有的会话资源】
4. WHEN 【定义 get 和 _get 方法】 THEN 【系统】 SHALL 【使用 async 关键字定义为异步方法】

## 模块结构图

```
data_provider/
├── __init__.py              # 导出 BaseStockDataProvider, TencentStockDataProvider
├── provider.py              # 包含 BaseStockDataProvider 抽象基类
├── models.py                # 包含 StockQuote 数据模型
├── exceptions.py            # 包含通用异常类
├── logger.py                # 包含日志配置
└── tencent/                 # 腾讯财经子模块
    ├── __init__.py          # 导出 TencentStockDataProvider, TencentFinanceParser
    ├── provider.py          # 包含 TencentStockDataProvider 实现类
    └── parser.py            # 包含 TencentFinanceParser 解析器
```
