MyGoogleAlertPapers
项目调研、扩写与蓝图落实
报告
|        | +    | +     | + enrich |        |
| ------ | ---- | ----- | -------- | ------ |
| 工程研究报告 | 目标蓝图 | 实施路线图 |          | 提速专项方案 |
交付对象: 项目开发团队、AI开发代理、后续维护者
|     | 审阅日期: | 2026‑04‑26 |     |     |
| --- | ----- | ---------- | --- | --- |
基于项目代码、测试、验证记录与公开技术文档整理

目录
MyGoogleAlertPapers项目调研、扩写与蓝图落实报告 2
0.摘要 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 2
1.本次审阅范围与证据来源 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 3
1.1本地项目材料 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 3
1.2外部调研范围 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 3
1.3重要边界 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 3
2.项目目标重述 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 4
3.当前项目蓝图 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 4
3.1当前pipeline . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 4
3.2当前CLI表面 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 5
3.3当前主线策略 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 5
4.当前项目进度评估 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 6
4.1成熟度分级 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 6
4.2当前阶段判断 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 6
5.已有验证结果的含金量 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 6
5.1PackageA . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 6
5.2PackageB . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 7
5.3TrackA . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 7
5.4TrackB . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 7
5.5163本地正文抓取验证 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 7
6.外部生态与合规约束 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 8
6.1GoogleScholar:只把alert邮件作为事件源 . . . . . . . . . . . . . . . . . . . . . . . . . . . . 8
6.2Gmail:实时化的优先路线 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 8
6.3163邮箱:优先做artifact可靠性 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 8
7.多源学术API调研与工程约束 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 9
7.1Crossref . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 9
7.2OpenAlex . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 9
7.3SemanticScholar . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 9
7.4PubMed/NCBIE‑utilities . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 10
7.5EuropePMC . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 10
7.6arXiv . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 10
7.7Unpaywall . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 10
7.8SQLite . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 10
8.当前代码架构评估 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 11
8.1邮件摄取层 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 11
8.2解析与候选提取层 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 11
8.3标准化层 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 11
8.4enrich层 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 12
8.5merge层 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 12
8.6dedup层 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 12
8.7OA层 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 13
9.数据库与幂等性蓝图 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 13
9.1当前表设计优点 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 13
9.2关键缺口 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 13
9.3推荐新增表 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 14
10.enrich提速专项方案 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 15
10.1为什么enrich是关键瓶颈 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 15
10.2enrich耗时来源 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 16
10.3加速目标 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 16
10.4核心设计:从candidate‑driven改为intent‑driven . . . . . . . . . . . . . . . . . . . . . . . . 16
10.5核心设计:providerladder与earlystop . . . . . . . . . . . . . . . . . . . . . . . . . . . . 17
10.6核心设计:统一HTTPclient . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 17
10.7核心设计:cache语义修复 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 18
10.8核心设计:per‑provider加速策略 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 18
10.9并发模型 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 19
10.10质量守门指标 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 20
10.11预期提速区间 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 20
10.12enrich加速实施顺序 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 21
11.目标系统蓝图 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 22
11.1V1:可靠增量batch . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 22
1

11.2V2:事件驱动ingest . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 22
11.3V3:资料库服务化 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 22
12.开发路线图 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 22
12.1P0‑立即修复 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 22
12.2P1‑主线加固 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 23
12.3P2‑实时与可用性 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 23
12.4P3‑研究增强 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 23
13.AI开发团队协作规范 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 24
13.1AIagent阅读顺序 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 24
13.2AIagent任务模板 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 24
13.3AIagent禁止事项 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 24
14.风险登记表 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 24
15.推荐立即执行的命令与验证流程 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 25
15.1基础测试 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 25
15.2freshslice主线验证 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 25
15.3enrichbenchmark目标输出 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 25
16.结论 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 26
附录A.P0修复示例 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 26
A.1pyproject.toml . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 26
A.2OpenAlex配置 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 26
A.3query_cache错误缓存修复 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 27
A.4OAconfig_missing . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 27
附录B.enrichplanner伪代码 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 27
附录C.参考资料 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 28
MyGoogleAlertPapers 项目调研、扩写与蓝图落实报告
交付对象:项目开发团队、AI开发代理、后续维护者
项目:MyGoogleAlertPapers
审阅材料:/mnt/data/MyGoogleAlertPapers‑main.zip解压后的代码、测试、文档、验证记录、runbook与policyprofile
审阅日期:2026‑04‑26
审阅时区:Asia/Tokyo
本报告性质:工程研究报告+目标蓝图+实施路线图+enrich提速专项方案
0. 摘要
MyGoogleAlertPapers的方向是正确且有工程价值的:把个人已经订阅并接收的GoogleScholaralert邮件作为文献发现事件源,再通
过开放学术元数据源进行结构化补全、合并、去重和开放获取增强,最终形成一个local‑first的个人实时文献资料库。
从当前代码和文档看,项目已经越过了普通原型阶段。它拥有完整的batch/replaypipeline、SQLite数据层、邮件解析、候选论文抽取、标
准化、多源enrich、字段级merge、保守dedup、post‑dedupOAenrichment、策略profile和多轮验证记录。当前测试结果为:
45 passed in 2.22s
项目当前最准确的定位是:
一个已经完成真实邮箱切片验证的本地优先文献资料库构建原型,正在向可长期运行的增量更新系统和团队可维护工程转型。
最重要的结论如下:
1. 主线架构已经收敛: 当前默认主线应继续使用conditional_sources_v2 + author_blob_fallback_only + post‑dedup
enrich‑paper‑oa。
2. 不应爬取GoogleScholar搜索结果:GoogleScholar官方帮助说明其提供alerts,同时不提供bulkaccess,并会阻止自动下
载搜索结果。因此本项目以个人邮箱alert为事件源,是更稳妥的合规路线。 1
3. enrich是当前最大耗时瓶颈: 历史验证显示enrich平均约5.3‑5.8秒/候选。按163早期摄取的15,284个candidates线性外
推,冷启动顺序enrich约需22‑24小时。这个环节必须专项优化。
1GoogleScholar,“SearchHelp”,包括alerts与automateddownload/bulkaccess说明。https://scholar.google.com/intl/en/scholar/help.
html
2

4. 错误缓存是P0风险: 当前enrich中provider异常会写入query_cache,后续可能被读取成no_match,从而把临时网络/API错
误固化为权威无匹配。
5. 数据库幂等性需要下沉到SQLite约束:当前很多幂等假设由pipeline顺序保证,还没有足够多的唯一索引、partialuniqueindex
和连接级PRAGMA。
6. 实时化不应一步到位:建议按“可靠增量batch‑>事件驱动ingest‑>资料库服务化”三阶段推进。
7. enrich提速应遵循质量不回退原则: 所有加速必须通过fixed‑seedreplay验证canonical数、reviewqueue、severe
conflict、OA覆盖和人工抽样质量,不能为了速度牺牲资料库可信度。
1. 本次审阅范围与证据来源
1.1本地项目材料
本次审阅覆盖以下内容:
范围 内容
代码 src/mygooglealertpapers/下43个源码文件,约4,733行
测试 tests/下12个测试文件,约1,130行
文档 README.md,docs/,docs/validation/,runbooks/
策略配置 config/policy_profiles/*.yaml
脚本 scripts/下replay、TrackA/B、163本地抓取等脚本
验证记录 PackageA/B、TrackA/B、mainlinesummary、163
bodysweep与artifactreconciliation
本地验证命令:
cd /mnt/data/MyGoogleAlertPapers‑main
PYTHONPATH=src python ‑m pytest tests
结果:
45 passed in 2.22s
1.2外部调研范围
为把项目蓝图落实到长期可维护系统,本报告补充调研了以下官方或接近官方资料:
・ GoogleScholaralert与bulkaccess边界;
・ GmailAPIpushnotification、sync与history增量;
・ CrossrefRESTAPI认证、politepool、限速与缓存建议;
・ OpenAlexAPIkey、filterOR、select字段、search成本与snapshot;
・ SemanticScholarAPIkey、GraphAPI、batch/bulk思路;
・ NCBIE‑utilities/PubMed速率与tool/email/APIkey规范;
・ EuropePMCRESTAPI;
・ arXivAPI延时要求;
・ UnpaywallDOI/OA查询角色;
・ SQLiteWAL、partialindex、foreignkey、busytimeout。
1.3重要边界
本报告没有使用真实邮箱凭据,没有读取你的真实Gmail/163邮箱,也没有在报告生成阶段实际请求Crossref/OpenAlex/Semantic
Scholar/PubMed/EuropePMC/arXiv/Unpaywall。结论基于项目代码、历史验证记录、测试结果和公开文档。
3

2. 项目目标重述
项目的真实目标不只是“从邮件中提取论文”。更准确的目标应表述为:
构建一个个人化、可追溯、可增量更新、低成本、合规、可导出、可审核的科研文献资料库。
该目标可以拆成8个子目标:
子目标 说明
从GoogleScholaralert邮件中捕获与你关注研究者/主题相关的
发现
新论文事件
结构化 从半结构化邮件中提取标题、作者、venue、年份、URL、DOI、
PMID、PMCID、arXiv等字段
归一化 清洗DOI、标题、作者、标识符和URL,消除邮件模板和来源噪声
补全 调用开放学术元数据源补全缺失字段,提高可检索性
合并 在多源元数据冲突时进行字段级证据仲裁
去重 将多个alert、多个版本、多个来源合并到canonicalpaper层
开放获取 对canonicalDOI做OA状态和最佳访问URL补充
支持搜索、导出、reviewqueue、周报、兴趣图谱和后续AI辅助阅
使用
读
一个关键设计原则是: GoogleScholaralert是发现层,不是事实层。项目不应把邮件里解析到的字段直接视为最终权威事实,而应保留
rawsnapshot,通过多源证据和可审核规则逐步提升可信度。
3.
当前项目蓝图
3.1当前pipeline
当前代码和文档反映的主流程如下:
| Google | Scholar | alert | emails |     |
| ------ | ------- | ----- | ------ | --- |
￨
|     | ￨‑‑ | Path A: IMAP | read‑only    | scan |
| --- | --- | ------------ | ------------ | ---- |
|     | ￨   | mgap         | scan‑mailbox |      |
￨
|     | ￨‑‑ | Path B: 163 | Windows‑local       | body fetch            |
| --- | --- | ----------- | ------------------- | --------------------- |
|     | ￨   | Playwright  | / Chrome            | CDP ‑> JSONL artifact |
|     | ￨   | mgap        | import‑local‑bodies |                       |
￨
v
| Raw | mail snapshot |     |     |     |
| --- | ------------- | --- | --- | --- |
￨
v
| Mail | parsing | and Scholar | alert | detection |
| ---- | ------- | ----------- | ----- | --------- |
|      | mgap    | parse‑mails |       |           |
￨
v
| Paper | candidate | extraction |     |     |
| ----- | --------- | ---------- | --- | --- |
title / authors / venue / year / DOI / PMID / PMCID / arXiv / target URL
￨
v
| Candidate | normalization |                      |     |     |
| --------- | ------------- | -------------------- | --- | --- |
|           | mgap          | normalize‑candidates |     |     |
￨
v
| Multi‑provider |     | bibliographic | enrichment |     |
| -------------- | --- | ------------- | ---------- | --- |
4

mgap enrich‑candidates
Crossref / OpenAlex / Semantic Scholar / PubMed / Europe PMC / arXiv
￨
v
Field‑level metadata merge
mgap merge‑metadata
￨
v
Conservative deduplication and canonical paper creation
mgap dedup‑candidates
￨
v
Post‑dedup OA enrichment
mgap enrich‑paper‑oa
Unpaywall DOI‑led OA status / best OA URL
￨
v
Personal literature database
SQLite canonical_paper / source_record / review_queue / paper_open_access
3.2当前CLI表面
当前CLI已覆盖完整batch/replay主线:
init‑db
scan‑mailbox
parse‑mails
import‑local‑bodies
normalize‑candidates
enrich‑candidates
merge‑metadata
dedup‑candidates
enrich‑paper‑oa
report‑batch
report‑normalization
report‑enrichment
report‑merge
report‑dedup
report‑paper‑oa
report‑cost
report‑review‑queue
export‑review‑queue
这说明项目的“工程骨架”已经成形。下一阶段的重点不应是继续增加零散命令,而应是提高可靠性、并发能力、可观测性和资料库使用体验。
3.3当前主线策略
根据docs/13‑project‑phase‑map‑and‑current‑status‑2026‑04‑22.md与docs/14‑mainline‑promotion‑memo‑2026‑
04‑22.md,当前主线应确认为:
conditional_sources_v2
+ author_blob_fallback_only
+ post‑dedup enrich‑paper‑oa
含义如下:
1. conditional_sources_v2作为书目元数据增强与merge的默认baseline;
2. TrackA只保留很窄的finalfallback垃圾拦截规则,即author_blob_fallback_only;
3. Unpaywall不作为candidate‑levelbibliographicprovider,只作为dedup后canonicalDOI的OAenrichment
provider。
5

这个选择是合理的。更激进的fallback规则在PackageB中降低了canonical产出并增加了reviewqueue,说明规则扩张不是免费收
益。Unpaywall的角色也更适合作为OA状态和开放URL层,而不是书目元数据事实源。
4.
当前项目进度评估
4.1成熟度分级
| 模块   |                           |                   | 当前状态      |     |     |     |     | 成熟度 评价           |
| ---- | ------------------------- | ----------------- | --------- | --- | --- | --- | --- | ---------------- |
| 邮件读取 | IMAPread‑only+163local    |                   |           |     |     |     |     | 中 能跑,但还不是通用实时    |
|      |                           |                   | bodyfetch |     |     |     |     | ingest           |
|      |                           | SQLiterawsnapshot |           |     |     |     |     | local‑first思路正确  |
| 原始快照 |                           |                   |           |     |     |     |     | 中高               |
| 邮件解析 | MIME+HTML/text+Scholar    |                   |           |     |     |     |     | 中高 对当前样本有效,需模板回归 |
|      |                           | alertdetection    |           |     |     |     |     | 库                |
|      | anchor/text/url/snippet提取 |                   |           |     |     |     |     | 可用,作者和短标题边界需增    |
| 候选提取 |                           |                   |           |     |     |     |     | 中                |
强
| 标准化    | DOI/title/text/identifier清洗 |             |     |     |     |     |     | 中高 PackageA证明收益明显 |
| ------ | --------------------------- | ----------- | --- | --- | --- | --- | --- | ----------------- |
| enrich |                             | 多provider接入 |     |     |     |     |     | 覆盖面好,但性能和错误恢复     |
中
需重构
| merge        |                            | 字段级合并与冲突分级      |      |     |     |     |     | 高 项目核心优势之一          |
| ------------ | -------------------------- | --------------- | ---- | --- | --- | --- | --- | ------------------- |
| dedup        | DOI/PMID/PMCID/title‑      |                 |      |     |     |     |     | 中高 方向正确,canonical更新 |
|              |                            | author‑year保守合并 |      |     |     |     |     | 和versioning未完成      |
| OAenrichment | post‑dedupUnpaywall        |                 |      |     |     |     |     | 中高 架构位置正确           |
| 成本记录         | providerlatency/cost_event |                 |      |     |     |     |     | 中 可扩展为完整观测层         |
| 实时化          |                            |                 | 计划阶段 |     |     |     |     | 低 当前更接近             |
batch/replay
| 导出/检索/UI |                       |     | 计划阶段 |     |     |     |     | 低 资料库可用性层还缺 |
| -------- | --------------------- | --- | ---- | --- | --- | --- | --- | ----------- |
| 文档/验证    | 多轮replay与decisionmemo |     |      |     |     |     |     |             |
|          |                       |     |      |     |     |     |     | 高 很强的工程研究资产 |
4.2当前阶段判断
项目处在:
mainline convergence ‑> reliability hardening ‑> incremental runtime
也就是:
1. 主线策略已经有较强证据支持;
2. 下一步应先修可靠性和幂等性;
3. 然后再做增量运行与实时化;
4. 最后建设搜索、导出、reviewUI和digest。
5. 已有验证结果的含金量
5.1PackageA
PackageA 在249个 normalizedcandidates上验证了 DOI清洗、normalized‑onlyfallback、same‑batchreplay和
query_cachereset等改动。
|     | 指标                      |     |     | baseline |     | treatment |     | 变化  |
| --- | ----------------------- | --- | --- | -------- | --- | --------- | --- | --- |
|     | source_record           |     |     |          | 951 |           | 951 | 0   |
|     | matchedsource_record    |     |     |          | 503 |           | 498 | ‑5  |
|     | mergedproposal          |     |     |          | 219 |           | 249 | +30 |
|     | normalized‑onlyfallback |     |     |          | 0   |           | 30  | +30 |
|     | canonicalpaper          |     |     |          | 176 |           | 204 | +28 |
6

|     |     | 指标                |     | baseline | treatment     | 变化  |
| --- | --- | ----------------- | --- | -------- | ------------- | --- |
|     |     | reviewqueue       |     |          | 2             | 2 0 |
|     |     | severeDOIconflict |     |          | 2             | 2 0 |
|     |     | providerlatency   |     |          | ‑ 1,433,216ms | ‑   |
结论:PackageA在没有明显增加reviewqueue和severeconflict的情况下提升了coverage,是成功的增强。
5.2PackageB
PackageB使用更大切片比较conditional_sources_v2与更宽泛的v4fallback。
|     |     |                      |     |     | v2 v4       |     |
| --- | --- | -------------------- | --- | --- | ----------- | --- |
|     |     | 指标                   |     |     |             | 变化  |
|     |     | normalizedcandidates |     |     | 368 368     | 0   |
|     |     | providerintents      |     |     | 1,405 1,405 | 0   |
|     |     | matchedsource_record |     |     | 777 780     | +3  |
|     |     | mergedproposal       |     |     | 368 367     | ‑1  |
|     |     | canonicalpaper       |     |     | 293 284     | ‑9  |
|     |     | reviewqueue          |     |     | 2 10        | +8  |
结论: v4轻微增加上游matchedrecords,但没有转化为更好的下游结果,反而降低canonicalyield并增加人工审核压力。因此主线回
退到v2是正确决策。
5.3TrackA
TrackA的结论是:只保留finalfallback阶段的author‑blob垃圾拦截,不在providermatching阶段做广泛过滤。
这是一个重要的规则治理经验:
| 弱证据场景 | ‑> 允许窄规则      |     |                |        |     |     |
| ----- | ------------- | --- | -------------- | ------ | --- | --- |
| 强证据场景 | ‑> 不要用启发式规则覆盖 |     | DOI/PMID/PMCID | 等标识符证据 |     |     |
5.4TrackB
TrackB的结论是:Unpaywall不进入candidate‑levelbibliographicenrich,而作为post‑dedupOAenrichment。
理由:
1. Unpaywall主要围绕DOI返回开放获取状态和开放位置;
2. 它不是通用标题/作者/期刊书目信息authority;
3. 在canonicalDOI层调用可以减少请求数,避免候选级噪声;
4. OA信息是additive,不应改变dedup和书目merge的事实链。
5.5163本地正文抓取验证
docs/validation/163‑local‑body‑sweep‑and‑ingest‑validation‑20260424.md和reconciliation文档提供了非常重要
的容量证据。
|     |     | 指标          |     |     |                       | 结果  |
| --- | --- | ----------- | --- | --- | --------------------- | --- |
|     |     | 2‑pageprobe |     |     | 100success/0failure   |     |
|     |     | 10h主运行      |     |     | 1,878success/0failure |     |
24,267.564秒
主运行耗时
|     |     | 平均正文抓取耗时        |     |     |     | 12.922秒/封 |
| --- | --- | --------------- | --- | --- | --- | --------- |
|     |     | 早期ingest邮件数     |     |     |     | 1,878     |
|     |     | early‑ingest总耗时 |     |     |     | 16.633秒   |
|     |     | candidates      |     |     |     | 15,284    |
7

指标 结果
DOI 3,930
PMCID 29
arXiv 49
bodysweep与early‑ingest耗时比 约1459x
reconciledartifact 7,626validJSONrecords
结论:
1. 本地解析、入库、标准化不是瓶颈;
2. 163WebUI正文抓取是ingest层瓶颈;
3. enrich是进入候选规模后的最大远程I/O瓶颈;
4. 需要把163bodyfetch和enrich分别做专项优化,不要混在一起。
6. 外部生态与合规约束
6.1GoogleScholar: 只把alert邮件作为事件源
GoogleScholar官方帮助说明可以通过envelopeicon创建alerts,并通过邮件接收新论文等提醒;同时说明无法提供bulkaccess,
2
且会阻止自动化软件下载搜索结果。
因此本项目应明确三条红线:
1. 不批量抓取Scholar搜索结果页;
2. 不绕过Scholar的自动化访问限制;
3. 只处理用户自己邮箱中已经接收的alert邮件,并保留来源证据。
这条路线既降低合规风险,也避免Scholar页面模板变化对系统造成破坏。
6.2Gmail: 实时化的优先路线
如果最终邮箱主体是Gmail,推荐使用GmailAPI的watch+history.list增量模型。
官方文档说明 Gmail push notifications 可以通过 Cloud Pub/Sub 监视 mailbox changes, 避免轮询; watch 会返回当前
mailboxhistoryId,后续可用history增量同步。 3Gmail同步指南也强调先fullsync,保存最近historyId,后续partialsync;
如果startHistoryId过期或无效会返回404,需要fullsync。 4history.list的分页和historyId处理也需要正确实现。 5
建议目标结构:
Gmail watch
‑> Pub/Sub notification
‑> history.list since last_history_id
‑> message ids
‑> ingest queue
‑> parse / normalize / enrich / merge / dedup workers
如果暂时不接GmailAPI,也可以先做polling,但必须有sync_checkpoint表保存UID/historycursor。
6.3163邮箱: 优先做artifact可靠性
163WebUI抓取已经被验证为可行,但深页恢复成本高,且历史artifact出现过NULcorruption。下一步应把163路径定义为:
2GoogleScholar,“SearchHelp”,包括alerts与automateddownload/bulkaccess说明。https://scholar.google.com/intl/en/scholar/help.
html
3GoogleDevelopers,“PushNotifications”,GmailAPI.https://developers.google.com/workspace/gmail/api/guides/push
4GoogleDevelopers,“SynchronizingClients”,GmailAPI.https://developers.google.com/workspace/gmail/api/guides/sync
5GoogleDevelopers,users.history.list,GmailAPIreference.https://developers.google.com/workspace/gmail/api/reference/rest/v
1/users.history/list
8

Windows‑local fetch controller
‑> sharded JSONL artifact
‑> per‑shard checksum
‑> manifest
‑> importer validates before ingest
‑> corrupt lines quarantine
不要依赖单个超大JSONL文件作为唯一产物。
7. 多源学术API调研与工程约束
7.1Crossref
CrossrefRESTAPI有public、polite、plus等池。官方文档建议通过mailto参数或User‑Agent中的邮箱进入politepool,并
说明需要监测rate‑limit相关header,遇到429/503等需要退避,同时建议客户端缓存请求结果。 6Crossref2025年底的限速更新进一
步区分不同请求类型:politepool中单DOI请求为10/sec,list‑typerequest为3/sec,并发为3。 7
项目建议:
・ 保留CROSSREF_MAILTO;
・ 增加统一User‑Agent,格式类似:MyGoogleAlertPapers/0.x (mailto:...);
・ 对DOIlookup、titlesearch使用不同tokenbucket;
・ Crossreftitlesearch只作为fallback,不能无条件对所有候选调用;
・ 缓存no_match,但设置比positivematch更短的TTL。
7.2OpenAlex
OpenAlex当前API文档强调使用APIkey, 免费层提供一定预算; 传统email参数应作为兼容方式, 但不应再作为唯一身份配置。 8
OpenAlexfilter支持用pipe表示OR,文档示例显示DOIfilter可一次传多个DOI,且说明最多可合并100个值。 9 OpenAlex
search请求比普通list/filter请求更贵,且semanticsearch有更严格限制,因此titlesearch应受控使用。 10select参数可以减少
返回字段,但只支持root‑levelfields,不支持nestedselect。 11
项目建议:
・ 新增OPENALEX_API_KEY;
・ 保留OPENALEX_EMAIL但降低优先级;
・ DOI查询使用batchORfilter,chunksize调到100前必须用基准测试确认;
・ titlesearch只对无DOI且merge缺关键字段的候选触发;
・ 使用select限制根字段,减少payload;
・ 对大规模离线重建,评估OpenAlexsnapshot,但它体积很大,更适合团队基础设施而非轻量个人工具。 12
7.3SemanticScholar
SemanticScholarGraphAPI支持APIkey,官方资料说明未认证请求共享限速池,推荐使用key;introductorykey的限速较保守,
因此不能把S2无脑放在所有候选的必跑路径。 13 官方tutorial也强调使用APIkey、限制返回字段、利用批量/批处理思路并处理429。 14
项目建议:
・ S2应成为“补充型provider”,不应总是阻塞主线;
・ DOI/PMID/arXiv标识符查询优先于titlesearch;
6CrossrefDocumentation,“TipsforusingtheCrossrefRESTAPI”andauthentication/accessguidance.https://www.crossref.org/doc
umentation/retrieve‑metadata/rest‑api/tips‑for‑using‑the‑crossref‑rest‑api/
7Crossref,“NewratelimitsforthepublicCrossrefRESTAPI”,2025‑11‑12. https://www.crossref.org/blog/new‑rate‑limits‑for‑the‑
public‑crossref‑rest‑api/
8OpenAlexDevelopers,“Authentication”.https://docs.openalex.org/how‑to‑use‑the‑api/authentication
9OpenAlexDevelopers,“Filterworks”,includingORfilterexamples.https://docs.openalex.org/api‑entities/works/filter‑works
10OpenAlexDevelopers,“Searchworks”andAPIcostnotes.https://docs.openalex.org/api‑entities/works/search‑works
11OpenAlexDevelopers,“Selectfields”.https://docs.openalex.org/how‑to‑use‑the‑api/get‑lists‑of‑entities/select‑fields
12OpenAlexDocumentation,“Datadownloads”.https://docs.openalex.org/download‑all‑data/openalex‑snapshot
13SemanticScholar,“APIOverview”.https://www.semanticscholar.org/product/api
14SemanticScholar,“Tutorial:HowtousetheSemanticScholarAPI”.https://semanticscholar.readme.io/docs/tutorial
9

・ titlesearch只用于无标识符或核心字段缺失的candidate;
・ 能批量的IDlookup应批量;
・ 对citationcount、abstract、externalIds等非dedup必需字段,可放到post‑canonicalenrichment。
7.4PubMed/NCBIE‑utilities
NCBI对E‑utilities有明确速率建议:默认不超过3requests/sec,使用APIkey可到10requests/sec。 15 对大任务还建议在低峰时
间运行,并通过tool/email标识客户端。 16
项目建议:
・ 新增NCBI_TOOL,NCBI_EMAIL,NCBI_API_KEY;
・ PMIDlookup应支持批量efetch;
・ titlesearch只对biomedical‑likecandidate触发;
・ PubMed结果中DOI冲突应继续保持严格suppression策略。
7.5EuropePMC
EuropePMCRESTAPI提供文献、预印本、PubMed、fulltext等检索能力,可用于生物医学fallback。 17
项目建议:
・ 保留为biomedicalfallback;
・ 不要对全部候选默认调用;
・ 以PubMed/PMCID/DOI或biomedicalclassifier作为触发条件;
・ 对EuropePMCtitlequery的结果加严格相似度和年份/作者检查。
7.6arXiv
arXivAPI官方手册要求多次请求之间加入3秒延时,大查询需要分片,同一查询应缓存且不要高频重复。 18
项目建议:
・ arXivnativeID查询优先;
・ titlesearch极少触发;
・ 每个arXiv请求遵守3秒间隔;
・ 对arXiv结果建立versioning:arxiv_preprint与published_version不一定是同一个canonicalidentity。
7.7Unpaywall
Unpaywall更适合作为DOI‑ledOAstatusprovider。其支持文档显示titlesearch只是基础能力,官方API用例也围绕DOIobject
查询和email参数。 19 历史RESTAPI文档显示email是必需参数并有每日请求建议上限。 20
项目建议:
・ 保持post‑dedupOAenrichment;
・ 只对canonicalDOI调用;
・ 无UNPAYWALL_EMAIL时不应raise中断,应记录config_missing并跳过;
・ OA字段不参与bibliographicmerge和dedup决策。
7.8SQLite
SQLiteWAL模式通常能提升并发读写能力: readers不阻塞writer,writer也不阻塞readers,但仍然只有一个writer,且不适合网络
文件系统。 21Partialindexes支持只对部分行建索引,也可以做partialuniqueindex,很适合canonical_doi IS NOT NULL这类
15NCBISupportCenter,“APIratelimit”.https://support.nlm.nih.gov/kbArticle/?pn=KA‑05317
16NCBIBookshelf,“TheE‑utilitiesIn‑Depth:UsageGuidelinesandRequirements”.https://www.ncbi.nlm.nih.gov/books/NBK25497/
17EuropePMC,“RESTfulWebService”.https://europepmc.org/RestfulWebService
18arXiv,“APIUserManual”.https://info.arxiv.org/help/api/user‑manual.html
19UnpaywallSupport,“DoestheUnpaywallAPIsupporttitlesearch?”https://support.unpaywall.org/support/solutions/articles/44001
900212‑does‑the‑unpaywall‑api‑support‑title‑search‑
20Unpaywall,archivedRESTAPIdocumentation.https://web.archive.org/web/20240227160024/https://unpaywall.org/products/api
21SQLiteDocumentation,“Write‑AheadLogging”.https://sqlite.org/wal.html
10

唯一约束。
22foreign_keys、busy_timeout等PRAGMA应在连接建立时显式设置。 23
项目建议:
・ 启用WAL;
・ 启用foreignkeys;
・ 设置busytimeout;
・ 增加partialuniqueindex;
・ 后续worker化时使用单writer队列或批量事务。
8. 当前代码架构评估
8.1邮件摄取层
当前mail/imap_client.py使用IMAPSSL和BODY.PEEK[]读取,避免改变未读状态。这符合local‑first和read‑only的安全原则。
不足:
问题 影响 建议
主要按ALL或UNSEEN扫描 长期增量效率低 增加date/from/subject/filter与
checkpoint
缺少Gmailhistory增量 不是真实时 增加GmailAPIadapter
UID状态管理偏轻 重跑和断点恢复不稳 新增sync_checkpoint
163WebUIartifact可靠性不足 长跑文件损坏风险 分片、checksum、manifest、
quarantine
8.2解析与候选提取层
当前scholar_detector.py和candidate_extractor.py能识别Scholaralert并提取候选。它能解包ScholarwrapperURL,
过滤unsubscribe/profile/library等非论文链接,并提取PDF/HTMLresourcehints。
风险:
・ 过度依赖HTMLanchor;
・ title长度阈值可能误伤短标题;
・ 作者解析主要来自snippet,容易被机构/venue/authorblob污染;
・ alert类型没有结构化为一等字段;
・ candidate_id对邮件内顺序有依赖。
建议新增:
alert_type: new_article / citation / related_work / author_follow / unknown
candidate_anchor_hash
candidate_target_url_hash
parser_template_version
raw_snippet
parser_confidence
8.3标准化层
DOI、PMID、PMCID、arXiv、URL、标题清洗已经具备实用价值。PackageA也证明DOI清洗对coverage有明显收益。
短板是作者:
raw_author_string ‑> comma split ‑> first_author_family
建议改成:
22SQLiteDocumentation,“PartialIndexes”.https://sqlite.org/partialindex.html
23SQLiteDocumentation,“PRAGMAstatements”.https://sqlite.org/pragma.html
11

raw_author_string
‑> display_author_list
‑> first_author_family_candidate
‑> author_parser_confidence
‑> author_pollution_flags
把低置信作者字段从dedup强证据中降级。
8.4enrich层
enrich覆盖Crossref、OpenAlex、SemanticScholar、PubMed、EuropePMC、arXiv和Unpaywall,是项目能力上限的核
心来源。但当前也是最大风险区。
主要问题:
1. provider异常可能污染query_cache;
2. 没有统一HTTPclient、retry、backoff、ratelimit;
3. provider调用策略仍偏“候选逐个providerintent”;
4. titlesearch控制不够精细;
5. APIkey和官方新规范适配不足;
6. SQLite写入和远程请求没有清晰分层;
7. 没有benchmarkharness固定评估速度与质量。
本报告第10章专门给出enrich提速方案。
8.5merge层
pipeline/merge.py是项目中最有价值的复杂模块之一。它不是简单“谁先返回用谁”, 而是做字段级preferredvalue、source
priority、冲突分级、PubMedDOIsuppression、venuealias/equivalence、normalized‑onlyfallback和authorblob
guardrail。
建议保留该模块的conservativephilosophy,但增加:
・ 字段级provenance;
・ mergeexplain输出;
・ fixedgoldset;
・ conflictdiffreport;
・ 对每个policyprofile的自动回归指标。
8.6dedup层
当前dedup顺序正确:
DOI exact
‑> PMID exact
‑> PMCID exact
‑> title_key + first_author + year
‑> title_key + first_author
‑> create new canonical
这是“宁可重复,不要误合并”的策略。对于个人资料库,误合并会导致长期知识污染,代价通常高于重复。
不足:
・ canonical记录缺乏后续更新策略;
・ versioning尚未落地;
・ candidate_paper_link缺少更强唯一约束;
・ canonicalDOI/PMID/PMCIDpartialuniqueindex不足;
・ canonical字段来源没有结构化provenance。
12

8.7OA层
post‑dedupUnpaywall是正确方向。它应被视为canonicalpaper的可访问性增强,而不是候选级事实判断。
建议:
paper_open_access
paper_id
doi
provider
is_oa
oa_status
best_oa_url
best_landing_page_url
license
version
evidence_json
checked_at
如果没有UNPAYWALL_EMAIL,应记录状态而不是中断pipeline。
9. 数据库与幂等性蓝图
9.1当前表设计优点
当前schema已覆盖核心实体:
batch_run
mail_ingestion_record
raw_mail_snapshot
paper_candidate
paper_candidate_normalized
query_cache
source_record
candidate_enrichment_status
merged_metadata_proposal
canonical_paper
candidate_paper_link
merge_review_queue
paper_open_access
paper_oa_enrichment_status
cost_event
这说明项目数据模型方向正确。
9.2关键缺口
当前很多幂等性仍依赖pipeline顺序,而不是数据库约束。下一阶段必须把“不重复、不误写、不因重跑产生多份记录”下沉到SQLite。
建议增加如下索引:
CREATE UNIQUE INDEX IF NOT EXISTS idx_mail_ingestion_uid
ON mail_ingestion_record(mailbox, mail_uid);
CREATE UNIQUE INDEX IF NOT EXISTS idx_raw_mail_snapshot_uid_hash
ON raw_mail_snapshot(mail_uid, body_hash);
CREATE UNIQUE INDEX IF NOT EXISTS idx_paper_candidate_candidate_id
ON paper_candidate(candidate_id);
13

CREATE UNIQUE INDEX IF NOT EXISTS idx_candidate_normalized_candidate_id
ON paper_candidate_normalized(candidate_id);
| CREATE UNIQUE | INDEX | IF  | NOT EXISTS | idx_mmp_candidate_id |     |     |
| ------------- | ----- | --- | ---------- | -------------------- | --- | --- |
ON merged_metadata_proposal(candidate_id);
| CREATE UNIQUE | INDEX | IF  | NOT EXISTS | idx_canonical_paper_id |     |     |
| ------------- | ----- | --- | ---------- | ---------------------- | --- | --- |
ON canonical_paper(paper_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_candidate_paper_link_candidate
ON candidate_paper_link(candidate_id);
| CREATE UNIQUE | INDEX | IF  | NOT EXISTS | idx_canonical_doi_notnull |     |     |
| ------------- | ----- | --- | ---------- | ------------------------- | --- | --- |
ON canonical_paper(canonical_doi)
| WHERE canonical_doi |       | IS  | NOT NULL   | AND canonical_doi          |     | <> ''; |
| ------------------- | ----- | --- | ---------- | -------------------------- | --- | ------ |
| CREATE UNIQUE       | INDEX | IF  | NOT EXISTS | idx_canonical_pmid_notnull |     |        |
ON canonical_paper(canonical_pmid)
| WHERE canonical_pmid |       | IS  | NOT NULL   | AND canonical_pmid          |     | <> ''; |
| -------------------- | ----- | --- | ---------- | --------------------------- | --- | ------ |
| CREATE UNIQUE        | INDEX | IF  | NOT EXISTS | idx_canonical_pmcid_notnull |     |        |
ON canonical_paper(canonical_pmcid)
| WHERE canonical_pmcid |     | IS  | NOT | NULL AND canonical_pmcid |     | <> ''; |
| --------------------- | --- | --- | --- | ------------------------ | --- | ------ |
连接层建议:
| def connect(self)    |                                 | ‑> sqlite3.Connection: |              |     |             |     |
| -------------------- | ------------------------------- | ---------------------- | ------------ | --- | ----------- | --- |
| conn                 | = sqlite3.connect(self.db_path, |                        |              |     | timeout=30) |     |
| conn.execute("PRAGMA |                                 |                        | foreign_keys | =   | ON")        |     |
| conn.execute("PRAGMA |                                 |                        | journal_mode | =   | WAL")       |     |
| conn.execute("PRAGMA |                                 |                        | busy_timeout | =   | 5000")      |     |
| return               | conn                            |                        |              |     |             |     |
9.3推荐新增表
| sync_checkpoint |       | 用于Gmail/IMAP/163增量同步: |                 |          |              |     |
| --------------- | ----- | --------------------- | --------------- | -------- | ------------ | --- |
| CREATE TABLE    | IF    | NOT EXISTS            | sync_checkpoint |          | (            |     |
| source_name     |       | TEXT NOT              | NULL,           |          |              |     |
| mailbox         | TEXT  | NOT NULL,             |                 |          |              |     |
| cursor_type     |       | TEXT NOT              | NULL,           |          |              |     |
| cursor_value    |       | TEXT,                 |                 |          |              |     |
| last_success_at |       | TEXT,                 |                 |          |              |     |
| state_json      | TEXT, |                       |                 |          |              |     |
| PRIMARY         | KEY   | (source_name,         |                 | mailbox, | cursor_type) |     |
);
enrichment_intent 用于把provider请求从candidate维度提升到uniqueintent维度:
| CREATE TABLE   | IF    | NOT EXISTS | enrichment_intent |            | (   |     |
| -------------- | ----- | ---------- | ----------------- | ---------- | --- | --- |
| intent_id      | TEXT  | PRIMARY    | KEY,              |            |     |     |
| provider       | TEXT  | NOT NULL,  |                   |            |     |     |
| query_type     | TEXT  | NOT        | NULL,             |            |     |     |
| query_key      | TEXT  | NOT        | NULL,             |            |     |     |
| field_set_hash |       | TEXT       | NOT NULL,         |            |     |     |
| status         | TEXT  | NOT NULL   | DEFAULT           | 'pending', |     |     |
| cache_status   |       | TEXT,      |                   |            |     |     |
| http_status    |       | INTEGER,   |                   |            |     |     |
| error_type     | TEXT, |            |                   |            |     |     |
14

| retry_count      | INTEGER |             | NOT NULL | DEFAULT    | 0,  |                 |     |     |     |     |
| ---------------- | ------- | ----------- | -------- | ---------- | --- | --------------- | --- | --- | --- | --- |
| next_retry_at    |         | TEXT,       |          |            |     |                 |     |     |     |     |
| created_at       | TEXT    | NOT         | NULL,    |            |     |                 |     |     |     |     |
| updated_at       | TEXT    | NOT         | NULL,    |            |     |                 |     |     |     |     |
| UNIQUE(provider, |         | query_type, |          | query_key, |     | field_set_hash) |     |     |     |     |
);
candidate_enrichment_intent_link
| CREATE TABLE | IF NOT            | EXISTS   | candidate_enrichment_intent_link |            |     |     |     | (   |     |     |
| ------------ | ----------------- | -------- | -------------------------------- | ---------- | --- | --- | --- | --- | --- | --- |
| candidate_id |                   | TEXT NOT | NULL,                            |            |     |     |     |     |     |     |
| intent_id    | TEXT              | NOT      | NULL,                            |            |     |     |     |     |     |     |
| reason       | TEXT,             |          |                                  |            |     |     |     |     |     |     |
| created_at   | TEXT              | NOT      | NULL,                            |            |     |     |     |     |     |     |
| PRIMARY      | KEY(candidate_id, |          |                                  | intent_id) |     |     |     |     |     |     |
);
canonical_field_provenance
| CREATE TABLE     | IF NOT        | EXISTS    | canonical_field_provenance |     |     |     | (   |     |     |     |
| ---------------- | ------------- | --------- | -------------------------- | --- | --- | --- | --- | --- | --- | --- |
| paper_id         | TEXT          | NOT NULL, |                            |     |     |     |     |     |     |     |
| field_name       | TEXT          | NOT       | NULL,                      |     |     |     |     |     |     |     |
| field_value      | TEXT,         |           |                            |     |     |     |     |     |     |     |
| source_record_id |               | INTEGER,  |                            |     |     |     |     |     |     |     |
| confidence       | REAL,         |           |                            |     |     |     |     |     |     |     |
| evidence_json    |               | TEXT,     |                            |     |     |     |     |     |     |     |
| updated_at       | TEXT          | NOT       | NULL,                      |     |     |     |     |     |     |     |
| PRIMARY          | KEY(paper_id, |           | field_name)                |     |     |     |     |     |     |     |
);
paper_version_link
| CREATE TABLE  | IF NOT             | EXISTS | paper_version_link |              |     | (              |     |     |     |     |
| ------------- | ------------------ | ------ | ------------------ | ------------ | --- | -------------- | --- | --- | --- | --- |
| from_paper_id |                    | TEXT   | NOT NULL,          |              |     |                |     |     |     |     |
| to_paper_id   | TEXT               | NOT    | NULL,              |              |     |                |     |     |     |     |
| relation_type |                    | TEXT   | NOT NULL,          |              |     |                |     |     |     |     |
| evidence_json |                    | TEXT,  |                    |              |     |                |     |     |     |     |
| created_at    | TEXT               | NOT    | NULL,              |              |     |                |     |     |     |     |
| PRIMARY       | KEY(from_paper_id, |        |                    | to_paper_id, |     | relation_type) |     |     |     |     |
);
10. enrich提速专项方案
10.1为什么enrich是关键瓶颈
从PackageA、PackageB和mainlinesummary看,enrich的远程providerlatency是系统进入候选规模后最主要的耗时。
验证 candidates providerintents providerlatency 平均每intent 平均每candidate
| PackageA |     |     | 249 |     |     | 951   | 1,433.216s |     | 1.51s | 5.76s |
| -------- | --- | --- | --- | --- | --- | ----- | ---------- | --- | ----- | ----- |
| PackageB |     |     | 368 |     |     | 1,405 | 1,940.163s |     | 1.38s | 5.27s |
v2
| mainline |     |     | 368 |     | 约1,405 |     | 2,197.341s |     | 约1.56s | 5.97s |
| -------- | --- | --- | --- | --- | ------ | --- | ---------- | --- | ------ | ----- |
baseline
donor
| post‑dedup |     |           | 263DOI |     |     | 263 |     | 322.042s | 1.22s | ‑   |
| ---------- | --- | --------- | ------ | --- | --- | --- | --- | -------- | ----- | --- |
| OA         |     | canonical |        |     |     |     |     |          |       |     |
15

把PackageA/B的候选级平均值套到163early‑ingest的15,284candidates:
| 15,284 candidates | * 5.27‑5.76 | s/candidate |     |     |     |
| ----------------- | ----------- | ----------- | --- | --- | --- |
| = 80,543‑88,036   | seconds     |             |     |     |     |
| = 22.4‑24.5       | hours       |             |     |     |     |
这不是精确预测,因为真实运行会受到cachehit、provider错误、网络波动、batchDOI比例和titlefallback策略影响。但它足以说
明:如果不重构enrich,项目难以支撑7,626封邮件artifact或更大规模历史回填。
10.2enrich耗时来源
以PackageBv2为例:
|     |     | provider        | events | latency    | 占比    |
| --- | --- | --------------- | ------ | ---------- | ----- |
|     |     | Crossref        | 368    | 578.028s   | 29.8% |
|     |     | OpenAlex        | 368    | 413.587s   | 21.3% |
|     |     | SemanticScholar | 368    | 314.453s   | 16.2% |
|     |     | PubMed          | 146    | 319.527s   | 16.5% |
|     |     | EuropePMC       | 146    | 259.525s   | 13.4% |
|     |     | arXiv           | 9      | 55.043s    | 2.8%  |
|     |     | 合计              | 1,405  | 1,940.163s | 100%  |
可以看到:
1. Crossref/OpenAlex/S2对几乎所有候选触发;
2. PubMed/EuropePMC对约40%候选触发;
3. arXiv数量少但每次要遵守延时;
4. 总耗时不是某一个provider独占,而是多provider串行调用叠加。
10.3加速目标
enrich加速不应只追求“跑得快”,而应同时满足:
| 目标     |     |     | 指标                                        |     |     |
| ------ | --- | --- | ----------------------------------------- | --- | --- |
| 冷启动可接受 |     |     | 15kcandidates冷启动wall‑clock从22‑24h降到2‑6h区间 |     |     |
有cache的重跑应主要受SQLite和merge影响,不应重复请求
热启动很快
远程API
| 质量不回退 |     |     | canonical数、reviewqueue、severeconflict不劣化 |     |     |
| ----- | --- | --- | ---------------------------------------- | --- | --- |
遵守providerratelimit、User‑Agent/APIkey/email要求
合规
| 可恢复 |     |     | 临时错误不会污染cache,可retry,可断点续跑               |     |     |
| --- | --- | --- | ---------------------------------------- | --- | --- |
| 可观测 |     |     | 每个provider的请求数、429、5xx、latency、cachehit、 |     |     |
error都可报告
| 10.4核心设计: | 从candidate‑driven改为intent‑driven |     |     |     |     |
| --------- | -------------------------------- | --- | --- | --- | --- |
当前enrich基本按candidate构建providerintents,再利用query_cache减少重复。建议显式改为两阶段:
| Stage 1: build | unique enrichment | intents |     |     |     |
| -------------- | ----------------- | ------- | --- | --- | --- |
candidates ‑> unique(provider, query_type, query_key, field_set_hash)
| Stage 2: execute | intents | with provider scheduler |     |     |     |
| ---------------- | ------- | ----------------------- | --- | --- | --- |
unique intents ‑> provider calls ‑> source records ‑> fan out to candidates
好处:
1. 先全局去重,再请求远程;
2. 可以批量化DOI、PMID、arXivID;
3. 可以统一排序:先标识符,后titlefallback;
16

4. 可以对不同provider设不同速率;
5. 可以保存每个intent的独立生命周期;
6. 可以更准确地重跑failed/pendingintents。
推荐新增命令:
mgap plan‑enrichment
mgap run‑enrichment‑plan
mgap report‑enrichment‑plan
mgap retry‑enrichment‑errors
| 10.5核心设计: | providerladder与earlystop |     |     |     |
| --------- | ------------------------ | --- | --- | --- |
不应对每个候选都调用全部provider。建议采用分层策略:
| Tier 0: local            | normalized   | evidence                      |           |                |
| ------------------------ | ------------ | ----------------------------- | --------- | -------------- |
| DOI /                    | PMID / PMCID | / arXiv / title               | / authors | / venue / year |
| Tier 1: identifier‑first |              | bibliographic                 | providers |                |
| DOI ‑>                   | Crossref +   | OpenAlex batch                |           |                |
| PMID ‑>                  | PubMed       |                               |           |                |
| arXiv                    | ID ‑> arXiv  |                               |           |                |
| Tier 2: conditional      | fallback     |                               |           |                |
| no DOI                   | and title    | is clean ‑> Crossref/OpenAlex |           | title search   |
biomedical‑like and no strong match ‑> PubMed/Europe PMC title search
missing abstract/externalIds/citation‑like fields ‑> Semantic Scholar
| Tier 3: post‑canonical |                | enrichment                    |     |           |
| ---------------------- | -------------- | ----------------------------- | --- | --------- |
| Unpaywall              | OA             |                               |     |           |
| Semantic               | Scholar        | citation/abstract/externalIds |     | if needed |
| OpenAlex               | topic/concepts | if needed                     |     |           |
Earlystop规则示例:
If DOI exists and Crossref/OpenAlex agree on normalized title within threshold:
| skip S2 | title search |     |     |     |
| ------- | ------------ | --- | --- | --- |
skip PubMed/EuropePMC title search unless PMID/PMCID/native biomedical signal exists
| If PMID exists | and PubMed     | returns high‑confidence |     | record: |
| -------------- | -------------- | ----------------------- | --- | ------- |
| use PubMed     | for biomedical | metadata                |     |         |
call Crossref/OpenAlex by DOI only if DOI is present or PubMed provides DOI
If candidate has no identifier and title is short/noisy/author‑blob‑like:
| do not  | run expensive   | title search |            |          |
| ------- | --------------- | ------------ | ---------- | -------- |
| send to | fallback/review | or wait      | for better | evidence |
这种策略需要用replay验证,不能一次性大面积跳过provider。建议先实现“shadowmode”: 仍保留baseline结果,但模拟新策略
会跳过哪些调用,比较downstream指标。
| 10.6核心设计: | 统一HTTPclient |     |     |     |
| --------- | ------------ | --- | --- | --- |
新增enrich/http_client.py,提供:
@dataclass
class ProviderPolicy:
| provider:             | str |             |     |     |
| --------------------- | --- | ----------- | --- | --- |
| requests_per_second:  |     | float       |     |     |
| concurrency:          | int |             |     |     |
| min_interval_seconds: |     | float = 0.0 |     |     |
| max_retries:          | int | = 3         |     |     |
17

| timeout_seconds: |     |     | int = 20 |     |     |     |     |
| ---------------- | --- | --- | -------- | --- | --- | --- | --- |
retry_statuses: tuple[int, ...] = (408, 409, 425, 429, 500, 502, 503, 504)
class ProviderHttpClient:
| def | request_json(self, |     | provider, | url, | headers=None, |     | params=None): |
| --- | ------------------ | --- | --------- | ---- | ------------- | --- | ------------- |
...
能力要求:
・ 自动注入User‑Agent;
・ provider‑specificAPIkey/email/tool;
・ 处理429/Retry‑After;
・ 指数退避+jitter;
・ 记录request_event;
・ 区分transienterror和permanentno_match;
・ 支持dry‑run和fixturereplay。
| 10.7核心设计: | cache语义修复 |     |     |     |     |     |     |
| --------- | --------- | --- | --- | --- | --- | --- | --- |
当前P0bug是providerexception写入query_cache,后续可能被解释为no_match。建议立即修改:
| 原则 1: | transient | error    | 不写 query_cache |              |          |       |     |
| ----- | --------- | -------- | -------------- | ------------ | -------- | ----- | --- |
| 原则 2: | permanent | no_match | 可以写            | query_cache, |          | 但必须有短 | TTL |
| 原则 3: | positive  | match    | 写 query_cache, |              | TTL 可以更长 |       |     |
原则 4: cache entry 必须包含 provider, query_type, query_key, field_set_hash, cache_status,
| http_status, |     | created_at, | expires_at |     |     |     |     |
| ------------ | --- | ----------- | ---------- | --- | --- | --- | --- |
↪
原则 5: 读取 cache 时如果发现 raw_payload_json.status == error, 必须忽略并重新调度
建议schema:
| ALTER TABLE | query_cache |     | ADD COLUMN | cache_status |     | TEXT;    |     |
| ----------- | ----------- | --- | ---------- | ------------ | --- | -------- | --- |
| ALTER TABLE | query_cache |     | ADD COLUMN | http_status  |     | INTEGER; |     |
| ALTER TABLE | query_cache |     | ADD COLUMN | error_type   |     | TEXT;    |     |
| ALTER TABLE | query_cache |     | ADD COLUMN | expires_at   |     | TEXT;    |     |
ALTER TABLE query_cache ADD COLUMN field_set_hash TEXT DEFAULT 'default';
读取伪代码:
cached = repo.get_query_cache(provider, query_type, query_key, field_set_hash)
if cached:
| payload | =   | json.loads(cached.raw_payload_json |     |     |     | or  | '{}') |
| ------- | --- | ---------------------------------- | --- | --- | --- | --- | ----- |
if cached.cache_status in {'error', 'transient_error'} or payload.get('status') == 'error':
repo.mark_cache_ignored(cached.id, reason='transient_error_cache')
|      | cached            | = None |     |                   |     |        |     |
| ---- | ----------------- | ------ | --- | ----------------- | --- | ------ | --- |
| elif | cached.expires_at |        | and | cached.expires_at |     | < now: |     |
repo.mark_cache_expired(cached.id)
|     | cached | = None |     |     |     |     |     |
| --- | ------ | ------ | --- | --- | --- | --- | --- |
if not cached:
execute_provider_intent()
| 10.8核心设计: | per‑provider加速策略 |     |     |     |     |     |     |
| --------- | ---------------- | --- | --- | --- | --- | --- | --- |
Crossref
・ 必须使用mailto或User‑Agent邮箱进入politepool;
・ DOIlookup与titlesearch使用不同限速;
・ DOIlookup可以高优先级;
・ titlesearch只fallback;
・ 记录responseheaders;
・ 遇到429/503自动退避。
18

OpenAlex
・ 新增OPENALEX_API_KEY;
・ DOI查询使用ORfilter批量,一组最多100个值;
・ 使用select降低payload;
・ search或search.exact只fallback;
・ 大规模重建可考虑snapshot,但不作为个人轻量默认。
SemanticScholar
・ APIkey必配或降级为低优先级;
・ ID/DOI/arXiv查询优先;
・ 能batch的IDlookup批量;
・ citation/abstract/embedding/relatedpapers等非主线字段放到post‑canonical;
・ 无key时默认不应对所有候选运行。
PubMed
・ 新增NCBI_TOOL,NCBI_EMAIL,NCBI_API_KEY;
・ PMIDlist使用batchefetch;
・ titlesearch只对biomedical‑likecandidate;
・ 遵守3rps/10rps规则。
EuropePMC
・ 作为biomedicalfallback;
・ 对titlesearch加强title/year/authorguardrail;
・ 设置softlimiter;
・ 不对全量candidate默认调用。
arXiv
・ nativearXivIDlookup;
・ 请求间隔3秒;
・ titlesearch极少触发;
・ 结果用于versionlink,不要轻易把preprint和publishedversion硬合并。
Unpaywall
・ 只post‑dedup;
・ DOI‑only;
・ 无email记录config_missing,不中断;
・ OA结果只进入paper_open_access,不影响dedup。
10.9并发模型
建议采用“providerlane+SQLitesinglewriter”:
Intent planner
| ‑> provider      | queues   |             |             |           |
| ---------------- | -------- | ----------- | ----------- | --------- |
| Crossref         | lane     |             | concurrency | <= policy |
| OpenAlex         | lane     |             | concurrency | <= policy |
| Semantic         | Scholar  | lane        | concurrency | <= policy |
| PubMed           | lane     |             | concurrency | <= policy |
| Europe           | PMC lane |             | concurrency | <= policy |
| arXiv lane       |          |             | serial,     | 3s delay  |
| Unpaywall        | lane     |             | post‑dedup  | lane      |
| ‑> result queue  |          |             |             |           |
| ‑> SQLite writer |          | transaction | batches     |           |
19

实现方式有两个选择:
| 方案                  |     |     | 优点  |     | 缺点      |     |     | 建议   |
| ------------------- | --- | --- | --- | --- | ------- | --- | --- | ---- |
| ThreadPoolExecutor+ |     |     | 改动小 |     | 限速和取消复杂 |     |     | 短期可用 |
urllib/http.client
httpx.AsyncClient+
|     |     |     | 结构清晰 |     | 改动较大 |     |     | 中期目标 |
| --- | --- | --- | ---- | --- | ---- | --- | --- | ---- |
asynciotokenbucket
由于provider都是网络I/O,Python线程足以先拿到显著收益。不要在第一版就为了async大改所有provider。
10.10质量守门指标
任何enrich加速PR都必须通过以下replay:
| fixed seed   | small: | 249 candidates |         |     |     |     |     |     |
| ------------ | ------ | -------------- | ------- | --- | --- | --- | --- | --- |
| fixed seed   | large: | 368 candidates |         |     |     |     |     |     |
| fresh slice: | >= 500 | candidates,    | 不参与策略训练 |     |     |     |     |     |
验收指标:
|     |     | 指标                |     | 要求                                    |     |     |     |     |
| --- | --- | ----------------- | --- | ------------------------------------- | --- | --- | --- | --- |
|     |     | severeDOIconflict |     | 不增加                                   |     |     |     |     |
|     |     | reviewqueue       |     | 不超过baseline10%,除非人工确认是合理拦截            |     |     |     |     |
|     |     | canonicalpaper    |     | 不下降超过0.5%,除非减少的是垃圾canonical           |     |     |     |     |
|     |     | mergedproposal    |     | 不显著下降                                 |     |     |     |     |
|     |     | providererror     |     | transienterror可retry,不进入no_matchcache |     |     |     |     |
|     |     | cachehitreplay    |     | 第二次运行远程请求数接近0                         |     |     |     |     |
|     |     | 人工抽样              |     | 每次freshslice抽样100条,误合并为0目标            |     |     |     |     |
10.11预期提速区间
这里给出工程估算,不是承诺值。需要通过benchmark确认。
| 优化             |     |     | 对providerlatencysum |     |     | 对wall‑clock |      | 风险  |
| -------------- | --- | --- | ------------------- | --- | --- | ----------- | ---- | --- |
| 修复cache+正确warm |     |     | 热启动接近消除远程latency    |     |     |             | 极大提升 | 低   |
replay
| OpenAlexDOIbatch+ |     |     |     | 中等  |     |     | 中等  | 低   |
| ----------------- | --- | --- | --- | --- | --- | --- | --- | --- |
APIkey+select
| S2移到 |     |     | 可能减少10‑20%调用成本 |     |     |     |     | 中,需质量验证 |
| ---- | --- | --- | -------------- | --- | --- | --- | --- | ------- |
中等
conditional/post‑
canonical
| PubMed/EPMC只 |     |     | 可能减少10‑25%调用成本 |     |     |     |     |     |
| ------------ | --- | --- | -------------- | --- | --- | --- | --- | --- |
|              |     |     |                |     |     |     | 中等  | 中   |
biomedicalfallback
| titlesearchfallback收 |     |     | 可能减少20‑40%调用成本 |     |     |     |     | 高 中高,必须replay |
| -------------------- | --- | --- | -------------- | --- | --- | --- | --- | ------------- |
窄
| providerlane并发 |     |     | 不减少latencysum |        |     | wall‑clock约2‑4x |     | 中   |
| -------------- | --- | --- | ------------- | ------ | --- | --------------- | --- | --- |
| uniqueintent+  |     |     |               | 依重复率而定 |     |                 | 中高  | 低   |
fan‑out
| post‑canonical |     |     | 主线wall‑clock降低 |     |     |     |     |     |
| -------------- | --- | --- | -------------- | --- | --- | --- | --- | --- |
|                |     |     |                |     |     |     |     | 高 低 |
enrichment分离
对15,284candidates的冷启动估算:
| 当前顺序估算: | 22‑24h |     |     |     |     |     |     |     |
| ------- | ------ | --- | --- | --- | --- | --- | --- | --- |
T1: cache 修复 + 合规 HTTP + staged fallback: 10‑16h provider‑equivalent, 6‑10h wall‑clock
20

T2: unique‑intent + provider lanes + batch + conditional S2/PubMed/EPMC: 5‑10h provider‑equivalent,
2‑6h wall‑clock
↪
T3: warmed cache + 增量运行: 每批新增邮件主要受新增 candidate 数影响, 可进入分钟到几十分钟级
最现实的短期目标是:先让368‑candidatefixedslice的wall‑clock降到baseline的30‑50%,且replay指标不劣化。
10.12enrich加速实施顺序
PR‑E0: 错误缓存修复
・ 错误不写query_cache;
・ 或query_cache加cache_status并禁止error‑>no_match;
・ 增加回归测试:simulatedproviderexception后重跑必须重新请求。
PR‑E1: 统一providerHTTPclient
・ User‑Agent;
・ timeout;
・ Retry‑After;
・ exponentialbackoff;
・ 429/5xx分类;
・ request_eventlogging。
PR‑E2:OpenAlexAPIkey与batchhardening
・ 新增OPENALEX_API_KEY;
・ DOIORfilterchunksize测试50/100;
・ 增加select;
・ 报告batchhit/miss。
PR‑E3:enrichment_intentplanner
・ 先生成plan,不执行;
・ 输出按provider/query_type的intent计数;
・ 与当前candidate‑drivenintents对比。
PR‑E4:providerlanerunner
・ 每provider限速;
・ SQLitewriter批量提交;
・ 可resume;
・ 可retryfailedintents。
PR‑E5:conditionalproviderladder
・ Shadowmode比较会跳过哪些provider;
・ Fixedslicereplay;
・ Freshslicereplay;
・ 通过后设为默认。
PR‑E6:post‑canonicalenrich分层
・ S2citation/abstract/OA/topic等移出主线;
・ Unpaywall保持post‑dedup;
・ 主线只保留dedup必需书目证据。
21

11. 目标系统蓝图
| 11.1V1: | 可靠增量batch |     |     |
| ------- | --------- | --- | --- |
目标:每天/每小时稳定更新,不追求秒级实时。
| scheduled      | job |       |     |
| -------------- | --- | ----- | --- |
| ‑> scan/import | new | mails |     |
‑> parse
‑> normalize
| ‑> plan | enrichment |     |     |
| ------- | ---------- | --- | --- |
| ‑> run  | enrichment |     |     |
‑> merge
‑> dedup
| ‑> post‑dedup | OA  |     |     |
| ------------- | --- | --- | --- |
‑> reports
验收:
・ 可断点续跑;
・ 同一批重跑不重复入库;
・ providertransienterror不污染cache;
・ warmreplay不重复远程请求;
・ 输出dailyreport。
| 11.2V2: | 事件驱动ingest |     |     |
| ------- | ---------- | --- | --- |
目标:新邮件到达后自动进入ingestqueue。
Gmail路线:
Gmail watch ‑> Pub/Sub ‑> webhook ‑> history.list ‑> message ids ‑> ingest queue
163路线:
local fetch controller ‑> sharded JSONL ‑> import watcher ‑> ingest queue
验收:
・ sync_checkpoint正确保存cursor;
・ historyId过期可fullsync;
・ artifactcorruption自动隔离;
・ 邮件读操作不改变用户邮箱状态。
| 11.3V3: | 资料库服务化 |     |     |
| ------- | ------ | --- | --- |
目标:不只是构建数据库,而是真正帮助研究。
功能:
| SQLite FTS5  | search         |        |     |
| ------------ | -------------- | ------ | --- |
| BibTeX /     | RIS / CSL JSON | export |     |
| review queue | UI             |        |     |
weekly digest
| author/topic    | dashboard     |              |        |
| --------------- | ------------- | ------------ | ------ |
| paper version   | graph         |              |        |
| Obsidian/Zotero | integration   |              |        |
| AI‑assisted     | summarization | for selected | papers |
12.
开发路线图
12.1P0‑立即修复
22

| 编号   | 任务                 | 产出    | 验收                   |
| ---- | ------------------ | ----- | -------------------- |
| P0‑1 | 修复enricherrorcache | 代码+测试 | providerexception不会变 |
成no_match
| P0‑2 | 添加PyYAML依赖 | pyproject.toml | 干净环境启用policyprofile |
| ---- | ---------- | -------------- | ------------------- |
不失败
| P0‑3 | OpenAlexAPIkey配置 | config+provider | OPENALEX_API_KEY可用, |
| ---- | ---------------- | --------------- | ------------------- |
email兼容
| P0‑4 | SQLitePRAGMA与唯一索引 | migration/schema | 重跑不重复,foreignkeys开 |
| ---- | ----------------- | ---------------- | ------------------ |
启
| P0‑5 | enrich‑paper‑oa | OApipeline | 无email不中断batch |
| ---- | --------------- | ---------- | -------------- |
config_missing
| P0‑6 | 163artifact | importerscript | NUL/corruptline自动隔离 |
| ---- | ----------- | -------------- | ------------------- |
validate/quarantine
12.2P1‑主线加固
| 编号  | 任务  | 产出  | 验收  |
| --- | --- | --- | --- |
P1‑1 enrichHTTPclient enrich/http_client.py retry/backoff/rate‑limit
日志可见
P1‑2 fixed‑slicebenchmark scripts/benchmark_enrich.pbyaselinevsoptimized可
比较
| P1‑3 | enrichment_intent | 新表+CLI | intent去重、plan报告 |
| ---- | ----------------- | ------ | --------------- |
planner
| P1‑4 | providerlanerunner    | worker        | wall‑clock降低且质量不回退  |
| ---- | --------------------- | ------------- | ------------------- |
| P1‑5 | fresh‑slicevalidation | validationdoc | >=500candidates新样本通 |
过
| P1‑6 | canonicalfield | 表+mergeoutput | 每个核心字段可追溯来源 |
| ---- | -------------- | ------------- | ----------- |
provenance
12.3P2‑实时与可用性
| 编号   | 任务              | 产出                | 验收                      |
| ---- | --------------- | ----------------- | ----------------------- |
| P2‑1 | GmailAPIadapter | watch/historysync | historycheckpoint可恢复    |
| P2‑2 | SQLiteFTS5      | searchCLI         | title/abstract/authors可 |
搜索
| P2‑3 | Export | BibTeX/RIS/CSV/CSL | 可导入Zotero/其他工具 |
| ---- | ------ | ------------------ | -------------- |
JSON
| P2‑4 | ReviewUI | HTML/Streamlit | merge_review_queue可 |
| ---- | -------- | -------------- | ------------------- |
人工处理
| P2‑5 | Weeklydigest | markdown/emailreport | 新论文/OA/冲突摘要        |
| ---- | ------------ | -------------------- | ------------------ |
| P2‑6 | versioning   | paper_version_link   | arXiv/journal关系可表达 |
12.4P3‑研究增强
编号 任务 说明
P3‑1 学者画像 按alertsource、author、topic建兴趣图谱
P3‑2 只基于资料库内数据和开放metadata
推荐与聚类
P3‑3 AI摘要 只对用户选择或OAfulltext可用论文运行
P3‑4 阅读状态 unread/skimmed/saved/cited/discarded
P3‑5 Obsidian,Zotero,Notion,localmarkdown
知识库联动
23

13. AI开发团队协作规范
本项目很适合由人类开发者和AIagent共同推进,但必须有边界。
13.1AIagent阅读顺序
建议每个AIagent先读:
README.md
docs/README.md
docs/13‑project‑phase‑map‑and‑current‑status‑2026‑04‑22.md
docs/14‑mainline‑promotion‑memo‑2026‑04‑22.md
docs/validation/mainline‑summary‑20260422_mainline.md
src/mygooglealertpapers/cli.py
src/mygooglealertpapers/pipeline/enrich.py
src/mygooglealertpapers/pipeline/merge.py
src/mygooglealertpapers/pipeline/dedup.py
src/mygooglealertpapers/db/schema.py
src/mygooglealertpapers/db/repository.py
tests/
13.2AIagent任务模板
每个AI改动任务应包含:
Goal: 具体目标
| Do not change:   | 不允许改动的主线策略/质量指标  |        |     |     |
| ---------------- | ---------------- | ------ | --- | --- |
| Files likely     | involved: 相关文件   |        |     |     |
| Tests required:  | 必跑测试             |        |     |     |
| Replay required: | 是否需要 fixed‑slice | replay |     |     |
Acceptance metrics: canonical/review/severe conflict/cache/error/wall‑clock
13.3AIagent禁止事项
・ 不得把GoogleScholar搜索页scraping加入默认主线;
・ 不得为了速度删除reviewqueue;
・ 不得把transientprovidererror记为no_match;
・ 不得无replay修改merge/dedup规则;
・ 不得把Unpaywall重新放回candidate‑levelbibliographicprovider;
・ 不得在没有APIkey/email/User‑Agent的情况下做高频外部调用;
・ 不得引入不可复现的LLM判断作为默认事实链。
14. 风险登记表
| 风险              |     |     | 严重度 当前状态 | 处置   |
| --------------- | --- | --- | -------- | ---- |
| providererror污染 |     |     | 高 代码级存在  | P0修复 |
cache
| enrich冷启动过慢 |     |     | 高 22‑24h量级风险 | intentplanner+ |
| ----------- | --- | --- | ------------ | -------------- |
providerlanes
| SQLite幂等约束不足 |     |     | schema偏轻 | unique/partialindexes |
| ------------ | --- | --- | -------- | --------------------- |
高
| API规范变化 |     |     | 高 OpenAlex/Crossref等持 | 配置/APIclient更新 |
| ------- | --- | --- | --------------------- | -------------- |
续变化
| 163artifactcorruption |     |     | 历史出现NULline | shardedJSONL+ |
| --------------------- | --- | --- | ----------- | ------------- |
高
checksum
| Scholar邮件模板变化 |     |     | 中高 无模板fixture库 | fixtureregression |
| ------------- | --- | --- | -------------- | ----------------- |
|               |     |     | 简单split        | parserconfidence  |
| 作者解析不稳        |     |     | 中              |                   |
24

| 风险           |     |     | 严重度 当前状态   | 处置               |
| ------------ | --- | --- | ---------- | ---------------- |
| 误合并canonical |     |     | 高 保守策略降低风险 | goldset+reviewUI |
| LLM判断污染事实链   |     |     |            | 只用于辅助/摘要         |
中 尚未引入
| 缺少导出 |     |     | 中 资料库难使用 | BibTeX/RIS/CSV/CSL |
| ---- | --- | --- | -------- | ------------------ |
JSON
| GmailhistoryId过期 |     |     |     | fullsyncfallback |
| ---------------- | --- | --- | --- | ---------------- |
中 未实现
| providerratelimit封禁 |     |     | 高 当前无统一limiter | HTTPclient+token |
| ------------------- | --- | --- | -------------- | ---------------- |
bucket
15.
推荐立即执行的命令与验证流程
15.1基础测试
cd MyGoogleAlertPapers‑main
| PYTHONPATH=src | python ‑m pytest | tests |     |     |
| -------------- | ---------------- | ----- | --- | --- |
15.2freshslice主线验证
rm ‑f data/dev.sqlite3
mgap init‑db
| mgap import‑local‑bodies | ‑‑input |     |     |     |
| ------------------------ | ------- | --- | --- | --- |
data/local_mail_bodies/scholar_body_fetch_20260424_full_reconciled.jsonl
↪
mgap parse‑mails
mgap normalize‑candidates
MGAP_POLICY_PROFILE=config/policy_profiles/conditional_sources_v2_author_blob_fallback_only.yaml
| mgap enrich‑candidates |     |     |     |     |
| ---------------------- | --- | --- | --- | --- |
↪
mgap merge‑metadata
mgap dedup‑candidates
mgap enrich‑paper‑oa
mgap report‑batch
mgap report‑normalization
mgap report‑enrichment
mgap report‑merge
mgap report‑dedup
mgap report‑paper‑oa
mgap report‑cost
| mgap export‑review‑queue | ‑‑output | data/review_queue.jsonl |     |     |
| ------------------------ | -------- | ----------------------- | --- | --- |
15.3enrichbenchmark目标输出
建议scripts/benchmark_enrich.py输出JSON:
{
| "run_id":                  | "...",                                              |     |     |     |
| -------------------------- | --------------------------------------------------- | --- | --- | --- |
| "profile":                 | "conditional_sources_v2_author_blob_fallback_only", |     |     |     |
| "candidate_count":         | 368,                                                |     |     |     |
| "intent_count":            | 1405,                                               |     |     |     |
| "unique_intent_count":     | 0,                                                  |     |     |     |
| "remote_request_count":    | 0,                                                  |     |     |     |
| "cache_hit_count":         | 0,                                                  |     |     |     |
| "provider_latency_ms_sum": |                                                     | 0,  |     |     |
| "wall_clock_ms":           | 0,                                                  |     |     |     |
| "provider_summary":        | {},                                                 |     |     |     |
| "merge_summary":           | {},                                                 |     |     |     |
| "dedup_summary":           | {},                                                 |     |     |     |
25

| "quality_gates":                     |     | {   |      |       |     |     |
| ------------------------------------ | --- | --- | ---- | ----- | --- | --- |
| "severe_doi_conflict_not_increased": |     |     |      | true, |     |     |
| "review_queue_within_threshold":     |     |     |      | true, |     |     |
| "canonical_not_regressed":           |     |     | true |       |     |     |
}
}
16. 结论
MyGoogleAlertPapers已经具备成为个人研究基础设施的核心条件:
・ 事件源选择正确;
・ local‑first和rawsnapshot设计正确;
・ 多源metadataenrichment路线正确;
・ merge/dedup策略保守且有验证;
・ Unpaywallpost‑dedup定位正确;
・ 文档和replay文化明显优于普通个人项目。
接下来真正决定项目成败的不是再加更多provider,而是:
1. 修复错误缓存和数据库幂等性;
2. 把enrich从candidate‑driven改为intent‑driven;
3. 建立合规的providerHTTPclient与限速/退避;
4. 用fixed‑slice和fresh‑slice守住质量;
5. 把资料库从batchpipeline推进到可搜索、可导出、可审核、可增量运行的系统。
建议开发团队把下一阶段命名为:
| Phase 2: | Reliable | Incremental | Literature | Database |     |     |
| -------- | -------- | ----------- | ---------- | -------- | --- | --- |
Phase2的成功标准是:
|     | Google | Scholar | alert 邮件进入系统后, |                   | provider |        |
| --- | ------ | ------- | -------------- | ----------------- | -------- | ------ |
| 一批新 |        |         |                | 能在不污染邮箱、不重复请求、不违反 |          | 限速、不牺牲 |
merge/dedup质量的前提下,自动生成可搜索、可导出、可审核的canonical文献记录。
附录A.P0修复示例
A.1pyproject.toml
| dependencies | =   | [   |     |     |     |     |
| ------------ | --- | --- | --- | --- | --- | --- |
"beautifulsoup4>=4.12",
"python‑dotenv>=1.0",
"PyYAML>=6.0",
]
A.2OpenAlex配置
@dataclass
class Settings:
| openalex_email:   |     | str | ￨ None = None |     |     |     |
| ----------------- | --- | --- | ------------- | --- | --- | --- |
| openalex_api_key: |     | str | ￨ None = None |     |     |     |
请求header:
| headers | = { |     |     |     |     |     |
| ------- | --- | --- | --- | --- | --- | --- |
"User‑Agent": f"MyGoogleAlertPapers/{version} (mailto:{contact_email})",
}
if settings.openalex_api_key:
| headers["Authorization"] |     |     | = f"Bearer | {settings.openalex_api_key}" |     |     |
| ------------------------ | --- | --- | ---------- | ---------------------------- | --- | --- |
26

具体认证header形式应以OpenAlex当前官方文档为准;如果官方要求queryparameter或其他header,provideradapter应集
中封装,不要散落在pipeline中。
A.3query_cache错误缓存修复
try:
rec = provider.query(...)
| except Exception | as exc: |     |     |     |
| ---------------- | ------- | --- | --- | --- |
repo.finish_enrichment_status(
candidate_id=norm.candidate_id,
provider=intent.provider,
status="error",
error_message=str(exc),
)
| # Do not | put transient | errors into | query_cache. |     |
| -------- | ------------- | ----------- | ------------ | --- |
return
if rec.matched:
| repo.put_query_cache(..., |     | cache_status="ok") |     |     |
| ------------------------- | --- | ------------------ | --- | --- |
else:
repo.put_query_cache(..., cache_status="no_match", expires_at=short_ttl)
A.4OAconfig_missing
if not settings.unpaywall_email:
repo.finish_paper_oa_status(
paper_id=paper_id,
status="config_missing",
error_message="UNPAYWALL_EMAIL is required for Unpaywall API calls",
)
continue
附录B.enrichplanner伪代码
| def build_enrichment_plan(candidates, |     |     | policy): |     |
| ------------------------------------- | --- | --- | -------- | --- |
| intents =                             | {}  |     |          |     |
links = []
| for c in            | candidates:            |                                   |     |          |
| ------------------- | ---------------------- | --------------------------------- | --- | -------- |
| local               | = inspect_candidate(c) |                                   |     |          |
| for provider_intent |                        | in decide_provider_intents(local, |     | policy): |
| key                 | = (                    |                                   |     |          |
provider_intent.provider,
provider_intent.query_type,
provider_intent.query_key,
provider_intent.field_set_hash,
)
| intent_id                     | =   | stable_hash(key)                     |            |                          |
| ----------------------------- | --- | ------------------------------------ | ---------- | ------------------------ |
| intents[key]                  |     | = provider_intent.with_id(intent_id) |            |                          |
| links.append((c.candidate_id, |     |                                      | intent_id, | provider_intent.reason)) |
save_intents(intents.values())
save_candidate_links(links)
执行:
27

def run_enrichment_plan():
lanes = build_provider_lanes()
writer = SQLiteWriter(batch_size=100)
for provider in providers:
pending = repo.list_pending_intents(provider)
lanes[provider].submit(pending)
for result in collect_results(lanes):
writer.enqueue(result)
writer.flush()
附录C.参考资料
以下为本报告调研和技术判断引用的主要公开资料。PDF版本中,重要事实也以脚注形式出现在相关页面底部。
・ GoogleScholarSearchHelp:alerts与automateddownload/bulkaccess说明。https://scholar.google.com
/intl/en/scholar/help.html
・ GmailAPIPushNotifications。https://developers.google.com/workspace/gmail/api/guides/push
・ GmailAPISynchronizingClients。https://developers.google.com/workspace/gmail/api/guides/sync
・ GmailAPIusers.history.list。https://developers.google.com/workspace/gmail/api/reference/rest/v1/us
ers.history/list
・ Crossref REST API tips and access guidance。https://www.crossref.org/documentation/retrieve‑
metadata/rest‑api/tips‑for‑using‑the‑crossref‑rest‑api/
・ CrossrefpublicRESTAPIratelimitupdate,2025‑11‑12。https://www.crossref.org/blog/new‑rate‑limits‑
for‑the‑public‑crossref‑rest‑api/
・ OpenAlexAuthentication。https://docs.openalex.org/how‑to‑use‑the‑api/authentication
・ OpenAlexFilterworks。https://docs.openalex.org/api‑entities/works/filter‑works
・ OpenAlexSearchworks。https://docs.openalex.org/api‑entities/works/search‑works
・ OpenAlexSelectfields。https://docs.openalex.org/how‑to‑use‑the‑api/get‑lists‑of‑entities/select‑fields
・ OpenAlexdatasnapshot。https://docs.openalex.org/download‑all‑data/openalex‑snapshot
・ SemanticScholarAPIoverview。https://www.semanticscholar.org/product/api
・ SemanticScholarAPItutorial。https://semanticscholar.readme.io/docs/tutorial
・ NCBIAPIratelimitsupportarticle。https://support.nlm.nih.gov/kbArticle/?pn=KA‑05317
・ NCBIE‑utilitiesusageguidelines。https://www.ncbi.nlm.nih.gov/books/NBK25497/
・ EuropePMCRESTfulWebService。https://europepmc.org/RestfulWebService
・ arXivAPIUserManual。https://info.arxiv.org/help/api/user‑manual.html
・ Unpaywallsupport: titlesearch。https://support.unpaywall.org/support/solutions/articles/440019002
12‑does‑the‑unpaywall‑api‑support‑title‑search‑
・ UnpaywallarchivedAPIdocumentation。https://web.archive.org/web/20240227160024/https://unpayw
all.org/products/api
・ SQLiteWrite‑AheadLogging。https://sqlite.org/wal.html
・ SQLitePartialIndexes。https://sqlite.org/partialindex.html
・ SQLitePRAGMAstatements。https://sqlite.org/pragma.html
28
