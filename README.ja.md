# Quaere

> 動く前にまず問わせる、コーディングエージェント向けスキル集。

[![CI](https://github.com/haru0416-dev/quaere/actions/workflows/ci.yml/badge.svg)](https://github.com/haru0416-dev/quaere/actions/workflows/ci.yml)
[![Latest release](https://img.shields.io/github/v/release/haru0416-dev/quaere?label=release&color=6b3fa0)](https://github.com/haru0416-dev/quaere/releases/latest)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

```bash
curl -fsSL https://quaere.dev/install.sh | sh
```

[なぜ Quaere](#なぜ-quaere) · [スキル](#スキル) · [選び方](#選び方) · [インストール](#インストール) · [動作確認](#動作確認) · [quaere.dev](https://quaere.dev/)

これは [README.md](README.md) の日本語版。原文は英語、こちらは日本語で読みたい人向けの翻訳。

## なぜ Quaere

コーディングエージェントは、似たような場所で何度も同じズレ方をする。

- コードを読み流す
- もっともらしい主張を裏取りなしに受け入れる
- 見直されないままの大きな差分を出す
- 確認なしにコミットする

Quaere は、それぞれの地点で速度を一段落とすための五つのスキルからなる。手続きを増やすのではない。「主張する → 根拠で守る → そこではじめて動く」という一手を毎回挟ませる、それだけ。

名前はラテン語の *quaere* — 「問う、求める、突きつめる」 — から取った。どのスキルも同じゲートを強制する。

### 効果測定

最新の sweep は **v0.3.1**。v0.3.0 / v0.3.1 は CLI / インストール / リリース基盤に手を入れた版で、スキル本体は据え置き。だからこの数字はそのままシップ済みスキルの効きを表す。

**v0.3.1** — 18 シナリオ・106 個の決定論的アサーション、Codex CLI (OAuth Codex) で 1 回走らせた結果:

| モード | アサーション通過率 | シナリオ単位 |
| --- | ---: | ---: |
| Baseline (スキルなし) | 53% (56 / 106) | 0 / 18 pass |
| **with-skill** | **91% (96 / 106)** | **10 / 18 pass** |
| Δ | **+37.7 pp** | **+10 シナリオ** |

v0.2.1 の `+27 pp` (97 アサーション) から、敵対系アサーションを増やしたうえで差が広がっている。シナリオ通過数も初めて非ゼロ域に乗った。

別軸として Terminal-Bench (`terminal-bench-core==0.1.1`、80 タスク、v0.3.2 インストールパイプライン) も回した: baseline 51.25% → with-skill 52.50% (**Δ +1.25 pp**)。誤差レンジに収まる薄い positive で、勝ったというより「Quaere は Terminal-Bench で足を引っ張らない」と読むのが正直。タスク別の内訳は [`docs/evaluation.md`](docs/evaluation.md)。

eval ハーネスの使い方は [`evals/README.md`](evals/README.md) に集約してある。

## スキル

| スキル | こういうときに使う | 主なガード |
| --- | --- | --- |
| [`skills/quaere-semantic`](skills/quaere-semantic/SKILL.md) | 触る前にコードの意図・不変条件・「なぜこの形なのか」を把握したい | 単位ごとに `What / Why / Invariants / Failure / Connections` を埋めさせ、わからない箇所は「分からない」と明示させる |
| [`skills/quaere-grounding`](skills/quaere-grounding/SKILL.md) | SDK、API、CLI、クラウド、リリースノートなど、バージョンに敏感な外部事実が絡む | ローカル版を起点に source の質と version-fit を見て、確認できた事実だけを実装制約に昇格させる |
| [`skills/quaere-evidence`](skills/quaere-evidence/SKILL.md) | 不明な不具合、リスクのある PR レビュー、CI 失敗、flaky テスト、外部 API の挙動など、根拠なしには手を入れたくない | finding → 仮説 / Review Claim → 防御 → 反証プローブ → 判断 → 検証 の順を踏ませる |
| [`skills/quaere-execution`](skills/quaere-execution/SKILL.md) | 承認済みの多段実装を進める、計画を反映する、レビュー指摘を片付ける | `read → plan → execute → review → fix → verify → commit` を一周させ、commit は明示の承認があるときに限る |
| [`skills/quaere-audit`](skills/quaere-audit/SKILL.md) | 深いセキュリティ監査、バグバウンティ準備、プロトコル準拠の確認、攻撃可能性の検証 | セキュリティプロパティを先に出し、攻撃面と実装を対応づけ、false-positive のゲートを通したものだけを `confirmed` / `potential` として報告する |

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
- 単発の修正ではなく性質と攻撃面から脆弱性を見つけ出す作業なら `quaere-audit`。必要に応じて内部で他の四つを呼び分ける。

小さな変更なら `quaere-execution` の軽量モードで足りる。コードを読むだけの仕事は `quaere-semantic` で完結する。

### 単独で選ぶ: 主なリスクで決める

タスクの「主なリスク」が何かで決める。最初に当てはまった行のスキルから入る:

| 主なリスク | 最初に使う | 続けて使う |
| --- | --- | --- |
| 既存コードの意図や不変条件が不明 | `quaere-semantic` | 必要な不変条件が掴めてから `quaere-execution` |
| 答えが現行 SDK / API / CLI / クラウドの挙動に依存する | `quaere-grounding` | 確認済み制約だけで `quaere-execution`、または食い違いがあれば `quaere-evidence` |
| バグの原因、CI 失敗、flaky、レビュー指摘が本物か怪しい | `quaere-evidence` | 主張・仮説が confirmed になってから `quaere-execution` |
| 計画は承認済みで、実装が主作業 | `quaere-execution` | 途中で原因不明や危険な状況に転じたら `quaere-evidence` |
| 仕様と攻撃面から脆弱性を発見・検証する | `quaere-audit` | 内部で他の四つを必要に応じて呼び分ける |

### 迷ったときの分かれ目

二つで迷ったら、「いま答えるべき問い」が何かで選ぶ:

- 「このコードは何をしているのか？」 → `quaere-semantic`
- 「この外部事実は、このバージョンでも本当か？」 → `quaere-grounding`
- 「この主張は実際に証明されているのか？」 → `quaere-evidence`
- 「ファイルを書き換えていい段階か？」 → `quaere-execution`
- 「どんなセキュリティ性質が壊れうるか？」 → `quaere-audit`

## インストール

### curl ワンライナー (推奨)

```bash
curl -fsSL https://quaere.dev/install.sh | sh
```

取得、`SHA256SUMS` の cosign keyless OIDC 署名検証 (リリースワークフローの identity に bind 済み)、署名済み `SHA256SUMS` を使った tar.gz のチェックサム検証、`$HOME/.local/bin/quaere` への配置、`quaere install all` によるスキル展開、利用可能コマンドの表示までを一括で行う。

**前提: `cosign`** — `brew install cosign`、`apt install cosign` (Debian 13+ / Ubuntu 24.04+)、または <https://docs.sigstore.dev/cosign/system_config/installation/> を参照。v0.3.2 以降の release は必須。それ以前のタグを使うなら `cargo install quaere-cli --version <X.Y.Z>` を選ぶ。

環境変数で上書きできる項目: `QUAERE_VERSION` (タグ固定)、`QUAERE_REPO` (fork から取得)、`QUAERE_INSTALL_DIR` (バイナリの配置先)、`QUAERE_SKILLS=0` (スキル展開のスキップ)。

### cargo install (Rust 環境がある場合)

```bash
cargo install quaere-cli
quaere install all
```

二つ目で内蔵スキルを Claude Code と Codex の両方に展開する。

### Homebrew

```bash
brew install haru0416-dev/quaere/quaere
quaere install all
```

formula は専用 tap リポジトリ [`haru0416-dev/homebrew-quaere`](https://github.com/haru0416-dev/homebrew-quaere) にある。curl インストーラと同じ release tarball を取得し、`SHA256SUMS` と照合する。`quaere install all` でスキル本体を両エージェントに展開する。

### 手動 (ソース取得)

```bash
git clone https://github.com/haru0416-dev/quaere.git
cd quaere
mkdir -p ~/.claude/skills
cp -R skills/quaere-* ~/.claude/skills/
```

各スキルは SKILL.md を含むディレクトリで、frontmatter の `name` がディレクトリ名と一致する。

## 動作確認

```bash
quaere list      # インストール済みスキルと記録済みバージョンを表示
quaere doctor    # frontmatter / 名前 / 行数バジェット / オーファン検査
quaere update    # GitHub に新しい release があるか確認
quaere version   # CLI バージョンを表示
```

バージョンごとの変更履歴は [`CHANGELOG.md`](CHANGELOG.md) を見る。`Unreleased` セクションが次に出る分。

### CLI の挙動契約

CLI は以下の挙動を持つ (Python validator `scripts/validate_skills.py` と Rust の `quaere doctor` は `tests/test_validator_parity.py` で同等性を担保、CI の `parity` ジョブで実行):

- **`quaere install` は累積的**。同じ `--target` に対して `--skill quaere-semantic` → `--skill quaere-audit` の順で流せば、両方が manifest に蓄積する。manifest は (既存スキル ∪ 今回追加 ∪ 既存重複) の和集合として整合し、エントリーの並び順は毎回同じになるので diff が揺れない。
- **`quaere install --force` はスキル単位でアトミック**。新内容を `<target>/.<name>.staging` に展開、既存 dest を `<target>/.<name>.backup` に rename、staging を dest にスワップしてから backup を削除する。途中の I/O 失敗があっても、dest は前の状態のまま残る。クラッシュで残った `.staging` / `.backup` は `quaere doctor` のオーファン方針で黙って無視され、次回 install で回収される。
- **未知の `--skill` 名は早期に弾く**。`--skill quaere-semantik` のようなタイポは、書き込みが起きる前に有効なスキル一覧と一緒に拒否される。部分インストールには落ちない。
- **`quaere doctor` のオーファン方針**。manifest にないディレクトリはオーファンとして報告する。名前が `quaere-` で始まるなら error、それ以外は情報扱い。他のスキル管理ツールと install target を共有してもよい設計。
- **`quaere update` は semver で比較**する。`X.Y.Z` 形ならセマンティック比較、片方がパースできない場合は文字列比較にフォールバックする。バイナリを書き換えることはなく、上書き手順を表示するだけ。
- **デフォルトの `--repo` は `haru0416-dev/quaere`**。fork を追っているなら `quaere update --repo your-fork/quaere` で差し替える。`scripts/install.sh` は環境変数 `QUAERE_REPO` で同じことができる。

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

in-tree のハーネスは `evals/` にある。PR ごとに回すには十分軽く、判定がぶれない部分は確実に通すように作ってある。[効果測定](#効果測定)の数字は Codex CLI 経由で走らせた結果で、同じシナリオは Claude Code でも同程度の数字を出す。

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

frontmatter、ディレクトリ・名前の整合、README カバレッジ、行数バジェット、`.agent-state/` の混入をまとめて検査する。push と PR の都度、GitHub Actions が同じ検証 + Rust 側の `quaere doctor` parity check を流す。

`cli/` 配下を触る場合は commit 前に `cargo fmt --manifest-path cli/Cargo.toml` / `cargo build` / `cargo test` を回す。CI の `fmt` ゲートは厳しい。

## ライセンス

MIT。詳細は [`LICENSE`](LICENSE) を参照。
