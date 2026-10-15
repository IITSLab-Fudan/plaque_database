# 补充来源核对与入库报告

更新：2026-10-15（Asia/Shanghai），版本 v1.1。

来源总表扩展至 **35 项**。原有 18 项之外新增 10 个数据集登记号、4 篇原始论文及 3 篇参考文献。登记号之间有父子关系，论文与数据集也可来自同一队列，不能将其视为 35 个独立研究。

新增 **193 条去重样本/文库注释**，以及 217 条系列成员关系。193 条注释包含 172 个 GEO GSM 和 21 个 PRIDE 样本，不代表 193 位独立患者；单细胞文库更不是单细胞数量。

## 已有来源

- Naghavi 2002（S003）局部 pH 已有 5 条汇总记录，保留且不重复追加。
- Song 2026（S011）已有 1 条小鼠 H₂O₂ 汇总及 48 条其他 ROS 记录，保留且不重复追加。

## 逐项数据库登记

| 数据集 | 仓库样本/文库条目 | 本地保存范围 | 核对要点 |
|---|---:|---|---|
| [GSE28829](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE28829) | 29 | processed matrix + metadata | 13 early / 16 advanced；阶段不等于稳定/易损。 |
| [GSE43292](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE43292) | 64 | processed matrix + metadata | 32 名患者、64 个配对标本；外观完整对照仍为 Stary I/II。 |
| [GSE163154](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE163154) | 43 | processed matrix + metadata | 16 non-IPH / 27 IPH；non-IPH 不自动等于稳定斑块。 |
| [GSE159677](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE159677) | 6 | metadata only; expression files indexed remotely | 3 名患者的 AC/PA 配对；仅 AC 按研究设计映射为钙化。 |
| [GSE253902](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE253902) | 12 | metadata only; expression files indexed remotely | 为补全关系额外加入：6 名患者、12 个 GEX/ADT 文库；5 人有症状。 |
| [GSE253903](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE253903) | 12 | metadata only; expression files indexed remotely | scRNA 子系列：12 人、6 人有症状；不套用文章总队列 21/13。 |
| [GSE253904](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE253904) | 24 | metadata only; expression files indexed remotely | 总系列：24 个 GSM，18 个可识别供体标签、11 人有症状；不重复计数子系列。 |
| [GSE210152](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE210152) | 6 | metadata only; expression files indexed remotely | 6 个 CD45+ 文库；系列近期更新提供 4 有症状 / 2 无症状。 |
| [PXD031052](https://www.ebi.ac.uk/pride/archive/projects/PXD031052) | 未按仓库样本确认 | PRM result workbook + peptide annotation workbook | 研究总量 120 人 / 219 标本；不把工作簿列当患者数，也不猜测四类蛋白组亚型的临床标签。 |
| [PXD039077](https://www.ebi.ac.uk/pride/archive/projects/PXD039077) | 21 | 21 sample annotations; proteomic intensities remote | 21 人：7 hard / 7 soft / 7 mixed；肉眼分型不等于测得的机械模量。 |

## 下载范围与存储位置

- 三个表达矩阵已完整下载：GSE28829、GSE43292、GSE163154 的 series_matrix.txt.gz。保留原始探针/特征 ID、列名、预处理信息和缺失值；未再次归一化、批次校正或做基因映射。矩阵在 01_raw_sources，并通过 dataset_files 的 local_path 关联至 SQLite。
- PXD031052 已下载 PRM 结果工作簿及蛋白/肽注释工作簿。逐单元格无损导入 omics_workbook_cells（46761 条），保留 sheet、单元格地址及原始字符串。这些是工作簿单元格，不是独立生物观测；再进样、缺失、汇总行和临床标签需另行按实验设计解析。
- PXD039077 已下载 Sample_list.tsv，21 行样本分类、出血、erosion 等原始字段保存在 characteristics_json。该项目蛋白强度和原始质谱文件仍是远程索引。
- 全部 GEO SOFT 元数据、PRIDE 元数据/文件分页响应已保存并计算 SHA-256。单细胞表达矩阵、原始测序及大型质谱文件未整体下载；dataset_files.downloaded 明确区分远程可用与本地取得。仓库列表是本次快照，不保证覆盖其他版本或仓库端遗漏文件。

## 补充文献与去重

| 来源 | 本次处理 |
|---|---|
| S020，10.1038/s41467-019-11983-3 | 全文归档；作为人/鼠斑块酸化成像支持。未把 pHrodo 强度或探针响应阈值转成绝对局部 pH。 |
| S021，PMID 42313484 | 原始摘要归档；确认 O₂•⁻/H₂O₂/磷酸化探针研究。未取得可入主表的绝对斑块 H₂O₂ 数值，保留定量待提取状态。 |
| S022，PII S1522186500000305 | 原始摘要确认 33 个尸体斑块与 ICP-OES 总钙测量。摘要不给总钙浓度；不填游离 Ca²⁺。其密度分组 n=19+13 与总数 33 的差额未解释，备注保留。 |
| S023，PXD039077 对应论文 | 全文归档，用于核验最终研究结果及分型方法；与仓库同队列，不能重复计人。 |
| R004 | PMC11780792 与 DOI 10.1186/s13062-025-00600-7 是同一篇组学再分析，只登记一次。 |
| R005，PMC10165242 | 综述参考来源，不产生新的实测 pH 行。 |
| R006，PMC5446086 | AHA ROS 测量方法参考；全文接口失败，仅声明取得索引和摘要。 |

## 关键更正

1. GSE253904 为父系列，GSE253902/03 为子系列。GSM 使用全局唯一键，系列归属另存 membership；供体标签与队列组共同用于防止训练/测试泄漏。文章摘要的 21 个斑块、13 个有症状不等于当前已登记的 18 个供体、11 个有症状；差额没有补造。
2. PXD039077 仓库旧简介报告 575 个差异蛋白，正式论文报告 714 个；论文还报告 4498 个定量蛋白。原始仓库文本保留，notes 标注不一致，引用最终研究结论时采用论文。
3. 氧化应激相关基因表达、蛋白表达和钙化相关特征没有转换成 H₂O₂、局部 pH、游离 Ca²⁺或力学值。症状状态、病变阶段、出血状态与稳定/易损分型分别保留。

## 对原有训练与先验数据的影响

物理/化学主表仍为 102 条，八类先验表不变。新增数据用于表型、通路与组学研究，未新增真实同样本 pH + H₂O₂ + 力学的 A/B 级训练数据。dataset_samples.target_multimodal_eligible 全为 false；这不否认组学数据可在其原始研究设计下单独用于组学任务。

## 文件与查询

- sources.csv：统一来源总表；supplement_audit.csv：每项已有/新增状态。
- dataset_catalog.csv：数据集级信息；dataset_samples.csv：去重样本；dataset_membership.csv：系列归属；dataset_files.csv：远程与本地文件。
- SQLite 包含同名新表、omics_workbook_cells 和 omics_phenotype_samples 视图。

```sql
SELECT dataset_id, repository_sample_count, local_data_scope FROM dataset_catalog;
SELECT original_label, COUNT(*) FROM omics_phenotype_samples
WHERE dataset_id='PXD039077' GROUP BY original_label;
SELECT dataset_id, local_path FROM dataset_files WHERE downloaded=1;
```

注意：omics_phenotype_samples 会列出每个系列的成员；父子系列同时查询时要按 sample_key 去重。具体供体也可能有多个文库。自动校验详见 05_reports/supplement_verification.json。
