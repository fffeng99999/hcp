# HCP-Lab 开发指南与实验架构

## 📋 文档信息

- **项目名称**: HCP-Lab（高频金融交易区块链共识性能测试系统 - 实验编排层）
- **技术栈**: Python 3 + Bash + HCP-Consensus + HCP-LoadGen
- **开发语言**: Python 3.10+
- **运行依赖**: Linux / iostat / LaTeX（可选）
- **文档版本**: v1.0.0
- **最后更新**: 2026-04-08

---

## 1. 项目概述

**职责定位**: 统一编排实验参数矩阵、批量启动/停止节点、触发负载生成、采集日志与系统指标、导出报告。

**核心能力**:
1. 参数矩阵展开（节点数、交易量、分组规模、重复次数等）
2. 自动调用 `hcp/start_nodes.sh` 启动多节点并等待可用
3. 调用 `hcp-loadgen` 发送交易流量并消费实时指标
4. 解析日志得到确认时延、区块时延、RocksDB相关指标
5. 采集 CPU / 内存 / 网络 / I/O 指标
6. 生成 `result.json`、CSV、SVG、Markdown/PDF 报告

---

## 🏗️ 项目结构

```text
hcp-lab/
├── main.py                            # 通用实验入口（矩阵执行 + 报告导出）
├── controller/                        # 实验控制层
│   ├── experiment_runner.py           # 核心编排器
│   ├── node_manager.py                # 节点生命周期管理
│   ├── param_matrix.py                # 参数矩阵构造/加载
│   └── cpu_affinity.py                # CPU 绑定辅助
├── collector/                         # 指标采集层
│   ├── log_parser.py                  # 日志解析（延迟/RocksDB/异常）
│   ├── system_monitor.py              # CPU/内存/网络/iostat 采样
│   └── metrics_reader.py              # 指标读取辅助
├── analysis/                          # 分析层
│   ├── tps.py                         # TPS 计算
│   ├── latency.py                     # 百分位统计
│   ├── storage_model.py               # 存储模型估算
│   ├── probability.py                 # 概率模型分析
│   ├── svg_chart.py                   # SVG 图表渲染
│   └── common_charts.py               # 通用图表拼装
├── report/                            # 报告导出
│   ├── exporter.py                    # Markdown/PDF 导出
│   └── template.tex                   # LaTeX 模板
└── experiments/                       # 各实验套件
    ├── exp1_tx_nodes/
    ├── exp2_storage_share/
    ├── exp3_parallel_merkle/
    ├── exp4_hierarchical_consensus/
    ├── exp5_hierarchical_tpbft/
    ├── exp6_alpenglow_votor/
    ├── exp7_pow/
    └── exp8_ibft/
```

---

## 📦 核心依赖

项目未维护统一依赖清单文件，当前代码直接使用以下系统与 Python 能力：

- Python 标准库：`argparse`、`subprocess`、`pathlib`、`json`、`csv`、`threading`、`urllib`
- 系统工具：`bash`、`pkill`、`iostat`（`system_monitor.py` 中可选）
- 外部程序：`hcpd`（由 `hcp` 项目构建并启动）、`hcp-loadgen`（Rust 编译产物）
- 文档导出：`xelatex` 或 `pdflatex`（缺失时仍会生成 `report.tex` 和 `report.md`）

---

## ⚙️ 核心模块说明

### 1) `main.py`（通用入口）

支持两种参数输入：
- 直接传 `--nodes` 和 `--tx`（逗号分隔）
- 通过 `--matrix` 读取 JSON 参数矩阵

执行流程：
1. 构建输出目录与实验产物目录（支持 `EXP_ARTIFACT_ROOT` 覆盖）
2. 构建 `ExperimentRunner`
3. 运行矩阵实验并写出 `result.json`
4. 汇总指标并导出 `report.md` + `report.pdf`

### 2) `controller/experiment_runner.py`（编排核心）

关键行为：
1. 对每个实验点读取 `nodes/tx/share_size` 等参数
2. 通过 `NodeManager.start_nodes(...)` 启动共识节点
3. 启动 `SystemMonitor` 采样系统资源
4. 触发 `hcp-loadgen`，并读取 JSON/CSV 快照
5. 聚合日志解析指标与系统指标
6. 统一写入每个点的 `metrics` 字典并停止节点

### 3) `controller/node_manager.py`（节点管理）

- 使用 `start_nodes.sh <num_nodes>` 拉起节点
- 注入环境变量：`DATA_ROOT`、`LOG_DIR`、`USE_CPU_AFFINITY`、`STORAGE_GROUP_SIZE`
- 通过 RPC `/status` 检查区块高度是否推进，确保可用后再压测
- 结束时发送 SIGINT + `pkill -f "hcpd start"` 兜底清理

### 4) `collector/log_parser.py`（日志解析）

已支持：
- 区块时延、确认时延
- RocksDB 写耗时、写放大、L0 文件、压缩耗时、WAL 指标
- 共识失败统计
- 分层共识、分层 tPBFT、IBFT、Votor 的专用解析

### 5) `collector/system_monitor.py`（系统指标）

- CPU：读取 `/proc/stat`
- 内存：读取 `/proc/meminfo`
- 网络：读取 `/proc/net/dev`
- I/O：调用 `iostat -x`（不可用时自动降级为 0）

### 6) `report/exporter.py`（报告导出）

- Markdown：直接写 `report.md`
- PDF：以 `template.tex` 渲染后调用 `xelatex/pdflatex`
- 即使 LaTeX 不可用，仍保留 `report.tex` 供后续离线编译

---

## 🧪 实验目录规范

每个 `experiments/expX_*` 目录一般遵循：

1. `run_*.sh`：设置默认参数并转调测试脚本
2. `test_*.sh`：构建 `hcp-loadgen`，设置环境变量，调用 Python 驱动
3. `run_*.py`：实验主逻辑（repeat / 聚合 / 统计 / 作图）
4. `README.md`：单实验说明（变量、输出、路径约定）
5. `report/`：实验输出目录（`result.json`、CSV、SVG、报告）

---

## 🚀 开发流程

```bash
# 1) 进入项目根目录
cd /home/hcp-dev/hcp-project-experiment

# 2) 构建负载发生器（实验依赖）
cd hcp-loadgen
cargo build --release

# 3) 回到实验项目并执行通用入口
cd ../hcp-lab
python3 main.py --nodes "4,8" --tx "1000" \
  --out "outputs/dev_run" \
  --loadgen-args "--protocol grpc --grpc-endpoint http://127.0.0.1:9090 --total-txs {tx} --target-tps 1000 --csv-path {data_root}/loadgen.csv"

# 4) 执行预置实验（示例：实验1）
bash experiments/exp1_tx_nodes/run_exp1_tx_nodes.sh
```

---

## 📁 输出与产物

典型输出目录结构：

```text
<out>/
├── result.json
├── report.md
├── report.tex
├── report.pdf
└── figures/
    └── *.svg
```

典型中间产物（默认在 `tests/<exp>/`，可由 `EXP_ARTIFACT_ROOT` 覆盖）：

```text
tests/<exp>/
├── data/
│   └── nodes_<n>/...
└── logs/
    └── nodes_<n>/...
```

---

## 🔧 关键环境变量

- `EXP_ARTIFACT_ROOT`: 实验中间数据根目录覆盖
- `PORT_OFFSET`: 多实验并行时端口偏移
- `CHAIN_ID`: 链 ID
- `HCPD_BINARY`: 指定节点二进制路径
- `EXTRA_ACCOUNT_COUNT`: 额外账户数量
- `USE_CPU_AFFINITY`: 是否启用 CPU 亲和性绑定
- `STORAGE_GROUP_SIZE`: 共享存储实验分组大小

---

## ✅ 开发建议

1. 新增实验时优先复用 `ExperimentRunner`，避免重复造轮子
2. 将新指标解析放入 `collector/log_parser.py`，统一口径
3. 输出字段保持 `points[].metrics` 扁平结构，便于后续画图
4. 报告与图表命名保持 `expX_` 前缀，便于多实验并行归档

---

**文档版本**: v1.0.0  
**最后更新**: 2026-04-08  
**维护者**: HCP Team
