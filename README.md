# Calcura Backend

## 项目简介

Calcura 后端是前后端分离计算器的计算与数据服务。它负责表达式校验、安全解析、计算、异常处理，以及历史记录的数据库持久化。前端只提交表达式字符串，不能把已经算好的结果交给后端保存。

在线地址：<https://calcura-backend.vercel.app>

接口文档：<https://calcura-backend.vercel.app/docs>

## 技术栈

- Python 3.11+
- FastAPI 与 Uvicorn
- SQLAlchemy 2
- SQLite，也可通过连接串切换到 PostgreSQL
- pytest

计算使用自写的词法分析和递归下降解析器，不使用 `eval`、`exec` 或任何把用户输入当程序执行的方法。

## 运行环境

建议 Python 3.11 或更高版本。Docker 镜像使用 Python 3.12。

## 安装与启动

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

启动后：

- API：`http://localhost:8000`
- Swagger：`http://localhost:8000/docs`
- 健康检查：`http://localhost:8000/api/health`

## 数据库初始化

首次启动时自动创建 `calculation_history` 表。本地数据库文件为 `data/calculator.db`。如果旧表缺少新字段，启动时会自动补充 `is_favorite` 和 `steps_json`。

`calculation_history`：

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER | 主键 |
| expression | VARCHAR(200) | 用户提交的原始表达式 |
| result | FLOAT | 后端计算结果 |
| is_favorite | BOOLEAN | 是否收藏 |
| steps_json | VARCHAR(2000) | 后端生成的计算步骤 |
| created_at | DATETIME | UTC 创建时间 |

## API

| 方法 | 路径 | 状态码 | 说明 |
|---|---|---|---|
| POST | `/api/calculate` | 201 / 400 | 计算成功后保存记录；非法表达式返回 400 |
| GET | `/api/history` | 200 | 查询历史，支持 `keyword` 和 `limit` |
| GET | `/api/history/export` | 200 | 导出 CSV |
| POST | `/api/history/{id}/favorite` | 200 / 404 | 切换收藏 |
| DELETE | `/api/history/{id}` | 200 / 404 | 删除指定记录 |
| DELETE | `/api/history` | 200 | 清空全部记录 |
| GET | `/api/stats` | 200 | 数量、平均值、最小值、最大值 |
| GET | `/api/health` | 200 | 健康检查 |

计算请求：

```json
{ "expression": "(1+2)*3" }
```

成功响应：

```json
{
  "success": true,
  "expression": "(1+2)*3",
  "result": 9,
  "steps": ["1 + 2 = 3", "3 * 3 = 9"],
  "record": {}
}
```

错误响应使用 HTTP 400，内容类似：

```json
{ "detail": { "success": false, "message": "Division by zero is not allowed" } }
```

## 支持的表达式

- 运算符优先级：幂高于乘除，乘除高于加减；幂从右向左结合，因此 `-2^2 = -4`
- 括号、一元正负号和小数
- `sqrt(x)`、`abs(x)`、`x!`、`x%`、`pi`、`e`
- `Ans` 表示最近一次成功结果
- 除零、负数开方、非法阶乘和无法识别的字符都会返回明确错误

## 配置

- `CALCULATOR_DATABASE_URL`：默认本地 SQLite。部署到 PostgreSQL 时改为对应连接串。
- `CALCULATOR_CORS_ORIGINS`：逗号分隔的前端来源。未设置时允许所有来源。
- 在 Vercel 上，未配置外部数据库时使用 `/tmp/calculator.db`。同一运行实例内刷新页面历史仍在；实例回收后文件型 SQLite 可能被清空。长期保存可配置 PostgreSQL 连接串。

## 测试

```powershell
pytest -q
```

## 部署

Vercel 使用仓库中的 `api/index.py` 作为 FastAPI 入口。前端通过 `VITE_API_BASE_URL` 连接本服务。
