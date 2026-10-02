# ai-seo-cn

中文 AI 搜索优化（AEO/GEO 中文语境）：让内容被元宝、DeepSeek、豆包、百度 AI、微信搜一搜，以及 ChatGPT/Perplexity/Claude/Gemini 的中文回答引用。

一句话：**渠道引用偏好分「实测/假设待测」双轨——优化建议只能引用实测行（带次数统计+留档路径+日期）；固定 5 问题 × 每渠道 5 次的测量协议是「假设」升级为「实测」的唯一路径；先采可见性基线再优化，复测同问题集 ≥2 周闭环；中文合规 veto list 机器可读进配置。**

## 为什么是中文本地化（不是翻译版 ai-seo）

- 上游 `coreyhaines31/marketingskills` 的 ai-seo（v2.5.0，488 行，MIT）默认语境是海外 AI 系统（ChatGPT/Perplexity/Claude/Gemini）的英文引用逻辑
- 中文 AI 渠道（元宝/DeepSeek/豆包/百度 AI/微信搜一搜）的引用源池、结构偏好、入口行为均无公开文档——**任何"DeepSeek 偏好 X 结构"的结论都必须自己测，不存在可转述的权威数据**
- 执行中发现的真问题：海外版工作流假设实施者"已有渠道数据"，中文语境下这一步不存在——所以本 Skill 把"测量协议"本身做成工作流的第一步（渠道映射表），而不是优化建议的附属品

## 与上游的差异（三处硬差异）

| 维度 | 上游 ai-seo | ai-seo-cn |
|---|---|---|
| 渠道偏好来源 | 机制推断+英文渠道经验 | 双轨状态：实测（带留档）/假设待测；优化只依据实测行 |
| 测量 | 无固定协议 | 固定 5 问题（品类/对比/场景/竞品/长尾）× 每渠道 5 次，留档结构强制 |
| 合规 | 无（英文语境） | 中文 veto list（广告法绝对化用语等）机器可读进配置，不可判定条件禁入 |

机制级内容（可提取性/实体密度/可验证性/时效信号）与上游一致，输出时与渠道实测结论分开陈述，不混写。

## 安装

复制本目录到 `~/.agents/skills/`（或你的 Skill 加载路径）即可。依赖：`.agents/product-marketing.md` 产品上下文底座（本 Skill 的 Before Starting 第一步会读它）。

## 自检

```bash
python scripts/validate.py tests/sample_good.json   # 必须 exit 0
python scripts/validate.py tests/sample_bad.json    # 必须 exit 1
```

## 结构

```
SKILL.md                              工作流入口（诚实性总纪律 + 五步：渠道映射表→可见性审计→优化策略→合规 veto→监控复测 + 7 条硬规则）
references/channel-research-protocol.md  渠道测量协议：5 问题设计判据、5 次/问题的稳定性信号、留档目录结构（questions.md+30 回答+summary.md 缺一不算数）、结构偏好从被引片段反推的归纳法（3 类禁止归纳）、实测句式（带次数+路径）、假设→实测升级/降级条件、5 类测量误差、最小启动集排期（1 个 P0 渠道先跑，不铺矩阵）
references/ai-visibility-audit-cn.md  审计与监控：5 问题模板、基线表格式（出现率口径+歧义命中单列）、复测 5 项检查（同问题/同入口/≥2 周/留档/动作定稿）、下降归因三步法（先怀疑测量→区分你的动作 vs 渠道波动→内容侧检查）、映射表完整模板（7 渠道，初始全 pending 是唯一合法初始态）、监控节奏与 skill-eval 接口
scripts/validate.py                   执行计划七维校验器（exit 0/1/2）：D1 底座 / D2 映射表双轨（第三态拦截、measured 行三件齐、初始全 pending、未实测当事实拦截）/ D3 测量协议（5 类问题齐全、≥5 次、留档齐全）/ D4 基线先行 / D5 优化只依据实测行+机制渠道分开 / D6 veto 进配置+全可判定+全带出处 / D7 复测同问题+≥2 周+归因+状态对账
tests/sample_good.json                通过基准（DeepSeek 一行实测带完整留档句式 + 6 行 pending + 初始全 pending / 5 类问题 ×5 次 / 基线 3 渠道优化前已建 / 3 个动作只依据实测行 / veto 3 条进配置 / 复测同问题 3 周留档归因）
tests/sample_bad.json                 拦截基准（没底座没目标 query / "百度 AI 好像偏列表"第三态 + 两行无留档却标 measured + 初始预填偏好 + 未实测当事实 / 问题集缺对比+竞品 + 每问题 1 次 + 留档不全 / 优化前无基线 / 建议引用 pending 行 + 机制渠道混写 / veto 没进配置 + 不可判定 + 无出处 / 复测换问题 + 间隔 1 周 + 没留档 + 没归因）
```

## 相关

- 上游：`coreyhaines31/marketingskills` 的 `ai-seo`（MIT，2026-10-02 实测 main 分支 v2.5.0）
- 效果评估方法论（本 Skill 的监控节是其最小实例）：`skill-eval`
- 方法来源：`skill-lib-iterate` L2-a（AI 搜索本土化动作的可执行展开）
