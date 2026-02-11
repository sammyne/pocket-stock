# LLM 股票分析模块实施计划

## 任务清单

- [x] 1. 设置项目结构和依赖
   - 在 `src/pocket_stock` 下创建 `llm` 模块目录结构
   - 在 `pyproject.toml` 中添加 `langchain-openai` 依赖
   - 创建项目根目录的 `.env.example` 文件，包含 `OPENAI_MODEL`、`OPENAI_API_BASE_URL`、`OPENAI_API_KEY` 配置项示例
   - _需求：8.2、8.3、8.4、12.8_

- [x] 2. 实现自定义异常类
   - 创建 `LLMApiTimeoutError`、`LLMAuthenticationError`、`LLMServiceError`、`NetworkConnectionError`、`LLMResponseParseError`、`ConfigurationError` 自定义异常
   - 为每个异常编写单元测试
   - _需求：10.2、10.3、10.4、10.5、10.7_

- [x] 3. 实现配置管理
   - 创建 `LLMConfig` 配置类，使用 Pydantic BaseSettings 从环境变量读取 `OPENAI_MODEL`、`OPENAI_API_BASE_URL`、`OPENAI_API_KEY`
   - 实现配置验证，确保所有必需配置项存在，否则抛出 `ConfigurationError`
   - 为配置类编写单元测试，测试配置加载和验证逻辑
   - _需求：8.1、8.2、8.3、8.4、8.5、8.6、8.7、9.1_

- [x] 4. 实现数据模型
   - 创建 `PositionSuggestion` 子模型（包含空仓者建议和持仓者建议字段）
   - 创建 `TargetPrices` 子模型（包含买入价、止损价、目标价字段，使用 Field 验证器确保精度保留两位小数）
   - 创建 `ChecklistItem` 子模型（包含检查项内容和状态符号字段）
   - 创建 `StockAnalysisResult` 主模型（包含 stock_name、core_conclusion、position_suggestion、target_prices、checklist 字段）
   - 为所有数据模型编写单元测试，测试数据验证和序列化
   - _需求：9.1、9.2、9.3、9.4、9.5、9.6、9.7、9.8_

- [x] 5. 实现 LLM 集成服务
   - 创建 `LLMStockAnalyser` 服务类，使用 `ChatOpenAI` 创建 LLM 实例
   - 实现提示词模板生成函数，将 `StockQuote` 和 `StockSearchResponse` 格式化为 LLM 可理解的上下文
   - 实现 `analyse` 方法，调用 LLM API 并返回结构化结果
   - 实现响应解析和验证逻辑，确保返回结果符合 `StockAnalysisResult` 模型
   - 使用 `unittest.mock` 编写单元测试，模拟 LLM API 响应
   - _需求：7.1、7.2、7.3、7.4、7.5、7.6、7.8、11.7_

- [x] 6. 实现 analyse_stock 主函数
   - 创建 `analyse_stock` 主函数，接收 `StockQuote` 和 `StockSearchResponse` 参数
   - 实现参数验证逻辑，检查参数是否为 `None` 或空，以及 `StockQuote` 必要字段是否存在
   - 集成 `LLMStockAnalyser` 服务，调用其 `analyse` 方法
   - 实现错误处理，捕获并转换各类异常为自定义异常
   - 为 `analyse_stock` 函数编写单元测试，测试参数验证和错误处理路径
   - _需求：1.1、1.2、1.3、1.4、1.5、10.1、10.6_

- [x] 7. 实现集成测试
   - 创建完整的集成测试，测试 `analyse_stock` 函数的端到端流程
   - 使用 mock 的 LLM 服务模拟各种场景（正常返回、超时、认证失败、服务错误、网络错误）
   - 确保集成测试覆盖所有主要业务逻辑和错误处理路径
   - _需求：11.5、11.6_

- [x] 8. 编写模块文档
   - 在 `llm` 模块目录创建 `README.md` 文档，说明模块功能、使用方法和配置说明
   - 为所有公共函数和类添加 Google 风格的 Docstring，使用中文编写
   - _需求：12.6、12.7_

- [x] 9. 代码规范检查和优化
   - 使用 `ruff` 进行 Lint 检查，确保代码符合 PEP 8 规范
   - 使用 `ruff` 进行格式化，确保使用 4 空格缩进、每行不超过 120 字符
   - 确保所有类型注解使用 PEP 585/PEP 604 规范
   - _需求：12.1、12.2、12.3、12.4_

- [x] 10. 运行测试套件并确保覆盖率
   - 运行完整的测试套件，确保所有测试通过
   - 检查代码覆盖率，确保不低于 80%
   - 如覆盖率不足，补充相应的测试用例
   - _需求：11.6_
