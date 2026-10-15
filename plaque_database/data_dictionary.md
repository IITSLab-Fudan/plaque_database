# 数据字典

CSV 使用 UTF-8 BOM、逗号分隔、NA 缺失；SQLite 缺失是 NULL。零是真实零，不是缺失。Boolean 在 CSV 中为 True/False，在 SQLite 中为 1/0。每行只代表一种指标的一个观测或一组统计，不代表完整患者。

## 主表字段

| 字段 | 类型 | 定义 |
|---|---|---|
| record_id | text / NA | 唯一提取记录 ID；绝不是患者或样本 ID。 |
| source_id | text / NA | 关联 sources.csv 的主键。 |
| source_type | text / NA | 来源载体；当前 journal；supplementary 数据在 extraction_method 标记。 |
| title | text / NA | 文章题名 |
| authors | text / NA | 作者列表 |
| year | text / NA | 期刊出版年份 |
| journal | text / NA | 期刊名 |
| doi | text / NA | DOI |
| url | text / NA | 原始论文索引页面 |
| dataset_url | text / NA | 相关仓库/补充数据地址，不表示所有指标原始数据都公开 |
| species | text / NA | human/mouse/rabbit/pig/other；不可跨种合并。 |
| vascular_bed | text / NA | carotid/coronary/aorta/femoral/other；更具体解剖位置见 sample_location。 |
| sample_type | text / NA | in_vivo/ex_vivo/tissue/cell/animal_model。 |
| n_subjects | number | 该行所对应群组的受试者/动物数；未确认则 NA。 |
| n_samples | number | 该行条带/斑块/标本数；不是测量点数；见 sample_count_basis。 |
| original_plaque_type | text / NA | 原论文分类或区域/处理组名称，保留合并类型。 |
| standardized_plaque_type | text / NA | 八类标准 phenotype；不能可靠映射则 NA。 |
| histology_validation | text / NA | yes/no/NA；yes 的具体验证范围由 histology_scope 限定，可能只是相邻切片或子集。 |
| mechanical_parameter | text / NA | 精确物理量/本构参数；Young 模量、纤维刚度、相对倍数、波速、位移不可混合。 |
| mechanical_value | number | 力学：单项数值（不把群体均值写入此栏） |
| mechanical_unit | text / NA | 力学：单位 |
| mechanical_mean | number | 力学：算术均值 |
| mechanical_sd | number | 力学：原文明确确认的标准差 |
| mechanical_median | number | 力学：中位数 |
| mechanical_iqr | text / NA | 忠实保存 IQR 表达；可能是 [Q1,Q3] 或 IQR 宽度，需看 statistic_type。 |
| stress | text / NA | 原始逐点应力；本次未取得。 |
| strain | text / NA | 原始逐点应变；本次未取得。 |
| measurement_frequency | number | 机械波/加载频率，不能用超声载频替代。 |
| mechanical_method | text / NA | 力学：测量方法 |
| pH_value | text / NA | pH：单项数值（不把群体均值写入此栏） |
| pH_mean | number | pH：算术均值 |
| pH_sd | text / NA | pH：原文明确确认的标准差 |
| pH_range_min | text / NA | pH：最小值/下限，具体含义见统计类型 |
| pH_range_max | text / NA | pH：最大值/上限，具体含义见统计类型 |
| pH_method | text / NA | 局部 pH 实验方法；目前 glass_microelectrode。 |
| pH_location | text / NA | pH：局部位置 |
| h2o2_value | text / NA | H₂O₂：单项数值（不把群体均值写入此栏） |
| h2o2_unit | text / NA | H₂O₂：单位 |
| h2o2_mean | number | H₂O₂：算术均值 |
| h2o2_sd | number | H₂O₂：原文明确确认的标准差 |
| h2o2_range_min | text / NA | H₂O₂：最小值/下限，具体含义见统计类型 |
| h2o2_range_max | text / NA | H₂O₂：最大值/上限，具体含义见统计类型 |
| h2o2_method | text / NA | H₂O₂：测量方法 |
| measurement_basis | text / NA | 组织含量/组织荧光/局部 pH 等；不是统一的细胞外浓度。 |
| ros_other_type | text / NA | 非特异 DHE ROS 荧光；不能填入 H2O2。 |
| ros_other_value | number | 其他 ROS：单项数值（不把群体均值写入此栏） |
| ros_other_unit | text / NA | 其他 ROS：单位 |
| temperature | number | 测试温度，只有原文明示才填。 |
| experimental_condition | text / NA | 实验条件、保存、预处理 |
| sample_location | text / NA | 具体取样/测试部位 |
| data_level | text / NA | A 同样本三模态；B 同样本两模态；C 人体单样本单模态；D 人体群体统计；E 动物/体外。E 优先覆盖动物群体/单项观测。 |
| raw_data_available | text / NA | true/false/partial/request_required/not_located；not_located 不等于作者确认不存在。 |
| raw_data_format | text / NA | 数据文件格式与获取状态 |
| extraction_method | text / NA | original_table/supplementary/repository/digitized_from_figure/text_extracted；本次未数字化图像。 |
| confidence_level | text / NA | 提取和 provenance 可信度 high/medium/low；不是临床证据等级。 |
| notes | text / NA | 重要限制及使用说明 |
| source_location | text / NA | 可查找的表/行/条件/段落或 sheet+cell。 |
| source_quote | text / NA | 可选的短原文片段；本版以 original_value 和精确 locator 为主，避免冗长复制。 |
| original_value | text / NA | 原始数值或统计表达文本，包含原文排版异常。 |
| original_unit | text / NA | 原始单位；不做不成立的量纲换算。 |
| normalized_value | number | 仅等价压力单位缩放后的中心统计值；不能脱离 normalized_statistic 使用。 |
| normalized_unit | text / NA | 归一化单位；当前压力参数仅 kPa。 |
| modality | text / NA | 对应指标的原始报告信息；缺失用 NA。 |
| record_kind | text / NA | group_summary 或 raw_observation；后者也可能没有可链接的生物样本 ID。 |
| subject_id | text / NA | 仅作者提供的可追溯受试者 ID；当前全部 NA。 |
| sample_id | text / NA | 仅作者提供的可跨测定关联的样本 ID；当前全部 NA。 |
| specimen_group_id | text / NA | 提取者标记的群组标识，不能用于真实样本配对。 |
| cohort_group | text / NA | 潜在同一队列的防泄漏分组；并非确认不同论文完全相同。 |
| n_subjects_study | number | 原始研究总队列人数；不一定参与该行统计。 |
| n_observations | number | 该行涉及的测点/原始观测数量；不等于独立样本数。 |
| sample_count_basis | text / NA | 各 n 字段的计数单位 |
| label_scope | text / NA | whole_plaque/component/region/vessel/vessel_region/plaque_unspecified。 |
| tissue_component | text / NA | 组织成分名称；与整块斑块 phenotype 分开。 |
| mapping_rationale | text / NA | 映射/不映射理由。 |
| histology_scope | text / NA | 组织学验证的实际覆盖范围 |
| mechanical_min | number | 力学：最小值/下限，具体含义见统计类型 |
| mechanical_max | number | 力学：最大值/上限，具体含义见统计类型 |
| mechanical_q1 | number | 第一四分位数，非最小值。 |
| mechanical_q3 | number | 第三四分位数，非最大值。 |
| mechanical_iqr_width | number | Q3-Q1 宽度；仅原文报告时填写。 |
| stretch_ratio | number | 条件 lambda=L/L0；不自动改写为 strain。 |
| statistic_type | text / NA | raw_observation、mean_SD、mean_2SD_as_reported、median_Q1_Q3、median_IQR_width、median_range、mean_only、reported_ratio_range 或 author_model_estimate。 |
| reported_dispersion | number | 作者报告的 ± 数值，和中心值分开；有时含义不确定。 |
| dispersion_type | text / NA | SD / 2SD_as_reported / unspecified_plus_minus；缺失不推测。 |
| measurement_error | text / NA | 测量仪器误差；不以人群 SD 代替。 |
| measurement_error_unit | text / NA | 仪器测量误差单位 |
| temperature_unit | text / NA | 温度单位 degC |
| measurement_frequency_unit | text / NA | 频率单位 Hz |
| loading_direction | text / NA | 加载方向 |
| loading_rate_mm_s | number | 位移控制速度，mm/s；不是应变率。 |
| stress_definition | text / NA | 应力定义。 |
| strain_definition | text / NA | 应变/伸长比定义。 |
| uncertainty_notes | text / NA | 排版、误差项、分母等未解决问题。 |
| same_sample_linkage | text / NA | 跨所需模态的关联核验状态；当前 not_available。 |
| ml_eligible | boolean | 当前全部 false；C/D 依用户规则仅供先验，E 仅供模拟。 |
| intended_use | text / NA | prior_only/simulation_only。 |
| access_tier | text / NA | full_text_archived 或 primary_abstract_only。 |
| raw_data_obtained | boolean | 对应记录的原始观测文件是否确实在本地取得。全文统计表不等于原始样本数据。 |
| evidence_file | text / NA | 相对数据库目录的本地证据路径。 |
| evidence_sha256 | text / NA | 对应证据文件的 SHA-256。 |
| original_secondary_value | number | 同一观测的另一种作者原始表示；不是第二个独立样本。 |
| original_secondary_unit | text / NA | 另一表示的单位；未必经过本库验证可换算。 |
| h2o2_location | text / NA | H₂O₂：局部位置 |
| collection_timepoint | text / NA | 测量或采集时间点 |
| intervention | text / NA | 药物/对照组；未知则 NA。 |
| species_domain | text / NA | human/animal/cell，供数据域筛选。 |
| synthetic_value | text / NA | 预留字段；实验表全部 NA。 |
| normalized_statistic | text / NA | value/mean/median；归一化没有改变统计形式。 |
| normalization_rule | text / NA | 逐行单位转换依据。 |

## sources.csv

每行一个来源；v1.1 共 35 项，含原始论文、参考文献与仓库登记号，不能作为独立队列计数。source_id 主键。mechanical_data/pH_data/H2O2_data 指发现的可用性而非已成功取得全部原始值。decision=include/exclude/deferred 为原有定量处理决定；catalogued_omics/qualitative_support/auxiliary_support/dataset_publication/secondary_reference/review_reference/method_reference 表示补充用途。data_repository 为相关仓库链接，access_status 区分全文和摘要。cohort_group 处理可能重叠。metadata_path/full_text_path 为本地存档路径。其余书目信息来自原始索引元数据。

## plaque_type_priors.csv

每行一种目标 phenotype，共 8 行；数字栏只选人体证据。distribution=NA 表示未拟合，不等于 uniform。human_evidence_count / animal_evidence_count 是按该标准类型可映射的独立来源 ID 数，非受试者数，也不保证队列独立。supporting_source_ids 列所有相关定量来源；selected_record_ids 明示主先验各数值究竟取自哪行。机械单位、方法、伸长条件和分位数在附加栏保留。covariance_available=false，绝不能把同一先验行当作真实多模态样本。

## 检索与排除

search_log.csv 的 screened 是实际审计结果卡/标题数量，不是搜索引擎总命中数；跨查询重复不可相加作为独立文献数。number_included 是该批返回范围中匹配入库研究的去重数。search_candidates.csv 保留 title_only 未精读候选。excluded_sources.csv 的 scope 限定被排除的是整篇研究、某类指标还是重复镜像；deferred 不表示研究无效。

## 分层文件

plaque_prior_evidence.csv 按 phenotype 列出原始约束；component_prior_evidence.csv 保留不能映射的力学组织成分；human_evidence.csv、animal_evidence.csv、ros_other_data.csv 是主表筛选视图的 CSV，不是新增或独立样本。


## v1.1 组学扩展表

| 表 | 主键 | 用途 |
|---|---|---|
| dataset_catalog | dataset_id | source_id 关联 sources；parent_dataset 关联同表父系列 |
| dataset_samples | sample_key | GEO GSM 或 PRIDE命名空间样本键，去重保存文库/标本注释 |
| dataset_membership | membership_id | dataset_id 与 sample_key 外键关联，保留父子系列重复成员关系 |
| dataset_files | file_id | dataset_id+原始 URL 唯一；保存文件获取状态、哈希与矩阵维数 |
| supplement_audit | audit_id | 已有/新增来源逐项核对，与 sources 关联 |
| omics_workbook_cells | cell_id | 原始文件+sheet+cell 唯一，raw_value 为原样字符串，不推定数据类型或生物样本身份 |

repository_sample_count 是仓库文库/样本条目数；identifiable_donor_count 是明确原始患者标签去重数，缺失不猜测。study_n_subjects/study_n_samples 是文献或系列说明中的研究范围；GSE25390x 的 21 是整体研究数，子系列人数由 identifiable_donor_count 与 notes 限定，不可互换。subject_id 是原始标签且只在 cohort_group 内有意义。PRIDE 的 Record ID 原样保存在 characteristics_json，未自动认定为跨项目患者 ID。

original_label 保留原始分组；standardized_plaque_type 仅在 mapping_rationale 支持时映射。PXD039077 的 hard/soft 映射只是作者肉眼分型下的暂定映射，不表示测得力学量或独立组织学验证。symptom_status 不映射为稳定/易损。target_multimodal_eligible 不表示组学自身任务的训练可用性。

processed_data_local 指是否保存表达/蛋白结果文件，不包含仅样本注释。downloaded 精确到文件。bytes 是本地字节数，repository_bytes 是仓库报告；sha256 为本地实算，repository_sha1 为仓库校验值。FTP URL 保留原始仓库地址；实际下载可能使用 HTTPS，同名 .meta.json 保存实际请求地址。feature_rows 与 sample_columns 是本地表达矩阵维数，不是基因或患者的去重数。license 保留仓库许可声明，GEO 未额外核验各来源特定许可。

补充查询基于用户给定 accession/DOI 的直接解析，审计在 supplement_audit.csv 与原始下载 .meta.json；没有追加成虚构的关键词搜索批次。
