# Codex CLI は SKILL.md を何行読むか — Terminal-Bench 実測ノート

Zenn 記事「Codex が SKILL.md を 220 行で打ち切っていた話」の、計測の裏付け。記事が経験的な主張をしているので、その元データを切り出して公開する。

対象は「読み取り深度」だけ。skill が有効かどうか（resolution rate への寄与など）は、ここでは扱わない。それは別の計測で、性質も信頼度も違う。

## 計測条件

- Terminal-Bench（`terminal-bench-core==0.1.1`）の 80 タスクを 1 sweep。
- エージェントは Codex CLI v0.128.0、ChatGPT-OAuth 認証、タスクごとのコンテナ内で実行。
- `--global-agent-timeout-sec 1800` / `--dangerously-bypass-approvals-and-sandbox`。後者のモードでは、Codex のツール使用がすべて `exec`（シェル）に寄る。
- skill 集は Quaere v0.3.2。
- データ源は各タスクの `sessions/agent.log`。集計対象は 79 タスク（1 タスクはログ無し）。
- **これは 1 回の sweep**。分散を取った計測ではない。ただし後述のとおり、ここで見ているのは「各 `sed` が何行目で止まったか」という回数・行数であって、走るたびにぶれる精度の差分ではない。

## 何を測ったか

with-skill の各タスクについて、`agent.log` から「Codex が SKILL.md を読むために実行したシェルコマンド」を全部抜き出し、それぞれがカバーした行範囲を集計した。

Codex には skill を読めという指示はしていない。skill ファイルは `~/.claude/skills/` と `~/.agents/skills/` に置いてあるだけで、Codex がそれを自分で見つけて読んだ。プロンプトに skill 名を埋めたわけでもなく、Quaere 側の wrapper から渡したわけでもない。

## 結果

- SKILL.md の読み取りイベントは、79 タスクで計 **56 件**。
- うち **47 件**が `sed -n '1,<N>p'` 形式で、N は **201〜250** の範囲に収まった。
- 少なくとも 1 本の skill を読んだのは **41 タスク**。そのうち **39 タスク**が、読み取りの最も深い行を **きっかり 220** に揃えた。
- この 39 タスクでは、220 行目より先を取りにいく二手目（`sed -n '221,...p'` のようなコマンド）は出ていない。読み取りは 220 で終わっている。

残り 2 タスクは、複数 skill をまたいで読み取り、片方を 220 で止めもう片方を 240 まで取った。

- `git-workflow-hack`: `quaere-audit/SKILL.md` を `sed -n '1,240p'`、`quaere-execution/SKILL.md` を `sed -n '1,220p'`。最深 240 行。
- `write-compressor`: `quaere-execution/SKILL.md` を `sed -n '1,220p'`、`quaere-semantic/SKILL.md` を `sed -n '1,240p'`。最深 240 行。

241 行目以降を取りに行く二手目 (`sed -n '221,...p'` のような追加読み込み) や、`cat <skill>/SKILL.md` のような全文取得は、79 タスク全体で 1 件も観測されなかった。**SKILL.md の全文を読み切ったタスクは無い**。

dispatch は `quaere-execution` に偏っている（56 件中 45 件、80%）。Terminal-Bench のタスクが実装中心なので妥当な分布。

## 原因 — Codex 自身の prompt の 1 行

Codex CLI v0.128.0 (および 2026-05-28 時点の main HEAD `5314f550`) の `codex-rs/core-skills/src/render.rs` に、skill 起動時に model に渡す prompt の中の次の行がある:

```rust
// codex-rs/core-skills/src/render.rs (line 31, ABSOLUTE_PATHS 版)
// line 48 にも ALIASES 版で同じ文言あり
- How to use a skill (progressive disclosure):
  1) After deciding to use a skill, open its `SKILL.md`.
     Read only enough to follow the workflow.
```

「Read only enough to follow the workflow」── これが「partial にしか読むな」という明示指示。`grep` で確認したとおり、この文字列は私の 2026-05-28 の Codex セッションログにそのまま入っている (runtime に渡っている)。

model はその「enough」を、自分が持っている prior でそれぞれ違う数字に解く:

- gpt-5.5 → だいたい 220 行
- gpt-5.4 → だいたい 260 行

これが上の表でみた cap 分布の正体。同じ prompt 指示を、model 世代ごとに違う数字に翻訳しているだけ。

### 既存の Issue

[openai/codex#16479](https://github.com/openai/codex/issues/16479) (2026-04-01 hannesrudolph 氏) で同じ問題が指摘されており、proposed wording も書かれている:

```diff
- 1) After deciding to use a skill, open its `SKILL.md`. Read only enough to follow the workflow.
+ 1) After deciding to use a skill, open and read its `SKILL.md` in full. ...
```

community contributor cluedesc 氏が patch まで作っているが ([`cluedesc:fix/skills-read-skill-md-first`](https://github.com/cluedesc/codex/tree/fix/skills-read-skill-md-first))、openai/codex は invitation-only PR で外部から merge できない。Issue は OPEN、コメントは全部 `author_association: NONE`、OpenAI team の応答なし、最終更新は 2026-04-06 (約 2 ヶ月停滞)。

なお live main は wording が 2 箇所 (`SKILLS_HOW_TO_USE_WITH_ABSOLUTE_PATHS` + `SKILLS_HOW_TO_USE_WITH_ALIASES`) にあり、cluedesc patch (2026-04-02) は片方しか触っていない (2 番目の const は 2026-04-24 の `#19098 "Compress skill paths with root aliases"` で後から増えた)。rebase + 両方更新が要る。

### 最新版で直っているか

v0.128.0 (私の計測) と最新の **v0.134.0 (2026-05-26)** で `render.rs` を diff すると、変更は `plugin_id: None,` の 1 行追加 (skill analytics) だけ。**prompt 文字列は 1 文字も変わっていない**。

runtime でも追試: v0.134.0 で gpt-5.5 / gpt-5.4 を回したところ、cap 分布 (gpt-5.5 で 220、gpt-5.4 で 260) も、cap-test (明示すれば二手目を打つ挙動) も、chain (non-uniform を含む) も、すべて v0.128.0 と同じ。**update では消えない**。

## 読まれない範囲

読み取りが 220 で止まるので、各 skill の 221 行目以降は構造的に読まれない。Quaere の skill はいずれも 220 行を超えている。

| skill | 行数 | 220 行以降（読まれない） |
|---|---:|---:|
| quaere-semantic | 256 | 36 行 / 14% |
| quaere-audit | 299 | 79 行 / 26% |
| quaere-execution | 302 | 82 行 / 27% |
| quaere-grounding | 357 | 137 行 / 38% |
| quaere-evidence | 441 | 221 行 / 50% |

220 行より後ろに置かれているのは、各 skill の Worked example、想定される drift パターン、Anti-patterns、他 skill との連携（Handoff テンプレート）、Stop condition。指示としていちばん強い部分が、ここに集中している。

## ログ抜粋

代表的な 1 行 (タスク `blind-maze-explorer-5x5`、`sessions/agent.log` 517 行目):

```
/bin/bash -lc "sed -n '1,220p' /root/.agents/skills/quaere-execution/SKILL.md"
```

例外側の 240 行版 (タスク `git-workflow-hack`、`sessions/agent.log` 337 行目):

```
/bin/bash -lc "sed -n '1,240p' /root/.agents/skills/quaere-audit/SKILL.md"
```

どちらも Codex が自前で組み立てたコマンドで、プロンプトで指示したものでも Quaere 側 wrapper のテンプレートでもない。`/root/.agents/skills/` 配下を Codex CLI が自力で見つけ、`sed -n '1,<N>p'` で読みに行っている。

## モード横断・agent 横断の追試

「220 行で打ち切り」は Docker や bypass-sandbox 由来の artefact なのか、それとも Codex CLI v0.128.0 の `codex exec` 挙動として一般的なのか。手元の `~/.codex/sessions/` と `~/.claude/transcripts/` を追加で集計した。

### 同じ Codex CLI、別コンテキストで

`~/.codex/sessions/` に残る `codex exec` 系セッション 176 件全部をスキャンし、SKILL.md を sed で読みに行った 39 セッションの最大読み取り行を集計:

| sed `1,Np` の N | セッション数 | 含まれる文脈 |
|---:|---:|---|
| **220** | **31** | TB Docker / in-tree eval harness / `/tmp/cogency-dogfood-*` の手元 ad-hoc |
| 260 | 6 | in-tree eval harness (v0.2.1 sweep) |
| 240 | 2 | in-tree eval harness |
| `cat <skill>/SKILL.md` で全文取得 | **0** | — |

220 が約 80%、上限は 260。`cat` で全文を取りに行ったセッションはゼロ。**Docker / bypass-sandbox 限定の挙動ではなく、harness 経由でも `/tmp` での ad-hoc usage でも同じ場所で止まる**。Codex CLI v0.128.0 を `codex exec` 経由で使う限り、走らせる場所は読み取り深度にほぼ影響していない。

(対話 TUI モード — `codex` を引数なしで起動するパス — は `~/.codex/sessions/` にログが残らない仕様で、ここでは確認できていない。)

### 補足: 非 Quaere skill での挙動 — 制御テスト

176 セッションの sed read 50 件を skill 名で割ると、実はすべて **Quaere 系統** (現行 `quaere-*` 名 20 件 + リネーム前の `cogency-*` / `evidence-gated-review` / `external-grounding` / `semantic-review` 30 件) だった。

同じ host に同居している他系統 (`harden`、`pptx`、`claude-api` 等) はこの期間 Codex から呼ばれなかった。だから、220 cap が skill の内容や frontmatter に依存するかは、ここまでのデータだけでは決められない。

そこで `codex exec` を 2 回明示的に走らせて補った。`yield_time_ms` / `workdir` 等を含む生の `function_call.arguments` を抜粋:

```
# Test A — prompt: "Harden this signup form spec for production: ..."
sed -n '1,220p' /home/haru/.agents/skills/harden/SKILL.md

# Test B — prompt: "I want to create a new Claude Code skill ..."
sed -n '1,220p' /home/haru/.codex/skills/.system/skill-creator/SKILL.md
```

両方とも 220 行ぴったり。`harden` (3rd party、353 行) は `~/.agents/skills/` 配下、`skill-creator` (Codex CLI 同梱の system skill、485 行) は `~/.codex/skills/.system/` 配下にあり、Quaere とは無関係。

したがって 220 cap は:

- **Quaere 系統に依存しない** (3rd-party `harden` で 220)
- **配置パスに依存しない** (`~/.agents/skills/` でも Codex の同梱 system skill 配置でも 220)
- **ファイル長に依存しない** (353 行も 485 行も等しく 220 で打ち切り)

Codex CLI v0.128.0 + gpt-5.5 が SKILL.md を sed で読みにいくとき、行数境界はほぼ **常に 220 行付近** に張り付く、という強い結論になる。

### 他の agent (Claude Code / OpenCode)

別 agent はそもそも skill の読み込み機構が違う。両者とも model 側で sed を書く分岐は通らず、**`skill` ツール呼び出しで SKILL.md 全文を返す**。

**Claude Code** — `~/.claude/transcripts/*.jsonl` 1210 件全部から `tool_name=skill` イベントを抽出して集計:

| skill | 元 SKILL.md | invocations | tool_output 行数 (min / max) |
|---|---:|---:|---:|
| quaere-semantic | 256 | 10 | 256 / 256 |
| quaere-audit | 299 | 6 | 299 / 299 |
| quaere-execution | 302 | 19 | 302 / 302 |
| quaere-grounding | 357 | 5 | 357 / 357 |
| quaere-evidence | 441 | 17 | 441 / 441 |

57 invocations すべてで min = max = 元行数。truncation はゼロ。441 行の quaere-evidence も毎回 441 行で配信される。

**OpenCode** (`sst/opencode`) は単一バイナリ (Bun ビルド) で、Claude Code のような JSONL の transcript が残らない。代わりに `strings ~/.opencode/bin/opencode` でバイナリから抜いた skill ツール実装に、以下の literal が直接埋まっている:

```js
// バイナリから抽出した minified source
output: [
  `<skill_content name="${t.name}">`,
  `# Skill: ${t.name}`,
  "",
  t.content.trim(),   // ← SKILL.md 全文
  ...
]
```

`t.content.trim()` の embed が示すとおり、SKILL.md 本体は **読み込み時点でメモリ上にあり**、`skill` ツール呼び出しに対してそのまま model に返される。行数で切り取る分岐は無い。起動時 (skill の register) も、内容を切るのではなく全文を読んで `~/.claude/skills/` と `~/.agents/skills/` の重複を warn にしているだけ (ログで観測済み)。

### Skill から Skill を呼んだとき、cap はどう振る舞うか

handoff の連鎖 (Skill A の body が推奨する Skill B を、続けて読みにいく挙動) が Codex 経路でも起きるか、起きたとして cap はどう効くか。

`~/.codex/sessions/` の 178 セッション中、distinct な `SKILL.md` を 2 件以上 sed で読んだセッションは 7 件。中身を割ると 3 種類になる:

| パターン | セッション | 内訳 |
|---|---:|---|
| 別 skill への true chain | **3** | (A) `external-grounding → cogency-version-sensitive-guard` (B) `evidence-gated-review → external-grounding` (C) `quaere-audit → evidence-gated-review → external-grounding` (3-chain) |
| 同 skill の re-read | 3 | `cogency-version-sensitive-guard` を absolute path と relative path で 2 回 |
| rename 前後の同 skill | 1 | `external-grounding` → `quaere-grounding` (本体は同じ) |

true chain の代表として 3-chain の session `019e467b` のシーケンス:

```
17:42:25  sed -n '1,220p' .../quaere-audit/SKILL.md
17:43:14  sed -n '1,220p' .../evidence-gated-review/SKILL.md
17:43:14  sed -n '1,220p' .../external-grounding/SKILL.md   (前と 20ms 差 = parallel-batch)
```

quaere-audit を 220 行読んだ model が、その body の handoff 記述 (evidence-gated-review / external-grounding) を見て、続けて両方を 1 turn で並列に sed 起動した。

観察:

- **chain は Codex 経路でも起きる**。Skill A の body から handoff 先を読み取り、続けて Skill B (C) を読みにいく。
- **chain も sed 経由**。Codex には skill 専用 tool が無いので、2 件目以降も shell に落ちる。
- **220 cap は chain の全 hop に等しく効く**。1 件目だけ深く・2 件目を浅く、という非対称は無い。240 のセッションは初手から 240 で揃っており、hop ごとに数字が変わる挙動は観測されていない。

ただし true chain 発生率は 3 / 41 ≈ **7%** (SKILL.md を 1 件以上読んだ Codex session 41 件中)。harness 側 (Claude Code/OpenCode 互換 transcripts) では 2 件以上 Skill 呼び出しを含む session が 226 / 1210 ≈ **19%** で、Codex 経路の方が低い。

この差を説明できそうな構造的事情がある。Quaere skill 5 本の SKILL.md で、他 Quaere skill が最初に出る行を拾うと:

| skill | 他 4 つの handoff target、最初の出現行 |
|---|---|
| quaere-audit | 25 / 26 / 52 / 117 ── **全て 220 内** |
| quaere-execution | 21 / 21 / 21 / 26 ── **全て 220 内** |
| quaere-evidence | 63 / 64 / 260 / 411 ── 半分は 220 超 |
| quaere-grounding | 17 / 255 / 335 / 335 ── 1 つだけ 220 内 |
| quaere-semantic | 207 / 221 / 221 / 221 ── 3 つは **221 行目** で 1 行差 |

quaere-audit と quaere-execution は全方向の handoff が 220 内に入っている。一方 quaere-evidence、quaere-grounding、quaere-semantic は半数〜ほぼ全数の handoff が cap の向こうに落ちている。とくに quaere-semantic は **3 つの handoff が line 221** に揃っていて、220 で打ち切られると 1 行差で構造的に届かない。

実観測の true chain 3 件はすべて、handoff 記述が 220 行内に収まる skill (quaere-audit、execution-loop、evidence-gated-review、external-grounding ── 旧称含む) を起点にしている。Codex 経路で chain 率が低いのは、Codex 自体の挙動ではなく、**SKILL.md 側で handoff 記述を 220 行の向こうに置いてしまったため**、と説明するのが素直。authoring 側で直せる問題。

### モデルを固定して harness だけ差し替えると

ここまでの観察は「harness が違うと挙動が違う」だが、harness と model が同時に変わっているので、220 が model に紐づくのか harness に紐づくのかは分離できていない。元の Zenn 記事でも「同じ Codex CLI で model だけ差し替えたら 220 が消えるか」を留保にしてあった。

逆方向の差し替え ── **model は gpt-5.5 のまま、harness だけ Claude Code 側に差し替える** ── は [claudex](https://github.com/EdamAme-x/claudex) で可能だった。claudex は Claude Code を OpenAI 互換 endpoint に向けて起動するラッパで、tool 形状と prompt は Claude Code のものを使い、推論は ChatGPT OAuth 経由で gpt-5.5 が担当する。

なお claudex 自体に streaming SSE で function_call の output_item を取りこぼすバグがあって、最初は tool 呼び出し自体が空で返ってきていた。patch を当てて上流に出した ([PR #7](https://github.com/EdamAme-x/claudex/pull/7))。以下の観察はその patch を当てたバイナリで取ったもの。

3 セッション走らせた。skill 名を明示したのが 1 件、明示せず自然な依頼にしたのが 2 件:

| session | prompt の系統 | first tool_use | Skill envelope の到達 |
|---|---|---|---|
| `173aaafd` | "Use evidence-gated investigation. Apply quaere-evidence skill." | `Skill(skill="quaere-evidence")` | tool_result が `is_error: true` で本文未着 |
| `cf40e6c9` | "CI 失敗を investigate。skill 名は出さない" | `Skill(skill="quaere-evidence")` | 次の user-message として **439 行** (元 441 行、YAML frontmatter 除く) が届く |
| `eb863b22` | "SDK の現行 API を local で確認してくれ。skill 名は出さない" | `Skill(skill="claude-api")` → `Skill(skill="quaere-grounding")` | 同じ envelope 経由で **259 行 + 353 行** (元 262 / 357 行) |

3 セッション全部で **first move は `Skill` tool 呼び出し**。`sed -n '1,Np' SKILL.md` のような shell 経由読み込みは 0 件。**Skill 実行が error になった `173aaafd` ですら、model は sed に fallback しなかった** (TodoWrite → Glob → Bash → Agent で進めた)。

2/3 では Skill envelope が機能し、`<system> Base directory for this skill: ... # <skill name> ...` という固定 prefix の user-message として SKILL.md 全文が次のターンに挿入されていた。YAML frontmatter を除いた本文はすべて、行数差なく届いている。model はこの envelope を読んでから具体作業に入っていた (e.g. `eb863b22` では claude-api と quaere-grounding を取り、その後に anthropic SDK 周りを `pip show` / `uv pip show` で local 確認)。

つまり 220 行打ち切りは「gpt-5.5 が無条件にやること」ではなく、「**Codex CLI が skill 専用 tool を持っていないので、model が shell に落ちる時のイディオムが 220 行で出る**」という harness-shape 由来の挙動だと言ってよさそうだ。

留保: n=3 の小さな観察。とくに `173aaafd` の Skill 実行 error は claudex 側の Skill 実行ルート上の実装抜けの可能性が高く、Claude Code 本来 (Anthropic endpoint 向け) の挙動とは別物。確認できたのは「**first move の選好が Skill tool に切り替わる**」「**Skill envelope が機能すれば SKILL.md 全文が届く**」「**Skill が落ちても sed に fallback しない**」の 3 点まで。

もう一方の留保 (元の Zenn 記事に書いてあった方) ── 「Codex CLI のまま model を Claude などに差し替えたら 220 が消えるか」 ── は今回も測れていない。Codex CLI は実装上 OpenAI モデルに紐づいているので、対称な実験には別ルートが要る。

### 含意

「SKILL.md 末尾を読まない問題」は **Codex CLI v0.128.0 の `codex exec` を経由したときに限る** Codex-architecture-specific な挙動で、agent 横断で起きる問題ではない。同じ gpt-5.5 でも Claude Code の tool catalog の前に置けば、first move は shell ではなく Skill tool に切り替わる。authoring 側で「first 200 行に prescriptive な部分を寄せる」助言は、Codex 利用者向けのチューニング。Claude Code や OpenCode 経由でしか使わないなら不要。複数 agent 向けに skill を出すなら、Codex 制約に合わせた構成が最も保守的。

## この計測で言えること / 言えないこと

**言えること**

- **原因は Codex CLI 自身の prompt の 1 行**。`codex-rs/core-skills/src/render.rs` (line 31 / 48) が「open its `SKILL.md`. Read only enough to follow the workflow.」と書いており、これが runtime にそのまま model に渡っている (Codex セッションログから verbatim 確認)。既存 Issue [#16479](https://github.com/openai/codex/issues/16479) が同じ問題を指摘済み、proposed wording / community patch まで存在。
- `~/.codex/sessions/` 全 209 sessions のうち、71 sessions が SKILL.md を sed で読みにいき計 143 個の read を生成。**model 軸でくっきり分かれる**:
  - gpt-5.5: 220 が 80 件 (76%)、240 が 10、260 が 11、140 が 4 (cap-test の段階読み)
  - gpt-5.4: 260 が 27 件 (71%)、220 が 9、240 が 2
- 220 という数字は **Codex の prompt + model の prior の合算**。model は「Read only enough」の「enough」を自分の prior で解いており、gpt-5.5 は 220、gpt-5.4 は 260 に着地する。
- **Docker / bypass-sandbox 固有の artefact ではない**。TB Docker、in-tree eval harness、`/tmp` での手元 ad-hoc いずれでも同じ境界が出ている。
- **Quaere skill / 配置パス / ファイル長に依存しない**。3rd-party `harden` (353 行) と Codex 同梱 `skill-creator` (485 行) を invoke させても同じ挙動。
- **agent 横断の問題ではない**。Claude Code (57 invocations 全数検証) と OpenCode (バイナリソース確認) では、`skill` ツールが SKILL.md 全文を model に返している。
- **harness の tool 形状が決めている**。gpt-5.5 を Claude Code harness に流し込んだ追試 (claudex 経由、**n=11**) では、first move 11/11 で `Skill` tool 呼び出し、`sed -n '1,Np' SKILL.md` は 0/11。同じ model でも Codex の prompt に晒さない経路なら cap はそもそも発生しない。
- **Skill envelope 経由なら本文は丸ごと届く**。claudex 追試の 9 セッション (1 件 Skill 実行 error、1 件 envelope なし type) で、`Skill(...)` 直後の user-message envelope に SKILL.md 全文 (frontmatter のみ落とした形) が挿入されていた。
- **skill 自身が「もっと読め」と明示すれば、model は二手目を打つ**。cap-test 実験 (200 行を超えた位置に Iron Law marker、prefix で `sed -n '221,$p'` を指示): gpt-5.5 7/7、gpt-5.4 4/4 で marker 取得。model は本来 partial 読みに固執していない。
- **chain は Codex 経路でも起きる**。Skill A の body から handoff を読み取り、Skill B (場合により C) を続けて読む。**chain の cap は uniform とは限らない** (gpt-5.4 で 260→240→220 のように shrink するケース、gpt-5.5 でも 240→220 の non-uniform を観測)。authoring 側で handoff 記述を line 220 を超えた位置に置くと、その chain は構造的に起きなくなる (Quaere 5 skill のうち quaere-semantic は 3 つの handoff が line 221 で 1 行差で落ちる)。
- **最新版でも消えない**。v0.128.0 と v0.134.0 (2026-05-26、最新) で render.rs を diff すると変更は `plugin_id: None,` の 1 行だけで、prompt 文字列は完全同一。v0.134.0 で再計測しても挙動は変わらない。Issue #16479 が修正されない限り、update では消えない。

**言えないこと**

- **対話 TUI モード** (`codex` を引数なしで起動するパス) は `~/.codex/sessions/` にログが残らず、未確認。本 doc の計測対象は `codex exec` 経由のみ。
- **Codex CLI 固定で non-OpenAI model に差し替えた場合の挙動** は実機検証できていない (Codex CLI は実装上 OpenAI 系 model に紐づいているため)。
- gpt-5.4 の調査は **n=10** で central tendency は出るが、long tail の精度は粗い。
- claudex 追試は **n=11**。傾向は綺麗だが、Claude Code 本来 (Anthropic endpoint) の挙動とは 1:1 ではない (claudex 内の Skill 実行が完全には Claude Code を再現していない、1/11 で Skill 実行 error)。
- **gpt-5.5 でも条件次第で follow-up read が起きる**。「明示的に handoff を促す prompt」を出した D-probe 8 件のうち 3 件で同 skill の続きを sed で読みにいった (`sed -n '221,520p'` 等)。原典の 176 sessions で 0 件 follow-up と書いた言明は、「default prompt 領域では」という但し書き付き。
- **skill が有効かどうか** (resolution rate を上げるか) は、この計測の範囲外。Quaere の effect 計測は [`docs/evaluation.md`](https://github.com/haru0416-dev/quaere/blob/main/docs/evaluation.md) を参照。

## 再現

Quaere リポジトリの `evals/` にある runner で Terminal-Bench を回すと、各タスクに `sessions/agent.log` が残る。skill を読む `sed` コマンドは、そこにそのまま記録されている。

- Quaere: https://github.com/haru0416-dev/quaere
