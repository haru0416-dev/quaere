# Quaere

> 動く前にまず問わせる、コーディングエージェント向けスキル集。

[![CI](https://github.com/haru0416-dev/quaere/actions/workflows/ci.yml/badge.svg)](https://github.com/haru0416-dev/quaere/actions/workflows/ci.yml)
[![Latest release](https://img.shields.io/github/v/release/haru0416-dev/quaere?label=release&color=6b3fa0)](https://github.com/haru0416-dev/quaere/releases/latest)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

これは [README.md](README.md) の日本語版。原文は英語、こちらは日本語で読みたい人向けの翻訳。

コーディングエージェントは「分からない」と言って失敗しない。仕上がる前に仕上がったような声で失敗する ─ コードを読み流し、もっともらしい主張を裏取りなしに受け入れ、広い差分を出し、原因が証明される前に成功宣言する。

Quaere は Claude Code、Codex CLI、その他 skill 機構を持つコーディングエージェント向けの [skill](https://docs.claude.com/en/docs/claude-code/skills) 集で、コア 4 つと任意で入れる拡張 5 つから成る。skill はタスクに応じてエージェント自身が読み込む markdown ファイルで、コアの 4 つはそれぞれ別の drift point を塞ぐ ─ コードを意味で読む / 外部事実を ground する / 主張を証明する / 変更を小さく検証しながら実行する。拡張はその上にセキュリティ監査・発想の発散・ネーミング・0→1 の起案・コミット前の敵対的詰問を足す。

> Quaere は独立プロジェクトで、Anthropic とは無関係。Claude Code / Codex CLI が組み込みで持つ skill システムを介して動く。

名前はラテン語の *quaere* — 「問う、求める、突きつめる」 — から取った。手続きを増やすのではなく、「主張する → 根拠で守る → そこではじめて動く」という一手をドリフトの起きやすい地点で挟ませる、それだけ。

```text
Quaere なし: もっともらしい主張 → 広い差分 → 部分的なテスト → 自信ありげな要約
Quaere あり: 主張 → 根拠 → 反証プローブ → 絞った差分 → 検証済みの差分
```

v0.3.1 時点の in-tree eval sweep では、同じシナリオがスキルなしで **53%**、スキルありで **91%** のアサーション通過率だった。外部ベンチマークの代わりではなく、Quaere が狙う失敗モードに対する回帰ハーネス。

[効果測定](#効果測定) · [スキル](#スキル) · [選び方](#選び方) · [インストール](#インストール) · [動作確認](#動作確認) · [quaere.dev](https://quaere.dev/) · [English](README.md)

## 効果測定

ヘッドラインは v0.3.1 時点の skill セットに対する in-tree eval sweep。skill 本体は測定後に変わっている ── v0.5.0 で Codex の read cap に合わせて全スキルを再構成し、その後の未リリースコミットで `quaere-naming`・`quaere-prospect`・`quaere-crucible` 拡張の追加、`quaere-semantic` の実測コアへの蒸留、certainty ラベル (`confident` / `locally novel`) のプローブ必須化が入った。公開済みの sweep の数字はこれらの変更より前の測定:

| モード | アサーション通過率 | シナリオ単位 |
| --- | ---: | ---: |
| Baseline (スキルなし) | 53% (56 / 106) | 0 / 18 pass |
| **with-skill** | **91% (96 / 106)** | **10 / 18 pass** |
| Δ | **+37.7 pp** | **+10 シナリオ** |

測定は v0.3.1 時点、18 シナリオ / 106 アサーションのスイートで行った。スイートはその後 22 シナリオ / 125 アサーションに増えている。測定の注記は [`docs/evaluation.md`](docs/evaluation.md) を参照。

別軸として Terminal-Bench (`terminal-bench-core==0.1.1`、v0.3.2 インストールパイプライン) も回した。数字は 2 通りの cut で報告する:

- **80 タスク全体で +1.25 pp** (41/80 → 42/80、51.25% → 52.50%)。run-to-run variance 圏内、「悪化はしない」と読むのが正直。
- **インストールパイプラインが壊れなかった 69 タスクで +8.7 pp** (52.2% → 60.9%)。残り 11 タスクは skill が load される前に install で失敗していて、skill の効きとは無関係。

per-category cut は clean 69 タスク subset から取った。カテゴリごとのサンプルが小さい (n = 3〜10) ので、suggestive 扱いに留めて confirmed effect とは見ない: data-processing +60 pp、SWE-bench 系 +25 pp、security +22 pp、build/compile +17 pp、ML/AI −10 pp、残り 5 カテゴリは ~0。タスク別の内訳は [`docs/evaluation.md`](docs/evaluation.md)。

eval ハーネスの使い方は [`evals/README.md`](evals/README.md) に集約してある。

### 1 つのタスクで見ると

Terminal-Bench の `csv-to-parquet` — *「`/app/data.csv` を `/app/data.parquet` に変換する」* — は recovered タスク (baseline ✗ → with-skill ✓)。同じモデル、同じタスクで 2 回走らせた結果。

**Baseline (test_data_matches: failed)**

> CSV は小さくて単純。Node/npm が見つかったので、一時的な Node パッケージで処理する… *[npm が `parquetjs-lite` を install、CSV パーサーと型推定を手書きで起こしてファイル出力]*
>
> `/app/data.csv` を `/app/data.parquet` に変換完了。読み戻し確認済: 5 行、columns: name, age, city、最初の行: John, 25, New York…

エージェントは自分が書いたファイルを自分が書いたライブラリで読み戻し、自分と整合していることを根拠に成功宣言した。Terminal-Bench の test は canonical な Parquet reader でデコードするので、そちらは同意しなかった。

**With skill (test_data_matches: passed)**

> 構造化された CSV reader と Parquet writer で変換し、出力ファイルが存在して読み戻せるかを確認する。*[`python3-venv` を bootstrap、`pyarrow` を install、`pyarrow.csv` で読み、`pyarrow.parquet.write_table` で書き、`pq.read_table` で読み戻し]*
>
> `/app/data.csv` を `/app/data.parquet` に変換完了。Parquet ファイルが読み戻せることを確認: 5 行、3 columns: name, age, city。

変わったのは 2 点。最初の発話で書く前に検証ステップを置く (*「出力ファイルが存在して読み戻せるかを確認する」*) こと、そして検証に canonical なライブラリ (`pyarrow`) ─ Terminal-Bench の test が同意するもの ─ を使っていること。自分の出力を自分の writer で読み戻す自己充足にはなっていない。これが skill 設計の意図: 検証可能な claim を出し、第三者の判定に耐える検証を走らせ、通らなければ止まる。

## スキル

Quaere は **コア 4 スキル** と、任意で入れる **拡張** に分かれている。`quaere install`
はコアだけを入れ、拡張は要求したときだけ入る (`quaere install --extensions`、
または `quaere install --skill <名前>`)。

### コア (既定でインストール)

| スキル | こういうときに使う | 主なガード |
| --- | --- | --- |
| [`skills/core/quaere-semantic`](skills/core/quaere-semantic/SKILL.md) | 触る前にコードの意図・不変条件・「なぜこの形なのか」を把握したい | 単位ごとに `What (mechanical) / What (domain intent) / Why / Invariants / Failure / Connections (← / →)` を埋めさせ、わからない箇所は「分からない」と明示させる |
| [`skills/core/quaere-grounding`](skills/core/quaere-grounding/SKILL.md) | SDK、API、CLI、クラウド、リリースノートなど、バージョンに敏感な外部事実が絡む | ローカル版を起点に source の質と version-fit を見て、確認できた事実だけを実装制約に昇格させる |
| [`skills/core/quaere-evidence`](skills/core/quaere-evidence/SKILL.md) | 不明な不具合、リスクのある PR レビュー、CI 失敗、flaky テスト、外部 API の挙動など、根拠なしには手を入れたくない | finding → 仮説 / Review Claim → 防御 → 反証プローブ → 判断 → 検証 の順を踏ませる |
| [`skills/core/quaere-execution`](skills/core/quaere-execution/SKILL.md) | 承認済みの多段実装を進める、計画を反映する、レビュー指摘を片付ける | `read → plan → execute → review → fix → verify → commit` を一周させ、commit は明示の承認があるときに限る |

### 拡張 (任意)

| スキル | こういうときに使う | 主なガード |
| --- | --- | --- |
| [`skills/extensions/quaere-audit`](skills/extensions/quaere-audit/SKILL.md) | 深いセキュリティ監査、バグバウンティ準備、プロトコル準拠の確認、攻撃可能性の検証 | セキュリティプロパティを先に出し、攻撃面と実装を対応づけ、false-positive のゲートを通したものだけを `confirmed` / `potential` として報告する。`quaere install --skill audit` で導入 |
| [`skills/extensions/quaere-invention`](skills/extensions/quaere-invention/SKILL.md) | 計画を固める前に、非自明な解法・代替アーキ・研究の方向・プロダクト/収益のアイデアが欲しい | 逃げ出す「普通の答え」を先に名指しさせ、構造化した mutation で前提を壊し、novelty を固定ラベルで正直に分類し (「本当に新しい」の自己評価は禁止)、案を昇格させる前に kill-probe を設計させる。`quaere install --skill invention` で導入 |
| [`skills/extensions/quaere-naming`](skills/extensions/quaere-naming/SKILL.md) | プロダクト、SaaS、ブランド、ライブラリ、OSS、CLI、bot、アプリの名前を決めたい、AI スロップ的な凡庸名から抜け出したい | メタファー駆動のプロセスを強制する ── 名前を出す前に naming brief、類語の言い換えではなく概念テリトリーの探索、アンチパターンによる絞り込み、そしてツール検証必須の可用性ゲート (記憶からの判定は禁止)。origin story 付きの検証済みファイナリストだけがユーザーに届く。`quaere install --skill naming` で導入 |
| [`skills/extensions/quaere-prospect`](skills/extensions/quaere-prospect/SKILL.md) | まだ問題が決まっていない段階で、コードベースやドメインに「次に何を作るべきか」(足りない機能・ツール・プロダクト・改善) を決めたい。凡庸なウィッシュリストではなく根拠ある機会が欲しい | 機会ごとに、実システムで実在を検証したギャップ・受益者とその job・(仮定でない) 需要の証拠・検証プローブを名指しさせ、`verified gap` / `assumed gap` / `already covered` / `wishlist` の固定ラベルで分類する (「game-changing」の自己評価は禁止)。`quaere install --skill prospect` で導入 |
| [`skills/extensions/quaere-crucible`](skills/extensions/quaere-crucible/SKILL.md) | コミット前に、計画・主張・設計・決定・PR・自分の理解を敵対的に詰めたい(「grill me」「穴を突いて」「red-team」)、またはエージェントが自分の提案を出荷前に自分で詰めたい | ターゲットを load-bearing な主張に分解し、各主張を falsifier と代替仮説の質問で詰める。新証拠か防御済み反論で生き残る(自信ありげな未検証の反発では折れない)か unresolved gap に記録するまで bless しない。強度は stakes に比例。`quaere install --skill crucible` で導入 |

## 選び方

### 多段作業のパイプライン

複数のスキルを組み合わせるときの標準フロー:

```text
quaere-semantic → quaere-grounding → quaere-evidence → quaere-execution
```

- 既存コードの理解に不安が残るなら、最初に `quaere-semantic`。
- 外部事実が変わっていそうなら `quaere-grounding`。
- 主張や原因仮説、修正案そのものが疑わしいなら `quaere-evidence`。
- 計画が固まってから `quaere-execution` で diff を作る。

小さな変更なら `quaere-execution` の軽量モードで足りる。コードを読むだけの仕事は `quaere-semantic` で完結する。SDK・クラウド API・依存まわりの仕事は `quaere-grounding` から始められる。

性質と攻撃面から脆弱性を見つけ出す深いセキュリティ作業には、`quaere-audit` 拡張を入れる (`quaere install --skill audit`)。必要に応じてコア 4 つを内部で呼び分ける。

明らかな答えに早く収束してしまうのがリスクのとき ── アプローチ・アーキ・研究/プロダクトの方向を、選択肢を広げる前に決めてしまいそうなとき ── は `quaere-invention` 拡張を入れる (`quaere install --skill invention`)。chain では grounding と evidence の間に入る (`semantic → grounding → invention → evidence → execution`)。単発の発想出しなら `invention → evidence` だけでも使える。

さらにその上流 ── どのアプローチかではなく、そもそも何を作るか (問題が決まる前の、足りない機能・ツール・プロダクト) がリスクのとき ── は `quaere-prospect` 拡張を入れる (`quaere install --skill prospect`)。invention の手前に入る (`prospect → invention → grounding/evidence → execution`): prospect が解く価値のあるギャップを見つけ、invention がその非自明な解き方を出す。提示する機会はすべて、検証済みギャップ・受益者・需要の証拠・検証プローブを伴う ── 凡庸なウィッシュリストではない。

コミットの反対側がリスクのとき ── 計画・主張・設計・PR・自分の理解が「堅そう」だが、本気で壊そうとした試練をまだくぐっていないとき ── は `quaere-crucible` 拡張を入れる (`quaere install --skill crucible`)。Quaere 流の「Grill Me」: ターゲットを load-bearing な主張に分解し、最重要主張を falsifier と代替仮説で攻め、各主張が新証拠で生き残る(または unresolved gap に記録される)まで bless しない ── 自信ありげな未検証の反発では折れない。commit 境界、execution の手前に入る。

### 単独で選ぶ: 主なリスクで決める

タスクの「主なリスク」が何かで決める。最初に当てはまった行のスキルから入る:

| 主なリスク | 最初に使う | 続けて使う |
| --- | --- | --- |
| 既存コードの意図や不変条件が不明 | `quaere-semantic` | 必要な不変条件が掴めてから `quaere-execution` |
| 答えが現行 SDK / API / CLI / クラウドの挙動に依存する | `quaere-grounding` | 確認済み制約だけで `quaere-execution`、または食い違いがあれば `quaere-evidence` |
| バグの原因、CI 失敗、flaky、レビュー指摘が本物か怪しい | `quaere-evidence` | 主張・仮説が confirmed になってから `quaere-execution` |
| 計画は承認済みで、実装が主作業 | `quaere-execution` | 途中で原因不明や危険な状況に転じたら `quaere-evidence` |
| 仕様と攻撃面から脆弱性を発見・検証する | `quaere-audit` (拡張) | 内部でコア 4 つを必要に応じて呼び分ける |
| 明らかな解法に飛びつく前に選択肢を広げたい | `quaere-invention` (拡張) | kill-probe 付きで生き残った案を `quaere-grounding` / `quaere-evidence` / `quaere-execution` に渡す |
| まだ問題が決まる前で、何を作るべきかを決めたい。ウィッシュリストではなく根拠あるギャップが欲しい | `quaere-prospect` (拡張) | 検証プローブ付きの verified gap を `quaere-invention` (解き方) / `quaere-grounding` / `quaere-evidence` / `quaere-execution` に渡す |
| 計画・主張・設計・PR が「堅そう」だが本気で壊そうとしていない。今コミットしようとしている | `quaere-crucible` (拡張) | blessed な主張と unresolved-gap リストを `quaere-execution` に、実行プローブが要る挑戦を `quaere-evidence`、別モデルの反論を `cross-check` に渡す |

### 迷ったときの分かれ目

二つで迷ったら、「いま答えるべき問い」が何かで選ぶ:

- 「このコードは何をしているのか？」 → `quaere-semantic`
- 「この外部事実は、このバージョンでも本当か？」 → `quaere-grounding`
- 「この主張は実際に証明されているのか？」 → `quaere-evidence`
- 「ファイルを書き換えていい段階か？」 → `quaere-execution`
- 「どんなセキュリティ性質が壊れうるか？」 → `quaere-audit`
- 「明らかな解法の空間に閉じ込められていないか？」 → `quaere-invention`
- 「そもそもここで何を作る価値があるのか？」 → `quaere-prospect`
- 「コミット前に、これは本気の詰問に耐えるか？」 → `quaere-crucible`

## インストール

Quaere は npm パッケージ `quaere-cli` として公開している。CLI の仕事はスキルファイルを `~/.claude/skills/` と `~/.agents/skills/` にコピーするだけなので、グローバルに置かず zero-install で動かして問題ない。

```bash
npx quaere-cli install
```

存在しているエージェント (Claude Code / Codex CLI) を自動検出して、見つかった全てに展開する。範囲を指定したいときはターゲットを渡す:

```bash
npx quaere-cli install claude     # Claude Code のみ
npx quaere-cli install codex      # Codex CLI のみ
npx quaere-cli install all        # 両方
```

### Bun

```bash
bunx quaere-cli install
```

### グローバルインストール

PATH に常駐させたい場合:

```bash
npm install -g quaere-cli
quaere install                    # `quaere` の別名でも起動できる
```

## 動作確認

```bash
npx quaere-cli list               # インストール済みスキルと記録済みバージョンを表示
npx quaere-cli doctor             # frontmatter / 名前 / 行数バジェット / オーファン検査
npx quaere-cli update             # GitHub Releases に新しい版があるか確認
```

グローバルインストール済みなら `npx quaere-cli` を `quaere` に置き換えてよい。

リリースは npm provenance attestation (Sigstore OIDC) 付きで公開される。tarball が `release.yml` の正しいタグから生成されたことは `npm audit signatures` で依存ツリーごとまとめて検証できる。

バージョンごとの変更履歴は [`CHANGELOG.md`](CHANGELOG.md)。`Unreleased` セクションが次に出る分。

### CLI の挙動契約

`quaere-cli install` / `update` / `doctor` の挙動を以下に固定する。Python validator `scripts/validate_skills.py` は frontmatter / name / 行数の不変条件を CI で検査する:

- **`quaere-cli install` は対象自動検出**。位置引数なしで実行すると `~/.claude/` / `~/.agents/` の存在を見て両方に配置する。`claude` / `codex` / `all` を位置引数で渡せば対象を固定できる。
- **`quaere-cli install` は累積的かつ冪等**。バンドル済みスキル全てを target manifest に展開する。既に同じ version がインストール済みの target に再実行しても no-op (`<target>/.quaere/manifest.json` の version 一致を見て判定)。再インストールしたい場合は `--force` を渡す。manifest は他のスキル管理ツールが書き込んだエントリーも含めた union として保たれ、並び順は毎回ソート済み。
- **スキル単位の install は atomic**。新内容を `<target>/.<name>.staging` に展開、既存 dest を `<target>/.<name>.backup` に rename、staging を dest にスワップしてから backup を削除する。途中の I/O 失敗があっても、dest は前の完全な状態のまま残る。クラッシュで残った `.staging` / `.backup` は `quaere-cli doctor` のオーファン方針で黙って無視され、次回 install で回収される。
- **`quaere-cli update` は何も書き換えない**。`haru0416-dev/quaere` の latest release を GitHub Releases API で取得し、semver で比較 (`X.Y.Z` 形ならセマンティック、片方が parse 不能なら文字列フォールバック) してアップグレード手順を出力するだけ。バイナリも installed skills も触らない。
- **`quaere-cli doctor` のオーファン方針**。manifest にないディレクトリはオーファンとして報告する。名前が `quaere-` で始まるなら error、それ以外は情報扱い。他のスキル管理ツールと install target を共有してもよい設計。

## 使用例

`examples/` に現実的なプロンプトと、それに対する期待される振る舞いの例を置いている。

すぐ思いつくところでは:

- 「このモジュールを読んで、変更前に意図を説明して」 → `quaere-semantic`
- 「変更を提案する前に、インストール済みの SDK 版と現行ドキュメントを確認して」 → `quaere-grounding`
- 「この CI 失敗は flaky に見える。レビュー指摘が実在するか確かめてからパッチを当てて」 → `quaere-evidence`
- 「この計画通りに進めて、テストを走らせ、diff をレビューして、通ったらコミットして」 → `quaere-execution`
- 「このプロトコル実装を仕様と突き合わせて、confirmed か potential な脆弱性を根拠つきで挙げて」 → `quaere-audit`

## 安全側の取り決め

- コミットは明示の承認があるときだけ実行する。
- `.agent-state/` はローカルの調査メモで、明示的に成果物として求められない限りコミットしない。
- リスクが高い作業では、手早く片付きそうなパッチに飛びつかず、根拠の確保と反証プローブを優先する。

## スキル評価

in-tree のハーネスは `evals/` にある。PR ごとに回すには十分軽く、判定がぶれない部分は確実に通すように作ってある。[効果測定](#効果測定)の数字は Codex CLI 経由で走らせた結果。

シナリオを 1 つだけ流す例:

```bash
python evals/run_skill_evals.py \
  --runner 'codex=codex exec - < $prompt_file' \
  --scenario sdk-version-grounding \
  --mode both \
  --output-dir "$(pwd)/eval-results/$(date -u +%Y%m%dT%H%M%SZ)"
```

アサーション種別の一覧、3 つの `llm_judge` バックエンド (Anthropic SDK / openai-compat / Codex CLI)、ロケール選言の仕組み、Terminal-Bench アダプタの詳細は [`evals/README.md`](evals/README.md) を参照。

## 外部ベンチマーク (Roadmap)

in-tree eval は第三者検証の代わりにはならない。優先順位つきで以下の 4 つを次フェーズ以降の組み込み候補としている。

1. **[Terminal-Bench v2](https://www.tbench.ai/)** — 公開 leaderboard の対象は `terminal-bench-core` v0.1.1 の 80 タスク (より広いプールには 241 タスクある)。SWE / セキュリティ / データ / sysadmin。`quaere-execution` と `quaere-grounding` の領域そのもので、最も Δ が出やすい想定。**v0.3.0 でアダプタをリリース済み**。[`evals/terminal_bench/`](evals/terminal_bench/) に Codex CLI を wrap した 2 つのエージェント (`quaere-tb-codex-baseline` / `quaere-tb-codex-with-skill`) と manual-trigger CI workflow を同梱している。smoke / full / leaderboard の 3 フェーズはアダプタ README 参照。
2. **[SWE-bench Verified](https://www.swebench.com/)** — 人手で正解確認された 500 個の GitHub issue パッチ。コーディングエージェント界隈の信頼度の基準。いずれは避けて通れない。eval host に ≥ 120 GB ストレージ・16 GB RAM・8 CPU と API 予算が要る。v1.0 ターゲット。
3. **[SkillsBench](https://www.skillsbench.ai/)** — 3D / ロボティクス / セキュリティ PCAP / エネルギーなど 84 個のドメインスキルタスク。提出単位は「スキルを使うエージェント」。ドメイン色が濃いぶん、Quaere のプロセス補正は Δ が小さく出る可能性が高い。追跡だけ。
4. **SWE-Bench Pro** — Verified の後継。難度が一段上がる。Verified を通してから検討。

Quaere の主張は「プロセス補正がエージェントの熟考の質を底上げする」というもの。Terminal-Bench はこの主張を直接、SWE-bench Verified は長文パッチ生成への汎化を間接的に検証する。どちらの数字も出るまで、公開できる根拠は上の in-tree eval だけ。

## コントリビュート

変更を公開する前にローカル検証を走らせる:

```bash
python scripts/validate_skills.py
```

frontmatter、ディレクトリ・名前の整合、README / README.ja カバレッジ、Codex read cap 内のアンカー位置、行数バジェット、参照リンクの解決、`.agent-state/` の混入をまとめて検査する。push と PR の都度、GitHub Actions が同じ検証を流す。

`cli/` (npm パッケージ) を触る場合は commit 前にローカルチェックを回す:

```bash
cd cli
pnpm install --frozen-lockfile
pnpm check                        # oxlint + tsc --noEmit + vitest
```

CI も publish 前に同じパイプラインを走らせるので、ここで落ちるとリリースは進まない。

## ライセンス

MIT。詳細は [`LICENSE`](LICENSE) を参照。
