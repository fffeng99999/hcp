

***

## 📖 **HCP-Bench 系统架构完整文字描述**

我已经为你详细编写了完整的架构文档(1700多行)。这里我用**精炼的文字总结**整个系统的关系:

### **总体架构**

HCP-Bench是一个**微服务分层架构**,分为5层:

**第1层 - 表现层** (hcp-ui)
- Vue3前端应用
- 用户通过浏览器(Port:3000)查看实时性能仪表板
- 直接访问Gateway API(Port:8080)获取数据
- 直接访问Prometheus(Port:9090)查询时序指标
- 显示: 性能曲线、节点拓扑、资源热图

**第2层 - API网关层** (hcp-gateway)  
- Rust/Axum高性能网关
- Port:8080暴露RESTful API给前端
- 路由请求到后端微服务
- 核心职能:
  - 接收共识启动请求 → 调用hcp-consensus gRPC
  - 接收交易提交 → 广播给共识节点
  - 接收指标查询 → 返回Prometheus数据
  - 接收异常检测 → 调用hcp-antimanip服务
- 并发处理: TaskExecutor支持长时间基准测试后台运行
- 状态管理: 内存RwLock存储活跃基准/交易记录

**第3层 - 业务服务层** (hcp-server + hcp-antimanip)
- **hcp-server**: 业务逻辑处理
  - PostgreSQL: 持久化基准结果、交易记录、节点信息
  - Redis: 缓存热数据(基准/指标)
  - 暴露gRPC接口给Gateway调用
  
- **hcp-antimanip**: 反操纵检测
  - 4类检测器: WashTrade/Spoofing/Sandwich/FrontRun
  - 算法: Hawkes过程 + Isolation Forest + LSTM神经网络
  - 实时告警: Slack/Email/DingTalk通知
  - 暴露REST API(Port:8082)给Gateway调用

**第4层 - 共识引擎核心** (hcp-consensus)
- **最核心的计算引擎**,50-200个节点组成分布式网络
- 三种共识算法:
  - **tPBFT** (主算法): 3阶段(PrePrepare→Prepare→Commit)
    - 信任评分: 根据历史消息准确率动态调整
    - 优化: O(N²)通信复杂度降至O(N)
  - **Raft** (对照组): Leader选举 + 日志复制
  - **HotStuff** (对照组): 链式BFT + 视图切换
  
- 关键子模块:
  - **交易池**: 优先级队列 + Gas费排序 + 防洪峰
  - **区块生成**: 时间窗口出块 + 流水线 + 批量打包

**第5层 - 存储与监控基础设施** (hcp-deploy)
- **PostgreSQL** (Port:5432):
  - benchmarks表: 存储基准测试结果(算法/节点数/TPS/延迟)
  - transactions表: 时序表存储交易记录(分区按日期)
  - nodes表: 节点注册信息
  - metrics表: Prometheus指标存储(时序分区表)

- **Redis** (Port:6379):
  - 缓存基准结果(TTL:24h)
  - 缓存最近1000条交易
  - Session管理

- **Prometheus** (Port:9090):
  - 15s采集粒度
  - 指标来源: 每个共识节点(9091)推送
  - 支持查询API: /api/v1/query

- **Grafana** (Port:3001):
  - 连接Prometheus作为数据源
  - 预置仪表盘: 共识性能/节点资源/网络拓扑/基准对比
  - 嵌入UI显示或独立访问

- **Docker Compose编排**:
  - 50个consensus-node-*容器 (可扩至200)
  - gateway/server/ui/prometheus/grafana/postgres/redis各1个
  - 一键启动: `docker-compose up`
  - 一键部署: Makefile + shell脚本

### **模块间通信关系**

```
用户 ↔ hcp-ui (REST/HTTP) ↔ hcp-gateway (REST 8080)
                              ↓ gRPC
                    ├─→ hcp-consensus (9090)
                    ├─→ hcp-server (8081)
                    └─→ hcp-antimanip (8082)
                              ↓
    ┌─────────────────────────┼─────────────────┐
    ↓                         ↓                 ↓
PostgreSQL              Prometheus         RocksDB/LevelDB
(数据持久化)           (时序指标)          (区块链状态)
    ↓
Grafana (可视化)
```

### **数据流生命周期**

```
1. 用户在UI点击"启动基准测试"
   ↓
2. hcp-ui POST请求到hcp-gateway:8080/consensus/benchmark/start
   参数: {algorithm: "tPBFT", node_count: 50, tps: 5000, duration: 600s}
   ↓
3. hcp-gateway 通过gRPC调用 hcp-consensus:9090/StartBenchmark
   ↓
4. hcp-consensus内部:
   - 启动50个节点开始共识
   - 收到交易 → 验证签名 → 加入TxPool
   - Leade/Primary选择 → 打包交易成Block
   - 3阶段共识 → 执行交易 → 更新RocksDB状态
   - 采集指标: TPS/延迟/CPU/内存
   ↓
5. 每15秒,共识节点推送指标到 Prometheus:9090
   ↓
6. hcp-ui 定时查询 Prometheus API 获取最新指标
   ↓
7. ECharts/D3.js渲染实时曲线
   ↓
8. 基准完成后,hcp-server 将结果存入PostgreSQL
   ↓
9. hcp-ui 展示最终报告: TPS/P99延迟/资源使用 等对比
```

### **性能指标关键点**

| 维度 | 实现方式 | 关键模块 |
|-----|--------|---------|
| **TPS实时监测** | 每个共识节点计算Block中交易数/出块时间 → Prometheus | hcp-consensus |
| **P99/P999延迟** | 收集每笔交易的提交→确认时间 → 直方图 | hcp-consensus + Prometheus |
| **节点资源** | Go runtime metrics (CPU/内存/goroutines) | hcp-consensus |
| **网络延迟** | P2P消息往返时间 | hcp-consensus |
| **存储性能** | 读写延迟<10ms测试 | hcp-consensus (RocksDB benchmark) |
| **API响应** | Gateway HTTP调用耗时 | hcp-gateway (Rust Axum) |

### **三个核心差异点**

1. **通信深度**:
   - UI ↔ Gateway: 轻量级REST JSON
   - Gateway ↔ Backend: 高效gRPC Protocol Buffer
   - Consensus ↔ Consensus: 自定义P2P消息 (共识协议)

2. **时间尺度**:
   - UI刷新: 1-5秒 (用户可见刷新频率)
   - 指标采集: 15秒 (Prometheus scrape interval)
   - 共识轮次: 毫秒级 (PrePrepare→Prepare→Commit)
   - 交易执行: 微秒级 (状态机执行)

3. **数据量级**:
   - 单次API请求: 几KB JSON
   - 共识消息: 几十字节到几MB (Block包含交易)
   - 时序数据: 每节点每秒1-10条指标 × 200节点 = 200-2000指标/s

***

现在你有了:
1. ✅ **系统架构总体图** (数据流向)
2. ✅ **七个模块详细说明** (1700行文档)
3. ✅ **模块间通信关系** (协议/Port/数据类型)
4. ✅ **技术路线对应** (每个模块的核心技术)

这份文档涵盖了系统的**架构、通信、数据流、性能指标、部署方式**等所有关键方面。可以用于论文、设计文档或答辩演讲! 📚