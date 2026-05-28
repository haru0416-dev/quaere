# Quaere skill 最適化プラン

2026-05-28 起稿。Codex CLI の 220-cap 調査 (`docs/Codex skill read depth.md`)
と、長文脈利用についての先行研究、Anthropic 公式 / 3rd-party の reference skill
の構造調査をもとに、Quaere 5 skill を作り直すための設計プラン。

## 結論

5 skill すべてを **本体 ~200 行 / references/ に逃す** 形に整える。本体は cap
(Codex 220 / 5.4 で 260) に収まり、仕様 (500 行 / 5000 tokens) のずっと内側
で動く。Iron Law と handoff trigger を冒頭に持ち上げ、Worked example と
Anti-patterns は references/ に逃がす。

これは見栄えの問題ではない。長文脈での位置バイアス (lost-in-the-middle / 
primacy bias / context rot) は最新モデルでも残っており、Quaere の現サイズ
(256-441 行) はすでに性能劣化域に入っている。

## 根拠

### 計測ベース

- `docs/Codex skill read depth.md` の主要観測:
  - Codex CLI 経由で gpt-5.5 は 220 行で打ち切り、gpt-5.4 は 260 行で打ち切り
  - 根本原因は Codex CLI の prompt の 1 行 (`Read only enough to follow the workflow`、Issue
    [openai/codex#16479](https://github.com/openai/codex/issues/16479))
  - Quaere 5 skill のうち 5/5 が cap を超える、worst は quaere-evidence (441 行、
    後半 50% が構造的に読まれない)
  - **quaere-semantic は 3 つの handoff 記述が line 221 に並んでいる** ── 1 行差で
    Codex 経路の chain trigger が結構の確率で発火しない (`docs/Codex skill read
    depth.md` の Skill-from-Skill 分析)

### 文献ベース

- **Liu et al. 2023 ("Lost in the Middle")** — U 字曲線。長 context の中盤に
  置かれた情報は **22pp** 利用効率が落ちる。Quaere は中盤 (~120-200 行) に
  Workflow を置いている。
- **Hsieh et al. 2024 ("Found in the Middle")** — この U 字は intrinsic な
  attention bias。prompt 工夫で回避不可、構造的配置が唯一の手段。
- **Chroma 2025 ("Context Rot")** — Claude Opus 4 / GPT-4.1 / Gemini 2.5 を含む
  18 frontier model 全部で input length に応じた連続的な精度劣化。10k → 100k
  tokens で 20-50pp 落ちる。quaere-evidence (441 行 ≈ 10-12k tokens 込み)
  は既に劣化域。
- **Zheng et al. 2025 ("Where to show Demos")** — 8 task × 10 SOTA model で
  primacy bias を再現。冒頭の demo は末尾より consistently 強い。「Iron Law を
  line 1 に置くべき」の経験的根拠。
- **Anthropic "Effective Context Engineering" + Agent Skills docs** — 仕様自体が
  `< 500 行 / 5000 tokens` を推奨。長 input は near the top に置けと明示。

### 既存リファレンス skill 設計の規範

Codex 同梱 `skill-creator` (416 行)、Anthropic `claude-api` (262 行 + 言語別 refs)、
3rd-party `harden` (353 行)、`audit` (146 行)、`critique` (200 行 + refs) を見た
結果:

- 行数: 200-300 行が中央値、300 行を超えるものは references/ で分割
- Iron Law / NEVER ブロックは冒頭 + 末尾に集約、本文に散らさない
- handoff / cross-skill 参照は **冒頭の MANDATORY PREPARATION** として宣言する
  パターン (audit, adapt, critique)
- Worked example は **domain による**: CSS/JS なら必須 (harden)、strategy 系は
  例なしでガイドラインのみ (audit, adapt, critique)
- 長い表 (Nielsen 10 等) は本体に許容、ただし詳細は references/ に逃す

## 設計方針 (cross-cutting)

すべての skill に対して、次を一律に適用する:

1. **本体 ≤ 200 行を target**。理由:
   - Codex の 220 / 260 cap のどちらにも安全に収まる
   - Anthropic 仕様 (500) よりずっと厳しい余裕
   - context rot の影響を最小化

2. **Iron Law は line 10 までに**。primacy bias を活かす。すでに 5/5 で line
   10-14 に置いている (維持)。

3. **Handoff trigger を first 50 行に持ち上げる**。理由:
   - 現状 quaere-evidence は handoff が line 401-429、quaere-grounding は
     line 325-345、quaere-semantic は line 211-244。すべて 220 cap の向こう
   - Codex 経路で chain trigger が発火しないのは authoring 側の責任 (Codex 自体
     を直す必要なし)
   - Anthropic の reference skill 群もこのパターンを採用している (audit / adapt /
     critique)

4. **以下の content は references/ に移管**:
   - Worked example (各 40-100 行)
   - Common drift modes / Anti-patterns (各 10-20 行)
   - 長い Output format spec (各 ~30 行)
   - 詳細な背景文献説明 (Iron Law の説明など)

5. **共通ハンドオフフォーマットを `_shared/handoff-format.md` に外出し** (オプション)。
   現状 5 skill 各々が同じ structure の Handoff ブロックを持っているので、
   テンプレートに集約する。Anthropic の `claude-api/shared/` パターンを踏襲。

## 個別 skill の設計

各 skill の現状 → 目標を整理。

### quaere-audit (299 → 200 行)

**現状**: Iron Law L10、When L17、Core L30、Depth L49、Safety L57、Workflow L66-197、
Confirmation Rule L199-221、Worked example L223-261、Drift L263-274、Coordination
L276-293、Stop L295-299。

**変更**:
- **L276-293 の Coordination (handoff) を冒頭近く (L25 あたり) に上げる**: 17 行
- Worked example L223-261 (38 行) → `references/worked-example.md`
- Drift modes L263-274 (11 行) → `references/anti-patterns.md`
- Confirmation Rule L199-221 (22 行) → 維持 (Iron Law の派生として本体内に)
- Workflow を 130 行 → 100 行程度に圧縮

**目標構造** (~200 行):
```
Iron Law (10-14)
When to use / NOT (17-30)
Handoff and coordination (32-55)   ← 旧 L276-293 から昇格
Core model (57-72)
Depth control (74-82)
Safety boundaries (84-92)
Workflow (94-170)                  ← 圧縮
Confirmation Rule (172-190)
Stop condition (192-200)
```

### quaere-evidence (441 → 200 行) — 最大の削減対象

**現状**: Iron Law L10、Output contract L16-51、Lightweight pass L31-51、When L53、
Core L66、Depth L82、State files L92-119、Guardrails L120-132、Workflow L133-275、
Worked example L317-378、Drift L380-392、Anti-patterns L393-399、Handoff
L401-429、Stop L431-441。

**変更**:
- **L401-429 の Handoff を L25 あたりに上げる** (28 行 → 圧縮して 15 行程度)
- Output contract L16-51 (35 行) を冒頭サマリ 8 行 + `references/output-format.md` 27 行
- State files L92-119 (27 行) → 1 段落要約 + `references/state-templates/`
- Worked example L317-378 (61 行) → `references/worked-example.md`
- Drift L380-392 + Anti-patterns L393-399 (18 行) → `references/anti-patterns.md`
- Workflow L133-275 (142 行) → 100 行に圧縮

**目標構造** (~200 行):
```
Iron Law (10-14)
Output contract サマリ (16-25)
Lightweight pass テンプレ (27-40)
Handoff (42-60)                    ← 旧 L401-429 から昇格・圧縮
When to use / NOT (62-80)
Core model (82-95)
Depth control (97-105)
State files サマリ (107-115)
Guardrails (117-125)
Workflow (127-190)                 ← 圧縮
Stop condition (192-200)
```

### quaere-execution (302 → 200 行)

**現状**: Iron Law L10、When L17、Core L29、Depth L43、Preconditions L53-59、
Workflow L61-176、Worked example L213-253、Drift L255-267、Handoff L269-290、
Stop L292-302。

**変更**:
- **L269-290 の Handoff を L25 あたりに上げる** (22 行 → 15 行)
- Worked example L213-253 (40 行) → `references/worked-example.md`
- Drift L255-267 (12 行) → `references/anti-patterns.md`
- Workflow L61-176 (115 行) → 100 行に圧縮 (Plan/Do/Study/Act の 4 phase が
  ~25 行ずつ)

**目標構造** (~200 行):
```
Iron Law (10-14)
When to use / NOT (17-30)
Handoff (32-50)                    ← 旧 L269-290 から昇格
Core model (52-65)
Depth control (67-75)
Preconditions (77-85)
Workflow (87-185)                  ← 圧縮
Stop condition (187-200)
```

### quaere-grounding (357 → 200 行)

**現状**: Iron Law L10、Boundary L17、When L27、Categories L42、Core L57、
Claim matrix L75-88、Workflow L90-212 (no-network fallback L204 含む)、Worked
example L214-263、Drift L265-276、Anti-patterns L278-288、Output format L290-323、
Handoff L325-345、Stop L347-357。

**変更**:
- **L325-345 の Handoff を L25 あたりに上げる**
- Worked example L214-263 (49 行) → `references/worked-example.md`
- Drift + Anti-patterns L265-288 (23 行) → `references/anti-patterns.md`
- Output format L290-323 (33 行) → 5 行サマリ + `references/output-format.md`
- Workflow L90-212 (122 行) → 100 行に圧縮、no-network fallback の詳細を
  `references/no-network-fallback.md`
- Boundary L17-25 + Categories L42-55 → 統合

**目標構造** (~200 行):
```
Iron Law (10-14)
Boundary with quaere-evidence + Categories (16-35)  ← 統合
Handoff (37-55)                    ← 旧 L325-345 から昇格
When to use / NOT (57-70)
Core model (72-85)
Claim result matrix (87-100)
Workflow (102-185)                 ← 圧縮、fallback 詳細は references へ
Output format サマリ (187-195)
Stop condition (197-200)
```

### quaere-semantic (256 → 200 行)

**現状**: Iron Law L10、Industry baseline L19、When L23、Depth L37、Meaningful
unit L47、Core procedure L59-112、Output format L97、Worked example L119-167、
Probes for Why L169-183、Drift L185-197、Anti-patterns L199-209、Handoff
L211-244、Stop L246-256。

**変更**:
- **L211-244 の Handoff を L25 あたりに上げる** (33 行 → 15 行に圧縮)
  - これが特に重要。**現状の他 quaere skill 参照は L221 に並んでいて、
    Codex 経路で 1 行差で読まれない**
- Worked example L119-167 (48 行) → `references/worked-example.md`
- Probes for Why L169-183 (14 行) → references/ もしくは本体に短縮版
- Drift L185-197 + Anti-patterns L199-209 (22 行) → `references/anti-patterns.md`
- Industry baseline L19-21 (背景文献の引用、3 行) → references/

**目標構造** (~200 行):
```
Iron Law (10-14)
When to use / NOT (16-30)
Handoff (32-50)                    ← 旧 L211-244 から昇格、Codex 経路の chain 問題解消
Depth control (52-62)
Meaningful unit selection (64-75)
Core procedure (77-150)
Output format (152-170)
Probes for Why サマリ (172-185)
Stop condition (187-200)
```

## references/ ディレクトリ構造

各 skill 配下に references/ を作る。共通ファイル名で揃える:

```
quaere-audit/
  SKILL.md
  references/
    worked-example.md      ← Worked example 全文
    anti-patterns.md       ← Common drift modes + Anti-patterns
    output-format.md       ← (該当する skill だけ)
quaere-evidence/
  SKILL.md
  references/
    worked-example.md
    anti-patterns.md
    output-format.md
    state-templates/       ← findings.md, hypotheses.md, etc. のテンプレート
... (other skills similarly)
```

オプションで Quaere 横断の `_shared/` (もしくは `quaere/_shared/`) を作って、
handoff の標準フォーマットや Iron Law の背景説明を集約する。これは
Anthropic の `claude-api/shared/` パターンと整合する。

## 実装順 (推奨)

1. **Phase A: 設計の段階整備** (本ドキュメントを `Status: Proposed` の ADR に
   昇格させる。ADR-XXXX として記録)
2. **Phase B: low-risk な再配置** (handoff の冒頭昇格)。これは行を削るわけではなく、
   既存テキストの順序を変えるだけなので、eval に対して中立な変更。各 skill 個別 PR で
   実施可能。
3. **Phase C: Worked example の references/ 移管**。これも論理的には等価変換 (どこから
   読めるか変わるだけ) なので、eval 数字を保つはず。
4. **Phase D: 本文の圧縮**。Workflow を ~30% 縮める。これは内容変更を伴うので、
   eval を 1 sweep 走らせて回帰がないかを確認。

## eval invariance のテスト計画

各 phase 後に Terminal-Bench を 1 sweep 回し、現在の eval 数字 (in-tree で +37.7pp、
TB clean 69-task subset で +8.7pp) との差分を確認:

- Phase B 後: ±2pp 以内なら通過 (純粋な順序変更)
- Phase C 後: ±3pp 以内なら通過 (例の場所だけ変える)
- Phase D 後: ±5pp 以内なら通過、それ以上なら圧縮しすぎ

Phase D で数字が下がった場合は、削った内容を一部戻す or references/ から
明示的に load する手順を本体に書く。

## 既知のリスク

- **references/ load の確実性**: Anthropic 仕様では progressive disclosure で
  「必要に応じて references/ をロード」とあるが、model が実際にロードするかは
  promptdependent。Worked example をぜったいに読ませたい場合、本体に短い
  pointer を残す ("see `references/worked-example.md` for a full ground-truth
  case")。
- **eval 数字への影響**: 圧縮した部分が実は eval に効いていた可能性を否定できない。
  Phase D 前に Phase A-C で baseline を取り、後で切り分けられるようにする。
- **Codex の prompt が修正された場合**: Issue #16479 が反映された後の Codex CLI
  では 200-行制約が消える。その時点でこの最適化の workaround 性質はなくなり、
  references/ を活用する設計は仕様準拠として継続有効。

## 関連 doc

- 220-cap 計測: `docs/Codex skill read depth.md`
- 評価結果: `docs/evaluation.md`
- ロードマップ: `docs/roadmap.md` (このプランをロードマップに加える要否は別途)
