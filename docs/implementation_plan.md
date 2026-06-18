# Gemini API × ずんだもん音声化機能の設計案

プロンプト（質問）をDiscordで送信し、Gemini APIが考えた回答をずんだもんの音声で読み上げる機能を追加します。

## 概要のフロー
1. ユーザーが `/chat_zundamon プロンプト` のようにコマンドを実行する
2. BotがGemini APIにプロンプトを送信し、回答テキストを生成する（ずんだもん風のプロンプトをシステムプロンプトとして仕込みます）
3. 生成されたテキストをVoicevox APIに送信し、音声ファイル（.wav）を作成する
4. ボイスチャンネルで音声を再生しつつ、テキストチャンネルにも回答の文字を出力する

## User Review Required

> [!IMPORTANT]
> 以下の設計内容について、要望や修正したい箇所があれば教えてほしいのだ！

### 1. 新しいライブラリの追加
Gemini APIを叩くために `google-generativeai` パッケージを使用します。
- `requirements.txt` に追加してDockerを再ビルドする必要があります。

### 2. 環境変数（.env）の追加
Gemini APIにアクセスするためのAPIキーが必要になります。
- `GEMINI_API_KEY=あなたのGemini APIキー` を追加します。

### 3. コマンドの実装場所と名前
既存の `voicevox_cog.py` の中に、新しく以下のようなコマンドを追加するのはどうなのだ？
- コマンド名: `/chat_zundamon` または `/ask_zunda`
- 引数: `prompt` (質問内容)

### 4. Geminiへの「キャラクター設定（システムプロンプト）」
設定をコードに直書きするのではなく、新しく `gemini.md` というファイルを作成し、そこにキャラクター設定や文字数制限などの制約事項をまとめます。
プログラム実行時にこのMarkdownファイルを読み込んで、Gemini APIのシステムプロンプトとして渡すようにします。

## Open Questions

> [!QUESTION]
> 1. コマンドの名前は `/chat_zundamon` などで良いのだ？他に希望はあるのだ？
> 2. Geminiの回答は、音声だけじゃなくて文字（テキスト）としてもDiscordのチャットに送信した方が良いのだ？
> 3. もし長文すぎる回答が返ってくると音声生成に時間がかかるから、Geminiへの指示で「100文字以内で答えて」のように制限をかけた方が良いのだ？

## Proposed Changes

### [Timmer/gemini.md]
#### [NEW] gemini.md
- ずんだもんのキャラクター設定や回答の制約事項を記述する設定ファイル

### [Timmer/voicevox_cog.py]
#### [MODIFY] voicevox_cog.py
- `google.generativeai` のimport追加
- `gemini.md` を読み込む処理の追加
- 新しいスラッシュコマンド `chat_zundamon` メソッドを追加
- （※ Geminiの回答生成と音声生成で3秒以上かかる可能性が高いため、`interaction.response.defer()` を使ってタイムアウトを回避する処理を入れます）

### [requirements.txt]
#### [MODIFY] requirements.txt
- `google-generativeai` パッケージを追記

### [.env (ユーザー側での作業)]
#### [MODIFY] .env
- `GEMINI_API_KEY` をユーザーに追加してもらう

## Verification Plan

### Manual Verification
1. `.env` に `GEMINI_API_KEY` を設定し、Dockerコンテナを再ビルドして起動する
2. ボイスチャンネルに入った状態で `/chat_zundamon おはよう` と打つ
3. 3秒以上の処理時間がかかってもエラーにならず、Botがテキストで回答を返しつつ、ボイスチャンネルでずんだもんが回答を読み上げるか確認する
