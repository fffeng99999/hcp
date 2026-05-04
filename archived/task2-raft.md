在**单机多节点**（一台 Linux 跑 n 个本地进程）场景下，Raft 的集成逻辑与 IBFT/HotStuff 完全一致：**不需要真实网络层，只需数学模拟模型**。

---

## 一、Raft 核心参数（业界通用 vs 您项目现状）

| 参数 | 业界典型值 | 您项目现状 | 单机建议 |
|------|-----------|-----------|---------|
| `ElectionTimeout` | 150~1000ms | ✅ 150ms | 100~500ms |
| `HeartbeatInterval` | 50~500ms | ✅ 50ms | 50~200ms（必须 < ElectionTimeout） |
| `ElectionTimeoutRange` | [T, 2T] 随机 | ⚠️ 硬编码 `+150ms` | 可配置随机范围 |
| `SnapshotDistance` | 10000~100000 条 | ❌ 无 | 10000 |
| `MaxLogEntriesPerRPC` | 100~1000 | ❌ 无 | 500（Batch Size） |
| `MessageBytes` | 256B~1KB | ❌ 无 | 256~512 |

> **Raft 关键约束**：`HeartbeatInterval < ElectionTimeout`，否则 Follower 会在收到心跳前触发选举。

---

## 二、Raft 与 BFT 共识的关键区别（影响参数设计）

| 特性 | Raft (CFT) | HotStuff/IBFT (BFT) |
|------|-----------|---------------------|
| 容错类型 | 崩溃故障 (Crash) | 拜占庭故障 (Byzantine) |
| 最小节点数 | 2f+1 | 3f+1 |
| 最大故障数 | f = (n-1)/2 | f = (n-1)/3 |
| Quorum | majority = n/2 + 1 | 2f+1 |
| 正常消息复杂度 | O(n) | O(n) ~ O(n²) |
| 视图切换 | Leader Election | View Change |
| 故障模拟 | 节点崩溃/失联 | 恶意行为/沉默/分叉 |

---

## 三、需要修改/增加的代码（按文件）

### 1. `hcp-consensus/app/app.go`（修复编译错误）

**现状**：`app.go:342` 调用 `raft.NewRaftConsensus()` 无参数，但定义需要 `(nodeID, peers, cfg)`。

**修改**：
```go
case "raft":
    consensusEngine = raft.NewRaftConsensus(raft.Config{
        NodeCount:              readInt("raft-node-count", 4),
        ElectionTimeoutMs:      readFloat("raft-election-timeout-ms", 150),
        HeartbeatIntervalMs:    readFloat("raft-heartbeat-interval-ms", 50),
        ElectionTimeoutRangeMs: readFloat("raft-election-timeout-range-ms", 150),
        SnapshotDistance:       readInt("raft-snapshot-distance", 10000),
        MaxLogEntriesPerRPC:    readInt("raft-max-log-entries-per-rpc", 500),
        MessageBytes:           readInt("raft-message-bytes", 256),
        FaultyRatio:            readFloat("raft-faulty-ratio", 0), // 崩溃比例
    })
```

### 2. `hcp-consensus/consensus/raft/consensus.go`（重构 Config）

```go
type Config struct {
    NodeCount              int
    ElectionTimeoutMs      float64
    HeartbeatIntervalMs    float64
    ElectionTimeoutRangeMs float64
    SnapshotDistance       int
    MaxLogEntriesPerRPC    int
    MessageBytes           int
    FaultyRatio            float64
}

func NewRaftConsensus(cfg Config) *RaftConsensus {
    cfg = normalizeConfig(cfg)
    // 移除 nodeID/peers 参数
}
```

### 3. `hcp-consensus/consensus/raft/node.go`（核心：增加 ComputeMetrics）

Raft 的数学模型与 BFT 不同，需单独建模：

```go
type Metrics struct {
    BlockTimeMs        float64
    AppendEntriesMs    float64  // Leader→Followers 广播时延
    ReplicationMs      float64  // Followers→Leader 确认时延
    ElectionMs         float64  // 选举耗时（故障时）
    Elections          int      // 选举次数
    HeartbeatMessages  int      // 心跳消息数
    TotalMessages      int      // 总消息数
    CommBytes          float64
    NodeCount          int
    Quorum             int
    FaultyRatio        float64
    ElectionTimeoutMs  float64
    HeartbeatIntervalMs float64
}

func (n *Node) ComputeMetrics(height int64) Metrics {
    nodeCount := n.cfg.NodeCount
    quorum := nodeCount/2 + 1
    
    // 正常路径：每块共识
    // 1. Leader AppendEntries 广播 (n-1)
    // 2. Followers 回复 (n-1)
    appendEntriesLatency := n.phaseLatencyMs(nodeCount, quorum)
    
    messagesPerBlock := 2 * (nodeCount - 1)
    
    // 心跳：每 HeartbeatInterval 发送一轮
    // 假设每块平均间隔 blockTime，期间的心跳轮数
    heartbeatsPerBlock := int(blockTimeMs / n.cfg.HeartbeatIntervalMs)
    if heartbeatsPerBlock < 1 {
        heartbeatsPerBlock = 1
    }
    heartbeatMessages := heartbeatsPerBlock * (nodeCount - 1)
    
    // 故障模拟：Leader 崩溃
    electionMs := 0.0
    elections := 0
    if n.rng.Float64() < n.cfg.FaultyRatio {
        elections++
        // 随机选举超时 [T, T+Range]
        electionTimeout := n.cfg.ElectionTimeoutMs + n.rng.Float64()*n.cfg.ElectionTimeoutRangeMs
        //  RequestVote 广播 + 收集 Majority 投票
        voteLatency := n.phaseLatencyMs(nodeCount, quorum)
        electionMs = electionTimeout + voteLatency
    }
    
    totalMessages := messagesPerBlock + heartbeatMessages
    if elections > 0 {
        totalMessages += (nodeCount - 1) + (quorum - 1) // RequestVote + votes
    }
    
    blockTime := appendEntriesLatency + electionMs
    
    return Metrics{
        BlockTimeMs:         blockTime,
        AppendEntriesMs:     appendEntriesLatency / 2, // 去程
        ReplicationMs:       appendEntriesLatency / 2, // 回程
        ElectionMs:          electionMs,
        Elections:           elections,
        HeartbeatMessages:   heartbeatMessages,
        TotalMessages:       totalMessages,
        CommBytes:           float64(totalMessages * n.cfg.MessageBytes),
        NodeCount:           nodeCount,
        Quorum:              quorum,
        FaultyRatio:         n.cfg.FaultyRatio,
        ElectionTimeoutMs:   n.cfg.ElectionTimeoutMs,
        HeartbeatIntervalMs: n.cfg.HeartbeatIntervalMs,
    }
}
```

### 4. `hcp-consensus/consensus/raft/consensus.go`（EndBlock 输出日志）

```go
func (r *RaftConsensus) EndBlock(ctx sdk.Context) []abci.ValidatorUpdate {
    metrics := r.Node.ComputeMetrics(ctx.BlockHeight())
    fmt.Printf(
        "raft_metrics block_time_ms=%.6f append_entries_ms=%.6f replication_ms=%.6f election_ms=%.6f elections=%d heartbeat_messages=%d total_messages=%d comm_bytes=%.0f node_count=%d quorum=%d faulty_ratio=%.4f election_timeout_ms=%.6f heartbeat_interval_ms=%.6f height=%d\n",
        metrics.BlockTimeMs,
        metrics.AppendEntriesMs,
        metrics.ReplicationMs,
        metrics.ElectionMs,
        metrics.Elections,
        metrics.HeartbeatMessages,
        metrics.TotalMessages,
        metrics.CommBytes,
        metrics.NodeCount,
        metrics.Quorum,
        metrics.FaultyRatio,
        metrics.ElectionTimeoutMs,
        metrics.HeartbeatIntervalMs,
        ctx.BlockHeight(),
    )
    return nil
}
```

### 5. `hcp/start_nodes.sh`（增加 Raft 参数分支）

```bash
if [ "$CONSENSUS_ENGINE" = "raft" ]; then
    start_args+=("--raft-node-count" "$NUM_NODES")
    [ -n "$RAFT_ELECTION_TIMEOUT_MS" ] && start_args+=("--raft-election-timeout-ms" "$RAFT_ELECTION_TIMEOUT_MS")
    [ -n "$RAFT_HEARTBEAT_INTERVAL_MS" ] && start_args+=("--raft-heartbeat-interval-ms" "$RAFT_HEARTBEAT_INTERVAL_MS")
    [ -n "$RAFT_ELECTION_TIMEOUT_RANGE_MS" ] && start_args+=("--raft-election-timeout-range-ms" "$RAFT_ELECTION_TIMEOUT_RANGE_MS")
    [ -n "$RAFT_FAULTY_RATIO" ] && start_args+=("--raft-faulty-ratio" "$RAFT_FAULTY_RATIO")
    [ -n "$RAFT_MESSAGE_BYTES" ] && start_args+=("--raft-message-bytes" "$RAFT_MESSAGE_BYTES")
    [ -n "$RAFT_SNAPSHOT_DISTANCE" ] && start_args+=("--raft-snapshot-distance" "$RAFT_SNAPSHOT_DISTANCE")
    [ -n "$RAFT_MAX_LOG_ENTRIES_PER_RPC" ] && start_args+=("--raft-max-log-entries-per-rpc" "$RAFT_MAX_LOG_ENTRIES_PER_RPC")
fi
```

### 6. `hcp-lab/collector/log_parser.py`（增加解析）

```python
import re

def parse_raft_metrics(log_dir: Path) -> List[Dict[str, Any]]:
    pattern = re.compile(
        r"raft_metrics block_time_ms=([\d.]+) .* elections=(\d+) heartbeat_messages=(\d+) total_messages=(\d+) comm_bytes=([\d.]+) .* height=(\d+)"
    )
    # 类似其他解析函数实现
```

### 7. `hcp-lab/hcp-lab-server/internal/experiments/experiments.go`（注册实验）

```go
{
    ID: "exp9_raft",
    Name: "实验九：Raft 共识性能",
    RunScript: "hcp-lab/experiments/exp9_raft/run_exp9_raft.sh",
    ReportDir: "hcp-lab/experiments/exp9_raft/report",
    Params: []ParamSchema{
        {Name: "NODES_LIST", Type: ParamTypeListInt, Default: "4,8,16,32", Description: "节点数量列表", Required: true},
        {Name: "TX_COUNT", Type: ParamTypeInt, Default: 1000, Description: "交易数量", Required: true},
        {Name: "RAFT_ELECTION_TIMEOUT_MS", Type: ParamTypeFloat, Default: 150, Description: "选举超时(ms)", Required: false},
        {Name: "RAFT_HEARTBEAT_INTERVAL_MS", Type: ParamTypeFloat, Default: 50, Description: "心跳间隔(ms)", Required: false},
        {Name: "RAFT_ELECTION_TIMEOUT_RANGE_MS", Type: ParamTypeFloat, Default: 150, Description: "选举超时随机范围(ms)", Required: false},
        {Name: "RAFT_FAULTY_RATIO", Type: ParamTypeFloat, Default: 0, Description: "节点崩溃比例", Required: false},
        {Name: "RAFT_MESSAGE_BYTES", Type: ParamTypeInt, Default: 256, Description: "消息大小(字节)", Required: false},
        {Name: "RAFT_SNAPSHOT_DISTANCE", Type: ParamTypeInt, Default: 10000, Description: "快照间隔(日志条数)", Required: false},
    },
}
```

---

## 四、Raft 单机多节点特殊注意

| 方面 | Raft 特性 | 单机建议 |
|------|----------|---------|
| **心跳风暴** | Leader 每 HeartbeatInterval 广播 (n-1) 条 | 单机回环快，但 32 节点 × 频繁心跳 = 消息风暴，建议 HeartbeatInterval ≥ 50ms |
| **选举分裂** | 多 Candidate 同时发起选举会分裂选票 | ElectionTimeoutRange 必须足够大（≥ 2×HeartbeatInterval） |
| **故障模拟** | 只有 Crash Fault，没有 Byzantine | `FaultyRatio` 含义是"节点崩溃失联"，不是恶意行为 |
| **快照频率** | SnapshotDistance 过大→恢复慢；过小→CPU/IO 高 | 10000~50000 条为宜 |

---

## 五、最小可行改动（MVP）

| 优先级 | 改动 | 说明 |
|--------|------|------|
| P0 | 修复 `NewRaftConsensus` 参数不匹配 | 和 HotStuff 一样，当前 `app.go` 调用无参数会导致编译失败 |
| P0 | 增加 `ComputeMetrics` + `EndBlock` 日志 | 核心数学模型 |
| P1 | `start_nodes.sh` 增加 Raft 分支 | 传递参数 |
| P1 | 实验注册 + 脚本 | 让实验框架识别 |
| P1 | 日志解析器 | 采集 metrics |

---

## 六、关键对比：Raft vs HotStuff（单机实验）

| 维度 | Raft | HotStuff |
|------|------|----------|
| **容错数 f** | (n-1)/2 | (n-1)/3 |
| **正常时延** | 1 RTT (AppendEntries) | 3~4 消息往返 (三阶段) |
| **故障时延** | ElectionTimeout + 1 RTT | ViewTimeout × 指数退避 |
| **每块消息数** | 2(n-1) + 心跳 | 2(n-1)（Pipeline 摊薄后） |
| **心跳开销** | 高（Leader 主动周期性广播） | 低（无显式心跳，QC 即心跳） |
| **故障模拟** | 节点崩溃 | 拜占庭 leader（不发送消息） |

> 在您的单机实验框架中，Raft 的预期表现：**正常路径比 HotStuff 快**（1 RTT vs 3 阶段），**但心跳开销更大**（周期性广播 vs 无心跳），**故障恢复也更快**（ElectionTimeout 通常 < ViewTimeout）。

需要我直接帮您实现 Raft 的某个文件代码吗？