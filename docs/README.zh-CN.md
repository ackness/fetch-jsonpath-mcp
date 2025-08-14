# Fetch JSONPath MCP

一个 MCP 服务器，提供使用 JSONPath 模式从 URL 获取和提取 JSON 数据的工具。

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

### `get-json`
使用 JSONPath 模式提取 JSON 数据。

```json
{
  "name": "get-json",
  "arguments": {
    "url": "http://localhost:8080",
    "pattern": "foo[*].baz"
  }
}
```
返回：`[1, 2]`

### `get-text`
从任何 URL 获取原始文本内容。

```json
{
  "name": "get-text",
  "arguments": {
    "url": "http://localhost:8080"
  }
}
```
返回：`{"foo": [{"baz": 1, "qux": "a"}, {"baz": 2, "qux": "b"}], "bar": {"items": [10, 20, 30], "config": {"enabled": true, "name": "example"}}, "metadata": {"version": "1.0.0"}}`

### `batch-get-json`
使用不同的 JSONPath 模式处理多个 URL。

```json
{
  "name": "batch-get-json",
  "arguments": {
    "requests": [
      {"url": "http://localhost:8080", "pattern": "foo[*].baz"},
      {"url": "http://localhost:8080", "pattern": "bar.items[*]"}
    ]
  }
}
```
返回：`[[1, 2], [10, 20, 30]]`

### `batch-get-text`
从多个 URL 获取文本内容。

```json
{
  "name": "batch-get-text",
  "arguments": {
    "urls": ["http://localhost:8080", "http://localhost:8080"]
  }
}
```
返回：`["JSON内容...", "JSON内容..."]`

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

## 配置

设置环境变量：

```bash
export JSONRPC_MCP_TIMEOUT=30
export JSONRPC_MCP_HEADERS='{"Authorization": "Bearer token"}'
export JSONRPC_MCP_PROXY="http://proxy.example.com:8080"
```

## 开发

```bash
# 运行测试
pytest

# 检查代码质量
ruff check --fix
```