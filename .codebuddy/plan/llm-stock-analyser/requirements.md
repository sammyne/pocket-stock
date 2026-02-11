# LLM 股票分析模块需求文档

## 引言

本功能旨在为 Pocket-Stock 项目添加一个 LLM（大语言模型）驱动的股票分析模块。该模块将基于实时行情数据（`StockQuote`）和相关新闻资讯（`StockSearchResponse`），利用大语言模型的推理能力，为用户提供结构化的股票买卖决策建议。

该模块将作为项目的独立模块存在，提供清晰的 API 接口，供 CLI 或其他组件调用。输出结果将以结构化格式呈现，包括核心结论、持仓建议、具体价位和检查清单，帮助用户快速做出投资决策。

模块将使用 `langchain-openai` 库集成兼容 OpenAI 接口的 LLM 服务，所有配置信息从 `.env` 文件读取。

## 需求

### 需求 1：analyse_stock 接口定义

**用户故事：** 作为一名股票投资者，我希望通过一个简洁的接口调用股票分析功能，以便基于实时行情和新闻资讯获取买卖决策建议。

#### 验收标准

1. WHEN 调用 `analyse_stock` 函数时 THEN 系统 SHALL 接收 `StockQuote` 类型的实时行情参数。
2. WHEN 调用 `analyse_stock` 函数时 THEN 系统 SHALL 接收 `StockSearchResponse` 类型的新闻资讯参数。
3. WHEN 提供的参数为 `None` 或空数据时 THEN 系统 SHALL 抛出 `ValueError` 异常。
4. WHEN `StockQuote` 对象中缺少必要的字段（如股票名称、当前价格）时 THEN 系统 SHALL 进行数据验证并拒绝处理。
5. WHEN 函数被调用时 THEN 系统 SHALL 返回结构化的分析结果对象。

---

### 需求 2：股票名称输出

**用户故事：** 作为一名股票投资者，我希望分析结果中显示股票的正确中文全称，以便我能确认分析的股票对象是否正确。

#### 验收标准

1. WHEN 输出分析结果时 THEN 系统 SHALL 输出股票名称字段。
2. WHEN 输出股票名称时 THEN 系统 SHALL 使用 `StockQuote` 中的 `name` 字段值。
3. WHEN 输出股票名称时 THEN 系统 SHALL 确保名称为中文全称（如"贵州茅台"而非"股票600519"）。
4. WHEN 股票名称包含非中文字符时 THEN 系统 SHALL 保持原始名称输出。

---

### 需求 3：核心结论输出

**用户故事：** 作为一名股票投资者，我希望快速了解对股票的整体判断（该买/该卖/该等），以便节省阅读时间并把握核心观点。

#### 验收标准

1. WHEN 输出分析结果时 THEN 系统 SHALL 输出核心结论字段。
2. WHEN 生成核心结论时 THEN 系统 SHALL 使用一句话概括投资建议。
3. WHEN 核心结论包含决策建议时 THEN 系统 SHALL 明确指出"买入"、"卖出"或"持有"三种状态之一。
4. WHEN 核心结论超过 50 个字符时 THEN 系统 SHALL 精简表达至一句话。

---

### 需求 4：持仓分类建议

**用户故事：** 作为一名股票投资者，我希望针对不同持仓状态（空仓/持仓）获得不同的操作建议，以便根据自己的实际情况做出决策。

#### 验收标准

1. WHEN 输出分析结果时 THEN 系统 SHALL 输出持仓分类建议字段。
2. WHEN 生成持仓建议时 THEN 系统 SHALL 提供针对"空仓者"的操作建议。
3. WHEN 生成持仓建议时 THEN 系统 SHALL 提供针对"持仓者"的操作建议。
4. WHEN 空仓者建议与持仓者建议相同时 THEN 系统 SHALL 分别输出两者的完整建议内容。

---

### 需求 5：具体狙击点位

**用户故事：** 作为一名股票投资者，我希望获得精确的买入价、止损价和目标价，以便制定详细的交易计划和风险管理策略。

#### 验收标准

1. WHEN 输出分析结果时 THEN 系统 SHALL 输出具体狙击点位字段。
2. WHEN 生成狙击点位时 THEN 系统 SHALL 包含买入价（精确到分，保留两位小数）。
3. WHEN 生成狙击点位时 THEN 系统 SHALL 包含止损价（精确到分，保留两位小数）。
4. WHEN 生成狙击点位时 THEN 系统 SHALL 包含目标价（精确到分，保留两位小数）。
5. WHEN 分析结果为"持有"建议时 THEN 系统 SHALL 仍提供买入价、止损价和目标价作为参考。
6. WHEN 分析结果为"卖出"建议时 THEN 系统 SHALL 将目标价设置为 `None` 或 `null`。

---

### 需求 6：检查清单

**用户故事：** 作为一名股票投资者，我希望通过检查清单了解各项指标的状态，以便全面评估投资机会的风险和收益。

#### 验收标准

1. WHEN 输出分析结果时 THEN 系统 SHALL 输出检查清单字段。
2. WHEN 生成检查清单项时 THEN 系统 SHALL 使用 ✅ 符号标记通过/积极指标。
3. WHEN 生成检查清单项时 THEN 系统 SHALL 使用 ⚠️ 符号标记警告/中性指标。
4. WHEN 生成检查清单项时 THEN 系统 SHALL 使用 ❌ 符号标记失败/消极指标。
5. WHEN 检查清单包含 5-10 个检查项时 THEN 系统 SHALL 涵盖技术面、基本面、消息面等维度。
6. WHEN 某个检查项无法判断时 THEN 系统 SHALL 使用 ⚠️ 符号标记。

---

### 需求 7：LLM 集成

**用户故事：** 作为一名系统开发者，我希望模块能够使用 `langchain-openai` 库调用兼容 OpenAI 接口的 LLM 进行智能分析，以便从非结构化的新闻数据中提取有价值的信息并形成决策建议。

#### 验收标准

1. WHEN `analyse_stock` 被调用时 THEN 系统 SHALL 将 `StockQuote` 数据格式化为 LLM 可理解的上下文。
2. WHEN `analyse_stock` 被调用时 THEN 系统 SHALL 将 `StockSearchResponse` 中的新闻内容格式化为 LLM 可理解的上下文。
3. WHEN 调用 LLM API 时 THEN 系统 SHALL 使用 `langchain-openai` 库中的 `ChatOpenAI` 类创建 LLM 实例。
4. WHEN 创建 LLM 实例时 THEN 系统 SHALL 仅支持兼容 OpenAI 接口的 LLM 服务。
5. WHEN 调用 LLM API 时 THEN 系统 SHALL 设置合适的提示词（Prompt）以引导模型生成结构化输出。
6. WHEN LLM 返回结果时 THEN 系统 SHALL 解析并验证结果是否符合预定义的数据结构。
7. WHEN LLM API 调用失败时 THEN 系统 SHALL 捕获 `langchain_openai` 库抛出的异常并转换为自定义异常。
8. WHEN LLM 返回的内容无法解析时 THEN 系统 SHALL 抛出 `LLMResponseParseError` 异常。

---

### 需求 8：配置管理

**用户故事：** 作为一名系统运维人员，我希望能够通过 `.env` 文件配置 LLM 的 API 密钥和模型参数，以便灵活切换不同的兼容 OpenAI 接口的 LLM 服务提供商。

#### 验收标准

1. WHEN 模块初始化时 THEN 系统 SHALL 从项目根目录的 `.env` 文件读取配置信息。
2. WHEN 读取配置时 THEN 系统 SHALL 必须读取 `OPENAI_MODEL` 配置项作为模型名称。
3. WHEN 读取配置时 THEN 系统 SHALL 必须读取 `OPENAI_API_BASE_URL` 配置项作为兼容 OpenAI API 接口的服务地址。
4. WHEN 读取配置时 THEN 系统 SHALL 必须读取 `OPENAI_API_KEY` 配置项作为访问 API 服务依赖的密钥。
5. WHEN `.env` 文件中未设置 `OPENAI_API_KEY` 配置项时 THEN 系统 SHALL 抛出 `ConfigurationError` 异常。
6. WHEN `.env` 文件中未设置 `OPENAI_MODEL` 配置项时 THEN 系统 SHALL 抛出 `ConfigurationError` 异常。
7. WHEN `.env` 文件中未设置 `OPENAI_API_BASE_URL` 配置项时 THEN 系统 SHALL 抛出 `ConfigurationError` 异常。
8. WHEN 创建 `ChatOpenAI` 实例时 THEN 系统 SHALL 使用 `OPENAI_API_BASE_URL` 作为 `base_url` 参数。
9. WHEN 创建 `ChatOpenAI` 实例时 THEN 系统 SHALL 使用 `OPENAI_API_KEY` 作为 `api_key` 参数。
10. WHEN 创建 `ChatOpenAI` 实例时 THEN 系统 SHALL 使用 `OPENAI_MODEL` 作为 `model` 参数。
11. WHEN 读取 `.env` 文件时 THEN 系统 SHALL 使用 `python-dotenv` 库的 `load_dotenv` 函数加载环境变量。

---

### 需求 9：数据模型

**用户故事：** 作为一名系统开发者，我希望使用 Pydantic 定义分析结果的数据模型，以便确保数据的一致性和便于序列化。

#### 验收标准

1. WHEN 定义分析结果模型时 THEN 系统 SHALL 使用 Pydantic 的 `BaseModel` 作为基类。
2. WHEN 定义分析结果模型时 THEN 系统 SHALL 包含 `stock_name` 字段（类型为 `str`）。
3. WHEN 定义分析结果模型时 THEN 系统 SHALL 包含 `core_conclusion` 字段（类型为 `str`）。
4. WHEN 定义分析结果模型时 THEN 系统 SHALL 包含 `position_suggestion` 字段（类型为包含空仓和持仓建议的结构）。
5. WHEN 定义分析结果模型时 THEN 系统 SHALL 包含 `target_prices` 字段（包含买入价、止损价、目标价）。
6. WHEN 定义分析结果模型时 THEN 系统 SHALL 包含 `checklist` 字段（类型为包含检查项的列表）。
7. WHEN 定义价格字段时 THEN 系统 SHALL 使用 `float` 类型并允许 `None` 值。
8. WHEN 定义价格字段时 THEN 系统 SHALL 使用 Field 验证器确保精度保留两位小数。

---

### 需求 10：错误处理

**用户故事：** 作为一名用户，我希望在分析过程中遇到错误时能获得清晰的错误信息，以便快速定位问题并采取相应措施。

#### 验收标准

1. WHEN `analyse_stock` 参数验证失败时 THEN 系统 SHALL 抛出包含具体错误原因的 `ValueError`。
2. WHEN LLM API 调用超时时 THEN 系统 SHALL 捕获超时异常并抛出 `LLMApiTimeoutError` 异常。
3. WHEN LLM API 返回认证错误时 THEN 系统 SHALL 捕获认证异常并抛出 `LLMAuthenticationError` 异常。
4. WHEN LLM API 返回服务错误（如 500）时 THEN 系统 SHALL 捕获服务异常并抛出 `LLMServiceError` 异常。
5. WHEN 网络连接失败时 THEN 系统 SHALL 捕获连接异常并抛出 `NetworkConnectionError` 异常。
6. WHEN 所有自定义异常都应包含友好的错误描述 AND 系统应在日志中记录详细的堆栈信息。
7. WHEN `.env` 文件缺少必需的配置项时 THEN 系统 SHALL 抛出包含缺失配置项名称的 `ConfigurationError`。

---

### 需求 11：测试覆盖

**用户故事：** 作为一名质量保证工程师，我希望模块具备完善的单元测试和集成测试，以便确保代码质量和功能的可靠性。

#### 验收标准

1. WHEN 编写单元测试时 THEN 系统 SHALL 为所有公共函数编写测试用例。
2. WHEN 编写单元测试时 THEN 系统 SHALL 为数据模型验证编写测试用例。
3. WHEN 编写单元测试时 THEN 系统 SHALL 为错误处理路径编写测试用例。
4. WHEN 编写单元测试时 THEN 系统 SHALL 为 `.env` 配置加载编写测试用例。
5. WHEN 编写集成测试时 THEN 系统 SHALL 测试完整的 `analyse_stock` 调用流程。
6. WHEN 运行测试套件时 THEN 系统 SHALL 确保代码覆盖率不低于 80%。
7. WHEN 编写测试时 THEN 系统 SHALL 使用 `unittest.mock` 模拟 `ChatOpenAI` 实例和 LLM API 响应。

---

### 需求 12：文档和代码规范

**用户故事：** 作为一名代码贡献者，我希望代码遵循项目规范并有完整的文档注释，以便团队协作和代码维护。

#### 验收标准

1. WHEN 编写代码时 THEN 系统 SHALL 遵循 PEP 8 代码风格规范。
2. WHEN 编写代码时 THEN 系统 SHALL 遵循 PEP 585/PEP 604 类型注解规范。
3. WHEN 编写代码时 THEN 系统 SHALL 使用 4 空格缩进。
4. WHEN 编写代码时 THEN 系统 SHALL 确保每行长度不超过 120 字符。
5. WHEN 编写代码时 THEN 系统 SHALL 使用中文编写文档注释和字符串消息。
6. WHEN 编写模块时 THEN 系统 SHALL 在模块根目录创建 README.md 文档说明模块功能和使用方法。
7. WHEN 编写函数文档字符串时 THEN 系统 SHALL 遵循 Google 风格的 Docstring 格式。
8. WHEN 创建 `.env.example` 文件时 THEN 系统 SHALL 包含所有必需的配置项及其示例值。
