# 第四章架构图 Mermaid 参考稿

本目录只存放论文第四章架构图的 Mermaid 源稿，用于后续手工重画参考；不参与实验运行，也不修改现有代码。

本版按当前论文正文口径重新整理，关键词统一为：

- 平台名称：`HCAP-Bench`
- 三个子系统：`HCAP-Consensus`、`HCAP-Loadgen`、`HCAP-Lab`
- 方法名称：`PB-PEFCA`
- 两类共识执行路径：`轻量共识算法模块路径` 与 `官方 CometBFT 对照路径`
- 轻量算法集合：`PBFT`、`HotStuff`、`Raft`、`CometBFT-light`、`tPBFT`、`分层 tPBFT`
- 负载提交协议：`HTTP`、`gRPC`、`QUIC`
- 核心指标：`TPS`、`P50`、`P95`、`P99`、`成功率`、`消息数`、`字节数`、`吞吐量饱和边界`、`尾延迟退化`、`扩展性退化率`

建议图号对应：

- 图 4-1：HCAP-Bench 总体架构
- 图 4-2：端到端实验数据流
- 图 4-3：HCAP-Consensus 共识引擎子系统
- 图 4-4：官方 CometBFT 与 CometBFT-light 执行路径差异
- 图 4-5：HCAP-Loadgen 高并发负载生成子系统
- 图 4-6：HCAP-Lab 实验编排与 PB-PEFCA 分析子系统
- 图 4-7：HCAP-Bench 数据分层流转
- 图 4-8：区块链执行数据存储
- 图 4-9：系统实验数据存储
- 补充图：QUIC 并发提交路径细化图，可并入图 4-5

## 图 4-1 HCAP-Bench 总体架构

```mermaid
flowchart LR
  User["实验研究者<br/>配置实验矩阵<br/>读取论文结果"]

  subgraph HCAP["HCAP-Bench<br/>高并发交易负载下共识算法性能基准测试平台"]
    subgraph Lab["HCAP-Lab<br/>实验编排与分析子系统"]
      L1["实验矩阵配置<br/>算法、节点规模、交易数量、负载模式、重复次数"]
      L2["实验生命周期管理<br/>初始化、启动、监控、清理"]
      L3["指标聚合与模型分析<br/>均值、标准差、ANOVA、拟合"]
      L4["PB-PEFCA 输出<br/>T_sat、L_tail、R_deg、综合评分"]
    end

    subgraph Loadgen["HCAP-Loadgen<br/>高并发负载生成子系统"]
      G1["交易构建器 TxBuilder<br/>SDK交易字节、账户、nonce、payload、timestamp"]
      G2["账户池 AccountPool<br/>并发安全账户选择、nonce管理、余额状态"]
      G3["调度器 Scheduler<br/>Fixed、Burst、Sustained、Jitter、Zipf偏斜"]
      G4["广播器 Broadcaster<br/>HTTP、gRPC、QUIC"]
      G5["负载侧观测<br/>发送时间、响应时间、成功/拒绝、资源占用"]
      G6["负载侧持久化<br/>PostgreSQL schema、CSV、JSON输出"]
    end

    subgraph Consensus["HCAP-Consensus<br/>共识引擎子系统"]
      C1["轻量共识算法模块路径<br/>统一engine入口、统一提交接口、统一指标口径"]
      C2["本地多节点引擎集群<br/>Cluster、Node、模拟网络"]
      C3["共识算法模块<br/>PBFT、HotStuff、Raft、CometBFT-light、tPBFT、分层tPBFT"]
      C4["SDK执行适配层<br/>共识提交后执行交易并更新应用状态"]
      C5["官方CometBFT对照路径<br/>Cosmos SDK + CometBFT多进程节点"]
      C6["共识侧观测<br/>提交数量、提交窗口、消息数、字节数、区块高度"]
    end

    subgraph Data["数据与结果层"]
      D1["区块链数据<br/>交易、区块、应用状态、验证者集合、提交结果"]
      D2["系统实验数据<br/>配置、日志、样本、聚合指标、异常记录"]
      D3["论文分析数据<br/>表格、图表、边界模型、结论支撑"]
    end
  end

  User --> L1
  L1 --> L2
  L2 --> C1
  L2 --> C5
  L2 --> G1
  G1 --> G2 --> G3 --> G4
  G4 -- "交易注入<br/>HTTP/gRPC/QUIC" --> C1
  G4 -- "官方节点RPC或gRPC" --> C5
  C1 --> C2 --> C3 --> C4
  C5 --> C6
  C4 --> C6
  C6 --> D1
  G5 --> D2
  G6 --> D2
  D1 --> L3
  D2 --> L3
  L3 --> L4 --> D3
  D3 --> User

  classDef lab fill:#f9f0ff,stroke:#722ed1,color:#262626;
  classDef load fill:#f6ffed,stroke:#389e0d,color:#262626;
  classDef con fill:#e6f4ff,stroke:#1677ff,color:#262626;
  classDef data fill:#fff7e6,stroke:#d48806,color:#262626;
  classDef user fill:#fff1f0,stroke:#cf1322,color:#262626;
  class User user;
  class L1,L2,L3,L4 lab;
  class G1,G2,G3,G4,G5,G6 load;
  class C1,C2,C3,C4,C5,C6 con;
  class D1,D2,D3 data;
```

## 图 4-2 端到端实验数据流

```mermaid
flowchart TB
  A["HCAP-Lab读取实验矩阵<br/>engine、nodes、txs、mode、groups、repeat、protocol"] --> B["准备运行环境<br/>二进制、端口、节点目录、账户文件、数据库schema"]
  B --> C{"选择执行路径"}

  C -- "轻量共识算法模块路径" --> D["启动 hcap-bench serve<br/>HTTP /tx、/status<br/>同时启动QUIC监听"]
  C -- "官方CometBFT对照路径" --> E["启动官方CometBFT + Cosmos SDK节点<br/>多进程节点、RPC/gRPC入口"]

  D --> F["等待共识入口可用<br/>health/status/端口检查"]
  E --> F

  F --> G["启动 HCAP-Loadgen<br/>按协议和负载模式注入交易"]

  subgraph LoadSide["负载生成侧"]
    G1["账户选择<br/>RoundRobin / Zipf / Hotspot"]
    G2["SDK交易字节构造<br/>发送方、接收方、nonce、payload、timestamp"]
    G3["异步并发调度<br/>concurrency、worker_threads、channel_capacity"]
    G4["协议广播<br/>HTTP POST、gRPC BroadcastTx、QUIC双向流"]
    G5["响应记录<br/>sent、success、reject、latency"]
  end

  G --> G1 --> G2 --> G3 --> G4 --> G5
  G4 -- "交易请求" --> H["共识交易入口"]

  subgraph ConsensusSide["共识执行侧"]
    H1["交易缓存<br/>txpool / mempool"]
    H2["区块打包<br/>leader/proposer"]
    H3["共识排序<br/>投票、日志复制、分层汇聚"]
    H4["提交确认<br/>达到算法确认条件"]
    H5["SDK执行适配<br/>更新账户状态、应用状态、提交结果"]
  end

  H --> H1 --> H2 --> H3 --> H4 --> H5
  H5 -- "确认结果" --> G5

  G5 --> I["负载侧周期JSON<br/>TPS、成功率、P50/P95/P99、CPU、内存"]
  H5 --> J["共识侧状态<br/>committed、height、messages、bytes、window"]
  G5 --> K["PostgreSQL / CSV<br/>原始样本与交易记录"]
  I --> L["HCAP-Lab结果解析"]
  J --> L
  K --> L
  L --> M["聚合统计<br/>均值、标准差、异常值检查"]
  M --> N["PB-PEFCA分析<br/>吞吐量饱和边界、尾延迟、退化率"]
  N --> O["论文结果<br/>表格、图表、结论"]

  classDef prep fill:#fff7e6,stroke:#d48806;
  classDef load fill:#f6ffed,stroke:#389e0d;
  classDef con fill:#e6f4ff,stroke:#1677ff;
  classDef ana fill:#f9f0ff,stroke:#722ed1;
  class A,B,C,D,E,F prep;
  class G,G1,G2,G3,G4,G5 load;
  class H,H1,H2,H3,H4,H5,J con;
  class I,K,L,M,N,O ana;
```

## 图 4-3 HCAP-Consensus 共识引擎子系统

```mermaid
flowchart LR
  Entry["统一交易入口<br/>HTTP /tx 或 QUIC stream<br/>benchmark内部SubmitTx"] --> Submit["SubmitTx<br/>记录提交时间、客户端ID、交易序号"]

  Submit --> Factory["Engine Factory<br/>按engine名称创建算法模块"]

  subgraph Engines["轻量共识算法模块"]
    PBFT["PBFT<br/>PrePrepare -> Prepare -> Commit"]
    TPBFT["tPBFT<br/>信任评分 -> 验证者筛选 -> BFT确认"]
    HotStuff["HotStuff<br/>Proposal -> Vote -> QC -> Commit"]
    Raft["Raft<br/>Leader日志复制 -> 多数派确认"]
    CLight["CometBFT-light<br/>Proposal -> Prevote -> Precommit -> Commit"]
    Hier["分层tPBFT<br/>组内共识 -> 全局汇聚"]
  end

  Factory --> PBFT
  Factory --> TPBFT
  Factory --> HotStuff
  Factory --> Raft
  Factory --> CLight
  Factory --> Hier

  subgraph Runtime["统一运行时"]
    Cluster["Cluster<br/>创建N个本地节点"]
    Node["Node<br/>节点ID、角色、算法实例、局部状态"]
    Net["模拟网络<br/>广播、点对点投递、延迟、消息统计"]
    Pool["交易池<br/>待排序交易、提交队列"]
    Commit["提交路径<br/>确认交易、提交高度、提交窗口"]
  end

  PBFT --> Cluster
  TPBFT --> Cluster
  HotStuff --> Cluster
  Raft --> Cluster
  CLight --> Cluster
  Hier --> Cluster

  Cluster --> Node
  Node <--> Net
  Node --> Pool --> Commit
  Commit --> Exec["SDK执行适配层<br/>交易执行、状态更新、执行结果"]
  Exec --> ChainData["区块链执行数据<br/>区块、应用状态、提交结果"]

  Net --> Metrics["共识指标采集<br/>消息数、字节数、提交数量、延迟分位"]
  Commit --> Metrics
  Metrics --> Status["状态查询 /status<br/>benchmark_tps、sample_status、network"]
  ChainData --> Status

  classDef entry fill:#fff7e6,stroke:#d48806;
  classDef engine fill:#fff1f0,stroke:#cf1322;
  classDef runtime fill:#e6f4ff,stroke:#1677ff;
  classDef output fill:#f6ffed,stroke:#389e0d;
  class Entry,Submit,Factory entry;
  class PBFT,TPBFT,HotStuff,Raft,CLight,Hier engine;
  class Cluster,Node,Net,Pool,Commit runtime;
  class Exec,ChainData,Metrics,Status output;
```

## 图 4-4 官方 CometBFT 与 CometBFT-light 执行路径差异

```mermaid
flowchart TB
  A["实验配置<br/>engine名称、节点规模、交易数、协议"] --> B{"执行路径判定"}

  B -- "官方 CometBFT" --> O1["官方CometBFT对照路径"]
  B -- "CometBFT-light" --> L1["轻量共识算法模块路径"]
  B -- "PBFT / HotStuff / Raft / tPBFT / 分层tPBFT" --> L1

  subgraph Official["官方 CometBFT 对照路径"]
    O1 --> O2["Cosmos SDK应用"]
    O2 --> O3["官方CometBFT多进程节点"]
    O3 --> O4["真实P2P、ABCI、mempool、区块提交链路"]
    O4 --> O5["作为工程化基线<br/>不直接参与轻量模块公平排序"]
  end

  subgraph Light["轻量共识算法模块路径"]
    L1 --> L2["hcap-bench serve / benchmark"]
    L2 --> L3["统一engine factory"]
    L3 --> L4["统一本地多节点模拟网络"]
    L4 --> L5["CometBFT-light或其他轻量算法"]
    L5 --> L6["统一SubmitTx、统一指标采集、统一SDK执行适配"]
  end

  O5 --> C["实验结果解释"]
  L6 --> C

  C --> C1["官方CometBFT<br/>反映完整工程链路开销"]
  C --> C2["CometBFT-light<br/>反映Tendermint类多轮投票机制在统一engine中的开销"]
  C --> C3["其他轻量算法<br/>用于横向比较算法机制差异"]

  classDef decide fill:#fff7e6,stroke:#d48806;
  classDef off fill:#f9f0ff,stroke:#722ed1;
  classDef light fill:#e6f4ff,stroke:#1677ff;
  classDef explain fill:#f6ffed,stroke:#389e0d;
  class A,B decide;
  class O1,O2,O3,O4,O5 off;
  class L1,L2,L3,L4,L5,L6 light;
  class C,C1,C2,C3 explain;
```

## 图 4-5 HCAP-Loadgen 高并发负载生成子系统

```mermaid
flowchart LR
  CLI["命令行 / 配置文件 / 环境变量"] --> Config["Config合并<br/>protocol、endpoint、mode、target_tps、total_txs、concurrency"]

  subgraph TxBuild["交易构造层"]
    Account["AccountPool<br/>账户数量、账户选择、nonce策略、余额"]
    Signer["Signer<br/>Ed25519 / Secp256k1、签名缓存、并行签名"]
    Builder["TxBuilder<br/>Transfer / Stake / ContractCall<br/>Proto / JSON、payload、memo"]
  end

  subgraph Schedule["负载调度层"]
    Fixed["Fixed<br/>固定速率"]
    Burst["Burst<br/>周期性突发"]
    Sustained["Sustained<br/>持续高负载"]
    Jitter["Jitter<br/>随机抖动"]
    Zipf["Zipf偏斜<br/>模拟热点账户或热点交易"]
  end

  subgraph Concurrency["异步并发执行层"]
    Runtime["Tokio Runtime<br/>async_runtime_threads"]
    Queue["发送队列<br/>channel_capacity、worker_buffer_capacity"]
    Workers["Worker池<br/>worker_threads、concurrency"]
    Backpressure["反压控制<br/>backpressure_threshold"]
  end

  subgraph Broadcast["协议广播层"]
    HTTP["HTTP Broadcaster<br/>POST /tx、连接池复用"]
    GRPC["gRPC Broadcaster<br/>Cosmos BroadcastTx<br/>Async / Sync / Block"]
    QUIC["QUIC Broadcaster<br/>quinn双向流、hcap-quic ALPN、OK/ERR响应"]
  end

  subgraph Observe["观测与持久化层"]
    Metrics["Metrics Aggregator<br/>sent、success、reject、actual_tps、P50/P95/P99"]
    DB["PostgreSQL Writer<br/>schema隔离、交易记录、账户状态"]
    CSV["CSV Writer<br/>压测明细"]
    JSON["JSON Reporter<br/>json_interval_ms周期输出"]
    Prom["Prometheus Exporter<br/>可选监控端口"]
  end

  Config --> Account
  Config --> Fixed
  Config --> Burst
  Config --> Sustained
  Config --> Jitter
  Config --> Zipf
  Account --> Builder
  Signer --> Builder
  Builder --> Queue
  Fixed --> Queue
  Burst --> Queue
  Sustained --> Queue
  Jitter --> Queue
  Zipf --> Queue
  Runtime --> Workers
  Queue --> Workers
  Backpressure <--> Queue
  Workers --> HTTP
  Workers --> GRPC
  Workers --> QUIC
  HTTP --> Target["共识入口<br/>HCAP-Consensus或官方节点"]
  GRPC --> Target
  QUIC --> Target
  Target --> Metrics
  Metrics --> DB
  Metrics --> CSV
  Metrics --> JSON
  Metrics --> Prom

  classDef cfg fill:#fff7e6,stroke:#d48806;
  classDef tx fill:#f6ffed,stroke:#389e0d;
  classDef sch fill:#e6f4ff,stroke:#1677ff;
  classDef br fill:#fff1f0,stroke:#cf1322;
  classDef obs fill:#f9f0ff,stroke:#722ed1;
  class CLI,Config cfg;
  class Account,Signer,Builder tx;
  class Fixed,Burst,Sustained,Jitter,Zipf,Runtime,Queue,Workers,Backpressure sch;
  class HTTP,GRPC,QUIC,Target br;
  class Metrics,DB,CSV,JSON,Prom obs;
```

## 图 4-6 HCAP-Lab 实验编排与 PB-PEFCA 分析子系统

```mermaid
flowchart TB
  Entry["实验入口<br/>run_all_experiments / run_exp*.py / common_engine_runner"] --> Matrix["实验矩阵<br/>算法、节点规模、交易数量、负载模式、协议、重复次数"]
  Matrix --> Prepare["环境准备<br/>构建二进制、分配端口、准备账户文件、创建输出目录"]
  Prepare --> Loop["按实验点顺序执行"]

  Loop --> Path{"运行路径"}
  Path -- "轻量共识算法模块" --> StartBench["启动 hcap-bench<br/>serve模式、HTTP与QUIC监听、/status"]
  Path -- "官方CometBFT" --> StartComet["启动官方CometBFT/Cosmos SDK<br/>多进程节点、RPC/gRPC入口"]

  StartBench --> Health["健康检查<br/>端口、/health、/status、进程状态"]
  StartComet --> Health
  Health --> Load["启动 HCAP-Loadgen<br/>protocol=http/grpc/quic、固定交易数或目标TPS"]
  Load --> Collect["采集运行状态<br/>loadgen JSON、CSV、数据库、节点日志、共识状态"]
  Collect --> Stop["停止进程并清理资源"]
  Stop --> Parse["指标解析<br/>TPS、成功率、P50、P95、P99、消息数、字节数"]
  Parse --> Check["一致性检查<br/>缺失值、异常值、未完成状态、重复轮次"]
  Check --> Persist["结果归档<br/>summary.json、table.md、csv、log"]
  Persist --> More{"还有实验点?"}
  More -- "是" --> Loop
  More -- "否" --> Analyze["统计分析与建模"]

  subgraph PEFCA["PB-PEFCA分析"]
    A1["吞吐量饱和边界<br/>T_sat(A,N)"]
    A2["尾延迟上限<br/>L_tail(A,N,lambda)"]
    A3["扩展性退化率<br/>R_deg(A,N)"]
    A4["综合评分<br/>不同算法与优化组件比较"]
  end

  Analyze --> A1
  Analyze --> A2
  Analyze --> A3
  A1 --> A4
  A2 --> A4
  A3 --> A4
  A4 --> Paper["论文实验材料<br/>基准对比、参数扫描、消融实验、边界建模"]

  Health -- "失败" --> Fail["异常记录<br/>端口占用、节点失败、数据库失败、超时"]
  Load -- "异常退出" --> Fail
  Fail --> Stop

  classDef init fill:#fff7e6,stroke:#d48806;
  classDef run fill:#e6f4ff,stroke:#1677ff;
  classDef data fill:#f6ffed,stroke:#389e0d;
  classDef model fill:#f9f0ff,stroke:#722ed1;
  classDef fail fill:#fff1f0,stroke:#cf1322;
  class Entry,Matrix,Prepare init;
  class Loop,Path,StartBench,StartComet,Health,Load,Stop,More run;
  class Collect,Parse,Check,Persist data;
  class Analyze,A1,A2,A3,A4,Paper model;
  class Fail fail;
```

## 图 4-7 HCAP-Bench 数据分层流转

```mermaid
flowchart TB
  subgraph ConfigLayer["实验配置层"]
    C1["算法配置<br/>PBFT、HotStuff、Raft、CometBFT-light、tPBFT、分层tPBFT、官方CometBFT"]
    C2["负载配置<br/>交易数、目标TPS、负载模式、Zipf参数、协议HTTP/gRPC/QUIC"]
    C3["环境配置<br/>节点规模、组数、端口、数据库URL、随机种子"]
  end

  subgraph RuntimeLayer["运行时数据层"]
    R1["交易请求数据<br/>SDK交易字节、账户、nonce、payload、timestamp"]
    R2["共识过程数据<br/>proposal、vote、commit、append entries、分层汇聚"]
    R3["节点状态数据<br/>height、round、leader、trust score、message stats"]
    R4["应用执行数据<br/>账户状态、KV状态、应用哈希、交易结果"]
  end

  subgraph MeasureLayer["观测指标层"]
    M1["负载侧指标<br/>sent、success、reject、actual_tps"]
    M2["延迟指标<br/>P50、P95、P99、平均延迟"]
    M3["共识开销<br/>消息数、字节数、提交窗口"]
    M4["资源指标<br/>CPU、内存、运行时长"]
  end

  subgraph PersistLayer["持久化层"]
    P1["区块链数据<br/>交易、区块、应用状态、验证者集合、提交结果"]
    P2["系统数据<br/>实验配置、节点日志、原始样本、聚合指标"]
    P3["外部数据库<br/>PostgreSQL schema隔离"]
    P4["文件制品<br/>CSV、JSON、Markdown、log"]
  end

  subgraph AnalysisLayer["论文分析层"]
    A1["基准对比<br/>算法横向比较"]
    A2["参数扫描<br/>节点规模、分组数、负载模式"]
    A3["消融实验<br/>信任评分、分层结构、轻量子层"]
    A4["性能边界建模<br/>T_sat、L_tail、R_deg"]
  end

  C1 --> R2
  C2 --> R1
  C3 --> R3
  R1 --> R2
  R2 --> R3
  R3 --> R4
  R1 --> M1
  R2 --> M3
  R4 --> M2
  R3 --> M4
  R1 --> P1
  R4 --> P1
  M1 --> P2
  M2 --> P2
  M3 --> P2
  M4 --> P2
  P2 --> P3
  P2 --> P4
  P1 --> A1
  P2 --> A1
  P3 --> A2
  P4 --> A3
  A1 --> A4
  A2 --> A4
  A3 --> A4

  classDef cfg fill:#fff7e6,stroke:#d48806;
  classDef run fill:#e6f4ff,stroke:#1677ff;
  classDef met fill:#f6ffed,stroke:#389e0d;
  classDef per fill:#f9f0ff,stroke:#722ed1;
  classDef ana fill:#fff1f0,stroke:#cf1322;
  class C1,C2,C3 cfg;
  class R1,R2,R3,R4 run;
  class M1,M2,M3,M4 met;
  class P1,P2,P3,P4 per;
  class A1,A2,A3,A4 ana;
```

## 图 4-8 区块链执行数据存储

```mermaid
flowchart LR
  subgraph ChainData["区块链执行数据<br/>由HCAP-Consensus维护"]
    TxData["交易数据<br/>SDK交易字节、账户方向、nonce、payload、时间戳、执行结果"]
    BlockData["区块数据<br/>高度、时间戳、交易列表、区块哈希、前一区块哈希"]
    AppState["应用状态<br/>账户余额、KV状态、应用哈希、交易执行状态"]
    Validator["验证者集合<br/>节点编号、角色、组信息、参与状态"]
    Trust["tPBFT信任评分状态<br/>历史成功率、响应时间、稳定性、筛选依据"]
    CommitData["提交结果<br/>提交高度、区块哈希、应用哈希、提交交易数、失败信息"]
  end

  subgraph LightPath["轻量共识算法模块路径"]
    L1["交易进入统一入口"]
    L2["共识模块排序<br/>PBFT/HotStuff/Raft/CometBFT-light/tPBFT/分层tPBFT"]
    L3["SDK执行适配层提交"]
  end

  subgraph OfficialPath["官方CometBFT对照路径"]
    O1["Cosmos SDK交易入口"]
    O2["官方CometBFT节点排序"]
    O3["ABCI状态提交"]
  end

  L1 --> TxData
  L2 --> BlockData
  L2 --> Validator
  L2 --> Trust
  L3 --> AppState
  L3 --> CommitData

  O1 --> TxData
  O2 --> BlockData
  O2 --> Validator
  O3 --> AppState
  O3 --> CommitData

  TxData --> Verify["结果核对<br/>交易是否被提交、是否执行成功"]
  BlockData --> Trace["历史追溯<br/>区块高度、提交顺序、哈希关系"]
  AppState --> Consistency["状态一致性<br/>应用哈希、账户状态"]
  Validator --> Explain["实验解释<br/>节点规模、分层结构、动态筛选"]
  Trust --> Explain
  CommitData --> Metrics["共识侧指标<br/>提交窗口、提交数量、失败原因"]

  classDef data fill:#e6f4ff,stroke:#1677ff;
  classDef light fill:#f6ffed,stroke:#389e0d;
  classDef official fill:#f9f0ff,stroke:#722ed1;
  classDef use fill:#fff7e6,stroke:#d48806;
  class TxData,BlockData,AppState,Validator,Trust,CommitData data;
  class L1,L2,L3 light;
  class O1,O2,O3 official;
  class Verify,Trace,Consistency,Explain,Metrics use;
```

## 图 4-9 系统实验数据存储

```mermaid
erDiagram
  EXPERIMENT_RUN {
    string run_id "实验批次ID"
    string engine "算法或执行路径"
    int nodes "节点规模"
    int groups "分组数量"
    int txs "交易数量"
    string load_mode "Fixed/Burst/Sustained/Jitter"
    string protocol "HTTP/gRPC/QUIC"
    int repeat_index "重复轮次"
    string status "运行状态"
    datetime start_time "开始时间"
    datetime end_time "结束时间"
  }

  LOADGEN_SAMPLE {
    string run_id "实验批次ID"
    float elapsed_s "运行秒数"
    int sent "已发送交易"
    int success "成功交易"
    int reject "拒绝交易"
    float actual_tps "实际TPS"
    float success_rate "成功率"
    float latency_p50_ms "P50延迟"
    float latency_p95_ms "P95延迟"
    float latency_p99_ms "P99延迟"
    float cpu_percent "CPU占用"
    int mem_bytes "内存占用"
  }

  CONSENSUS_STATUS {
    string run_id "实验批次ID"
    int received_txs "接收交易数"
    int accepted_txs "接受交易数"
    int committed_txs "提交交易数"
    float benchmark_tps "共识侧TPS"
    float completion_duration_s "提交完成窗口"
    int message_count "共识消息数"
    int message_bytes "共识消息字节数"
    int height "提交高度"
  }

  TRANSACTION_RECORD {
    string tx_id "交易ID"
    string run_id "实验批次ID"
    string account_from "发送账户"
    string account_to "接收账户"
    int nonce "交易序号"
    int amount "交易数量"
    string encoding "Proto/JSON"
    string result "成功/拒绝/失败"
    float latency_ms "单笔延迟"
    datetime created_at "创建时间"
  }

  ACCOUNT_STATE {
    string account_id "账户ID"
    string schema_name "数据库schema"
    int nonce "当前nonce"
    decimal balance "账户余额"
    datetime updated_at "更新时间"
  }

  ARTIFACT {
    string run_id "实验批次ID"
    string file_path "文件路径"
    string file_type "json/csv/md/log"
    string purpose "用途"
  }

  PB_PEFCA_RESULT {
    string run_id "实验批次ID"
    string algorithm "算法配置A"
    int nodes "节点规模N"
    float lambda_value "负载强度lambda"
    float t_sat "吞吐量饱和边界"
    float l_tail "尾延迟上限"
    float r_deg "扩展性退化率"
    float score "综合评分"
  }

  EXPERIMENT_RUN ||--o{ LOADGEN_SAMPLE : "产生负载样本"
  EXPERIMENT_RUN ||--o{ CONSENSUS_STATUS : "产生共识状态"
  EXPERIMENT_RUN ||--o{ TRANSACTION_RECORD : "包含交易记录"
  EXPERIMENT_RUN ||--o{ ARTIFACT : "生成文件制品"
  EXPERIMENT_RUN ||--o{ PB_PEFCA_RESULT : "进入边界建模"
  ACCOUNT_STATE ||--o{ TRANSACTION_RECORD : "参与交易"
  LOADGEN_SAMPLE }o--|| PB_PEFCA_RESULT : "支撑负载指标"
  CONSENSUS_STATUS }o--|| PB_PEFCA_RESULT : "支撑共识开销"
```

## 补充图 QUIC 并发提交路径细化图

这张图可单独作为补充图，也可把其中的 QUIC 分支压缩进图 4-5。

```mermaid
sequenceDiagram
  participant Lab as HCAP-Lab
  participant Loadgen as HCAP-Loadgen
  participant QB as QuicBroadcaster
  participant Bench as hcap-bench QUIC Listener
  participant Engine as 轻量共识算法模块
  participant Exec as SDK执行适配层
  participant Store as 指标与结果存储

  Lab->>Bench: 启动 hcap-bench serve，同端口监听HTTP与QUIC
  Lab->>Loadgen: --protocol quic --quic-endpoint 127.0.0.1:port
  Loadgen->>QB: 创建QUIC客户端Endpoint
  QB->>Bench: 建立QUIC连接，ALPN=hcap-quic
  loop 每笔交易或并发worker
    Loadgen->>QB: 传入已编码SDK交易字节
    QB->>Bench: 打开双向流并写入payload
    Bench->>Engine: submit(payload, remoteAddr)
    Engine->>Engine: 缓存、排序、投票/复制/分层汇聚
    Engine->>Exec: 共识提交后执行交易
    Exec-->>Engine: 返回执行结果与提交高度
    Engine-->>Bench: 返回txID与sequence
    Bench-->>QB: 写回 OK txID sequence 或 ERR reason
    QB-->>Loadgen: 记录success与latency_ms
  end
  Loadgen->>Store: 写入JSON/CSV/PostgreSQL
  Bench->>Store: /status暴露committed、messages、bytes、benchmark_tps
  Lab->>Store: 汇总TPS、P95、P99、成功率和PB-PEFCA指标
```

## 手工重画提示

如果版面太密，可以这样拆：

- 论文“总体架构设计”：使用图 4-1 和图 4-2。
- 论文“功能模块设计”：使用图 4-3、图 4-4、图 4-5、图 4-6。
- 论文“数据存储设计”：使用图 4-7、图 4-8、图 4-9。
- QUIC 是新增协议能力，建议在图 4-5 中明确画出，也可以额外画成“协议提交路径细化图”。
