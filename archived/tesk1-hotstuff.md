明白，您的场景是**单机多进程**（一台 Linux 跑 n 个本地节点）。针对这个约束，我重新整理一份**精简版实操建议**：

---

## 核心前提（单机多节点）

您的项目中，IBFT/PoW 等替代共识引擎都是**数学模拟器**——真实区块仍由 CometBFT 产出，共识引擎只在 `EndBlock` 时根据参数计算出该算法的耗时/消息量/带宽。HotStuff 也应走这个路线，**不需要实现真实 P2P 网络**。

---

## 一、需要增加的参数

| 参数 | 类型 | 默认值 | 单机场景建议值 | 作用 |
|------|------|--------|---------------|------|
| `hotstuff-node-count` | int | 4 | 实验规模 | 节点总数 n |
| `hotstuff-faulty-ratio` | float | 0.0 | 0, 0.1, 0.2 | 拜占庭节点比例 |
| `hotstuff-view-timeout-ms` | float | 5000 | 2000~5000 | 视图超时（ms） |
| `hotstuff-timeout-exponent` | float | 2.0 | 2.0 | 超时指数退避倍数 |
| `hotstuff-base-latency-ms` | float | 1.0 | **0.1~1** | 单机回环基础延迟 |
| `hotstuff-jitter-ms` | float | 0.5 | **0~0.5** | 网络抖动（单机设小） |
| `hotstuff-message-bytes` | int | 256 | 256~512 | 共识消息大小 |
| `hotstuff-pipeline-depth` | int | 3 | 2或3 | 2=FastHotStuff, 3=ChainedHotStuff |
| `hotstuff-enable-threshold-sig` | bool | false | false/true | BLS门限签名开关 |

> **单机特殊点**：`base-latency` 和 `jitter` 应设很小（本地回环实际 <0.1ms），否则模拟会失真。

---

## 二、需要修改/增加的代码（按文件）

### 1. `hcp-consensus/app/app.go`（修复编译错误）

**现状**：`app.go:344` 调用 `hotstuff.NewHotStuffConsensus()` 无参数，但定义需要 `(nodeID, peers, cfg)`，**会导致编译失败**。

**修改**：
```go
case "hotstuff":
    consensusEngine = hotstuff.NewHotStuffConsensus(hotstuff.Config{
        NodeCount:              readInt("hotstuff-node-count", 4),
        FaultyRatio:            readFloat("hotstuff-faulty-ratio", 0),
        ViewTimeoutMs:          readFloat("hotstuff-view-timeout-ms", 5000),
        TimeoutExponent:        readFloat("hotstuff-timeout-exponent", 2.0),
        BaseLatencyMs:          readFloat("hotstuff-base-latency-ms", 1),
        JitterMs:               readFloat("hotstuff-jitter-ms", 0.5),
        MessageBytes:           readInt("hotstuff-message-bytes", 256),
        PipelineDepth:          readInt("hotstuff-pipeline-depth", 3),
        EnableThresholdSig:     readBool("hotstuff-enable-threshold-sig", false),
    })
```

### 2. `hcp-consensus/consensus/hotstuff/consensus.go`（重构 Config + 增加 normalize）

```go
type Config struct {
    NodeCount          int
    FaultyRatio        float64
    ViewTimeoutMs      float64
    TimeoutExponent    float64
    BaseLatencyMs      float64
    JitterMs           float64
    MessageBytes       int
    PipelineDepth      int
    EnableThresholdSig bool
}

func NewHotStuffConsensus(cfg Config) *HotStuffConsensus {
    cfg = normalizeConfig(cfg)
    // ... 移除 nodeID/peers 依赖
}

func normalizeConfig(cfg Config) Config {
    // 类似 ibft/trust_scorer.go 的 normalizeConfig
    // 处理默认值、环境变量读取、越界检查
}
```

### 3. `hcp-consensus/consensus/hotstuff/node.go`（核心：增加 ComputeMetrics）

参考 `ibft/node.go:48` 的 `ComputeMetrics`，将事件驱动代码转为**数学模型**：

```go
type Metrics struct {
    BlockTimeMs   float64
    PrepareMs     float64
    PreCommitMs   float64
    CommitMs      float64
    ViewChanges   int
    TotalMessages int
    CommBytes     float64
    NodeCount     int
    F             int
    Quorum        int
    FaultyRatio   float64
    ViewTimeoutMs float64
    BaseLatencyMs float64
}

func (n *Node) ComputeMetrics(height int64) Metrics {
    nodeCount := n.cfg.NodeCount
    f := (nodeCount - 1) / 3
    quorum := 2*f + 1
    
    // Chained HotStuff 每块消息数：
    // leader 广播 Prepare (n-1) + 收集 Quorum 个 votes (n-1)
    // Pipeline 摊薄后，每块实际完成 1 个 phase 的消息往返
    messagesPerBlock := 2 * (nodeCount - 1)
    if n.cfg.EnableThresholdSig {
        messagesPerBlock = (nodeCount - 1) + 1 // 广播 + 聚合后单条 QC
    }
    
    // 计算正常路径时延（取 quorum-1 个延迟的最大值）
    phaseLatency := n.phaseLatencyMs(nodeCount, quorum)
    
    // 视图切换模拟
    viewChanges := 0
    totalTimeout := 0.0
    currentTimeout := n.cfg.ViewTimeoutMs
    
    // 以概率 faultyRatio 遇到故障 leader，触发视图切换
    if n.rng.Float64() < n.cfg.FaultyRatio {
        viewChanges++
        totalTimeout += currentTimeout
        currentTimeout *= n.cfg.TimeoutExponent
    }
    
    blockTime := phaseLatency*float64(n.cfg.PipelineDepth) + totalTimeout
    
    return Metrics{
        BlockTimeMs:   blockTime,
        PrepareMs:     phaseLatency,
        PreCommitMs:   phaseLatency,
        CommitMs:      phaseLatency,
        ViewChanges:   viewChanges,
        TotalMessages: messagesPerBlock,
        CommBytes:     float64(messagesPerBlock * n.cfg.MessageBytes),
        NodeCount:     nodeCount,
        F:             f,
        Quorum:        quorum,
        FaultyRatio:   n.cfg.FaultyRatio,
        ViewTimeoutMs: n.cfg.ViewTimeoutMs,
        BaseLatencyMs: n.cfg.BaseLatencyMs,
    }
}
```

### 4. `hcp-consensus/consensus/hotstuff/consensus.go`（EndBlock 输出日志）

```go
func (h *HotStuffConsensus) EndBlock(ctx sdk.Context) []abci.ValidatorUpdate {
    metrics := h.node.ComputeMetrics(ctx.BlockHeight())
    fmt.Printf("hotstuff_metrics block_time_ms=%.6f prepare_ms=%.6f precommit_ms=%.6f commit_ms=%.6f view_changes=%d total_messages=%d comm_bytes=%.0f node_count=%d f=%d quorum=%d faulty_ratio=%.4f view_timeout_ms=%.6f base_latency_ms=%.6f height=%d\n",
        metrics.BlockTimeMs, metrics.PrepareMs, metrics.PreCommitMs, metrics.CommitMs,
        metrics.ViewChanges, metrics.TotalMessages, metrics.CommBytes,
        metrics.NodeCount, metrics.F, metrics.Quorum,
        metrics.FaultyRatio, metrics.ViewTimeoutMs, metrics.BaseLatencyMs,
        ctx.BlockHeight(),
    )
    return nil
}
```

### 5. `hcp/start_nodes.sh`（增加 HotStuff 参数分支）

在 `start_node()` 函数的共识引擎条件分支中，参照 `ibft` 和 `pow` 的方式增加：

```bash
if [ "$CONSENSUS_ENGINE" = "hotstuff" ]; then
    start_args+=("--hotstuff-node-count" "$NUM_NODES")
    [ -n "$HOTSTUFF_FAULTY_RATIO" ] && start_args+=("--hotstuff-faulty-ratio" "$HOTSTUFF_FAULTY_RATIO")
    [ -n "$HOTSTUFF_VIEW_TIMEOUT_MS" ] && start_args+=("--hotstuff-view-timeout-ms" "$HOTSTUFF_VIEW_TIMEOUT_MS")
    [ -n "$HOTSTUFF_BASE_LATENCY_MS" ] && start_args+=("--hotstuff-base-latency-ms" "$HOTSTUFF_BASE_LATENCY_MS")
    [ -n "$HOTSTUFF_JITTER_MS" ] && start_args+=("--hotstuff-jitter-ms" "$HOTSTUFF_JITTER_MS")
    [ -n "$HOTSTUFF_MESSAGE_BYTES" ] && start_args+=("--hotstuff-message-bytes" "$HOTSTUFF_MESSAGE_BYTES")
    [ -n "$HOTSTUFF_PIPELINE_DEPTH" ] && start_args+=("--hotstuff-pipeline-depth" "$HOTSTUFF_PIPELINE_DEPTH")
    [ -n "$HOTSTUFF_ENABLE_THRESHOLD_SIG" ] && start_args+=("--hotstuff-enable-threshold-sig" "$HOTSTUFF_ENABLE_THRESHOLD_SIG")
    [ -n "$HOTSTUFF_TIMEOUT_EXPONENT" ] && start_args+=("--hotstuff-timeout-exponent" "$HOTSTUFF_TIMEOUT_EXPONENT")
fi
```

### 6. `hcp-lab/collector/log_parser.py`（增加解析函数）

```python
import re

def parse_hotstuff_metrics(log_dir: Path) -> List[Dict[str, Any]]:
    pattern = re.compile(
        r"hotstuff_metrics block_time_ms=([\d.]+) prepare_ms=([\d.]+) precommit_ms=([\d.]+) commit_ms=([\d.]+) view_changes=(\d+) total_messages=(\d+) comm_bytes=([\d.]+) .* height=(\d+)"
    )
    # ... 类似 parse_block_times 的实现
```

### 7. `hcp-lab/hcp-lab-server/internal/experiments/experiments.go`（注册实验）

```go
{
    ID: "exp9_hotstuff",
    Name: "实验九：HotStuff 共识性能",
    RunScript: "hcp-lab/experiments/exp9_hotstuff/run_exp9_hotstuff.sh",
    ReportDir: "hcp-lab/experiments/exp9_hotstuff/report",
    Params: []ParamSchema{
        {Name: "NODES_LIST", Type: ParamTypeListInt, Default: "4,8,16,32", Description: "节点数量列表", Required: true},
        {Name: "TX_COUNT", Type: ParamTypeInt, Default: 1000, Description: "交易数量", Required: true},
        {Name: "HOTSTUFF_VIEW_TIMEOUT_MS", Type: ParamTypeFloat, Default: 5000, Description: "视图超时(ms)", Required: false},
        {Name: "HOTSTUFF_BASE_LATENCY_MS", Type: ParamTypeFloat, Default: 1, Description: "基础延迟(ms)", Required: false},
        {Name: "HOTSTUFF_JITTER_MS", Type: ParamTypeFloat, Default: 0.5, Description: "网络抖动(ms)", Required: false},
        {Name: "HOTSTUFF_FAULTY_RATIO", Type: ParamTypeFloat, Default: 0, Description: "故障节点比例", Required: false},
        {Name: "HOTSTUFF_MESSAGE_BYTES", Type: ParamTypeInt, Default: 256, Description: "消息大小(字节)", Required: false},
        {Name: "HOTSTUFF_PIPELINE_DEPTH", Type: ParamTypeInt, Default: 3, Description: "流水线深度", Required: false},
        {Name: "HOTSTUFF_ENABLE_THRESHOLD_SIG", Type: ParamTypeBool, Default: false, Description: "门限签名", Required: false},
    },
}
```

---

## 三、关键结论

在您的**单机多节点**场景下：

| 不需要做 ❌ | 需要做 ✅ |
|------------|----------|
| 真实 P2P 网络层 | 数学模型（`ComputeMetrics`） |
| 跨进程通信 | `EndBlock` 输出结构化日志 |
| 真实签名验证 | 参数配置 + 环境变量传递 |
| 状态持久化/WAL | 实验脚本 + 注册 |
| Catch-up 同步 | 日志解析器 |

**最小改动 = 修复构造函数 + 写 ComputeMetrics + EndBlock 打印日志 + start_nodes.sh 传参**。这是让 HotStuff 在您的实验框架中跑起来的最快路径。