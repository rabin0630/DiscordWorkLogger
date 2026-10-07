"""メンバーの読み書き。見つからなければNoneを返し、例外は投げない。コミットもしない"""
from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.models import Member


def get_member_by_id(db: Session, user_id: int) -> Member | None:
    """user_idでメンバーを1件探す

    Args:
        db (Session): DBのセッション
        user_id (int): DiscordのユーザーID

    Returns:
        Member | None: 見つかったメンバー。いなければNone
    """
    return db.query(Member).filter(Member.user_id == user_id).first()


def get_member_by_name(db: Session, user_name: str) -> Member | None:
    """名前でメンバーを1件探す。大文字・小文字は区別しない

    Args:
        db (Session): DBのセッション
        user_name (str): 探す名前

    Returns:
        Member | None: 見つかったメンバー。いなければNone

    Note:
        照合順序に任せず、func.lowerで両方を小文字にして比べる(コードを読むだけで分かるようにするため)
    """
    return db.query(Member).filter(func.lower(Member.user_name) == user_name.lower()).first()


def create_member(db: Session, user_id: int, user_name: str, created_date: date) -> Member:
    """メンバーを追加する。db.addだけ行い、コミットしない

    Args:
        db (Session): DBのセッション
        user_id (int): DiscordのユーザーID
        user_name (str): 登録名
        created_date (date): 登録日

    Returns:
        Member: 追加したメンバー
    """
    member = Member(user_id=user_id, user_name=user_name, created_date=created_date)
    db.add(member)
    return member


def update_member_name(member: Member, user_name: str) -> Member:
    """メンバーの名前を書き換える。コミットしない

    Args:
        member (Member): 名前を変えるメンバー。DBのセッションから取ったもの
        user_name (str): 変更後の名前

    Returns:
        Member: 名前を書き換えたメンバー
    """
    member.user_name = user_name
    return member
