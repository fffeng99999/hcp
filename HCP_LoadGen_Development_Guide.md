# HCP-LoadGen 开发指南与编程架构（Final）

## 📋 文档信息

- **项目名称**: HCP-LoadGen（高频金融交易区块链共识性能测试系统 - 负载生成层）
- **技术栈**: Rust 2021 + Tokio + Reqwest + Tonic + Prometheus + SQLx + Tokio-Postgres
- **开发语言**: Rust 1.75+
- **目标协议**: HTTP / gRPC（Cosmos Tx Service）
- **文档版本**: v2.0.0
- **最后更新**: 2026-04-08

---

## 1. 项目概述

HCP-LoadGen 负责在高并发环境下构造、签名与广播交易，实时输出性能指标，并在收尾阶段将内存数据批量回写数据库。当前版本采用冷热分离架构，确保压测热路径不被数据库 I/O 干扰。

核心能力：
1. 多模式调度：`fixed` / `burst` / `sustained` / `jitter`
2. 双通道广播：HTTP 与 gRPC
3. 内存账户池：`DashMap` + 原子 nonce
4. Thread-local 交易缓冲 + MPSC 异步持久化
5. COPY BINARY 高速回写 PostgreSQL
6. 启动参数单行 JSON 元数据输出（实验可观测）

---

## 🏗️ 当前项目结构

```text
hcp-loadgen/
├── src/
│   ├── main.rs
│   ├── config.rs
│   ├── account_pool.rs
│   ├── metrics.rs
│   ├── types.rs
│   ├── core/
│   │   ├── mod.rs
│   │   ├── scheduler.rs
│   │   ├── broadcaster.rs
│   │   ├── signer.rs
│   │   └── tx_builder.rs
│   └── persistence/
│       ├── mod.rs
│       └── storage.rs
├── scripts/
│   ├── init_loadgen_db.py
│   ├── insert_one_user.py
│   └── seed_ten_users_data.py
└── Cargo.toml
```

---

## ⚙️ 架构分层（冷热分离）

```text
Config(TOML + CLI)
        │
        ▼
core::Scheduler ──> AccountPool(DashMap/InMemoryAccount)
   │                      │
   │                      └── nonce/balance in-memory mutation
   │
   ├──> core::TxBuilder + core::Signer + core::Broadcaster
   │
   ├──> thread-local Vec<TransactionRecord> (per worker)
   │
   └──> mpsc<Vec<TransactionRecord>> ──> persistence::Storage
                                         ├── COPY BINARY trades
                                         └── batch upsert balances/accounts
```

---

## 🔧 核心模块说明

### `main.rs`

启动流程：
1. `load_config()` 合并默认值、TOML、CLI
2. 输出单行 JSON 的启动性能元数据
3. 初始化 `Storage`
4. `load_initial_state()` 预加载账户/余额
5. 创建 `Broadcaster`
6. 启动后台持久化线程消费 `mpsc` 缓冲
7. 运行 `Scheduler`
8. 收到停止信号后优雅 drain，并回写最终余额状态

### `config.rs`

配置优先级：
1. 默认值
2. TOML（支持 `[performance]`）
3. CLI（最高优先级）

关键性能参数：
- `worker_buffer_capacity`
- `backpressure_threshold`
- `storage_channel_size`

校验规则：
- `worker_buffer_capacity > 0`
- `storage_channel_size > 0`
- `effective_backpressure > worker_buffer_capacity * worker_threads`

### `core/scheduler.rs`

- 每个 worker 维护独立 local buffer（thread-local）
- local buffer 满后批量发送到持久化通道
- 当 backlog 超过阈值时微降速（背压保护）
- 停机时发送 `Shutdown`，确保本地缓冲先 flush

### `persistence/storage.rs`

- `load_initial_state()`：从数据库预加载 `accounts` 与 `balances`
- `flush_trade_batch()` / `flush_results_to_db()`：统一走 COPY BINARY 路径写入交易
- COPY 错误处理：事务回滚，避免连接挂起

---

## 🗄️ 数据库设计（schema: `loadgendata`）

以下为当前建议并已对齐的核心四表设计。

### 1) 账户表 `accounts`

| 字段名 | 类型 | 说明 |
|---|---|---|
| `account_id` | BIGINT (PK) | 唯一账户 ID |
| `address` | VARCHAR(64) | 链上地址/公钥 |
| `username` | VARCHAR(50) | 用户名（可选） |
| `created_at` | TIMESTAMP | 创建时间 |

### 2) 资产余额表 `balances`

| 字段名 | 类型 | 说明 |
|---|---|---|
| `account_id` | BIGINT (FK) | 关联账户 ID |
| `asset_symbol` | VARCHAR(10) | 资产符号（如 BTC/ETH/USD） |
| `available` | DECIMAL | 可用余额 |
| `frozen` | DECIMAL | 冻结余额 |
| `updated_at` | TIMESTAMP | 最后更新时间 |

### 3) 订单表 `orders`

| 字段名 | 类型 | 说明 |
|---|---|---|
| `order_id` | BIGINT (PK) | 唯一订单 ID |
| `account_id` | BIGINT (FK) | 下单人 ID |
| `side` | ENUM | BUY / SELL |
| `price` | DECIMAL | 委托价格 |
| `quantity` | DECIMAL | 委托数量 |
| `filled_qty` | DECIMAL | 已成交数量 |
| `status` | ENUM | 待撮合/已成交/已撤单/部分成交 |
| `timestamp` | TIMESTAMP | 下单时间 |

### 4) 成交流水表 `trades`

| 字段名 | 类型 | 说明 |
|---|---|---|
| `trade_id` | BIGINT (PK) | 唯一成交 ID |
| `buy_order_id` | BIGINT (FK) | 关联买单 ID |
| `sell_order_id` | BIGINT (FK) | 关联卖单 ID |
| `price` | DECIMAL | 成交价格 |
| `quantity` | DECIMAL | 成交数量 |
| `tx_hash` | VARCHAR(128) | 共识层交易哈希 |
| `latency_ms` | INTEGER | 端到端延迟 |
| `created_at` | TIMESTAMP | 成交/上链时间 |

---

## 🧩 参考 DDL（PostgreSQL）

```sql
CREATE SCHEMA IF NOT EXISTS loadgendata;
SET search_path TO loadgendata, public;

CREATE TABLE IF NOT EXISTS accounts (
    account_id BIGSERIAL PRIMARY KEY,
    address VARCHAR(64) NOT NULL UNIQUE,
    username VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS balances (
    account_id BIGINT REFERENCES accounts(account_id),
    asset_symbol VARCHAR(10) NOT NULL,
    available DECIMAL(20, 8) DEFAULT 0,
    frozen DECIMAL(20, 8) DEFAULT 0,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (account_id, asset_symbol)
);

CREATE TABLE IF NOT EXISTS orders (
    order_id BIGSERIAL PRIMARY KEY,
    account_id BIGINT REFERENCES accounts(account_id),
    side VARCHAR(10) CHECK (side IN ('BUY', 'SELL')),
    price DECIMAL(20, 8) NOT NULL,
    quantity DECIMAL(20, 8) NOT NULL,
    filled_qty DECIMAL(20, 8) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'PENDING',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS trades (
    trade_id BIGSERIAL PRIMARY KEY,
    buy_order_id BIGINT,
    sell_order_id BIGINT,
    price DECIMAL(20, 8) NOT NULL,
    quantity DECIMAL(20, 8) NOT NULL,
    tx_hash VARCHAR(128),
    latency_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_trades_tx_hash ON trades(tx_hash);
CREATE INDEX IF NOT EXISTS idx_balances_account_id ON balances(account_id);
```

---

## 🚀 运行与验证

```bash
cd /home/hcp-dev/hcp-project-experiment/hcp-loadgen
cargo check
cargo clippy --all-targets -- -D warnings
```

配置文件运行：

```bash
./target/release/hcp-loadgen --config ./config.toml
```

---

## 🧪 配置建议（实验矩阵）

推荐在 TOML 中显式设置：

```toml
[performance]
worker_buffer_capacity = 1000
backpressure_threshold = 5000000
storage_channel_size = 20000
```

CLI 可覆盖同名参数（优先级更高）：
- `--buffer-size`
- `--backpressure-limit`
- `--channel-capacity`

---

**文档版本**: v2.0.0  
**最后更新**: 2026-04-08  
**维护者**: HCP Team
