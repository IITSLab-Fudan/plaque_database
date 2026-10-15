# 斑块多模态证据数据库

面向血管介入机器人研究的可追溯数据工程项目，保存斑块力学、pH、H₂O₂ 与其他 ROS 的实测证据，并关联公开组学数据集与样本注释。

当前版本 **v1.1（2026-10-15）**：35 项来源、102 条物理/化学证据记录、10 个组学数据集登记号、193 条去重样本/文库注释。来源与样本计数包含不同层级，不能直接解释为独立研究数或患者数。

- [数据库说明](plaque_database/README.md)
- [补充数据集核对报告](plaque_database/supplement_update_report.md)
- [数据字典](plaque_database/data_dictionary.md)
- [质量控制报告](plaque_database/quality_control_report.md)
- [SQLite 数据库](plaque_database/plaque_database.sqlite)
- [来源表](plaque_database/sources.csv) / [数据集目录](plaque_database/dataset_catalog.csv)

## 离线重建与验证

Python 3.10+，只使用标准库。克隆后在项目根目录运行：

```sh
python plaque_database/04_scripts/build_database.py
python plaque_database/04_scripts/verify_release.py
python plaque_database/04_scripts/verify_supplement.py
```

原始证据与下载文件保存在 `plaque_database/01_raw_sources/`，包含 URL、取得时间和 SHA-256；重建不联网，也不改写原始证据。大型单细胞表达、原始测序与质谱文件的本地取得状态见 `dataset_files.csv`。根目录发行 ZIP 是工作副本打包件，不纳入 Git；数据库、CSV、脚本和报告均保存在仓库。

## 数据语义

组学表达、荧光强度与总钙含量不等于局部 pH、特异性 H₂O₂ 浓度或游离 Ca²⁺。不跨论文制造同样本配对；当前没有已验证的人体同样本 pH + H₂O₂ + 力学监督训练数据。各数据域、分组映射与适用限制见数据字典。

第三方论文、数据与补充材料保留各自版权和许可；出处与许可线索在来源及数据集目录中。本项目不赋予第三方材料新的使用许可。
