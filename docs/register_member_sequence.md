# register_member シーケンス図

APIの中をRouter・Service・CRUDの3つの層に分けたときの、メンバー登録(`/register_member`)の流れ。

```mermaid
sequenceDiagram
    actor User as ユーザー
    participant Bot as Bot<br>(frontend/register_cog.py)
    participant Router as Router<br>(routers/members.py)
    participant Service as Service<br>(services/member_service.py)
    participant CRUD as CRUD<br>(crud.py)
    participant DB as MySQL

    User->>Bot: /register {name}
    Bot->>Router: POST /register_member<br>{user_id, user_name, created_date}
    Note over Router: schemas.Memberで型チェック<br>(NGなら422を返す)
    Router->>Service: register_member(db, member)

    Service->>CRUD: get_member_by_id(db, user_id)
    CRUD->>DB: SELECT ... WHERE user_id = ?
    DB-->>CRUD: 結果
    CRUD-->>Service: Member または None

    alt IDがすでに登録されている
        Service-->>Router: 例外(IDの重複)
        Router-->>Bot: 409「このIDはすでに使われています」
        Bot-->>User: ID重複のメッセージ
    else IDは未登録
        Service->>CRUD: get_member_by_name(db, user_name)
        CRUD->>DB: SELECT ... WHERE user_name = ?
        DB-->>CRUD: 結果
        CRUD-->>Service: Member または None

        alt 名前がすでに使われている
            Service-->>Router: 例外(名前の重複)
            Router-->>Bot: 409「この名前はすでに使われています」
            Bot-->>User: 名前重複のメッセージ
        else 名前も未使用
            Service->>CRUD: create_member(db, member)
            CRUD->>DB: INSERT INTO Member_table ...
            DB-->>CRUD: 登録したデータ
            CRUD-->>Service: 登録したMember
            Service-->>Router: 登録したMember
            Router-->>Bot: 200 登録したデータ
            Bot-->>User: 登録完了のメッセージ
        end
    end
```

## 各層の役割

| 層 | やること | やらないこと |
| --- | --- | --- |
| Router | リクエストを受け取る。例外をHTTPのステータスコード(409など)に変えて返す | 重複チェックなどのルールの判断、DBの操作 |
| Service | 「IDが重複していたらダメ」「名前が重複していたらダメ」というルールを判断する | HTTPのこと(ステータスコード)、SQLを書くこと |
| CRUD | 「IDで探す」「名前で探す」「保存する」だけをする | ルールの判断 |

ServiceはHTTPのステータスコードを知らない。Serviceは例外で「重複している」とだけ伝え、それを409にするかどうかはHTTPの窓口であるRouterが決める。
