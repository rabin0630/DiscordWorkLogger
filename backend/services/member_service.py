from sqlalchemy.orm import Session
import models, schemas
from crud import members as member_crud

# メンバー関係のビジネスロジック
# HTTPのステータスコードは扱わず、ルールに違反した場合は例外で呼び出し元に伝える


class MemberIdAlreadyExistsError(Exception):
    """登録しようとしたuser_idがすでに使われている"""


class MemberNameAlreadyExistsError(Exception):
    """登録しようとしたuser_nameがすでに使われている"""


def register_member(db: Session, member: schemas.Member) -> models.Member:
    """メンバーを登録する

    Args:
        db (Session): DBのセッション
        member (schemas.Member): 登録するメンバーの情報

    Returns:
        models.Member: 登録したメンバー

    Raises:
        MemberIdAlreadyExistsError: user_idがすでに登録されている場合
        MemberNameAlreadyExistsError: user_nameがすでに使われている場合
    """
    # ① IDが重複していないかチェック
    if member_crud.get_member_by_id(db, member.user_id):
        raise MemberIdAlreadyExistsError()

    # ② 名前が重複していないかチェック
    if member_crud.get_member_by_name(db, member.user_name):
        raise MemberNameAlreadyExistsError()

    # ③ どちらも問題なければ登録する
    return member_crud.create_member(db, member)
