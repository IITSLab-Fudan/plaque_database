# 动脉粥样硬化斑块定量证据数据库

版本 v1.1 · 首版检索日期 2026-10-14 · 补充更新 2026-10-15 · 面向研究、数字斑块和后续传感器建模。

本库保存真实可核验的观测/群体统计和来源，不制造多模态患者。原有定量层评估 18 篇原始研究，13 篇贡献 102 条记录：**48 条力学、5 条 pH、1 条 H₂O₂、48 条其他 ROS**。54 条是统计/区域汇总，48 条是作者工作簿中的 ROS 原始观测；不是 102 位患者。人体直接三模态、二模态同样本数据均为 0。

v1.1 将来源表扩展至 **35 项**，补充 **10 个组学数据集登记号**（含父子系列）、**193 条去重样本/文库注释**、3 个 GEO 表达矩阵、2 个 PRM 工作簿及 PXD039077 样本表。组学记录与原有定量层分表保存，不能把这些样本当作已有 pH/H₂O₂/力学读数的患者。具体下载范围、父子系列去重和文献更正见 [补充入库报告](supplement_update_report.md)。

## 从这里开始

- [补充清单核对](supplement_audit.csv)、[数据集目录](dataset_catalog.csv)、[样本注释](dataset_samples.csv)、[文件获取状态](dataset_files.csv)：本轮新增内容。
- [质量控制与研究结论](quality_control_report.md)：回答证据数量、缺失、适用性和下一阶段模拟建议。
- [主数据库](plaque_multimodal_database.csv)：全部字段、缺失值、原始单位、统计形式及逐行 provenance。
- [来源表](sources.csv)：正式评估研究的元数据、访问状态、纳入/延后决定。
- [八类斑块先验约束](plaque_type_priors.csv)：只选人体数字；未确认的分布和参数均为 NA。
- [数据字典](data_dictionary.md)：字段语义与统计口径。
- [SQLite](plaque_database.sqlite)：结构化查询、外键和用于防止误用的筛选视图。
- [检索日志](search_log.csv)与[排除/延后表](excluded_sources.csv)：记录真实覆盖和访问限制。

## 目录

```text
plaque_database/
  01_raw_sources/      原始论文索引 JSON、全文 XML、原始 XLSX、网页及检索快照
  02_extracted_data/   来源决策、逐行提取数据、候选文献、工作簿单元格映射
  03_processed_data/   分层证据、单位规范化主表、文件 SHA-256 清单
  04_scripts/          Python 获取、提取、建库、先验与 QC 脚本
  05_reports/          研究报告和机器可读检查结果
```

根目录 CSV 是主交付版本；`03_processed_data/plaque_multimodal_database.csv` 是同内容的工作流副本。各筛选 CSV 不应再次追加回主表。

## 使用限制是数据含义的一部分

一行 = 一个原始观测或一个特定条件下的群体统计。多种力学参数仍然只算一种目标模态。record_id 和 specimen_group_id 均不代表真实受试者 ID。

本次 A/B/C 级为 0，D 级 47 条、E 级 55 条。C/D 按任务要求仅用于先验；E 仅用于仿真/域随机化。`ml_eligible` 当前全部为 false。

不按 plaque_type 跨论文拼接真实样本。`plaque_type_priors.csv` 中同一行的力学/pH 可以来自独立研究，**不表示配对或相关性证据**。distribution=NA 表示没有拟合依据；不表示默认服从均匀/正态分布。

纤维帽 ≠ 整块稳定斑块；脂质区 ≠ 自动等于坏死核心；IPH/血栓合并组 ≠ 纯 IPH；疾病血管中膜 ≠ 正常血管。无法映射的 standardized_plaque_type 保留 NA，原始类别不丢失。

ROS 荧光 ≠ H₂O₂。唯一已纳入的 H₂O₂ 来自小鼠组织匀浆汇总，绝不能当成人体细胞外浓度。S011 附加的两种单位表述是作者报告，数据库没有认可其相互换算。

μ、E、相对刚度、失效伸长比、波速和声辐射力位移不能混用。SWE 的等效模量不直接等于磁控导丝接触的局部本构参数。stress/strain 两列当前全部 NA，没有合成实验曲线。

## 离线重建

只需 Python 3.10+ 标准库，无需安装 pandas 等包。运行不需要网络，也不会写入 `01_raw_sources/`。

```powershell
python .\04_scripts\build_database.py
python .\04_scripts\quality_control.py
python .\04_scripts\verify_release.py
python .\04_scripts\verify_supplement.py
```

本机已验证的 Python：

```powershell
& 'C:\Users\Bai Chenyao\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' .\04_scripts\build_database.py
```

也可以从上级目录运行 `python plaque_database/04_scripts/build_database.py`。脚本路径与当前工作目录无关；所有输出定位到脚本所在数据库目录。

`acquire_sources.py` 和 `search_registry.py` 是可选联网步骤，会复用已有原始缓存，使用 exclusive-create 保存新文件并记录 URL、时间和 SHA-256；不会覆盖旧原始文件。更新检索时应使用新版本目录或新缓存文件名。公开平台的排序和可访问性会改变，旧检索快照是本版的复现依据。

`extract_quantitative.py` 使用原始 XML 表格和已核对的原文定位，保存原始统计表达；`normalize_units.py` 只做压力单位的精确缩放；`generate_priors.py` 不拟合未证实的分布；`quality_control.py` 检查关联、数值结构、哈希和科学隔离规则。

## 查询示例

```sql
-- 本版应返回 0 行
SELECT * FROM multimodal_supervised;

-- 真正的人体先验约束；还需按方法、参数、区域分层
SELECT record_id, original_plaque_type, mechanical_parameter,
       mechanical_median, mechanical_mean, mechanical_unit, source_location
FROM human_prior_evidence
WHERE modality = 'mechanical';

-- 只查看特异性 H2O2，不带入其他 ROS
SELECT record_id, species, h2o2_mean, h2o2_sd, h2o2_unit,
       measurement_basis, original_secondary_value, original_secondary_unit
FROM observations WHERE modality = 'H2O2';
```

CSV 为 UTF-8 BOM，缺失值为 NA；SQLite 用 NULL。Python `csv` 读取推荐 `encoding='utf-8-sig'`。将数据交给机器学习框架前，应先使用数据字典和筛选视图，而非对整个宽表直接填补缺失值。

## 核心来源

数据记录均有 source_id、DOI、定位和本地证据哈希。示例原始来源：[Teng 2014](https://doi.org/10.1016/j.actbio.2014.09.001)、[Teng 2015](https://doi.org/10.1016/j.jbiomech.2015.09.037)、[Naghavi 2002](https://doi.org/10.1016/S0021-9150(02)00018-7)、[Song 2026](https://doi.org/10.1038/s41467-026-70463-7)。完整书目见 sources.csv。

本次检索是明确边界的可审计证据收集，未声称穷尽全部平台或完成所有新候选全文审核。原始论文/补充材料版权与许可属于各来源；本库保存来源与许可线索，不改变其原始授权。
