# DiscordWorkLogger
Discordのスラッシュコマンドで出退勤を記録できる勤怠管理Botと、作業用タイマーBotのアプリケーション。
Discord Bot(discord.py)とAPIサーバー(FastAPI)、データベース(MySQL)をDockerで動かしている。

## 作成の経緯
勤務先ではDiscordで連絡を取っており、アルバイトの人は出退勤の時刻をスプレッドシートに手入力して記録していた。
出退勤時にはDiscordで挨拶をしていたので、挨拶のついでにワンクリックで出退勤を記録できるようにしようと考えた。
まずdiscord.pyの使い方を学ぶために作業用タイマーを作り、その後に出退勤記録の機能を開発している。

詳細な要件は[Timer_Product_Requirements_Document.md](./Timer_Product_Requirements_Document.md)に記載している。

## 主な機能
* **作業用タイマー**: 分単位のタイマー、一時停止・再開・停止、ポモドーロタイマー
* **ユーザー登録**: DiscordのユーザーIDと名前をDBに登録し、登録した名前を確認できる
* **出勤記録**: コマンドを実行した時刻を出勤時刻としてDBに記録する

## 使用技術
| 分類 | 技術 |
| --- | --- |
| 言語 | Python 3.13 |
| Bot | discord.py 2.7 |
| API | FastAPI / Uvicorn / Pydantic v2 |
| DB | MySQL 8.0 / SQLAlchemy 2.0 / phpMyAdmin |
| インフラ | Docker / Docker Compose |

## 構成
```mermaid
flowchart LR
    User[ユーザー] -->|スラッシュコマンド| Discord
    Discord <--> Bot[Discord Bot<br>timer/]
    Bot -->|HTTP| API[APIサーバー<br>FastAPI]
    API --> DB[(MySQL)]
    PMA[phpMyAdmin] --> DB
```

| ディレクトリ・ファイル | 内容 |
| --- | --- |
| `timer/` | Discord Bot本体。機能ごとにCogとして分割 |
| `timer/main.py` | Botの起動処理とCogの登録 |
| `timer/timer.py` | タイマー機能 |
| `timer/register_cog.py` | ユーザー登録機能 |
| `timer/time_stamp_cog.py` | 出勤記録機能 |
| `from_discord.py` | APIのエンドポイント定義 |
| `crud.py` | DBの読み書き処理 |
| `models.py` | テーブル定義(SQLAlchemy) |
| `schemas.py` | リクエストの型定義(Pydantic) |
| `docs/` | フローチャートやシーケンス図などの設計資料 |

---

# 環境構築
DockerとDocker Composeを使用する。

## Docker Desktopのインストール
[Docker Desktop](https://www.docker.com/products/docker-desktop/)をダウンロードしてインストールする。

1. `$docker -v` :インストール確認
2. `$docker compose version` :Docker Composeのインストール確認

## Discord Botの作成
1. [Discord Developer Portal](https://discord.com/developers/applications)でアプリケーションを作成する
2. 「Bot」のページでトークンを発行する
3. 同じページの「Privileged Gateway Intents」で`MESSAGE CONTENT INTENT`を有効にする
4. 「OAuth2」のページで`bot`と`applications.commands`のスコープを選び、発行したURLからBotをサーバーに招待する

## 環境変数の設定
プロジェクト直下に`.env`を作成し、下記の値を設定する。

| 変数名 | 内容 |
| --- | --- |
| `ENV` | `prod`で本番環境、それ以外で開発環境として起動する |
| `TARGET_TOKEN` | 本番環境で使用するBotのトークン |
| `TARGET_GUILD_ID` | 本番環境で使用するサーバーのID |
| `TEST_TOKEN` | 開発環境で使用するBotのトークン |
| `TEST_GUILD_ID` | 開発環境で使用するサーバーのID |
| `API_BASE_URL` | BotからアクセスするAPIサーバーのURL |
| `MYSQL_HOST` | MySQLのホスト名 |
| `MYSQL_ROOT_PASSWORD` | MySQLのrootパスワード |
| `MYSQL_DATABASE` | 使用するデータベース名 |
| `MYSQL_USER` | MySQLのユーザー名 |
| `MYSQL_PASSWORD` | MySQLのパスワード |

※ `.env`はGitの管理対象外にしているため、トークンやパスワードをコミットしないように注意する。

---

# アプリケーションの実行

## APIサーバーとDBの起動
`$docker compose up -d`

起動すると下記のサービスが立ち上がる。

| サービス | URL |
| --- | --- |
| APIサーバー | `http://localhost:8000` |
| APIドキュメント(Swagger UI) | `http://localhost:8000/docs` |
| phpMyAdmin | `http://localhost:8080` |
| MySQL | `localhost:3306` |

テーブルはAPIサーバーの起動時に`models.py`の定義から自動で作成される。

## Discord Botの起動
1. `$docker build -f Dockerfile.timer -t timer .` :イメージの作成
2. `$docker create --env-file .env -v $(pwd):/app --name timer timer` :コンテナの作成
3. `$docker start timer` :コンテナの起動

※ 作り直す場合は`$docker rm -f timer`で古いコンテナを削除してから2.を実行する。
※ `requirements.txt`を変更した場合は1.からやり直す。

## ログの確認
* `$docker logs timer` :Botのログを全て表示
* `$docker logs -f timer` :Botのログをリアルタイムで表示
* `$docker compose logs -f api` :APIサーバーのログをリアルタイムで表示

# コマンド一覧
| コマンド | 内容 |
| --- | --- |
| `/timer {minutes}` | 指定した分数のタイマーをセットする |
| `/pausetimer` | タイマーを一時停止する |
| `/resume_timer` | タイマーを再開する |
| `/stoptimer` | タイマーを停止する |
| `/showtimer` | タイマーの残り時間を表示する |
| `/pomodorotimer {sets}` | ポモドーロタイマーをセットする(デフォルトは4セット) |
| `/register {name}` | 名前を登録する |
| `/myname` | 登録した名前を確認する |
| `/start_work` | 出勤を記録する |

# API一覧
| メソッド | パス | 内容 |
| --- | --- | --- |
| POST | `/register_member` | メンバーを登録する。IDか名前が重複している場合は409を返す |
| POST | `/get_name` | ユーザーIDから登録名を取得する。未登録の場合は409を返す |
| POST | `/create_clock_in` | 出勤時刻を記録する |
| POST | `/update_clock_out` | 退勤時刻を記録する |

# DB設計
| テーブル | 内容 |
| --- | --- |
| `Member_table` | メンバーのユーザーID、名前、登録日、退職日 |
| `attendance_records` | 1回の出退勤。1行で1回分の出勤時刻と退勤時刻を管理する |
| `monthly_summary` | 1ヶ月分の総労働時間と出勤回数(集計処理は未実装) |

# 設計資料
* [start_workのフローチャート](./docs/flowchart.md)
* [start_workのシーケンス図](./docs/start_work_sequence_diagram.md)
* [ユーザー登録のシーケンス図](./docs/user_registration_sequence.md)

---

# 開発環境での起動
`.env`の`ENV`を`prod`以外にすると開発環境として起動する。

* `TEST_TOKEN`と`TEST_GUILD_ID`のBotとサーバーが使われる
* コマンド名の末尾に`_test`が付く(例: `/timer_test`)
* Botのステータスが「test」になる

これによって、本番環境のBotと同じサーバーに入れてもコマンドが重複しない。

# プロジェクトの運用

## コミットメッセージ
`{type}: {目的}のため、{変更内容}`の形式で書く。

(例)`feat: 出勤記録をAPIで処理するため、start_workコマンドに通信処理を追加`

| type | 内容 |
| --- | --- |
| `feat` | 機能の追加 |
| `fix` | 不具合の修正 |
| `refactor` | 動作を変えないコードの整理 |
| `docs` | ドキュメントの追加・修正 |
| `chore` | 設定ファイルなど、上記以外の変更 |

# 今後の予定
* 退勤を記録するコマンドの追加(APIは実装済み)
* 月ごとの労働時間の集計
* テストコードの導入
