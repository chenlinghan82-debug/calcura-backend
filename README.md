# Calcura Backend

## 项目简介

Calcura 后端是前后端分离计算器的 FastAPI 服务。后端负责表达式校验、安全解析、计算、异常处理和 SQLite 历史持久化；前端只发送表达式并展示后端结果。

## 技术栈

- Python 3.11+
- FastAPI + Uvicorn
- SQLAlchemy 2.x
- SQLite
- pytest

## 运行环境

建议使用 Python 3.11 或更高版本；Docker 镜像使用 Python 3.12。项目不使用 `eval`、`exec` 等任意代码执行方式。

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

首次启动会在 `data/calculator.db` 创建数据库和 `calculation_history` 表。

## API

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/calculate` | 后端计算并保存成功记录 |
| GET | `/api/history` | 查询历史，支持 `keyword` 和 `limit` |
| DELETE | `/api/history/{id}` | 删除指定记录 |
| DELETE | `/api/history` | 清空全部记录 |
| GET | `/api/stats` | 获取记录数量和结果统计 |
| GET | `/api/health` | 服务健康检查 |

计算示例：

```json
POST /api/calculate
{"expression":"(1+2)*3"}
```

```json
{"success":true,"expression":"(1+2)*3","result":9,"record":{}}
```

## 测试

```powershell
pytest -q
```

## 数据库设计

`calculation_history`：

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER | 主键 |
| expression | VARCHAR(200) | 原始表达式 |
| result | FLOAT | 后端计算结果 |
| created_at | DATETIME | UTC 创建时间 |

## 配置与前后端连接

前端通过 `VITE_API_BASE_URL` 指向后端地址。生产环境中必须把前端环境变量设置为实际后端公网地址。

后端可通过以下环境变量配置：

- `CALCULATOR_DATABASE_URL`：默认使用 `data/calculator.db`；部署到 PostgreSQL 时替换为对应连接串。
- `CALCULATOR_CORS_ORIGINS`：逗号分隔的前端来源，开发环境可使用 `*`，生产环境建议填写实际前端域名。
