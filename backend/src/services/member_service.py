import re
from datetime import date, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src import config
from src.crud import members
from src.exceptions import AppError
from src.models import Member

# 名前のチェックと、社長かどうかの判定

NAME_PATTERN = re.compile(r"[A-Za-z]+")
NAME_MAX_LENGTH = 10


def is_owner(user_id: int) -> bool:
    """社長かどうかを判定する

    Args:
        user_id (int): DiscordのユーザーID

    Returns:
        bool: OWNER_DISCORD_IDと同じならTrue。.envにOWNER_DISCORD_IDがなければ、いつもFalse
    """
    return config.OWNER_DISCORD_ID is not None and user_id == config.OWNER_DISCORD_ID


def validate_name(name: str) -> None:
    """名前のルール(空は不可、英字のみ、10文字まで)を確かめる

    上から順に確かめ、最初に当てはまったエラーを投げる。/renameでも使う。

    Args:
        name (str): 確かめる名前

    Raises:
        AppError: ルールに合わない時(400)。detailは次のどれか
            - name_empty: 前後の空白を除いて0文字
            - name_not_alpha: 英字以外が入っている
            - name_too_long: 11文字以上
    """
    if not name.strip():
        raise AppError(400, "name_empty")
    if not NAME_PATTERN.fullmatch(name):
        raise AppError(400, "name_not_alpha")
    if len(name) > NAME_MAX_LENGTH:
        raise AppError(400, "name_too_long")


def today_jst() -> date:
    """日本時間の今日の日付を返す

    Returns:
        date: 日本時間の今日。登録日(created_date)に使う
    """
    return datetime.now(config.JST).date()


def register_member(db: Session, user_id: int, user_name: str) -> Member:
    """メンバーを登録する

    「確認する順番」の表のとおりに確かめてから登録し、コミットする。
    同時に登録されてUNIQUE制約に引っかかった時は、ロールバックしてから、どちらのエラーかを決める。

    Args:
        db (Session): DBのセッション
        user_id (int): 登録する人のDiscordのユーザーID
        user_name (str): 登録する名前

    Returns:
        Member: 登録したメンバー

    Raises:
        AppError: 登録できない時。detailは次のどれか
            - employee_only(403): 社長
            - name_empty、name_not_alpha、name_too_long(400): 名前のルールに合わない
            - already_registered(409): もう登録している
            - name_taken(409): 他の人が同じ名前を使っている(大文字・小文字を区別しない)
    """
    if is_owner(user_id):
        raise AppError(403, "employee_only")
    
    validate_name(user_name)
    if members.get_member_by_id(db, user_id) is not None:
        raise AppError(409, "already_registered")
    if members.get_member_by_name(db, user_name) is not None:
        raise AppError(409, "name_taken")

    member = members.create_member(db, user_id, user_name, today_jst())
    try:
        db.commit()
    except IntegrityError:
        # 同時に登録された時。もう一度確かめて、どちらのエラーかを決める
        db.rollback()
        if members.get_member_by_id(db, user_id) is not None:
            raise AppError(409, "already_registered")
        raise AppError(409, "name_taken")
    db.refresh(member)
    return member
