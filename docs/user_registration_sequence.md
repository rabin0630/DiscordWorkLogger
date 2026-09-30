# ユーザー登録のシーケンス設計

ユーザーがDiscord上で自分の名前とIDを登録する際の流れ（シーケンス図）なのだ。

## シーケンス図

```mermaid
sequenceDiagram
    autonumber
    actor User as Discordユーザー
    participant Bot as Discord Bot
    participant API as FastAPI (routers/members.py)
    participant DB as データベース (crud/members.py / models.py)

    User->>Bot: スラッシュコマンド実行（例: /register）
    note over User, Bot: ユーザーID（19980630）や名前が自動でBotに渡る
    
    Bot->>API: HTTP POSTリクエスト<br/>(user_id, nameを送信)
    
    API->>API: データのバリデーション<br/>(schemas.pyで型チェック)
    
    API->>DB: 登録処理の呼び出し<br/>(crud/members.pyでMemberテーブルに追加・更新)
    
    DB-->>API: 登録完了
    
    API-->>Bot: HTTP 200 OK（成功レスポンス）
    
    Bot-->>User: 「登録が完了したのだ！」とメッセージを送信
```

## 各コンポーネントの役割

- **Discordユーザー**: コマンドを実行するだけなのだ。IDは裏側で自動的にBotに送られるのだ。
- **Discord Bot**: 送られてきたIDと名前を取り出して、FastAPIのサーバーに通信（POSTリクエスト）する役割なのだ。
- **FastAPI**: Botから送られてきたデータを受け取り、型が正しいかチェック（schemas.py）してから、データベース操作の処理を呼び出すのだ。
- **データベース**: 受け取ったユーザーIDと名前をテーブル（models.pyで定義したMemberテーブル）に保存する役割なのだ。
