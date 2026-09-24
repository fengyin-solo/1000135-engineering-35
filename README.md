# 冷链物流温控运营平台

面向冷链订单、运单、冷藏车、温控监控、冷库仓储与结算的一体化运营后台。

这是一个前后端分离的管理平台：前端 Vue 3 + Vite + TypeScript，后端 FastAPI（Python）。
两边各自独立启动，前端 dev server 已关掉自动打开页面，启动后按终端打印的地址手工打开。

## 目录结构

```text
.
├── frontend/                 Vue 3 + Vite + TypeScript 前端
│   ├── src/views/            每个业务模块一个页面
│   ├── src/api/              统一请求封装
│   ├── src/stores/           会话与筛选状态
│   └── vite.config.ts        dev server 配置（open: false）
├── backend/                  FastAPI（Python） 后端
│   ├── app/routers/          每个业务模块一组接口
│   ├── app/services/         业务规则与状态流转
│   └── app/store.py          内存数据仓库与示例数据
├── .gitignore
└── docker-compose.yml
```

## 启动

依赖要求：后端 Python 3.12+，前端 Node.js 20+。

### 一键安装并启动

```bash
make install   # 分别创建 backend/.venv 并安装 Python 依赖、安装前端 npm 依赖
make backend   # 启动后端（等价于 cd backend && ./run.sh）
make frontend  # 启动前端
```

### 后端（手动）

```bash
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
./run.sh
```

`./run.sh` 会自动创建虚拟环境、安装 `requirements.txt` 里的依赖，随后校验运行配置并启动
uvicorn；直接运行
`uvicorn app.main:app --host 127.0.0.1 --port 8000` 的原有命令仍然可用。

健康检查：`curl http://127.0.0.1:8000/api/health`

### 前端（手动）

```bash
cd frontend
npm install
npm run dev
```

前端默认监听 `http://127.0.0.1:5173/`，dev server 不会自动打开浏览器，
需要自己访问。`/api` 由 vite 代理到后端 `http://127.0.0.1:8000`（可用
`VITE_PROXY_TARGET` 覆盖代理目标，见 `frontend/vite.config.ts`）。

### Docker Compose

```bash
docker compose up --build
```

### 运行配置

本地开发与容器部署共用同一份配置来源：仓库根目录的 `.env` 文件与进程环境变量。
环境变量优先于 `.env`，两者都不设置时沿用内置默认值。复制示例文件即可开始：

```bash
cp .env.example .env
```

| 变量 | 说明 | 默认值 |
| --- | --- | --- |
| `APP_ENV` | 运行环境标识（如 `local`/`staging`/`prod`），会打印在启动日志里 | `local` |
| `APP_HOST` | 监听地址（容器内固定为 `0.0.0.0`） | `127.0.0.1` |
| `APP_PORT` | 监听端口，需为 1~65535 的整数 | `8000` |
| `APP_ALLOWED_ORIGINS` | 允许的跨域来源，多个用英文逗号分隔，如 `http://localhost:5173,http://localhost:8080` | `http://127.0.0.1:5173,http://localhost:5173` |
| `PAGE_SIZE_DEFAULT` | 列表接口不传 `size` 时的默认每页条数 | `20` |
| `PAGE_SIZE_MAX` | 每页条数上限，接口对超过上限的请求返回 400 | `200` |

启动时会打印一行业务名、运行环境、监听地址、跨域来源数量与分页参数，方便确认当前
生效的配置，例如：

```text
冷链物流温控运营平台 启动：运行环境=local，监听 http://127.0.0.1:8000，允许跨域来源 2 个（http://127.0.0.1:5173、http://localhost:5173），分页默认 20 条/上限 200 条，配置来源=/workspace/.env
```

任一配置缺失（空值）或格式非法（端口不是整数、跨域来源不是合法 URL、
`PAGE_SIZE_DEFAULT` 大于 `PAGE_SIZE_MAX` 等）时，服务不会启动，启动脚本会直接打印
原因并注明对应默认值，例如：

```text
启动失败：运行配置校验未通过：环境变量 APP_PORT=abc 不是整数；不设置它时默认值为 8000
```


## 业务模块

| 模块 | 目录 | 业务对象 | 主要字段 |
| --- | --- | --- | --- |
| 冷链订单 | `order` | 冷链订单 | 订单编号、客户名称、货物名称 |
| 运单管理 | `waybill` | 冷链运单 | 运单号、关联订单、承运车辆 |
| 冷藏车管理 | `vehicle` | 冷藏车辆 | 车牌号码、车辆类型、制冷机组型号 |
| 司机管理 | `driver` | 司机档案 | 司机工号、司机姓名、联系电话 |
| 温控监控 | `temperature` | 温控记录 | 记录编号、关联运单、测点编号 |
| 温度异常 | `excursion` | 温度异常事件 | 事件编号、关联运单、异常类型 |
| 冷库管理 | `warehouse` | 冷库档案 | 冷库编码、冷库名称、库区温区 |
| 入库管理 | `inbound` | 入库单 | 入库单号、供应商名称、货物名称 |
| 出库管理 | `outbound` | 出库单 | 出库单号、客户名称、货物名称 |
| 库存管理 | `inventory` | 库存批次 | 库存编码、货物名称、批次号 |
| 批次追溯 | `trace` | 追溯记录 | 追溯码、货物名称、生产批次 |
| 质检管理 | `quality` | 质检单 | 质检单号、关联批次、检测项目 |
| 线路管理 | `route` | 配送线路 | 线路编码、线路名称、起点冷库 |
| 调度派单 | `dispatch` | 调度单 | 调度单号、关联订单、配送线路 |
| 温控设备 | `device` | 温控设备 | 设备编号、设备名称、设备型号 |
| 维保工单 | `maint` | 维保工单 | 工单编号、关联设备、故障现象 |
| 告警中心 | `alarm` | 告警事件 | 告警编号、告警类型、告警等级 |
| 客户管理 | `customer` | 客户档案 | 客户编码、客户名称、客户类型 |
| 计费结算 | `billing` | 计费单 | 计费单号、客户名称、计费周期 |
| 报表导出 | `report` | 报表任务 | 报表名称、统计范围、统计周期 |
| 系统设置 | `setting` | 系统参数 | 参数编码、参数名称、参数值 |

## 约定

- 每个模块的前端页面在 `frontend/src/views/<模块>/index.vue`，后端接口在
  `backend/app/routers/<模块>.py`，业务规则在 `backend/app/services/<模块>.py`。
- 列表接口统一返回 `{ items, total, page, size }`，动作接口统一返回 `{ ok, message }`。
- 状态流转只允许在 `app/services` 里改，路由层不做业务判断。
