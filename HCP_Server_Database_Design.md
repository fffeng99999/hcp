# HCP-Server 数据库设计文档

## 📋 文档信息

- **项目名称**: HCP-Server (数据库设计)
- **数据库**: PostgreSQL 14+
- **版本**: v1.0.0
- **最后更新**: 2026-02-04
- **作者**: HCP Team

---

## 📊 数据库概览

### 设计原则

1. **规范化设计**: 符合第三范式(3NF)，减少数据冗余
2. **性能优化**: 合理使用索引、分区表、物化视图
3. **扩展性**: 支持水平扩展和垂直扩展
4. **数据完整性**: 外键约束、检查约束、触发器
5. **时序数据优化**: 按时间分区，支持高频数据写入
6. **审计追踪**: 创建时间、更新时间自动维护

### 核心表结构

| 表名 | 用途 | 记录数预估 | 分区策略 |
|------|------|-----------|---------|
| benchmarks | 基准测试记录 | 10K/年 | 无分区 |
| transactions | 交易记录 | 10M/天 | 按月分区 |
| nodes | 节点信息 | 50-200 | 无分区 |
| metrics | 性能指标 | 100M/天 | 按周分区 |
| anomalies | 异常记录 | 1K/天 | 无分区 |

### ER图概览

```
┌─────────────┐
│  benchmarks │
│             │
│ - id (PK)   │
│ - name      │
│ - algorithm │
│ - status    │
└──────┬──────┘
       │
       │ 1:N
       │
       ▼
┌─────────────────┐        ┌──────────┐
│  transactions   │◄───────┤  nodes   │
│                 │  N:1   │          │
│ - hash (PK)     │        │ - id (PK)│
│ - benchmark_id  │        │ - name   │
│ - from_address  │        │ - status │
│ - to_address    │        └──────┬───┘
│ - status        │               │
└────────┬────────┘               │
         │                        │
         │ 1:N                    │ 1:N
         │                        │
         ▼                        ▼
┌─────────────────┐        ┌─────────────┐
│    metrics      │        │  anomalies  │
│                 │        │             │
│ - timestamp (PK)│        │ - id (PK)   │
│ - node_id       │        │ - node_id   │
│ - metric_name   │        │ - type      │
│ - metric_value  │        │ - severity  │
└─────────────────┘        └─────────────┘
```

---

## 🗂️ 表结构详细设计

### 1. benchmarks 表（基准测试）

**用途**: 存储基准测试的配置、运行状态和性能结果

**表结构**:

```sql
CREATE TABLE benchmarks (
    -- 主键
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 基本信息
    name VARCHAR(255) NOT NULL,
    description TEXT,
    algorithm VARCHAR(50) NOT NULL,
    node_count INTEGER NOT NULL,
    duration INTEGER NOT NULL,
    target_tps INTEGER,
    
    -- 性能指标
    actual_tps DECIMAL(10,2),
    latency_p50 DECIMAL(10,4),
    latency_p90 DECIMAL(10,4),
    latency_p99 DECIMAL(10,4),
    latency_p999 DECIMAL(10,4),
    latency_avg DECIMAL(10,4),
    latency_max DECIMAL(10,4),
    latency_min DECIMAL(10,4),
    
    -- 区块链指标
    block_count INTEGER,
    transaction_count INTEGER,
    successful_tx INTEGER,
    failed_tx INTEGER,
    block_size_avg DECIMAL(10,2),
    block_propagation_time DECIMAL(10,4),
    
    -- 资源使用
    cpu_usage_avg DECIMAL(5,2),
    cpu_usage_max DECIMAL(5,2),
    memory_usage_avg DECIMAL(10,2),
    memory_usage_max DECIMAL(10,2),
    network_in_mbps DECIMAL(10,2),
    network_out_mbps DECIMAL(10,2),
    disk_io_read DECIMAL(10,2),
    disk_io_write DECIMAL(10,2),
    
    -- 共识特定指标
    view_change_count INTEGER,
    prepare_phase_latency DECIMAL(10,4),
    commit_phase_latency DECIMAL(10,4),
    
    -- 状态与元数据
    status VARCHAR(20) DEFAULT 'running',
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 约束
    CONSTRAINT chk_algorithm CHECK (algorithm IN ('tPBFT', 'Raft', 'HotStuff', 'Leios', 'HybridPBFT')),
    CONSTRAINT chk_status CHECK (status IN ('running', 'completed', 'failed', 'cancelled')),
    CONSTRAINT chk_node_count CHECK (node_count > 0 AND node_count <= 1000),
    CONSTRAINT chk_duration CHECK (duration > 0)
);

-- 索引
CREATE INDEX idx_benchmarks_algorithm ON benchmarks(algorithm);
CREATE INDEX idx_benchmarks_status ON benchmarks(status);
CREATE INDEX idx_benchmarks_created_at ON benchmarks(created_at DESC);
CREATE INDEX idx_benchmarks_node_count ON benchmarks(node_count);
CREATE INDEX idx_benchmarks_actual_tps ON benchmarks(actual_tps DESC);
CREATE INDEX idx_benchmarks_algorithm_status ON benchmarks(algorithm, status);

-- 触发器
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

**字段说明**:

| 字段 | 类型 | 说明 | 示例值 |
|------|------|------|--------|
| id | UUID | 主键，自动生成 | `550e8400-e29b-41d4-a716-446655440000` |
| name | VARCHAR(255) | 测试名称 | `tPBFT-100nodes-5min` |
| algorithm | VARCHAR(50) | 共识算法 | `tPBFT`, `Raft`, `HotStuff` |
| node_count | INTEGER | 参与节点数 | `100` |
| duration | INTEGER | 测试持续时间(秒) | `300` |
| actual_tps | DECIMAL(10,2) | 实际TPS | `1523.45` |
| latency_p99 | DECIMAL(10,4) | P99延迟(ms) | `458.3200` |
| status | VARCHAR(20) | 运行状态 | `running`, `completed` |

**常用查询**:

```sql
-- 查询最近7天的tPBFT测试结果
SELECT 
    id, name, node_count, actual_tps, latency_p99, status, created_at
FROM benchmarks
WHERE algorithm = 'tPBFT'
    AND created_at >= CURRENT_DATE - INTERVAL '7 days'
    AND status = 'completed'
ORDER BY actual_tps DESC
LIMIT 10;

-- 统计不同节点数的平均性能
SELECT 
    node_count,
    COUNT(*) as test_count,
    AVG(actual_tps) as avg_tps,
    AVG(latency_p99) as avg_p99_latency
FROM benchmarks
WHERE status = 'completed'
GROUP BY node_count
ORDER BY node_count;
```

---

### 2. transactions 表（交易记录 - 时序分区表）

**用途**: 存储所有交易记录，支持高频写入和时序查询

**表结构**:

```sql
CREATE TABLE transactions (
    -- 主键
    hash VARCHAR(66) PRIMARY KEY,
    
    -- 交易基本信息
    from_address VARCHAR(42) NOT NULL,
    to_address VARCHAR(42) NOT NULL,
    amount BIGINT NOT NULL,
    gas_price BIGINT,
    gas_limit BIGINT,
    gas_used BIGINT,
    nonce BIGINT,
    
    -- 区块信息
    block_number BIGINT,
    block_hash VARCHAR(66),
    transaction_index INTEGER,
    
    -- 状态
    status VARCHAR(20) NOT NULL,
    error_message TEXT,
    
    -- 时间戳
    submitted_at TIMESTAMP NOT NULL,
    confirmed_at TIMESTAMP,
    
    -- 性能指标
    latency_ms DECIMAL(10,4),
    
    -- 关联
    benchmark_id UUID REFERENCES benchmarks(id) ON DELETE CASCADE,
    
    -- 元数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 约束
    CONSTRAINT chk_status CHECK (status IN ('pending', 'confirmed', 'failed')),
    CONSTRAINT chk_amount CHECK (amount >= 0),
    CONSTRAINT chk_addresses CHECK (from_address != to_address)
) PARTITION BY RANGE (DATE(submitted_at));

-- 创建分区表（按月）
CREATE TABLE transactions_2024_01 PARTITION OF transactions
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
CREATE TABLE transactions_2024_02 PARTITION OF transactions
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
CREATE TABLE transactions_2024_03 PARTITION OF transactions
    FOR VALUES FROM ('2024-03-01') TO ('2024-04-01');

-- 索引
CREATE INDEX idx_transactions_from ON transactions(from_address);
CREATE INDEX idx_transactions_to ON transactions(to_address);
CREATE INDEX idx_transactions_status ON transactions(status);
CREATE INDEX idx_transactions_submitted_at ON transactions(submitted_at DESC);
CREATE INDEX idx_transactions_benchmark_id ON transactions(benchmark_id);

-- 自动分区创建触发器
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
    
    IF NOT EXISTS (SELECT 1 FROM pg_class WHERE relname = partition_name) THEN
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

**字段说明**:

| 字段 | 类型 | 说明 | 示例值 |
|------|------|------|--------|
| hash | VARCHAR(66) | 交易哈希 | `0x1234...abcd` |
| from_address | VARCHAR(42) | 发送方 | `0x742d35Cc...` |
| to_address | VARCHAR(42) | 接收方 | `0x5aAeb605...` |
| amount | BIGINT | 金额(wei) | `1000000000000000000` |
| status | VARCHAR(20) | 状态 | `pending/confirmed/failed` |
| latency_ms | DECIMAL(10,4) | 延迟(ms) | `342.5600` |

**常用查询**:

```sql
-- 查询某基准测试的交易统计
SELECT 
    status,
    COUNT(*) as count,
    AVG(latency_ms) as avg_latency
FROM transactions
WHERE benchmark_id = '550e8400-e29b-41d4-a716-446655440000'
GROUP BY status;

-- 时间序列查询（每小时TPS）
SELECT 
    DATE_TRUNC('hour', confirmed_at) as hour,
    COUNT(*) / 3600.0 as tps
FROM transactions
WHERE confirmed_at >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY hour
ORDER BY hour;
```

---

### 3. nodes 表（节点信息）

**用途**: 存储区块链网络中节点的配置、状态和性能信息

**表结构**:

```sql
CREATE TABLE nodes (
    -- 主键
    id VARCHAR(50) PRIMARY KEY,
    
    -- 节点基本信息
    name VARCHAR(255),
    address VARCHAR(255) NOT NULL,
    public_key TEXT,
    region VARCHAR(50),
    
    -- 角色与状态
    role VARCHAR(20) DEFAULT 'validator',
    status VARCHAR(20) DEFAULT 'offline',
    
    -- 性能指标
    trust_score DECIMAL(5,2) DEFAULT 100.00,
    uptime_percentage DECIMAL(5,2),
    total_blocks_proposed INTEGER DEFAULT 0,
    total_blocks_validated INTEGER DEFAULT 0,
    
    -- 资源状态
    cpu_usage DECIMAL(5,2),
    memory_usage DECIMAL(10,2),
    disk_usage DECIMAL(10,2),
    
    -- 网络状态
    peers_count INTEGER DEFAULT 0,
    network_latency_avg DECIMAL(10,4),
    
    -- 时间戳
    last_heartbeat TIMESTAMP,
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 约束
    CONSTRAINT chk_role CHECK (role IN ('leader', 'validator', 'follower', 'observer')),
    CONSTRAINT chk_status CHECK (status IN ('online', 'offline', 'syncing', 'failed')),
    CONSTRAINT chk_trust_score CHECK (trust_score >= 0 AND trust_score <= 100)
);

-- 索引
CREATE INDEX idx_nodes_status ON nodes(status);
CREATE INDEX idx_nodes_role ON nodes(role);
CREATE INDEX idx_nodes_trust_score ON nodes(trust_score DESC);
CREATE INDEX idx_nodes_last_heartbeat ON nodes(last_heartbeat DESC);

-- 触发器
CREATE TRIGGER update_nodes_updated_at
    BEFORE UPDATE ON nodes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

**字段说明**:

| 字段 | 类型 | 说明 | 示例值 |
|------|------|------|--------|
| id | VARCHAR(50) | 节点ID | `node-001` |
| name | VARCHAR(255) | 节点名称 | `Beijing-Validator-01` |
| address | VARCHAR(255) | 网络地址 | `192.168.1.100:8080` |
| role | VARCHAR(20) | 角色 | `leader/validator/follower` |
| status | VARCHAR(20) | 状态 | `online/offline/syncing` |
| trust_score | DECIMAL(5,2) | 信任评分 | `95.50` |

**常用查询**:

```sql
-- 查询在线节点统计
SELECT role, status, COUNT(*) as count
FROM nodes
GROUP BY role, status;

-- 查找最佳验证者节点
SELECT id, name, trust_score, network_latency_avg
FROM nodes
WHERE status = 'online' AND role = 'validator'
ORDER BY trust_score DESC
LIMIT 10;
```

---

### 4. metrics 表（性能指标 - 时序分区表）

**用途**: 存储实时性能指标，支持时序分析和聚合查询

**表结构**:

```sql
CREATE TABLE metrics (
    id BIGSERIAL,
    timestamp TIMESTAMP NOT NULL,
    node_id VARCHAR(50) REFERENCES nodes(id) ON DELETE CASCADE,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(20,6) NOT NULL,
    metric_unit VARCHAR(20),
    labels JSONB,
    benchmark_id UUID REFERENCES benchmarks(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (timestamp, node_id, metric_name)
) PARTITION BY RANGE (DATE(timestamp));

-- 创建分区表（按周）
CREATE TABLE metrics_2024_w01 PARTITION OF metrics
    FOR VALUES FROM ('2024-01-01') TO ('2024-01-08');
CREATE TABLE metrics_2024_w02 PARTITION OF metrics
    FOR VALUES FROM ('2024-01-08') TO ('2024-01-15');

-- 索引
CREATE INDEX idx_metrics_timestamp ON metrics(timestamp DESC);
CREATE INDEX idx_metrics_node_id ON metrics(node_id);
CREATE INDEX idx_metrics_metric_name ON metrics(metric_name);
CREATE INDEX idx_metrics_labels ON metrics USING GIN(labels);
```

**常见指标类型**:

| metric_name | metric_unit | 说明 |
|-------------|-------------|------|
| `consensus_tps` | `tx/s` | 共识TPS |
| `latency_p99` | `ms` | P99延迟 |
| `cpu_usage` | `%` | CPU使用率 |
| `memory_usage` | `MB` | 内存使用 |
| `network_in` | `Mbps` | 入站网络 |

**常用查询**:

```sql
-- 查询最近1小时的平均TPS
SELECT 
    DATE_TRUNC('minute', timestamp) as minute,
    AVG(metric_value) as avg_tps
FROM metrics
WHERE metric_name = 'consensus_tps'
    AND timestamp >= NOW() - INTERVAL '1 hour'
GROUP BY minute;
```

---

### 5. anomalies 表（异常记录）

**用途**: 存储检测到的异常交易和可疑行为

**表结构**:

```sql
CREATE TABLE anomalies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    anomaly_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    confidence_score DECIMAL(5,2) NOT NULL,
    transaction_hash VARCHAR(66),
    node_id VARCHAR(50) REFERENCES nodes(id),
    benchmark_id UUID REFERENCES benchmarks(id),
    description TEXT,
    evidence JSONB,
    status VARCHAR(20) DEFAULT 'new',
    assigned_to VARCHAR(100),
    resolved_at TIMESTAMP,
    resolution_notes TEXT,
    detected_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_anomaly_type CHECK (
        anomaly_type IN ('wash_trade', 'spoofing', 'sandwich', 'front_running', 'ddos', 'sybil')
    ),
    CONSTRAINT chk_severity CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    CONSTRAINT chk_status CHECK (status IN ('new', 'investigating', 'confirmed', 'resolved'))
);

-- 索引
CREATE INDEX idx_anomalies_type ON anomalies(anomaly_type);
CREATE INDEX idx_anomalies_severity ON anomalies(severity);
CREATE INDEX idx_anomalies_status ON anomalies(status);
CREATE INDEX idx_anomalies_detected_at ON anomalies(detected_at DESC);
```

**异常类型说明**:

| anomaly_type | 说明 |
|--------------|------|
| `wash_trade` | 洗盘交易 |
| `spoofing` | 欺骗订单 |
| `sandwich` | 三明治攻击 |
| `front_running` | 抢跑攻击 |

**常用查询**:

```sql
-- 查询未处理的严重异常
SELECT id, anomaly_type, severity, description
FROM anomalies
WHERE status = 'new' AND severity IN ('high', 'critical')
ORDER BY detected_at DESC;
```

---

## 📐 性能优化

### 索引策略

```sql
-- 查看未使用的索引
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY pg_relation_size(indexrelid) DESC;
```

### 物化视图

```sql
-- 创建每小时聚合视图
CREATE MATERIALIZED VIEW metrics_hourly AS
SELECT 
    DATE_TRUNC('hour', timestamp) as hour,
    node_id,
    metric_name,
    AVG(metric_value) as avg_value
FROM metrics
GROUP BY hour, node_id, metric_name;

-- 定期刷新
REFRESH MATERIALIZED VIEW CONCURRENTLY metrics_hourly;
```

---

## 🔧 维护脚本

### 备份

```bash
# 全量备份
pg_dump -U postgres -d hcp -F c -f /backups/hcp_$(date +%Y%m%d).dump

# 恢复
pg_restore -U postgres -d hcp -c /backups/hcp_20260204.dump
```

### 监控

```sql
-- 表大小统计
SELECT 
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## 📄 文档变更记录

| 版本 | 日期 | 变更内容 |
|------|------|---------|
| v1.0.0 | 2026-02-04 | 初始版本，包含5张核心表设计 |

---

**维护**: HCP Team  
**GitHub**: https://github.com/hcp-bench/hcp-server
