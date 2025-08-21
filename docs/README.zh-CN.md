# Fetch JSONPath MCP

[![PyPI Downloads](https://img.shields.io/pypi/dm/fetch-jsonpath-mcp)](https://pypi.org/project/fetch-jsonpath-mcp/)
[![English](https://img.shields.io/badge/docs-English-blue)](../README.md)

一个模型上下文协议 (MCP) 服务器，提供从 URL 获取 JSON 数据和网页内容的工具。具有智能内容提取、多种 HTTP 方法支持和浏览器式请求头，确保可靠的网页抓取。

## 🎯 为什么使用这个工具？

**减少 LLM Token 使用量和幻觉** - 无需获取整个 JSON 响应并浪费 token，只提取您需要的数据。

### 传统获取方式 vs JSONPath 提取

**❌ 传统获取方式（浪费的）：**
```json
// API 返回 2000+ token
{
  "data": [
    {
      "id": 1,
      "name": "Alice",
      "email": "alice@example.com", 
      "avatar": "https://...",
      "profile": {
        "bio": "长篇个人介绍文本...",
        "settings": {...},
        "preferences": {...},
        "metadata": {...}
      },
      "posts": [...],
      "followers": [...],
      "created_at": "2023-01-01",
      "updated_at": "2024-01-01"
    },
    // ... 还有 50 个用户
  ],
  "pagination": {...},
  "meta": {...}
}
```

**✅ JSONPath 提取（高效的）：**
```json
// 仅 10 个 token - 正是您需要的！
["Alice", "Bob", "Charlie"]
```

使用模式：`data[*].name` 可节省 **99% 的 token** 并消除无关数据导致的模型幻觉。

## 安装

对于大多数 IDE，使用 `uvx` 工具运行服务器。

```json
{
  "mcpServers": {
    "fetch-jsonpath-mcp": {
      "command": "uvx",
      "args": [
        "fetch-jsonpath-mcp"
      ]
    }
  }
}
```

<details>
<summary><b>在 Claude Code 中安装</b></summary>

```bash
claude mcp add fetch-jsonpath-mcp -- uvx fetch-jsonpath-mcp
```

</details>

<details>
<summary><b>在 Cursor 中安装</b></summary>

```json
{
  "mcpServers": {
    "fetch-jsonpath-mcp": {
      "command": "uvx",
      "args": ["fetch-jsonpath-mcp"]
    }
  }
}
```

</details>

<details>
<summary><b>在 Windsurf 中安装</b></summary>

将此添加到您的 Windsurf MCP 配置文件中。更多信息请参见 [Windsurf MCP 文档](https://docs.windsurf.com/windsurf/cascade/mcp)。

#### Windsurf 本地服务器连接

```json
{
  "mcpServers": {
    "fetch-jsonpath-mcp": {
      "command": "uvx",
      "args": ["fetch-jsonpath-mcp"]
    }
  }
}
```

</details>

<details>
<summary><b>在 VS Code 中安装</b></summary>

```json
"mcp": {
  "servers": {
    "fetch-jsonpath-mcp": {
      "type": "stdio",
      "command": "uvx",
      "args": ["fetch-jsonpath-mcp"]
    }
  }
}
```

</details>

## 开发环境设置

### 1. 安装依赖

```bash
uv sync
```

### 2. 启动演示服务器（可选）

```bash
# 安装演示服务器依赖
uv add fastapi uvicorn

# 在端口 8080 启动演示服务器
uv run demo-server
```

### 3. 运行 MCP 服务器

```bash
uv run fetch-jsonpath-mcp
```

## 演示服务器数据

位于 `http://localhost:8080` 的演示服务器返回：

```json
{
  "foo": [{"baz": 1, "qux": "a"}, {"baz": 2, "qux": "b"}],
  "bar": {
    "items": [10, 20, 30], 
    "config": {"enabled": true, "name": "example"}
  },
  "metadata": {"version": "1.0.0"}
}
```

## 可用工具

### `fetch-json`
使用 JSONPath 模式提取 JSON 数据，支持所有 HTTP 方法。

```json
{
  "name": "fetch-json",
  "arguments": {
    "url": "http://localhost:8080",
    "pattern": "foo[*].baz",
    "method": "GET"
  }
}
```
返回：`[1, 2]`

**参数：**
- `url`（必需）：目标 URL
- `pattern`（可选）：JSONPath 模式用于数据提取
- `method`（可选）：HTTP 方法（GET、POST、PUT、DELETE 等）- 默认值："GET"
- `data`（可选）：POST/PUT 请求的请求体
- `headers`（可选）：额外的 HTTP 请求头

### `fetch-text`
获取网页内容并智能提取文本。**默认转换为 Markdown 格式**以获得更好的可读性。

```json
{
  "name": "fetch-text",
  "arguments": {
    "url": "http://localhost:8080",
    "output_format": "clean_text"
  }
}
```
返回：JSON 数据的清洁文本表示

**输出格式：**
- `"markdown"`（默认）：将 HTML 转换为清洁的 Markdown 格式
- `"clean_text"`：移除 HTML 标签的纯文本
- `"raw_html"`：原始 HTML 内容

**参数：**
- `url`（必需）：目标 URL
- `method`（可选）：HTTP 方法 - 默认值："GET"
- `data`（可选）：POST/PUT 请求的请求体
- `headers`（可选）：额外的 HTTP 请求头
- `output_format`（可选）：输出格式 - 默认值："markdown"

### `batch-fetch-json`
使用不同 JSONPath 模式并发处理多个 URL。

```json
{
  "name": "batch-fetch-json",
  "arguments": {
    "requests": [
      {"url": "http://localhost:8080", "pattern": "foo[*].baz"},
      {"url": "http://localhost:8080", "pattern": "bar.items[*]"}
    ]
  }
}
```
返回：`[{"url": "http://localhost:8080", "pattern": "foo[*].baz", "success": true, "content": [1, 2]}, {"url": "http://localhost:8080", "pattern": "bar.items[*]", "success": true, "content": [10, 20, 30]}]`

**请求对象参数：**
- `url`（必需）：目标 URL
- `pattern`（可选）：JSONPath 模式
- `method`（可选）：HTTP 方法 - 默认值："GET"
- `data`（可选）：请求体
- `headers`（可选）：额外的 HTTP 请求头

### `batch-fetch-text`
从多个 URL 获取内容并智能提取文本。

```json
{
  "name": "batch-fetch-text",
  "arguments": {
    "requests": [
      "http://localhost:8080",
      {"url": "http://localhost:8080", "output_format": "raw_html"}
    ],
    "output_format": "markdown"
  }
}
```
返回：`[{"url": "http://localhost:8080", "success": true, "content": "# 演示服务器数据\n\n..."}, {"url": "http://localhost:8080", "success": true, "content": "{\"foo\": [{\"baz\": 1, \"qux\": \"a\"}, {\"baz\": 2, \"qux\": \"b\"}]..."}]`

**支持：**
- 简单的 URL 字符串
- 带有自定义方法和请求头的完整请求对象
- 在同一批次中混合输入类型

## JSONPath 示例

本项目使用 [jsonpath-ng](https://github.com/h2non/jsonpath-ng) 来实现 JSONPath。

| 模式 | 结果 | 描述 | 
|------|------|------|
| `foo[*].baz` | `[1, 2]` | 获取所有 baz 值 | 
| `bar.items[*]` | `[10, 20, 30]` | 获取所有项目 | 
| `metadata.version` | `["1.0.0"]` | 获取版本 | 

完整的 JSONPath 语法参考，请参见 [jsonpath-ng 文档](https://github.com/h2non/jsonpath-ng#jsonpath-syntax)。

## 🚀 性能优势

- **Token 效率**：仅提取所需数据，而非整个 JSON 响应
- **更快处理**：更小的数据负载 = 更快的 LLM 响应
- **减少幻觉**：更少的无关数据 = 更准确的输出
- **节约成本**：更少的 token = 更低的 API 成本
- **更好专注**：清洁的数据有助于模型保持专注
- **智能请求头**：默认浏览器请求头防止被阻止并改善访问
- **Markdown 转换**：清洁、可读的格式，保留结构

## 配置

设置环境变量来自定义行为：

```bash
# 请求超时时间（秒）（默认：10.0）
export JSONRPC_MCP_TIMEOUT=30

# SSL 验证（默认：true）
export JSONRPC_MCP_VERIFY=false

# 跟随重定向（默认：true）
export JSONRPC_MCP_FOLLOW_REDIRECTS=true

# 自定义请求头（将与默认浏览器请求头合并）
export JSONRPC_MCP_HEADERS='{"Authorization": "Bearer token"}'

# HTTP 代理配置
export JSONRPC_MCP_PROXY="http://proxy.example.com:8080"
```

**默认浏览器请求头**：服务器自动包含真实的浏览器请求头以防止被阻止：
- User-Agent：Chrome 浏览器模拟
- Accept：标准浏览器内容类型
- Accept-Language、Accept-Encoding：浏览器默认值
- 安全头：现代浏览器的 Sec-Fetch-* 头

`JSONRPC_MCP_HEADERS` 中的自定义请求头在冲突时会覆盖默认值。

## 开发

```bash
# 运行测试
pytest

# 检查代码质量
ruff check --fix

# 本地构建和测试
uv build
```

## v1.1.0 新功能

- ✨ **多种 HTTP 方法支持**：GET、POST、PUT、DELETE、PATCH、HEAD、OPTIONS
- 🔄 **工具重命名**：`get-json` → `fetch-json`，`get-text` → `fetch-text`
- 📄 **Markdown 转换**：使用 `markdownify` 默认进行 HTML 到 Markdown 转换
- 🌐 **智能浏览器请求头**：自动浏览器模拟请求头
- 🎛️ **格式控制**：文本内容的三种输出格式（markdown、clean_text、raw_html）
- 🚀 **增强批处理**：批处理操作支持不同方法