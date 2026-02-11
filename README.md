# 袋装股票看板

## 快速开始

### CLI 模式

```bash
uv run src/pocket_stock/cli/main.py sh600519
```

### Web UI 模式

启动 Web 界面：

```bash
uv run streamlit run src/pocket_stock/cli/web.py
```

Web 界面将在浏览器中自动打开，默认地址为 `http://localhost:8501`。

在 Web 界面中，您可以：
1. 输入股票代码（格式：sh600000 或 sz000001）
2. 点击"开始分析"按钮
3. 查看股票行情、相关新闻和 AI 智能分析结果
