# HCP-Server 开发指南与编程架构

## 📋 文档信息

- **项目名称**: HCP-Server (高频金融交易区块链共识性能测试系统 - 服务端)
- **技术栈**: Go 1.25 + gRPC + PostgreSQL + Redis + GORM
- **开发语言**: Go 1.25+
- **数据库**: PostgreSQL 14+, Redis 7.0
- **文档版本**: v1.0
- **最后更新**: 2026-02-05

---

## 1. 项目概述

**启动端口**: 8081 (gRPC服务)
**职责**: 数据持久化、基准管理、性能统计、缓存管理

**核心功能**:
1. 基准测试结果的CRUD操作
2. 交易记录的存储与查询
3. 节点信息管理
4. 性能指标的聚合与统计
5. 报告生成
6. Redis缓存加速热数据访问

---

## 🏗️ 项目结构

```
hcp-server/
├── cmd/
│   └── server/
│       └── main.go              # 应用入口
│
├── internal/                    # 内部包 (不暴露给外部)
│   ├── config/
│   │   ├── config.go            # 配置结构定义
│   │   └── loader.go            # 配置加载器
│   │
│   ├── models/                  # 数据模型 (GORM)
│   │   ├── benchmark.go         # 基准测试模型
│   │   ├── transaction.go       # 交易模型
│   │   ├── node.go              # 节点模型
│   │   ├── metric.go            # 指标模型
│   │   └── anomaly.go           # 异常记录模型
│   │
│   ├── repository/              # 数据访问层 (Repository Pattern)
│   │   ├── interface.go         # Repository接口定义
│   │   ├── benchmark_repo.go    # 基准测试Repository
│   │   ├── transaction_repo.go  # 交易Repository
│   │   ├── node_repo.go         # 节点Repository
│   │   └── metric_repo.go       # 指标Repository
│   │
│   ├── service/                 # 业务逻辑层
│   │   ├── benchmark_service.go # 基准测试服务
│   │   ├── transaction_service.go # 交易服务
│   │   ├── node_service.go      # 节点服务
│   │   ├── metric_service.go    # 指标服务
│   │   └── report_service.go    # 报告生成服务
│   │
│   ├── cache/                   # 缓存层
│   │   ├── redis_client.go      # Redis客户端封装
│   │   └── cache_manager.go     # 缓存管理器
│   │
│   ├── grpc/                    # gRPC服务实现
│   │   ├── server.go            # gRPC服务器
│   │   └── handlers/            # gRPC处理器
│   │       ├── benchmark_handler.go
│   │       ├── transaction_handler.go
│   │       ├── node_handler.go
│   │       └── metric_handler.go
│   │
│   ├── database/                # 数据库管理
│   │   ├── postgres.go          # PostgreSQL连接管理
│   │   ├── migrations/          # 数据库迁移
│   │   │   ├── 001_create_benchmarks.sql
│   │   │   ├── 002_create_transactions.sql
│   │   │   ├── 003_create_nodes.sql
│   │   │   ├── 004_create_metrics.sql
│   │   │   └── 005_create_anomalies.sql
│   │   └── seed.go              # 测试数据生成
│   │
│   └── utils/                   # 工具函数
│       ├── logger.go            # 日志工具
│       ├── validator.go         # 数据验证
│       ├── converter.go         # 数据转换
│       └── errors.go            # 错误处理
│
├── api/                         # API定义 (Protobuf)
│   ├── proto/
│   │   ├── benchmark.proto      # 基准测试服务定义
│   │   ├── transaction.proto    # 交易服务定义
│   │   ├── node.proto           # 节点服务定义
│   │   ├── metric.proto         # 指标服务定义
│   │   └── common.proto         # 通用类型定义
│   │
│   └── generated/               # Protobuf生成的Go代码
│       ├── benchmark.pb.go
│       ├── benchmark_grpc.pb.go
│       ├── transaction.pb.go
│       ├── transaction_grpc.pb.go
│       ├── node.pb.go
│       ├── node_grpc.pb.go
│       ├── metric.pb.go
│       ├── metric_grpc.pb.go
│       ├── common.pb.go
│       └── common_grpc.pb.go
│
├── configs/                     # 配置文件
│   ├── config.yaml              # 主配置
│   ├── config.dev.yaml          # 开发环境
│   ├── config.prod.yaml         # 生产环境
│   └── config.test.yaml         # 测试环境
│
├── scripts/                     # 脚本工具
│   ├── generate_proto.sh        # 生成Protobuf代码
│   ├── migrate.sh               # 数据库迁移
│   ├── seed.sh                  # 数据填充
│   └── build.sh                 # 构建脚本
│
├── tests/                       # 测试
│   ├── unit/                    # 单元测试
│   │   ├── service_test.go
│   │   ├── repository_test.go
│   │   └── cache_test.go
│   │
│   ├── integration/             # 集成测试
│   │   ├── grpc_test.go
│   │   ├── database_test.go
│   │   └── redis_test.go
│   │
│   └── fixtures/                # 测试数据
│       └── test_data.go
│
├── deployments/                 # 部署相关
│   ├── Dockerfile               # Docker镜像
│   ├── docker-compose.yml       # 本地开发
│   └── k8s/                     # Kubernetes配置
│       ├── deployment.yaml
│       ├── service.yaml
│       └── configmap.yaml
│
├── docs/                        # 文档
│   ├── API.md                   # API文档
│   ├── DATABASE.md              # 数据库设计
│   └── DEVELOPMENT.md           # 开发指南
│
├── go.mod                       # Go模块定义
├── go.sum                       # Go依赖校验
├── Makefile                     # Make命令
├── README.md                    # 项目说明
└── .env.example                 # 环境变量示例
```

---

## 📦 核心依赖 (go.mod)

```go
module github.com/fffeng99999/hcp-server

go 1.22

require (
    // gRPC相关
    google.golang.org/grpc v1.60.0
    google.golang.org/protobuf v1.32.0
    
    // 数据库
    gorm.io/gorm v1.25.5
    gorm.io/driver/postgres v1.5.4
    github.com/lib/pq v1.10.9
    
    // Redis
    github.com/redis/go-redis/v9 v9.4.0
    
    // 配置管理
    github.com/spf13/viper v1.18.2
    github.com/spf13/cobra v1.8.0
    
    // 日志
    go.uber.org/zap v1.26.0
    
    // 数据验证
    github.com/go-playground/validator/v10 v10.16.0
    
    // UUID生成
    github.com/google/uuid v1.5.0
    
    // 数据库迁移
    github.com/golang-migrate/migrate/v4 v4.17.0
    
    // 时间处理
    github.com/jinzhu/now v1.1.5
    
    // 测试
    github.com/stretchr/testify v1.8.4
    github.com/DATA-DOG/go-sqlmock v1.5.2
    github.com/alicebob/miniredis/v2 v2.31.1
)
```

---

## 🗄️ 数据库设计

### 1. benchmarks表 (基准测试)

```sql
CREATE TABLE benchmarks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 基本信息
    name VARCHAR(255) NOT NULL,
    description TEXT,
    algorithm VARCHAR(50) NOT NULL,  -- tPBFT/Raft/HotStuff
    node_count INTEGER NOT NULL,
    duration INTEGER NOT NULL,        -- 测试持续时间(秒)
    target_tps INTEGER,               -- 目标TPS
    
    -- 性能指标
    actual_tps DECIMAL(10,2),         -- 实际TPS
    latency_p50 DECIMAL(10,4),        -- P50延迟(ms)
    latency_p90 DECIMAL(10,4),        -- P90延迟(ms)
    latency_p99 DECIMAL(10,4),        -- P99延迟(ms)
    latency_p999 DECIMAL(10,4),       -- P999延迟(ms)
    latency_avg DECIMAL(10,4),        -- 平均延迟(ms)
    latency_max DECIMAL(10,4),        -- 最大延迟(ms)
    latency_min DECIMAL(10,4),        -- 最小延迟(ms)
    
    -- 区块链指标
    block_count INTEGER,              -- 生成区块数
    transaction_count INTEGER,        -- 交易总数
    successful_tx INTEGER,            -- 成功交易数
    failed_tx INTEGER,                -- 失败交易数
    block_size_avg DECIMAL(10,2),     -- 平均区块大小(KB)
    block_propagation_time DECIMAL(10,4),  -- 区块传播时间(ms)
    
    -- 资源使用
    cpu_usage_avg DECIMAL(5,2),       -- 平均CPU使用率(%)
    cpu_usage_max DECIMAL(5,2),       -- 最大CPU使用率(%)
    memory_usage_avg DECIMAL(10,2),   -- 平均内存使用(MB)
    memory_usage_max DECIMAL(10,2),   -- 最大内存使用(MB)
    network_in_mbps DECIMAL(10,2),    -- 入站网络(Mbps)
    network_out_mbps DECIMAL(10,2),   -- 出站网络(Mbps)
    disk_io_read DECIMAL(10,2),       -- 磁盘读(MB/s)
    disk_io_write DECIMAL(10,2),      -- 磁盘写(MB/s)
    
    -- 共识特定指标
    view_change_count INTEGER,        -- 视图切换次数(tPBFT)
    prepare_phase_latency DECIMAL(10,4),  -- Prepare阶段延迟(ms)
    commit_phase_latency DECIMAL(10,4),   -- Commit阶段延迟(ms)
    
    -- 状态与元数据
    status VARCHAR(20) DEFAULT 'running',  -- running/completed/failed/cancelled
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 索引优化
    CONSTRAINT chk_algorithm CHECK (algorithm IN ('tPBFT', 'Raft', 'HotStuff')),
    CONSTRAINT chk_status CHECK (status IN ('running', 'completed', 'failed', 'cancelled'))
);

-- 索引
CREATE INDEX idx_benchmarks_algorithm ON benchmarks(algorithm);
CREATE INDEX idx_benchmarks_status ON benchmarks(status);
CREATE INDEX idx_benchmarks_created_at ON benchmarks(created_at DESC);
CREATE INDEX idx_benchmarks_node_count ON benchmarks(node_count);
CREATE INDEX idx_benchmarks_actual_tps ON benchmarks(actual_tps DESC);

-- 更新时间戳触发器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_benchmarks_updated_at
    BEFORE UPDATE ON benchmarks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

### 2. transactions表 (交易记录 - 时序表)

```sql
CREATE TABLE transactions (
    hash VARCHAR(66) PRIMARY KEY,     -- 0x开头的交易哈希
    
    -- 交易基本信息
    from_address VARCHAR(42) NOT NULL,  -- 发送方地址
    to_address VARCHAR(42) NOT NULL,    -- 接收方地址
    amount BIGINT NOT NULL,             -- 金额(wei)
    gas_price BIGINT,                   -- Gas价格
    gas_limit BIGINT,                   -- Gas限制
    gas_used BIGINT,                    -- 实际使用Gas
    nonce BIGINT,                       -- Nonce
    
    -- 区块信息
    block_number BIGINT,                -- 所属区块高度
    block_hash VARCHAR(66),             -- 所属区块哈希
    transaction_index INTEGER,          -- 区块内索引
    
    -- 状态
    status VARCHAR(20) NOT NULL,        -- pending/confirmed/failed
    error_message TEXT,
    
    -- 时间戳
    submitted_at TIMESTAMP NOT NULL,    -- 提交时间
    confirmed_at TIMESTAMP,             -- 确认时间
    
    -- 性能指标
    latency_ms DECIMAL(10,4),           -- 确认延迟(ms)
    
    -- 基准测试关联
    benchmark_id UUID REFERENCES benchmarks(id) ON DELETE CASCADE,
    
    -- 元数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_status CHECK (status IN ('pending', 'confirmed', 'failed'))
) PARTITION BY RANGE (DATE(submitted_at));

-- 创建分区表 (按月)
CREATE TABLE transactions_2024_01 PARTITION OF transactions
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE transactions_2024_02 PARTITION OF transactions
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

-- 索引
CREATE INDEX idx_transactions_from ON transactions(from_address);
CREATE INDEX idx_transactions_to ON transactions(to_address);
CREATE INDEX idx_transactions_status ON transactions(status);
CREATE INDEX idx_transactions_submitted_at ON transactions(submitted_at DESC);
CREATE INDEX idx_transactions_benchmark_id ON transactions(benchmark_id);
CREATE INDEX idx_transactions_block_number ON transactions(block_number);

-- 自动创建未来分区的函数
CREATE OR REPLACE FUNCTION create_partition_if_not_exists()
RETURNS TRIGGER AS $$
DECLARE
    partition_date DATE;
    partition_name TEXT;
    start_date DATE;
    end_date DATE;
BEGIN
    partition_date := DATE_TRUNC('month', NEW.submitted_at);
    partition_name := 'transactions_' || TO_CHAR(partition_date, 'YYYY_MM');
    start_date := partition_date;
    end_date := partition_date + INTERVAL '1 month';
    
    IF NOT EXISTS (
        SELECT 1 FROM pg_class WHERE relname = partition_name
    ) THEN
        EXECUTE format(
            'CREATE TABLE IF NOT EXISTS %I PARTITION OF transactions FOR VALUES FROM (%L) TO (%L)',
            partition_name, start_date, end_date
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER create_transaction_partition
    BEFORE INSERT ON transactions
    FOR EACH ROW
    EXECUTE FUNCTION create_partition_if_not_exists();
```

### 3. nodes表 (节点信息)

```sql
CREATE TABLE nodes (
    id VARCHAR(50) PRIMARY KEY,       -- 节点ID
    
    -- 节点基本信息
    name VARCHAR(255),
    address VARCHAR(255) NOT NULL,    -- 网络地址 (host:port)
    public_key TEXT,                  -- 公钥
    region VARCHAR(50),               -- 地理区域
    
    -- 角色与状态
    role VARCHAR(20) DEFAULT 'validator',  -- leader/validator/follower
    status VARCHAR(20) DEFAULT 'offline',  -- online/offline/syncing/failed
    
    -- 性能指标
    trust_score DECIMAL(5,2) DEFAULT 100.00,  -- 信任评分(0-100)
    uptime_percentage DECIMAL(5,2),           -- 在线率(%)
    total_blocks_proposed INTEGER DEFAULT 0,  -- 提出的区块数
    total_blocks_validated INTEGER DEFAULT 0, -- 验证的区块数
    
    -- 资源状态
    cpu_usage DECIMAL(5,2),           -- 当前CPU使用率(%)
    memory_usage DECIMAL(10,2),       -- 当前内存使用(MB)
    disk_usage DECIMAL(10,2),         -- 当前磁盘使用(GB)
    
    -- 网络状态
    peers_count INTEGER DEFAULT 0,    -- 连接的对等节点数
    network_latency_avg DECIMAL(10,4),  -- 平均网络延迟(ms)
    
    -- 时间戳
    last_heartbeat TIMESTAMP,         -- 最后心跳时间
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_role CHECK (role IN ('leader', 'validator', 'follower')),
    CONSTRAINT chk_status CHECK (status IN ('online', 'offline', 'syncing', 'failed'))
);

-- 索引
CREATE INDEX idx_nodes_status ON nodes(status);
CREATE INDEX idx_nodes_role ON nodes(role);
CREATE INDEX idx_nodes_trust_score ON nodes(trust_score DESC);
CREATE INDEX idx_nodes_last_heartbeat ON nodes(last_heartbeat DESC);

-- 更新时间戳触发器
CREATE TRIGGER update_nodes_updated_at
    BEFORE UPDATE ON nodes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

### 4. metrics表 (性能指标 - 时序表)

```sql
CREATE TABLE metrics (
    id BIGSERIAL,
    
    -- 时间和关联
    timestamp TIMESTAMP NOT NULL,
    node_id VARCHAR(50) REFERENCES nodes(id) ON DELETE CASCADE,
    benchmark_id UUID REFERENCES benchmarks(id) ON DELETE CASCADE,
    
    -- 指标信息
    metric_name VARCHAR(100) NOT NULL,  -- consensus_tps/latency_p99/cpu_usage等
    metric_value DECIMAL(20,6) NOT NULL,
    metric_unit VARCHAR(20),            -- tx/s, ms, %, MB等
    
    -- 标签 (JSONB格式，支持灵活查询)
    labels JSONB,
    
    -- 元数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (timestamp, node_id, metric_name)
) PARTITION BY RANGE (DATE(timestamp));

-- 创建分区表 (按周)
CREATE TABLE metrics_2024_w01 PARTITION OF metrics
    FOR VALUES FROM ('2024-01-01') TO ('2024-01-08');

CREATE TABLE metrics_2024_w02 PARTITION OF metrics
    FOR VALUES FROM ('2024-01-08') TO ('2024-01-15');

-- 索引
CREATE INDEX idx_metrics_timestamp ON metrics(timestamp DESC);
CREATE INDEX idx_metrics_node_id ON metrics(node_id);
CREATE INDEX idx_metrics_benchmark_id ON metrics(benchmark_id);
CREATE INDEX idx_metrics_metric_name ON metrics(metric_name);
CREATE INDEX idx_metrics_labels ON metrics USING GIN(labels);

-- 自动创建未来分区
CREATE OR REPLACE FUNCTION create_metrics_partition_if_not_exists()
RETURNS TRIGGER AS $$
DECLARE
    partition_date DATE;
    partition_name TEXT;
    start_date DATE;
    end_date DATE;
BEGIN
    partition_date := DATE_TRUNC('week', NEW.timestamp);
    partition_name := 'metrics_' || TO_CHAR(partition_date, 'YYYY_"w"IW');
    start_date := partition_date;
    end_date := partition_date + INTERVAL '1 week';
    
    IF NOT EXISTS (
        SELECT 1 FROM pg_class WHERE relname = partition_name
    ) THEN
        EXECUTE format(
            'CREATE TABLE IF NOT EXISTS %I PARTITION OF metrics FOR VALUES FROM (%L) TO (%L)',
            partition_name, start_date, end_date
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER create_metrics_partition
    BEFORE INSERT ON metrics
    FOR EACH ROW
    EXECUTE FUNCTION create_metrics_partition_if_not_exists();
```

### 5. anomalies表 (异常记录)

```sql
CREATE TABLE anomalies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 异常基本信息
    anomaly_type VARCHAR(50) NOT NULL,  -- wash_trade/spoofing/sandwich/front_running
    severity VARCHAR(20) NOT NULL,      -- low/medium/high/critical
    confidence_score DECIMAL(5,2) NOT NULL,  -- 置信度(0-100)
    
    -- 关联信息
    transaction_hash VARCHAR(66),
    node_id VARCHAR(50) REFERENCES nodes(id),
    benchmark_id UUID REFERENCES benchmarks(id),
    
    -- 描述与证据
    description TEXT,
    evidence JSONB,                     -- 证据数据(JSON格式)
    
    -- 状态
    status VARCHAR(20) DEFAULT 'new',   -- new/investigating/confirmed/false_positive/resolved
    
    -- 处理信息
    assigned_to VARCHAR(100),
    resolved_at TIMESTAMP,
    resolution_notes TEXT,
    
    -- 时间戳
    detected_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_anomaly_type CHECK (
        anomaly_type IN ('wash_trade', 'spoofing', 'sandwich', 'front_running', 'other')
    ),
    CONSTRAINT chk_severity CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    CONSTRAINT chk_status CHECK (
        status IN ('new', 'investigating', 'confirmed', 'false_positive', 'resolved')
    )
);

-- 索引
CREATE INDEX idx_anomalies_type ON anomalies(anomaly_type);
CREATE INDEX idx_anomalies_severity ON anomalies(severity);
CREATE INDEX idx_anomalies_status ON anomalies(status);
CREATE INDEX idx_anomalies_detected_at ON anomalies(detected_at DESC);
CREATE INDEX idx_anomalies_benchmark_id ON anomalies(benchmark_id);
CREATE INDEX idx_anomalies_evidence ON anomalies USING GIN(evidence);

-- 更新时间戳触发器
CREATE TRIGGER update_anomalies_updated_at
    BEFORE UPDATE ON anomalies
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

---

*[文档继续，包含完整的GORM模型、Repository、Service、缓存、gRPC、配置等所有章节...]*

*由于字符限制，完整内容请参考原始文件*

---

## 🎯 开发指引总结

### 关键点

1. **分层架构**: Repository → Service → gRPC Handler
2. **GORM使用**: 充分利用钩子、关联、分区表
3. **Redis缓存**: 热数据缓存24小时,查询先缓存后数据库
4. **gRPC API**: Protobuf定义清晰,支持反射调试
5. **错误处理**: 统一错误类型,日志记录完整
6. **性能优化**: 批量插入、索引优化、连接池配置
7. **测试覆盖**: 单元测试 + 集成测试

### 开发流程

```bash
# 1. 克隆仓库
git clone https://github.com/fffeng99999/hcp-server.git
cd hcp-server

# 2. 安装依赖
make deps

# 3. 启动PostgreSQL和Redis (Docker Compose)
docker-compose up -d postgres redis

# 4. 运行数据库迁移
make migrate

# 5. 生成Protobuf代码
make proto

# 6. 运行服务器
make run

# 7. 运行测试
make test

# 8. 构建Docker镜像
make docker
```

---

**文档版本**: v1.0.0  
**最后更新**: 2026-02-04  
**作者**: HCP Team
