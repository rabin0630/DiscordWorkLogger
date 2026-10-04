# タイマーの詳細設計

基本設計は[basic_design.md](./basic_design.md)を参照。

## データベース
- timeテーブルにuser_idとdefault_time保存する。
- user_idは主キー、default_timeは整数単位で保存する。単位は分
- カラムの新規作成ではdefault_timeを30分にする。
- UPDATEでdefault_timeを変更する。

## メモリ
- 辞書名はtimer_dataとする。
- {user_id: {is_active: bool, remaining_time: int}} (remaining_timeの代わりにend_timeにするかもしれない)
