"""Offline reproducible build: python 04_scripts/build_database.py. No third-party dependencies."""
import csv,json,re,sqlite3,hashlib,collections,pathlib,difflib,shutil
from prepare_catalog import ROOT,write_csv,catalog
from extract_quantitative import extract,FIELDS
from normalize_units import normalize
from generate_priors import generate
from quality_control import validate
DATE='2026-10-14'
def match_sources(text,sources):
    text=text.lower(); matched=[]
    for s in sources:
        title=re.sub('[^a-z0-9 ]','',s['title'].lower())
        if (s.get('doi') and s['doi'].lower() in text) or (s.get('url') and s['url'].lower() in text) or (title and title in re.sub('[^a-z0-9 ]','',text)): matched.append(s['source_id'])
    return matched
def logs(sources):
    rows=[];candidates=[]
    included={s['source_id'] for s in sources if s['decision']=='include'}
    for archive in sorted((ROOT/'01_raw_sources').glob('web_search_archive*.json')):
        for search in json.loads(archive.read_text(encoding='utf-8'))['searches']:
            val=search['result'].get('value','')
            parts=[] if not isinstance(val,str) or val.startswith('Empty search results') else re.split('-{20,}',val)[:5]
            links=[];matched=set()
            for part in parts:
                first=part.strip().split('\n')[0]
                urls=re.findall(r'https?://[^\s]+',first)
                url=urls[-1].rstrip(')') if urls else None
                title=first[:first.rfind(' (http')] if ' (http' in first else first
                ids=match_sources(part,sources);matched.update(ids)
                candidates.append(dict(search_id=f'Q{len(rows)+1:03d}',title=title,url=url,matched_source_ids=';'.join(ids) or None,screening_stage='first_five_result_cards',disposition='quantitative_included' if set(ids)&included else 'not_selected_or_deferred_in_this_release'))
                if url:links.append(url)
            q=search['q']
            rows.append(dict(search_id=f'Q{len(rows)+1:03d}',search_engine='Web search (domain-filtered where specified)',query=q,date=DATE,number_of_results_screened=len(parts),number_included=len(matched&included),included_source_ids=';'.join(sorted(matched&included)) or None,screened_urls=';'.join(links),archive=str(archive.relative_to(ROOT)).replace('\\','/'),notes='First five returned result cards audited consistently; not the search engine total. Includes repeated studies across queries. Scholar/OSF empty results do not establish absence.'))
    for entry in json.loads((ROOT/'02_extracted_data/index_search_log.json').read_text(encoding='utf-8')):
        j=json.loads((ROOT/entry['archive']).read_text(encoding='utf-8'))
        hits=j['message']['items'] if entry['search_engine']=='Crossref API' else j['resultList']['result']
        matched=set()
        for h in hits:
            title=h.get('title');title=title[0] if isinstance(title,list) else title
            doi=h.get('doi') or h.get('DOI')
            url=h.get('URL') or ('https://pubmed.ncbi.nlm.nih.gov/'+h['id']+'/' if h.get('source')=='MED' else 'https://europepmc.org/article/'+h.get('source','MED')+'/'+h.get('id',''))
            ids=match_sources(str(title)+' '+str(doi)+' '+url,sources);matched.update(ids)
            candidates.append(dict(search_id=f'Q{len(rows)+1:03d}',title=title,url=url,matched_source_ids=';'.join(ids) or None,screening_stage='index_first_page_titles',disposition='quantitative_included' if set(ids)&included else 'title_only_not_fully_assessed'))
        rows.append(dict(entry,search_id=f'Q{len(rows)+1:03d}',number_included=len(matched&included),included_source_ids=';'.join(sorted(matched&included)) or None))
    rows.append(dict(search_id='Q-SEED',search_engine='Web search initial combined batch',query='human carotid plaque mechanical properties fibrous lipid hemorrhage Young modulus Teng 2014 | human atherosclerotic plaque pH lipid rich calcified Naghavi 2002 | atherosclerotic plaque hydrogen peroxide tissue content measurement human',date=DATE,number_of_results_screened=20,number_included=6,included_source_ids='S001;S002;S003;S004;S005;S010',notes='Initial combined discovery batch; per-query attribution unavailable. Primary metadata and evidence subsequently archived. Count refers to combined displayed result cards, not unique studies.'))
    write_csv(ROOT/'search_log.csv',rows)
    write_csv(ROOT/'02_extracted_data/search_candidates.csv',candidates)
    exclusions=json.loads((ROOT/'02_extracted_data/exclusions_manual.json').read_text(encoding='utf-8'))
    for s in sources:
        if s['decision'] in ('exclude','deferred'):exclusions.append(dict(title=s['title'],doi=s['doi'],url=s['url'],source_id=s['source_id'],reason_for_exclusion=s['notes'],scope='all quantitative extraction in this release',decision=s['decision']))
    write_csv(ROOT/'excluded_sources.csv',exclusions)
    return rows,candidates,exclusions
def sql_table(conn,name,rows,columns=None,primary=None,foreign=None):
    columns=columns or list(dict.fromkeys(k for r in rows for k in r))
    def val(v): return None if v is None or v=='NA' else v
    numeric=set('year n_subjects n_samples n_subjects_study n_observations mechanical_value mechanical_mean mechanical_sd mechanical_median mechanical_min mechanical_max mechanical_q1 mechanical_q3 mechanical_iqr_width stretch_ratio pH_value pH_mean pH_sd pH_range_min pH_range_max h2o2_value h2o2_mean h2o2_sd h2o2_range_min h2o2_range_max ros_other_value temperature measurement_frequency reported_dispersion loading_rate_mm_s normalized_value original_secondary_value human_evidence_count animal_evidence_count mechanical_stretch_ratio mechanical_min mechanical_max pH_min pH_max h2o2_min h2o2_max stress strain number_of_results_screened number_included'.split())
    numeric.update('repository_sample_count identifiable_donor_count study_n_subjects study_n_samples bytes repository_bytes feature_rows sample_columns'.split())
    boolean={'ml_eligible','raw_data_obtained','covariance_available','target_multimodal_eligible','clinical_label_available','mechanical_available','pH_available','H2O2_available','processed_data_local','downloaded'}
    def typ(k): return 'REAL' if k in numeric else 'INTEGER' if k in boolean else 'TEXT'
    defs=[f'"{k}" {typ(k)}'+(' PRIMARY KEY' if k==primary else '') for k in columns]
    if foreign:
        for fk in ([foreign] if isinstance(foreign[0],str) else foreign):
            defs.append(f'FOREIGN KEY ("{fk[0]}") REFERENCES "{fk[1]}" ("{fk[2]}")')
    conn.execute(f'CREATE TABLE "{name}" ('+', '.join(defs)+')')
    def coerce(k,v):
        v=val(v)
        if v is None:return None
        if k in numeric:return float(v)
        if k in boolean:return int(v)
        return str(v)
    conn.executemany(f'INSERT INTO "{name}" VALUES ('+','.join('?' for _ in columns)+')',[[coerce(k,r.get(k)) for k in columns] for r in rows])
def report(records,sources,priors,qc,searches,exclusions):
    modal=qc['counts']['modalities']; included=[s for s in sources if s['decision']=='include']
    humans={r['source_id'] for r in records if r['species']=='human'}
    animals={r['source_id'] for r in records if r['species']!='human' and r['sample_type']!='cell'}
    full={s['source_id'] for s in included if s['access_status']=='full_text_archived'}
    md=f'''# 数据质量与研究结果报告

首版检索日期：{DATE}（Asia/Shanghai）。版本：v1.1，补充更新日期 2026-10-15。

本报告下方主要统计原有物理/化学定量证据层；新增组学与参考来源、下载范围和更正见 [补充入库报告](supplement_update_report.md)。新增组学样本不计入下面的 A–E 定量记录。

## 实际交付与计数

原有定量证据层重点评估 18 篇原始研究，{len(included)} 篇提供了入库定量证据；其中 {len(full)} 篇已获取全文 XML，其余 6 篇采用原始论文摘要中的明确数值并降级标注，未把摘要访问写成全文访问。扩展后来源表有 {len(sources)} 项研究、参考文献与数据集；这些不是 {len(sources)} 个独立队列。来源表不是所有检索命中的全集。

纳入研究按实验数据域互斥统计：10 篇人体、2 篇动物、1 篇人体与动物混合。按“包含该域”统计：人体 {len(humans)} 篇、动物 {len(animals)} 篇；两者不可直接相加。细胞定量记录 0 篇（S011 还有细胞实验，但本库没有把它们当成斑块定量证据）。

| 记录类别 | 条数 | 实际含义 |
|---|---:|---|
| 力学 | {modal['mechanical']} | 43 条人体、5 条兔；包含模量、强度、失效伸长比、相对刚度及弹性成像响应，不能混为一种模量 |
| pH | {modal['pH']} | 4 条人体、1 条兔；全部来自 S003 的群体统计 |
| H₂O₂ | {modal['H2O2']} | 1 条小鼠组织匀浆群体统计；人体为 0 |
| 其他 ROS | {modal['ros_other']} | S011 工作簿的真实单项观测；DHE 信号，绝不是 H₂O₂ 浓度 |
| 合计 | {len(records)} | 54 条统计记录 + 48 条 ROS 原始观测；不是 102 位患者 |

数据级别：A=0，B=0，C=0，D=47，E=55。符合目标的真实三模态同样本记录为 0，二模态记录也为 0。公开工作簿中多种成像信号的“multimodal”不等于所需 mechanical+pH+H₂O₂。

## 是否可以直接训练多模态分类器

在本次实际检索、访问和核验的范围内，没有获得可直接训练该三模态人体分类器的公开同样本数据。这个结论不代表证明全球所有数据库均不存在。SQLite 的 multimodal_supervised 视图为 0 行，所有当前记录的 ml_eligible=false。遵守任务规则，C/D 也不作为真实监督训练样本。

## 哪些先验有支撑

八个目标 phenotype 各保留一行。当前可以建立的是**限定方法、组织层级和人群的统计约束**，没有一种类型具备已验证的完整三模态联合分布。

- 稳定/易损斑块：有整块斑块、术前 SWE、术后病理分类的力学统计。主表选 S014 的 mean/SD；S012/S016 和 S013 作为分层证据保留，不混合成一个总体。
- 富脂：S001 分离脂质成分在给定伸长比下的中位数和四分位数；S003 黄色富脂区 pH 均值。两项来自不同研究、不同人，不能据此拟合协方差。
- 钙化：有 S003 局部 pH 均值，以及 S019 钙化帽相对于细胞性帽的刚度倍数；没有本次已核验的绝对钙化模量数值用于主先验。
- 正常/无斑块区域：主表选脐动脉 pH 对照，不能当作成人颈/冠状动脉基线；S016 另有患病人群局部无斑块 ICA/CCA 的力学测量，保存在分层证据中，不跨域混合或配对。
- 纯斑块内出血、坏死核心和混合斑块：主先验保持 NA。IPH/T 合并组和纤维帽组织的数据在 component_prior_evidence.csv，未强制映射。

所有 distribution 字段保留 NA。未把均值±误差构造成范围，未把 Q1/Q3 当作 min/max，未假设正态分布。表内 confidence_level=low 指向整体先验的适用性；单条提取 high 只表示核验清晰，不表示研究本身无偏或可直接用于临床控制。

## 最强和最弱的证据

力学证据最丰富：有原始全文表格、多种组织和伸长条件；但样本条带、患者、重复条件必须区分。局部 pH 的直接测量证据集中于一篇研究，全文未获，误差类型未确认。人体斑块内特异性 H₂O₂ 证据最弱：本次成功入库为 0。小鼠 H₂O₂ 只有一个可核验组织测定均值，不能支持不同 phenotype 的浓度分布。

## 关键 QC 处置

1. S001 表 2 的 XML 单元格有 `533.4.4`、`176.9.0` 两处排版错误，分别用同篇摘要核验为 533.4、176.9；original_value 保留原样，修正记录降为 medium。
2. S012 统计学段明写 mean±2SD：保留 reported_dispersion 与 `2SD_as_reported`，不直接填 mechanical_sd。
3. S003 的 ± 尚不能确定 SD/SEM：pH_sd=NA，误差原值独立保存。人体 48 是整个研究队列，不冒充富脂/钙化子组人数。
4. S016 IQR 是宽度，未虚构上下四分位数；分组来自术者肉眼判断，89/100 有组织学验证；文中 FE 指定模量和计算应力未伪装为实测。ICA/CCA 数值来自作者明确称为无斑块的区域，但受试者并非健康对照。
5. S011 H₂O₂ 原文同时给出 0.34±0.05 mM 和约 0.34 μmol/g wet tissue。保存为同一条记录的主/附加原始表述，未认可缺少组织质量、提取体积信息时的量纲换算；measurement_basis=tissue content。
6. S011 已下载原始 XLSX，但未定位到与上述 n=6 对应的六个 H₂O₂ 原始数值。其 H₂O₂ 行 raw_data_available=false；同一工作簿中的其他 ROS 原始观测分别提取，不凭列顺序假定动物身份或跨实验配对。
7. S001/S002 的 21 例队列及 S012/S014/S016 的 CEA 系列存在重叠可能，用 cohort_group 明示，禁止累加 n 或按论文随机划分训练/测试集。
8. S006 Dryad 的曲线 XLSX、MAT 映射文件公开列出，但下载返回 403。原始仓库可用与本地已经取得是两个字段；没有声称已获得文件。
9. S017/S018 未取得数值全文；综述转述未录入。S018 摘要的 17–25 GPa 是与骨组织性质的比较，不作为本次观测到的斑块 min/max。
10. 48 条力学记录含成像速度/位移与模型推断参数；使用前必须按 mechanical_parameter 分层。失效 stretch ratio 未当作 strain，应力应变列保持 NA。

## 原始曲线与图像数字化

本次没有获得可核验的、带人类组织/患者标识的逐点原始 stress–strain 数据，stress_strain_pairs=0。S001/S002 全文含图，但未对重叠曲线进行不可靠的自动取点，digitized_from_figure=0。由材料模型重新计算的曲线不是实验原始曲线，本库未生成。后续可按来源表向作者索取；本任务没有联系作者或发送任何消息。

## Domain gap

主要差异包括：人体/兔/小鼠；成人颈动脉与脐动脉；整体斑块与局部成分；在体 SWE 与冻存后拉伸/压痕；测试方向、伸长比、频率、预载荷及保存状态；自由边界材料试验与导丝接触；局部微电极读数与组织匀浆；药物处理组与未处理人群。这些差异不能仅靠单位统一解决。

## 下一阶段 synthetic dataset generation

先定义用途和适用域，按患者/来源/组织成分/测量方法分层。保留“真实证据层”和“模拟层”的独立表。若采用 Monte Carlo、LHS 或贝叶斯人口模型，分布族、尾部、相关性和跨域映射应作为显式模型假设；未知 H₂O₂ 分布不能从其他 ROS 或给药浓度补齐。每条模拟数据必须有 synthetic 标志、seed、参数来源 record_id、模型版本和假设版本，不能转存进本实验表。

对导丝前向模型，需要另行标定接触几何、摩擦、速度、组织本构、FBG 灵敏度、温度漂移及化学探头响应。先完成同部位共定位测量和独立实验验证，再讨论安全阈值及闭环控制；本库没有给出可直接用于患者接触力控制的阈值。

## 检索边界与可复现性

共记录 {len(searches)} 个检索批次/查询（包括初始组合批次），正式排除或延后 {len(exclusions)} 项来源/来源片段。网页检索固定审计前五张结果卡；直接 Europe PMC 检索审计前 20 项，Crossref 前 10 项。屏蔽/未访问结果不能算作“该平台没有数据”。Google Scholar 未实现直接站内检索，仅尝试网页站点限定查询并如实记录；GEO、Dryad、Zenodo、Figshare、Mendeley、OSF、PRIDE、ProteomeXchange、BioStudies/ArrayExpress、GitHub 以公开网页索引检索为主，不是每个平台的全库导出。

检索覆盖和全文访问不完备，不是 PRISMA 意义上的穷尽性系统综述。index_search 原始响应及 search_candidates.csv 保留新候选的 title_only 状态，不能把这些未精读候选视为已完成全文排除。脚本离线重建相同数据；重新联网检索的排序与命中数可能变化。联网查询未设置发表日期上限，新增候选只有经过发表日期和全文审查才可入库；现有入库论文年份 1991–2026，S011 发表于 2026-03-11。

## 自动检查

{qc['check_count']} 项断言，失败 {len(qc['failed_checks'])} 项。检查涵盖主外键、来源哈希、数据域/级别、化学指标隔离、统计形式、范围顺序、真实样本关联及人体先验。运行结果详见 qc_results.json。自动通过表示结构与已设科学约束一致，不能替代第二位研究者对原文和方法学的独立复核。
'''
    (ROOT/'05_reports/quality_control_report.md').write_text(md,encoding='utf-8')
    (ROOT/'quality_control_report.md').write_text(md,encoding='utf-8')
def dictionary(records):
    special={
    'record_id':'唯一提取记录 ID；绝不是患者或样本 ID。','source_id':'关联 sources.csv 的主键。','source_type':'来源载体；当前 journal；supplementary 数据在 extraction_method 标记。','species':'human/mouse/rabbit/pig/other；不可跨种合并。','vascular_bed':'carotid/coronary/aorta/femoral/other；更具体解剖位置见 sample_location。','sample_type':'in_vivo/ex_vivo/tissue/cell/animal_model。','n_subjects':'该行所对应群组的受试者/动物数；未确认则 NA。','n_samples':'该行条带/斑块/标本数；不是测量点数；见 sample_count_basis。','n_subjects_study':'原始研究总队列人数；不一定参与该行统计。','n_observations':'该行涉及的测点/原始观测数量；不等于独立样本数。','original_plaque_type':'原论文分类或区域/处理组名称，保留合并类型。','standardized_plaque_type':'八类标准 phenotype；不能可靠映射则 NA。','histology_validation':'yes/no/NA；yes 的具体验证范围由 histology_scope 限定，可能只是相邻切片或子集。','data_level':'A 同样本三模态；B 同样本两模态；C 人体单样本单模态；D 人体群体统计；E 动物/体外。E 优先覆盖动物群体/单项观测。','original_value':'原始数值或统计表达文本，包含原文排版异常。','original_unit':'原始单位；不做不成立的量纲换算。','normalized_value':'仅等价压力单位缩放后的中心统计值；不能脱离 normalized_statistic 使用。','normalized_unit':'归一化单位；当前压力参数仅 kPa。','normalized_statistic':'value/mean/median；归一化没有改变统计形式。','normalization_rule':'逐行单位转换依据。','mechanical_parameter':'精确物理量/本构参数；Young 模量、纤维刚度、相对倍数、波速、位移不可混合。','mechanical_iqr':'忠实保存 IQR 表达；可能是 [Q1,Q3] 或 IQR 宽度，需看 statistic_type。','mechanical_q1':'第一四分位数，非最小值。','mechanical_q3':'第三四分位数，非最大值。','mechanical_iqr_width':'Q3-Q1 宽度；仅原文报告时填写。','stretch_ratio':'条件 lambda=L/L0；不自动改写为 strain。','strain':'原始逐点应变；本次未取得。','stress':'原始逐点应力；本次未取得。','measurement_frequency':'机械波/加载频率，不能用超声载频替代。','pH_method':'局部 pH 实验方法；目前 glass_microelectrode。','measurement_basis':'组织含量/组织荧光/局部 pH 等；不是统一的细胞外浓度。','ros_other_type':'非特异 DHE ROS 荧光；不能填入 H2O2。','reported_dispersion':'作者报告的 ± 数值，和中心值分开；有时含义不确定。','dispersion_type':'SD / 2SD_as_reported / unspecified_plus_minus；缺失不推测。','statistic_type':'raw_observation、mean_SD、mean_2SD_as_reported、median_Q1_Q3、median_IQR_width、median_range、mean_only、reported_ratio_range 或 author_model_estimate。','record_kind':'group_summary 或 raw_observation；后者也可能没有可链接的生物样本 ID。','subject_id':'仅作者提供的可追溯受试者 ID；当前全部 NA。','sample_id':'仅作者提供的可跨测定关联的样本 ID；当前全部 NA。','specimen_group_id':'提取者标记的群组标识，不能用于真实样本配对。','cohort_group':'潜在同一队列的防泄漏分组；并非确认不同论文完全相同。','label_scope':'whole_plaque/component/region/vessel/vessel_region/plaque_unspecified。','tissue_component':'组织成分名称；与整块斑块 phenotype 分开。','mapping_rationale':'映射/不映射理由。','same_sample_linkage':'跨所需模态的关联核验状态；当前 not_available。','ml_eligible':'当前全部 false；C/D 依用户规则仅供先验，E 仅供模拟。','intended_use':'prior_only/simulation_only。','raw_data_available':'true/false/partial/request_required/not_located；not_located 不等于作者确认不存在。','raw_data_obtained':'对应记录的原始观测文件是否确实在本地取得。全文统计表不等于原始样本数据。','extraction_method':'original_table/supplementary/repository/digitized_from_figure/text_extracted；本次未数字化图像。','confidence_level':'提取和 provenance 可信度 high/medium/low；不是临床证据等级。','source_location':'可查找的表/行/条件/段落或 sheet+cell。','source_quote':'可选的短原文片段；本版以 original_value 和精确 locator 为主，避免冗长复制。','evidence_file':'相对数据库目录的本地证据路径。','evidence_sha256':'对应证据文件的 SHA-256。','access_tier':'full_text_archived 或 primary_abstract_only。','original_secondary_value':'同一观测的另一种作者原始表示；不是第二个独立样本。','original_secondary_unit':'另一表示的单位；未必经过本库验证可换算。','synthetic_value':'预留字段；实验表全部 NA。','measurement_error':'测量仪器误差；不以人群 SD 代替。','uncertainty_notes':'排版、误差项、分母等未解决问题。','species_domain':'human/animal/cell，供数据域筛选。','intervention':'药物/对照组；未知则 NA。','temperature':'测试温度，只有原文明示才填。','loading_rate_mm_s':'位移控制速度，mm/s；不是应变率。','strain_definition':'应变/伸长比定义。','stress_definition':'应力定义。'}
    lines=['# 数据字典','','CSV 使用 UTF-8 BOM、逗号分隔、NA 缺失；SQLite 缺失是 NULL。零是真实零，不是缺失。Boolean 在 CSV 中为 True/False，在 SQLite 中为 1/0。每行只代表一种指标的一个观测或一组统计，不代表完整患者。','','## 主表字段','','| 字段 | 类型 | 定义 |','|---|---|---|']
    cols=list(dict.fromkeys(k for r in records for k in r))
    for k in cols:
        vals=[r.get(k) for r in records if r.get(k) is not None]
        typ='boolean' if vals and isinstance(vals[0],bool) else 'number' if vals and isinstance(vals[0],(float,int)) else 'text / NA'
        desc=special.get(k)
        if desc is None:
            suffix=k.rsplit('_',1)[-1]
            prefixes={'mechanical':'力学','pH':'pH','h2o2':'H₂O₂','ros_other':'其他 ROS'}
            prefix=next((v for p,v in prefixes.items() if k.startswith(p+'_')),None)
            meaning={'value':'单项数值（不把群体均值写入此栏）','mean':'算术均值','sd':'原文明确确认的标准差','median':'中位数','min':'最小值/下限，具体含义见统计类型','max':'最大值/上限，具体含义见统计类型','unit':'单位','method':'测量方法','location':'局部位置'}
            desc=(prefix+'：'+meaning[suffix]) if prefix and suffix in meaning else {'title':'文章题名','authors':'作者列表','year':'期刊出版年份','journal':'期刊名','doi':'DOI','url':'原始论文索引页面','dataset_url':'相关仓库/补充数据地址，不表示所有指标原始数据都公开','raw_data_format':'数据文件格式与获取状态','temperature_unit':'温度单位 degC','measurement_frequency_unit':'频率单位 Hz','measurement_error_unit':'仪器测量误差单位','experimental_condition':'实验条件、保存、预处理','sample_location':'具体取样/测试部位','notes':'重要限制及使用说明','histology_scope':'组织学验证的实际覆盖范围','sample_count_basis':'各 n 字段的计数单位','loading_direction':'加载方向','collection_timepoint':'测量或采集时间点'}.get(k,'对应指标的原始报告信息；缺失用 NA。')
        lines.append(f'| {k} | {typ} | {desc} |')
    lines+=['','## sources.csv','','每行一个正式评估的原始研究；18 行。source_id 主键。mechanical_data/pH_data/H2O2_data 指发现的可用性而非已成功取得全部原始值。decision=include/exclude/deferred。data_repository 为相关仓库链接，access_status 区分全文和摘要。cohort_group 处理可能重叠。metadata_path/full_text_path 为本地存档路径。其余书目信息来自原始索引元数据。','','## plaque_type_priors.csv','','每行一种目标 phenotype，共 8 行；数字栏只选人体证据。distribution=NA 表示未拟合，不等于 uniform。human_evidence_count / animal_evidence_count 是按该标准类型可映射的独立来源 ID 数，非受试者数，也不保证队列独立。supporting_source_ids 列所有相关定量来源；selected_record_ids 明示主先验各数值究竟取自哪行。机械单位、方法、伸长条件和分位数在附加栏保留。covariance_available=false，绝不能把同一先验行当作真实多模态样本。','','## 检索与排除','','search_log.csv 的 screened 是实际审计结果卡/标题数量，不是搜索引擎总命中数；跨查询重复不可相加作为独立文献数。number_included 是该批返回范围中匹配入库研究的去重数。search_candidates.csv 保留 title_only 未精读候选。excluded_sources.csv 的 scope 限定被排除的是整篇研究、某类指标还是重复镜像；deferred 不表示研究无效。','','## 分层文件','','plaque_prior_evidence.csv 按 phenotype 列出原始约束；component_prior_evidence.csv 保留不能映射的力学组织成分；human_evidence.csv、animal_evidence.csv、ros_other_data.csv 是主表筛选视图的 CSV，不是新增或独立样本。']
    (ROOT/'data_dictionary.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
def main():
    for d in ['01_raw_sources','02_extracted_data','03_processed_data','04_scripts','05_reports']:(ROOT/d).mkdir(exist_ok=True)
    sources=catalog()
    from supplement_catalog import build_supplement
    supplement=build_supplement()
    records=[normalize(r) for r in extract()]
    priors=generate(records)
    searches,candidates,exclusions=logs(sources)
    qc=validate(records,sources,priors)
    (ROOT/'05_reports/qc_results.json').write_text(json.dumps(qc,ensure_ascii=False,indent=2),encoding='utf-8')
    if not qc['passed']:raise RuntimeError(qc['failed_checks'])
    write_csv(ROOT/'plaque_multimodal_database.csv',records)
    write_csv(ROOT/'03_processed_data/plaque_multimodal_database.csv',records)
    for name,filtered in [('human_evidence',[r for r in records if r['species']=='human']),('animal_evidence',[r for r in records if r['species']!='human']),('ros_other_data',[r for r in records if r['modality']=='ros_other'])]:write_csv(ROOT/f'03_processed_data/{name}.csv',filtered,list(records[0]))
    db=ROOT/'03_processed_data/plaque_database.build.sqlite'
    if db.exists():db.unlink()
    with sqlite3.connect(db) as conn:
        conn.execute('PRAGMA foreign_keys=ON')
        sql_table(conn,'sources',sources,primary='source_id')
        sql_table(conn,'observations',records,primary='record_id',foreign=('source_id','sources','source_id'))
        sql_table(conn,'plaque_type_priors',priors,primary='standardized_plaque_type')
        sql_table(conn,'search_log',searches,primary='search_id')
        sql_table(conn,'excluded_sources',exclusions)
        sql_table(conn,'dataset_catalog',supplement['dataset_catalog'],primary='dataset_id',foreign=[('source_id','sources','source_id'),('parent_dataset','dataset_catalog','dataset_id')])
        sql_table(conn,'dataset_samples',supplement['dataset_samples'],primary='sample_key')
        sql_table(conn,'dataset_membership',supplement['dataset_membership'],primary='membership_id',foreign=[('dataset_id','dataset_catalog','dataset_id'),('sample_key','dataset_samples','sample_key')])
        sql_table(conn,'dataset_files',supplement['dataset_files'],primary='file_id',foreign=('dataset_id','dataset_catalog','dataset_id'))
        sql_table(conn,'supplement_audit',supplement['supplement_audit'],primary='audit_id',foreign=('source_id','sources','source_id'))
        sql_table(conn,'omics_workbook_cells',supplement['omics_workbook_cells'],primary='cell_id',foreign=('dataset_id','dataset_catalog','dataset_id'))
        conn.execute('CREATE VIEW omics_phenotype_samples AS SELECT m.dataset_id, s.* FROM dataset_membership m JOIN dataset_samples s USING(sample_key)')
        conn.execute("CREATE VIEW multimodal_supervised AS SELECT * FROM observations WHERE data_level IN ('A','B') AND ml_eligible=1 AND species='human' AND same_sample_linkage='verified'")
        conn.execute("CREATE VIEW human_prior_evidence AS SELECT * FROM observations WHERE species='human' AND data_level IN ('C','D')")
        conn.execute("CREATE VIEW animal_simulation_evidence AS SELECT * FROM observations WHERE data_level='E'")
        conn.execute("CREATE VIEW target_modality_evidence AS SELECT * FROM observations WHERE modality IN ('mechanical','pH','H2O2')")
        conn.execute("CREATE VIEW ros_other AS SELECT * FROM observations WHERE modality='ros_other'")
        assert conn.execute('PRAGMA foreign_key_check').fetchall()==[]
        assert conn.execute('SELECT count(*) FROM multimodal_supervised').fetchone()[0]==0
        assert conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        assert conn.execute('SELECT count(*) FROM observations').fetchone()[0]==len(records)
    conn.close()
    db.replace(ROOT/'plaque_database.sqlite')
    manifest=[dict(path=str(p.relative_to(ROOT)).replace('\\','/'),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted((ROOT/'01_raw_sources').glob('*')) if p.is_file()]
    write_csv(ROOT/'03_processed_data/source_file_manifest.csv',manifest)
    report(records,sources,priors,qc,searches,exclusions);dictionary(records)
    from supplement_report import write_report
    write_report(supplement,sources)
    print(json.dumps({k:v for k,v in qc.items() if k!='checks'},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
