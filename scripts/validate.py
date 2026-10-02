#!/usr/bin/env python3
"""validate.py — ai-seo-cn 中文 AI 搜索优化执行计划七维校验器

输入: 执行计划 JSON（schema 见 tests/sample_good.json）
  {
    "foundation": {
      "product_marketing_md_exists": true,   // 底座存在且已读（Before Starting 第一步）
      "target_queries_defined": true         // 目标 query 已定（5 问题的来源）
    },
    "channel_map": {
      "rows": [
        {"channel": "DeepSeek", "status": "measured",
         "structure_pref": "30 次回答中引用片段结构：FAQ 块 12 次/小标题+短段 9 次/列表 6 次/长文 3 次/表格 0 次",
         "evidence_path": ".agents/ai-seo-cn-evidence/deepseek/2026-10-05/",
         "date": "2026-10-05"},
        {"channel": "豆包", "status": "pending", "structure_pref": "待测",
         "evidence_path": "", "date": ""}
      ],
      "initial_all_pending": true,           // 建表初始状态全 pending（没预填"合理"偏好）
      "no_unmeasured_as_fact": true          // 输出/建议未把 pending 行当事实陈述
    },
    "measurement": {
      "question_set_fixed": true,            // 5 问题写进 questions.md 后不改
      "question_categories_covered": ["品类", "对比", "场景", "竞品", "长尾"],
      "runs_per_question": 5,                // 每问题 5 次
      "channels_measured": ["DeepSeek"],     // 已完整测量过的渠道
      "evidence_complete": true              // questions.md + 30 回答 + summary.md 齐全
    },
    "baseline": {
      "baseline_before_optimization": true,  // 优化动作之前已有基线（先采基线再用）
      "channels_in_baseline": 3,
      "appearance_rate_recorded": true
    },
    "optimization": {
      "based_on_measured_only": true,        // 优化建议只引用 measured 行
      "mechanism_vs_channel_separated": true,// 机制级常识与渠道实测结论分开陈述
      "actions_count": 3
    },
    "veto": {
      "config_path": ".agents/ai-seo-cn-veto.yaml",
      "in_machine_readable_config": true,    // 写进配置（非 README/记忆）
      "entries": 3,                          // ≥1
      "all_decidable": true,                 // 触发条件均可判定（无"语气不当"）
      "all_have_basis": true                 // 每条带法规/出处
    },
    "retest": {
      "same_question_set": true,             // 复测同一组 5 问题（一字不差）
      "interval_weeks": 3,                   // ≥2 周
      "evidence_archived": true,
      "decline_attributed": true             // 下降项已归因（含渠道波动记录）
    }
  }

七维校验（任一 FAIL → exit 1）：
  D1 底座: product_marketing_md_exists=true 且 target_queries_defined=true
     （没底座先优化 = 输出通用套话；没目标 query 就没有 5 问题来源）
  D2 渠道映射表: rows 非空；每行 status ∈ {measured, pending}（无第三态）；
     measured 行必须三件齐：structure_pref 为实测句式（含次数统计，"n 次"
     或"留档"字样）+ evidence_path 非空 + date 非空（无留档=自动降级 pending）；
     initial_all_pending=true（预填偏好=带日期的编造）；
     no_unmeasured_as_fact=true
  D3 测量协议: question_categories_covered 覆盖 5 类（品类/对比/场景/竞品/长尾，
     缺一类=审计不完整）；runs_per_question ≥5；channels_measured 非空
     （有 measured 行时）；evidence_complete=true（留档不齐全=实测资格不成立）
  D4 基线: baseline_before_optimization=true（优化前无基线=无法证明有效）
     且 channels_in_baseline ≥1 且 appearance_rate_recorded=true
  D5 优化: based_on_measured_only=true 且 mechanism_vs_channel_separated=true
     且 actions_count ≥1；一致性：actions_count>0 时映射表必须存在 ≥1 行
     measured（没有实测行却在做优化=建议无实证依据）
  D6 veto: in_machine_readable_config=true（写 README=veto 不存在）
     且 entries ≥1 且 all_decidable=true（不可判定条件入 list=veto 不生效）
     且 all_have_basis=true 且 config_path 非空
  D7 复测: same_question_set=true（换问题=不可比）且 interval_weeks ≥2
     且 evidence_archived=true 且 decline_attributed=true；
     一致性：复测字段生效时基线必须已建（无基线的复测=无米之炊）；
     measured 行与 channels_measured 对账（某渠道 measured 但不在
     channels_measured = 状态造假）

退出码：0=通过 / 1=有缺陷 / 2=文件/格式错误
"""
import json
import sys

REQUIRED_CATS = ("品类", "对比", "场景", "竞品", "长尾")
STATUS_OK = ("measured", "pending")


def fail(checks, code, msg):
    checks.append(("FAIL", code, msg))


def ok(checks, code, msg):
    checks.append(("OK", code, msg))


def is_nonempty_str(v):
    return isinstance(v, str) and v.strip() != ""


def measured_row_valid(r):
    """measured 行三件齐：实测句式 + 留档路径 + 日期"""
    pref = str(r.get("structure_pref") or "")
    is_empirical = ("次" in pref and ("留档" in pref or "/" in pref or "回答中" in pref))
    return (is_empirical
            and is_nonempty_str(r.get("evidence_path"))
            and is_nonempty_str(r.get("date")))


def validate(plan):
    checks = []

    fd = plan.get("foundation") or {}
    cm = plan.get("channel_map") or {}
    ms = plan.get("measurement") or {}
    bl = plan.get("baseline") or {}
    op = plan.get("optimization") or {}
    vt = plan.get("veto") or {}
    rt = plan.get("retest") or {}

    rows = cm.get("rows") or []
    measured_rows = [r for r in rows if r.get("status") == "measured"]
    measured_channels = {str(r.get("channel")) for r in measured_rows}
    listed_measured = ms.get("channels_measured") or []

    # D1 底座
    if fd.get("product_marketing_md_exists") is not True:
        fail(checks, "D1", "product_marketing_md_exists=false——没读底座先优化=输出通用套话（Before Starting 第一步）")
    elif fd.get("target_queries_defined") is not True:
        fail(checks, "D1", "target_queries_defined=false——没目标 query 就没有 5 问题来源（问题集是测出来的，不是现想的）")
    else:
        ok(checks, "D1", "底座就绪（product-marketing.md 已读 + 目标 query 已定）")

    # D2 渠道映射表
    if not rows:
        fail(checks, "D2", "channel_map.rows 为空——没建渠道映射表（本 Skill 的核心差异，先建表再优化）")
    else:
        bad_status = [str(r.get("channel", "?")) for r in rows if r.get("status") not in STATUS_OK]
        bad_measured = [str(r.get("channel", "?")) for r in measured_rows if not measured_row_valid(r)]
        if bad_status:
            fail(checks, "D2", f"状态非法: {bad_status}——只允许 measured/pending 两态（第三态=状态双轨失效）")
        elif bad_measured:
            fail(checks, "D2", f"measured 行不合格: {bad_measured}——实测句式(含次数)+留档路径+日期三件缺一不可"
                               "（无留档=自动降级 pending，不管写得多像真的）")
        elif cm.get("initial_all_pending") is not True:
            fail(checks, "D2", "initial_all_pending=false——建表时预填了'看起来合理'的偏好=带日期的编造")
        elif cm.get("no_unmeasured_as_fact") is not True:
            fail(checks, "D2", "no_unmeasured_as_fact=false——把 pending 行当事实陈述了（第一护栏破了）")
        else:
            ok(checks, "D2", f"映射表合规（{len(rows)} 行，measured {len(measured_rows)} 行全留档，初始全 pending，无未实测当事实）")

    # D3 测量协议
    cats = ms.get("question_categories_covered") or []
    missing_cats = [c for c in REQUIRED_CATS if c not in cats]
    rpm = ms.get("runs_per_question")
    if not missing_cats and (isinstance(rpm, int) and rpm >= 5) and ms.get("question_set_fixed") is True:
        if measured_channels and not listed_measured:
            fail(checks, "D3", f"channels_measured 为空但有 measured 行 {measured_channels}——测量记录缺失")
        elif ms.get("evidence_complete") is not True:
            fail(checks, "D3", "evidence_complete=false——留档不齐全（questions.md + 30 回答 + summary.md 缺一=实测资格不成立）")
        else:
            ok(checks, "D3", f"测量协议合规（5 类问题齐全 × {rpm} 次/问题，固定问题集，留档齐全，已测 {len(listed_measured)} 渠道）")
    elif missing_cats:
        fail(checks, "D3", f"问题集缺类别: {missing_cats}——5 类意图缺一类=审计不完整（不是 5 个品类词变体）")
    elif ms.get("question_set_fixed") is not True:
        fail(checks, "D3", "question_set_fixed=false——问题集没定死写进 questions.md（测中改问题=数据作废）")
    else:
        fail(checks, "D3", f"runs_per_question={rpm!r}——每问题 ≥5 次（单次出现可能是偶然，5 次才有稳定性信号）")

    # D4 基线
    nbl = bl.get("channels_in_baseline")
    if bl.get("baseline_before_optimization") is not True:
        fail(checks, "D4", "baseline_before_optimization=false——优化动作之前没有基线表（先采基线再用，不是用完补采）")
    elif not (isinstance(nbl, int) and nbl >= 1):
        fail(checks, "D4", f"channels_in_baseline={nbl!r}——基线表 0 渠道=没有基线")
    elif bl.get("appearance_rate_recorded") is not True:
        fail(checks, "D4", "appearance_rate_recorded=false——没记出现率（前/后 对比没有口径）")
    else:
        ok(checks, "D4", f"基线合规（优化前已建，{nbl} 渠道，出现率口径已记）")

    # D5 优化
    ac = op.get("actions_count")
    if op.get("based_on_measured_only") is not True:
        fail(checks, "D5", "based_on_measured_only=false——优化建议引用了 pending 行（未实测的偏好不是依据，是先测再优化的排期输入）")
    elif op.get("mechanism_vs_channel_separated") is not True:
        fail(checks, "D5", "mechanism_vs_channel_separated=false——机制级常识与渠道实测混写了（混写=把未实测包装成机制）")
    elif not (isinstance(ac, int) and ac >= 1):
        fail(checks, "D5", f"actions_count={ac!r}——0 个优化动作（审计完不落地=停在'看起来该改'）")
    elif ac > 0 and not measured_rows:
        fail(checks, "D5", f"actions_count={ac} 但映射表无 measured 行——优化建议无实证依据（先跑测量协议再优化）")
    else:
        ok(checks, "D5", f"优化合规（{ac} 个动作，只依据 measured 行，机制/渠道分开陈述）")

    # D6 veto
    ve = vt.get("entries")
    if vt.get("in_machine_readable_config") is not True:
        fail(checks, "D6", "in_machine_readable_config=false——veto 写进 README/文档/记忆=veto 不存在（AI 每次生成前读不到）")
    elif not is_nonempty_str(vt.get("config_path")):
        fail(checks, "D6", "config_path 为空——veto list 没有落盘位置（.agents/ai-seo-cn-veto.yaml）")
    elif not (isinstance(ve, int) and ve >= 1):
        fail(checks, "D6", f"entries={ve!r}——veto list 0 条=没加红线（中文合规约束是本土化的硬差异）")
    elif vt.get("all_decidable") is not True:
        fail(checks, "D6", "all_decidable=false——有不可判定的触发条件（'语气不当'类）——入 list 也=veto 不生效，删掉或改可判定")
    elif vt.get("all_have_basis") is not True:
        fail(checks, "D6", "all_have_basis=false——有 veto 条目没带法规/出处（出事时没有免责记录）")
    else:
        ok(checks, "D6", f"veto 合规（{ve} 条，机器可读配置，全可判定，全带出处）")

    # D7 复测
    iw = rt.get("interval_weeks")
    if rt.get("same_question_set") is not True:
        fail(checks, "D7", "same_question_set=false——复测换了问题=不可比（前后数据作废）")
    elif not (isinstance(iw, (int, float)) and iw >= 2):
        fail(checks, "D7", f"interval_weeks={iw!r}——复测间隔 <2 周（太短：效果未显现+渠道自身波动混淆）")
    elif rt.get("evidence_archived") is not True:
        fail(checks, "D7", "evidence_archived=false——复测没留档（无留档的复测=没发生）")
    elif rt.get("decline_attributed") is not True:
        fail(checks, "D7", "decline_attributed=false——下降项没归因（含'渠道自身波动'也要记录，不记录=下次还是归因不了）")
    elif not (bl.get("baseline_before_optimization") is True):
        fail(checks, "D7", "复测已做但基线未建——无米之炊（前/后 的'前'不存在）")
    else:
        mismatch = measured_channels - {str(c) for c in listed_measured}
        if mismatch:
            fail(checks, "D7", f"状态对账失败: {mismatch} 标了 measured 但不在 channels_measured——测量记录缺失=状态造假")
        else:
            ok(checks, "D7", f"复测合规（同问题集，间隔 {iw} 周，留档+归因齐全，状态对账一致）")

    return checks


def main():
    if len(sys.argv) != 2:
        print("usage: python validate.py plan.json", file=sys.stderr)
        return 2
    try:
        with open(sys.argv[1], encoding="utf-8") as f:
            plan = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"ERROR: 无法读取/解析: {e}", file=sys.stderr)
        return 2
    if not isinstance(plan, dict):
        print("ERROR: 顶层必须是 JSON 对象", file=sys.stderr)
        return 2

    checks = validate(plan)
    fails = [c for c in checks if c[0] == "FAIL"]
    for status, code, msg in checks:
        if status == "FAIL":
            print(f"[{code}] FAIL {msg}")
    print(f"== {len(checks) - len(fails)} OK / {len(fails)} FAIL ==")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
