# HCP-LoadGen 开发指南与编程架构

## 📋 文档信息

- **项目名称**: HCP-LoadGen（高频金融交易区块链共识性能测试系统 - 负载生成层）
- **技术栈**: Rust 2021 + Tokio + Reqwest + Tonic + Prometheus + SQLx
- **开发语言**: Rust 1.75+
- **目标协议**: HTTP / gRPC（Cosmos Tx Service）
- **文档版本**: v1.0.0
- **最后更新**: 2026-04-08

---

## 1. 项目概述

**职责定位**: 以高并发模式构造、签名并广播交易，实时输出吞吐与时延指标，并可将交易元数据批量落库。

**核心功能**:
1. 多模式负载调度：`fixed` / `burst` / `sustained` / `jitter`
2. 双广播通道：HTTP 广播与 gRPC 广播
3. 账户池轮转与 nonce 递增管理
4. 交易构造（随机 payload、可选压缩）
5. 指标输出：JSON stdout、CSV、Prometheus `/metrics`
6. 异步批量写入 PostgreSQL（用户/账户/交易）

---

## 🏗️ 项目结构

```text
hcp-loadgen/
├── src/
│   ├── main.rs              # 程序入口与组件装配
│   ├── config.rs            # 配置模型 + CLI 参数 + TOML 加载
│   ├── scheduler.rs         # 调度器（发送节奏与并发控制）
│   ├── broadcaster.rs       # HTTP/gRPC 广播实现
│   ├── account_pool.rs      # 账户池与轮转策略
│   ├── tx_builder.rs        # 交易构造与编码/压缩
│   ├── signer.rs            # 签名实现（当前为 SHA256 方案）
│   ├── metrics.rs           # 统计聚合 + JSON/CSV/Prometheus 输出
│   └── storage.rs           # SQLx 异步批量写库
├── Cargo.toml
├── Cargo.lock
└── README.md
```

---

## 📦 核心依赖（Cargo.toml）

```toml
[dependencies]
tokio = { version = "1", features = ["full"] }
clap = { version = "4", features = ["derive"] }
serde = { version = "1", features = ["derive"] }
reqwest = { version = "0.12", default-features = false, features = ["json", "rustls-tls"] }
tonic = "0.13"
cosmos-sdk-proto = { version = "0.27.0", features = ["default", "grpc"] }
prometheus = "0.13"
axum = "0.7"
hdrhistogram = "7"
sysinfo = "0.30"
sqlx = { version = "0.7", features = ["runtime-tokio", "postgres"] }
flate2 = "1"
```

---

## ⚙️ 架构分层

```text
Config(TOML + CLI)
        │
        ▼
Scheduler ──> AccountPool ──> TxBuilder ──> Signer
   │                                   │
   ├──────────────> Broadcaster <──────┘
   │                 ├─ HttpBroadcaster
   │                 └─ GrpcBroadcaster
   │
   ├──────────────> Metrics(JSON/CSV/Prometheus)
   │
   └──────────────> Storage(SQLx 批量落库)
```

---

## 🔧 核心模块详解

### 1) `main.rs`

启动顺序：
1. `load_config()` 读取 TOML/CLI 合并配置
2. 创建 `Metrics` 并启动后台任务
3. 初始化 `Storage`（PostgreSQL 连接池 + 队列消费者）
4. 构建 `AccountPool`（本地随机账户或账号文件）
5. 按协议构建 `Broadcaster`（HTTP/gRPC）
6. 创建 `Scheduler` 并运行，支持 Ctrl+C 优雅退出

### 2) `config.rs`

配置覆盖顺序：
1. 默认值（`impl Default for Config`）
2. TOML 文件（`--config`）
3. CLI 参数（最高优先级）

主要配置域：
- 发送策略：`mode`、`target_tps`、`duration`、`total_txs`
- 并发参数：`concurrency`、`batch_size`、`max_inflight_per_account`
- 广播协议：`protocol`、`http_endpoint`、`grpc_endpoint`
- 链相关：`chain_id`、`rpc_endpoint`、`fee_amount`、`denom`
- 指标输出：`metrics_interval_ms`、`json_interval_ms`、`csv_path`、`prometheus_addr`
- 存储参数：`database_url`、`storage_flush_interval_ms`、`storage_channel_size`

### 3) `scheduler.rs`

四种发送模式：
- `fixed`: 固定时间间隔发送
- `burst`: 间歇突发发送
- `sustained`: 尽可能持续发送
- `jitter`: 在基准间隔上附加抖动

关键机制：
- 通过 `Semaphore` 控制在途并发
- 每笔交易异步任务化，发送后记录 success/reject 与时延
- 支持两类签名路径：
  - 本地密钥签名（内置）
  - 调用链 CLI 生成与签名交易（`keyring_home + account_file`）

### 4) `broadcaster.rs`

- `HttpBroadcaster`: 使用 `reqwest::Client` 直接 POST payload
- `GrpcBroadcaster`: 调用 `cosmos.tx.v1beta1.Service/BroadcastTx`
- 输出统一为 `SendResult { latency_ms, success }`

### 5) `metrics.rs`

指标输出能力：
1. 周期性 stdout JSON 快照（便于 `hcp-lab` 实时消费）
2. 可选 CSV 追加（长期离线分析）
3. 可选 Prometheus 服务（默认 `0.0.0.0:9100`）

关键指标：
- `sent` / `success` / `reject`
- `actual_tps`
- `success_rate` / `reject_rate`
- `latency_avg_ms` / `latency_p50_ms` / `latency_p90_ms` / `latency_p99_ms`
- `cpu_percent` / `mem_bytes`

### 6) `storage.rs`

异步落库机制：
- 内部 `mpsc` 缓冲通道接收事件
- 达到 `batch_size` 或定时器到期触发批量写
- 写入表：
  - `users`
  - `transactions`
- `shutdown()` 时主动 flush，确保数据尽量落盘

---

## 🗄️ 数据写入设计（LoadGen 侧）

当前写入主要针对 `transactions`：

```sql
INSERT INTO transactions
  (hash, from_address, to_address, amount, gas_price, gas_limit, nonce, status, submitted_at, confirmed_at, latency_ms)
VALUES
  (...)
ON CONFLICT DO NOTHING;
```

状态映射：
- 广播成功 -> `confirmed`
- 广播失败 -> `failed`

---

## 🚀 开发与运行流程

```bash
# 1) 进入项目
cd /home/hcp-dev/hcp-project-experiment/hcp-loadgen

# 2) 构建
cargo build --release

# 3) 最小运行示例（gRPC）
./target/release/hcp-loadgen \
  --protocol grpc \
  --grpc-endpoint http://127.0.0.1:9090 \
  --rpc-endpoint tcp://127.0.0.1:26657 \
  --chain-id hcp-testnet-1 \
  --total-txs 1000 \
  --target-tps 500 \
  --concurrency 64 \
  --metrics-interval 100 \
  --json-interval-ms 100 \
  --csv-path /tmp/loadgen.csv
```

配置文件运行示例：

```bash
./target/release/hcp-loadgen --config ./config.toml
```

---

## 🧪 与 HCP-Lab 集成方式

`hcp-lab` 通过 `--loadgen-args` 注入参数模板，常见占位符：
- `{nodes}`
- `{tx}`
- `{data_root}`

典型参数片段：

```text
--protocol grpc
--grpc-endpoint http://127.0.0.1:<grpc_port>
--keyring-home {data_root}/nodes_{nodes}/node1
--account-file {data_root}/nodes_{nodes}/accounts.jsonl
--total-txs {tx}
--csv-path {data_root}/loadgen_nodes{nodes}_tx{tx}.csv
```

---

## ✅ 开发建议

1. 新增调度策略优先扩展 `SendMode` + `Scheduler` 分支
2. 新增输出字段时同步更新 `MetricsSnapshot` 与 CSV 头
3. 若调整广播协议，保持 `Broadcaster` trait 稳定
4. 高压场景优先调优 `concurrency`、`batch_size`、`storage_channel_size`
5. 生产环境避免在默认配置中保留真实数据库凭据

---

**文档版本**: v1.0.0  
**最后更新**: 2026-04-08  
**维护者**: HCP Team
