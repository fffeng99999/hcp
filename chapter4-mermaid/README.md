# 第四章架构图 Mermaid 参考稿

本目录只存放论文第四章架构图的 Mermaid 源稿，用于后续手工重画参考；不参与任何实验运行，也不修改现有代码。

建议对应关系：

- 图 4-1：HCP-Bench 总体架构
- 图 4-2：单轮实验数据流
- 图 4-3：共识执行子系统
- 图 4-4：引擎选择与执行路径
- 图 4-5：负载生成子系统
- 图 4-6：实验编排子系统
- 图 4-7：数据层次与流向
- 图 4-8：区块链节点本地存储
- 图 4-9：系统实验数据存储

手工绘制时可以把每个 `subgraph` 当成一个模块边界，把箭头文字作为论文图中的流程说明。

## 图 4-1 HCP-Bench 总体架构

```mermaid
flowchart LR
  U["实验使用者 / 论文实验入口"]

  subgraph Lab["实验编排层 hcp-lab"]
    L1["实验脚本<br/>run_exp*.sh / run_*.ps1"]
    L2["公共运行器<br/>common_runner / common_engine_runner"]
    L3["实验矩阵<br/>算法、节点数、交易数、重复次数"]
    L4["结果整理<br/>summary.json / table*.md / csv"]
  end

  subgraph Loadgen["负载生成层 hcp-loadgen"]
    G1["命令行参数解析<br/>protocol、endpoint、mode、total-txs"]
    G2["交易构造<br/>账户选择、交易编码、签名/序列化"]
    G3["并发调度<br/>worker threads、concurrency、backpressure"]
    G4["提交客户端<br/>HTTP / gRPC"]
    G5["指标采集<br/>TPS、成功率、延迟分位数、CPU、内存"]
    G6["负载侧持久化<br/>PostgreSQL schema、CSV"]
  end

  subgraph Bench["共识实验服务层 hcp-consensus / hcp-bench"]
    B1["hcp-bench CLI<br/>benchmark / serve / smoke"]
    B2["HTTP 交易入口<br/>/tx、/status"]
    B3["Engine Factory<br/>按算法名创建共识引擎"]
    B4["Cluster / Node<br/>本地多节点模拟集群"]
    B5["Simulated Network<br/>消息投递、延迟、统计"]
    B6["Executor Adapter<br/>提交后执行交易"]
  end

  subgraph Engines["共识算法层"]
    E1["PBFT<br/>pre-prepare / prepare / commit"]
    E2["tPBFT<br/>信任评分 + 委员会 + BFT确认"]
    E3["HotStuff<br/>QC 链式确认"]
    E4["Raft<br/>Leader 日志复制"]
    E5["CometBFT-light<br/>propose / prevote / precommit"]
    E6["Hierarchical<br/>分组共识 + 全局汇聚"]
    E7["CometBFT 官方版<br/>独立工程基线"]
  end

  subgraph Store["数据与制品层"]
    S1["节点运行目录<br/>node data / logs"]
    S2["实验报告目录<br/>report / summary / markdown"]
    S3["PostgreSQL<br/>loadgendata / public / per-schema"]
    S4["论文图表输入<br/>JSON、CSV、Markdown 表格"]
  end

  U --> L1
  L1 --> L2
  L2 --> L3
  L2 --> B1
  L2 --> G1
  G1 --> G2 --> G3 --> G4
  G4 -- "交易请求" --> B2
  B1 --> B2
  B2 --> B3 --> B4
  B4 --> B5
  B4 --> Engines
  Engines --> B6
  B6 -- "提交结果" --> B2
  B2 -- "响应延迟 / 成功失败" --> G5
  G5 --> G6
  B4 --> S1
  G6 --> S3
  L4 --> S2
  S2 --> S4
  S3 --> S4

  classDef user fill:#fff7e6,stroke:#d48806,color:#262626;
  classDef lab fill:#f9f0ff,stroke:#722ed1,color:#262626;
  classDef load fill:#f6ffed,stroke:#389e0d,color:#262626;
  classDef bench fill:#e6f4ff,stroke:#1677ff,color:#262626;
  classDef engine fill:#fff1f0,stroke:#cf1322,color:#262626;
  classDef store fill:#f5f5f5,stroke:#595959,color:#262626;
  class U user;
  class L1,L2,L3,L4 lab;
  class G1,G2,G3,G4,G5,G6 load;
  class B1,B2,B3,B4,B5,B6 bench;
  class E1,E2,E3,E4,E5,E6,E7 engine;
  class S1,S2,S3,S4 store;
```

## 图 4-2 单轮实验数据流

```mermaid
flowchart TB
  A["读取实验点<br/>engine、nodes、txs、groups、repeat"] --> B["准备运行环境<br/>创建报告目录、选择端口、检查二进制"]
  B --> C{"实验类型"}
  C -- "轻量共识模块版" --> D["启动 hcp-bench serve<br/>监听 /tx 与 /status"]
  C -- "CometSDK 官方版" --> E["启动官方节点进程<br/>使用官方链节点与 RPC 入口"]

  D --> F["等待服务健康<br/>轮询 /status 或端口"]
  E --> F
  F --> G["启动 hcp-loadgen<br/>构造交易并按配置压测"]

  subgraph LoadPath["负载侧数据路径"]
    G1["账户池选择<br/>RoundRobin / Hotspot"]
    G2["交易编码<br/>proto / json"]
    G3["并发 worker<br/>限流、反压、失败重试统计"]
    G4["请求响应记录<br/>sent / success / reject / latency"]
  end

  G --> G1 --> G2 --> G3 --> G4
  G3 -- "HTTP/gRPC 交易提交" --> H["共识交易入口"]

  subgraph ConsensusPath["共识侧数据路径"]
    H1["交易进入节点 txpool"]
    H2["Leader / Proposer 打包"]
    H3["节点间消息广播"]
    H4["达到算法确认条件"]
    H5["提交区块 / 交易结果"]
  end

  H --> H1 --> H2 --> H3 --> H4 --> H5
  H5 -- "响应 loadgen" --> G4

  G4 --> I["周期性输出 JSON 指标<br/>TPS、成功率、延迟分位数、资源占用"]
  G4 --> J["写入 PostgreSQL<br/>schema 隔离实验批次"]
  G4 --> K["写入 CSV<br/>保留单次压测统计"]
  I --> L["实验 runner 汇总"]
  J --> L
  K --> L
  L --> M["生成论文实验材料<br/>summary.json、table.md、图表输入"]

  classDef prep fill:#fff7e6,stroke:#d48806;
  classDef load fill:#f6ffed,stroke:#389e0d;
  classDef consensus fill:#e6f4ff,stroke:#1677ff;
  classDef result fill:#f9f0ff,stroke:#722ed1;
  class A,B,C,D,E,F prep;
  class G,G1,G2,G3,G4 load;
  class H,H1,H2,H3,H4,H5 consensus;
  class I,J,K,L,M result;
```

## 图 4-3 共识执行子系统

```mermaid
flowchart LR
  Client["外部交易请求<br/>loadgen / benchmark 内部压测"] --> API["交易入口层<br/>HTTP handler / benchmark driver"]
  API --> Factory["Engine Factory<br/>CreateEngine(engineName)"]

  Factory --> PBFT["PBFT Engine"]
  Factory --> TPBFT["tPBFT Engine"]
  Factory --> HotStuff["HotStuff Engine"]
  Factory --> Raft["Raft Engine"]
  Factory --> Comet["CometBFT-light Engine"]
  Factory --> Hier["Hierarchical Engine"]

  subgraph Runtime["统一运行时结构"]
    Cluster["Cluster<br/>创建 N 个本地节点"]
    Node["Node<br/>节点 ID、算法实例、本地状态"]
    Net["Simulated Network<br/>广播、点对点消息、延迟、统计"]
    TxPool["Tx Pool<br/>待排序交易队列"]
    Commit["Commit Path<br/>确认后形成提交结果"]
    Metrics["Runtime Metrics<br/>提交数、消息数、字节数、延迟"]
  end

  PBFT --> Cluster
  TPBFT --> Cluster
  HotStuff --> Cluster
  Raft --> Cluster
  Comet --> Cluster
  Hier --> Cluster

  Cluster --> Node
  Node --> TxPool
  Node <--> Net
  TxPool --> Commit
  Net --> Metrics
  Commit --> Exec["Executor Adapter<br/>SimpleExecutor / SDK Executor"]
  Exec --> State["应用状态<br/>账户、交易执行结果、区块高度"]
  Metrics --> Result["实验指标输出<br/>TPS、latency、message overhead"]
  State --> Result

  subgraph AlgoDetail["算法内部阶段示例"]
    P1["PBFT<br/>PrePrepare -> Prepare -> Commit"]
    P2["tPBFT<br/>Trust Score -> Committee -> BFT Vote"]
    P3["HotStuff<br/>Proposal -> Vote -> QC -> Commit"]
    P4["Raft<br/>Leader AppendEntries -> Majority Ack"]
    P5["CometBFT-light<br/>Proposal -> Prevote -> Precommit -> Commit"]
    P6["Hierarchical<br/>Group Consensus -> Global Consensus"]
  end

  PBFT -.-> P1
  TPBFT -.-> P2
  HotStuff -.-> P3
  Raft -.-> P4
  Comet -.-> P5
  Hier -.-> P6

  classDef input fill:#fff7e6,stroke:#d48806;
  classDef engine fill:#fff1f0,stroke:#cf1322;
  classDef runtime fill:#e6f4ff,stroke:#1677ff;
  classDef output fill:#f9f0ff,stroke:#722ed1;
  class Client,API,Factory input;
  class PBFT,TPBFT,HotStuff,Raft,Comet,Hier,P1,P2,P3,P4,P5,P6 engine;
  class Cluster,Node,Net,TxPool,Commit,Metrics runtime;
  class Exec,State,Result output;
```

## 图 4-4 引擎选择与执行路径

```mermaid
flowchart TD
  A["命令行 / 实验脚本传入 engine 名称"] --> B["标准化算法名<br/>pbft、tpbft、hotstuff、raft、cometbft-light、hierarchical"]
  B --> C{"Engine Factory 分派"}

  C -- "pbft" --> E1["NewPBFT()"]
  C -- "tpbft" --> E2["NewTPBFT()"]
  C -- "hotstuff" --> E3["NewHotStuff()"]
  C -- "raft" --> E4["NewRaft()"]
  C -- "cometbft-light / cometbft" --> E5["NewCometBFT()"]
  C -- "hierarchical" --> E6["NewHierarchical(groups)"]

  E1 --> I["Init(nodeID, nodeCount, network, executor)"]
  E2 --> I
  E3 --> I
  E4 --> I
  E5 --> I
  E6 --> H["按 groups 划分局部组<br/>每组内部运行局部共识"]
  H --> I

  I --> R{"运行模式"}
  R -- "benchmark" --> BM["内存内压测<br/>直接 SubmitTx"]
  R -- "serve" --> SV["启动 HTTP 服务<br/>loadgen 通过 /tx 提交"]
  R -- "smoke" --> SM["最小可用性测试<br/>少量交易验证链路"]

  BM --> S["SubmitTx(tx)"]
  SV --> S
  SM --> S

  S --> O{"算法确认条件"}
  O -- "BFT 类" --> O1["满足 2f+1 或多数确认"]
  O -- "Raft 类" --> O2["Leader 日志复制并获多数确认"]
  O -- "层级类" --> O3["组内确认后进入全局确认"]
  O1 --> CMT["Commit"]
  O2 --> CMT
  O3 --> CMT
  CMT --> M["返回实验指标<br/>committed、latency、messages、bytes"]

  classDef start fill:#fff7e6,stroke:#d48806;
  classDef create fill:#fff1f0,stroke:#cf1322;
  classDef run fill:#e6f4ff,stroke:#1677ff;
  classDef finish fill:#f6ffed,stroke:#389e0d;
  class A,B,C start;
  class E1,E2,E3,E4,E5,E6,H,I create;
  class R,BM,SV,SM,S,O,O1,O2,O3 run;
  class CMT,M finish;
```

## 图 4-5 负载生成子系统

```mermaid
flowchart LR
  CLI["hcp-loadgen 命令行参数"] --> Config["Config Builder<br/>协议、端点、交易数、并发、线程、编码、数据库"]

  Config --> Account["Account Manager<br/>账户数量、选择策略、nonce/序号"]
  Config --> TxGen["Transaction Generator<br/>转账参数、payload、proto/json 编码"]
  Config --> Scheduler["Load Scheduler<br/>fixed、burst、duration、target TPS"]
  Config --> DbInit["Database Init<br/>连接 PostgreSQL、创建 schema、初始化表"]

  Account --> TxGen
  TxGen --> Queue["Worker Queue<br/>channel_capacity、worker_buffer_capacity"]
  Scheduler --> Queue

  Queue --> W1["Worker 1"]
  Queue --> W2["Worker 2"]
  Queue --> WN["Worker N"]

  W1 --> Sender["Request Sender<br/>HTTP / gRPC"]
  W2 --> Sender
  WN --> Sender

  Sender -- "POST /tx 或 RPC submit" --> Target["共识服务入口<br/>hcp-bench serve / 官方节点 RPC"]
  Target -- "成功 / 拒绝 / 错误 / 延迟" --> Recorder["Result Recorder"]

  Recorder --> Metrics["Metrics Aggregator<br/>sent、success、reject、actual_tps、latency p50/p95/p99"]
  Recorder --> Csv["CSV Writer<br/>本轮压测明细"]
  Recorder --> DB["PostgreSQL Writer<br/>实验数据、账户、交易、统计"]
  Metrics --> JsonOut["周期性 JSON 输出<br/>供实验脚本读取"]

  subgraph Control["稳定性控制"]
    BP["Backpressure<br/>超过阈值时抑制继续投递"]
    Timeout["Timeout / Error Count<br/>避免卡死"]
    Prom["Prometheus Exporter<br/>可选监控端口"]
  end

  Queue <--> BP
  Sender --> Timeout
  Metrics --> Prom

  classDef cfg fill:#fff7e6,stroke:#d48806;
  classDef gen fill:#f6ffed,stroke:#389e0d;
  classDef work fill:#e6f4ff,stroke:#1677ff;
  classDef data fill:#f9f0ff,stroke:#722ed1;
  classDef ctrl fill:#fff1f0,stroke:#cf1322;
  class CLI,Config cfg;
  class Account,TxGen,Scheduler gen;
  class Queue,W1,W2,WN,Sender,Target work;
  class Recorder,Metrics,Csv,DB,JsonOut,DbInit data;
  class BP,Timeout,Prom ctrl;
```

## 图 4-6 实验编排子系统

```mermaid
flowchart TB
  Entry["实验入口脚本<br/>run_exp1 / run_exp2 / run_exp3 / run_exp4"] --> Env["读取环境变量与默认配置<br/>项目路径、端口、数据库 URL、输出目录"]
  Env --> Build{"二进制是否存在"}
  Build -- "不存在" --> Compile["构建 hcp-bench / hcp-loadgen"]
  Build -- "存在" --> Matrix
  Compile --> Matrix["生成实验矩阵<br/>算法 x 节点数 x 交易规模 x 重复次数"]

  Matrix --> Loop["遍历每个实验点"]
  Loop --> Clean["准备隔离目录<br/>data、logs、report、schema name"]
  Clean --> StartConsensus["启动共识侧<br/>轻量模块 hcp-bench 或官方 CometBFT SDK"]
  StartConsensus --> Health["健康检查<br/>端口、/status、进程状态"]
  Health --> RunLoad["启动负载侧<br/>固定交易数或持续压测"]
  RunLoad --> Collect["采集输出<br/>JSON 行、CSV、日志、退出码"]
  Collect --> Stop["停止进程并清理临时资源"]
  Stop --> Parse["解析指标<br/>TPS、成功率、平均延迟、P95/P99、消息开销"]
  Parse --> Persist["写入实验结果<br/>summary.json、table.md、原始日志"]
  Persist --> Next{"是否还有实验点"}
  Next -- "是" --> Loop
  Next -- "否" --> Report["生成最终报告材料<br/>汇总表、对比图输入、论文结果"]

  Health -- "失败" --> Fail["记录失败原因<br/>端口占用、数据库失败、二进制缺失"]
  RunLoad -- "异常退出" --> Fail
  Fail --> Stop

  classDef init fill:#fff7e6,stroke:#d48806;
  classDef run fill:#e6f4ff,stroke:#1677ff;
  classDef data fill:#f6ffed,stroke:#389e0d;
  classDef fail fill:#fff1f0,stroke:#cf1322;
  class Entry,Env,Build,Compile,Matrix init;
  class Loop,Clean,StartConsensus,Health,RunLoad,Stop,Next run;
  class Collect,Parse,Persist,Report data;
  class Fail fail;
```

## 图 4-7 数据层次与流向

```mermaid
flowchart TB
  subgraph Input["输入层"]
    I1["实验参数<br/>算法、节点数、交易数、并发、数据库 URL"]
    I2["账户参数<br/>账户数量、选择策略、初始余额"]
    I3["共识参数<br/>节点数量、组数、网络延迟模型"]
  end

  subgraph RuntimeData["运行时数据层"]
    R1["交易请求<br/>payload、account、nonce、timestamp"]
    R2["共识消息<br/>proposal、vote、commit、append entries"]
    R3["节点状态<br/>height、round、log index、trust score"]
    R4["应用状态<br/>账户余额、执行结果"]
  end

  subgraph Measurement["观测指标层"]
    M1["负载侧指标<br/>sent、success、reject、actual_tps"]
    M2["延迟指标<br/>avg、p50、p90、p95、p99"]
    M3["资源指标<br/>cpu_percent、mem_bytes"]
    M4["共识开销<br/>messages、bytes、commit_count"]
  end

  subgraph Persist["持久化层"]
    P1["PostgreSQL<br/>按 schema 隔离实验批次"]
    P2["CSV<br/>负载侧统计明细"]
    P3["JSON<br/>周期输出与 summary"]
    P4["日志文件<br/>stdout、stderr、节点日志"]
  end

  subgraph Paper["论文分析层"]
    A1["实验表格<br/>table*.md"]
    A2["对比图<br/>TPS / latency / success rate"]
    A3["结论分析<br/>算法适用场景、瓶颈、退化趋势"]
  end

  I1 --> R1
  I2 --> R1
  I3 --> R2
  R1 --> R2
  R2 --> R3
  R3 --> R4
  R1 --> M1
  R2 --> M4
  R4 --> M1
  M1 --> M2
  M1 --> M3
  M1 --> P1
  M2 --> P2
  M3 --> P3
  M4 --> P3
  R2 --> P4
  P1 --> A1
  P2 --> A2
  P3 --> A1
  P3 --> A2
  P4 --> A3
  A1 --> A3
  A2 --> A3

  classDef input fill:#fff7e6,stroke:#d48806;
  classDef runtime fill:#e6f4ff,stroke:#1677ff;
  classDef metric fill:#f6ffed,stroke:#389e0d;
  classDef persist fill:#f9f0ff,stroke:#722ed1;
  classDef paper fill:#fff1f0,stroke:#cf1322;
  class I1,I2,I3 input;
  class R1,R2,R3,R4 runtime;
  class M1,M2,M3,M4 metric;
  class P1,P2,P3,P4 persist;
  class A1,A2,A3 paper;
```

## 图 4-8 区块链节点本地存储

```mermaid
flowchart LR
  subgraph NodeRoot["节点根目录 node-i"]
    Config["config<br/>节点 ID、端口、共识参数"]
    Logs["logs<br/>启动日志、共识日志、错误日志"]
    Data["data<br/>区块、状态、交易缓存"]
    Meta["metadata<br/>height、round、last_commit"]
  end

  subgraph DataDetail["data 目录逻辑内容"]
    BlockStore["Block Store<br/>区块高度、交易列表、提交时间"]
    StateStore["State Store<br/>应用状态、账户余额、执行结果"]
    WAL["WAL / Message Log<br/>共识消息、投票记录、恢复依据"]
    TxPool["Tx Pool Snapshot<br/>未提交交易、重试交易"]
  end

  subgraph Runtime["运行时读写关系"]
    Engine["Consensus Engine"]
    Executor["Executor"]
    Network["Network Layer"]
  end

  Config --> Engine
  Engine --> BlockStore
  Engine --> WAL
  Engine --> Meta
  Engine <--> TxPool
  Executor --> StateStore
  Network --> Logs
  BlockStore --> Data
  StateStore --> Data
  WAL --> Data
  TxPool --> Data
  Logs --> Debug["故障定位<br/>实验失败、节点异常、消息阻塞"]
  Meta --> Resume["状态观测<br/>确认高度、轮次、提交进度"]

  classDef root fill:#fff7e6,stroke:#d48806;
  classDef data fill:#e6f4ff,stroke:#1677ff;
  classDef run fill:#f6ffed,stroke:#389e0d;
  classDef use fill:#f9f0ff,stroke:#722ed1;
  class Config,Logs,Data,Meta root;
  class BlockStore,StateStore,WAL,TxPool data;
  class Engine,Executor,Network run;
  class Debug,Resume use;
```

## 图 4-9 系统实验数据存储

```mermaid
erDiagram
  EXPERIMENT_RUN {
    string run_id "实验批次 ID"
    string engine "共识算法"
    int nodes "节点数量"
    int txs "交易总量"
    int concurrency "并发数"
    string mode "负载模式"
    datetime start_time "开始时间"
    datetime end_time "结束时间"
    string status "成功或失败"
  }

  LOADGEN_SAMPLE {
    string run_id "所属实验批次"
    float elapsed_s "已运行秒数"
    int sent "已发送交易"
    int success "成功交易"
    int reject "拒绝交易"
    float actual_tps "实际 TPS"
    float success_rate "成功率"
    float latency_avg_ms "平均延迟"
    float latency_p95_ms "P95 延迟"
    float latency_p99_ms "P99 延迟"
    float cpu_percent "CPU 占用"
    int mem_bytes "内存占用"
  }

  ACCOUNT_STATE {
    string schema_name "实验 schema"
    string account_id "账户 ID"
    int nonce "交易序号"
    decimal balance "账户余额"
    datetime updated_at "更新时间"
  }

  TRANSACTION_RECORD {
    string tx_id "交易 ID"
    string run_id "所属实验批次"
    string from_account "发送账户"
    string to_account "接收账户"
    int amount "金额"
    string encoding "交易编码"
    string result "执行结果"
    float latency_ms "单笔延迟"
    datetime created_at "创建时间"
  }

  CONSENSUS_METRIC {
    string run_id "所属实验批次"
    int committed "提交交易数"
    int message_count "消息数量"
    int message_bytes "消息字节数"
    float commit_latency_ms "共识提交延迟"
    int height "提交高度"
  }

  REPORT_ARTIFACT {
    string run_id "所属实验批次"
    string file_path "报告文件路径"
    string file_type "json/csv/md/log"
    string purpose "用途"
  }

  EXPERIMENT_RUN ||--o{ LOADGEN_SAMPLE : "产生周期指标"
  EXPERIMENT_RUN ||--o{ TRANSACTION_RECORD : "包含交易"
  EXPERIMENT_RUN ||--o{ CONSENSUS_METRIC : "包含共识指标"
  EXPERIMENT_RUN ||--o{ REPORT_ARTIFACT : "生成报告制品"
  ACCOUNT_STATE ||--o{ TRANSACTION_RECORD : "参与交易"
  LOADGEN_SAMPLE }o--|| REPORT_ARTIFACT : "汇总进入"
  CONSENSUS_METRIC }o--|| REPORT_ARTIFACT : "汇总进入"
```

## 论文手绘拆分建议

如果图太密，可以拆成两类：

- 第四章系统设计：优先使用图 4-1、4-3、4-4、4-5、4-6。
- 第四章数据设计：优先使用图 4-2、4-7、4-8、4-9。

答辩讲解时可以按“实验脚本发起、loadgen 造交易、共识引擎排序、执行器提交、数据库和报告归档”这一条主线串起来。
