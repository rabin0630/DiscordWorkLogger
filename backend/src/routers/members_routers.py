"""名前のAPIのエンドポイント"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.dependencies import get_db, verify_bot_key
from src.schemas.members import (
    RegisterMemberRequest,
    RegisterMemberResponse,
    RenameMemberRequest,
    RenameMemberResponse,
)
from src.services import member_service

router = APIRouter(dependencies=[Depends(verify_bot_key)])


@router.post("/register_member", response_model=RegisterMemberResponse)
def register_member(request: RegisterMemberRequest, db: Session = Depends(get_db)) -> RegisterMemberResponse:
    """POST /register_member: メンバーを登録する

    Args:
        request (RegisterMemberRequest): 登録する人のuser_idと名前
        db (Session): DBのセッション

    Returns:
        RegisterMemberResponse: 登録した名前

    Raises:
        AppError: 登録できない時(member_service.register_memberと同じ)

    Note:
        AppErrorは、main.pyの例外ハンドラーがエラーのレスポンスにする
    """
    member = member_service.register_member(db, request.user_id, request.user_name)
    return RegisterMemberResponse(user_name=member.user_name)


@router.post("/rename_member", response_model=RenameMemberResponse)
def rename_member(request: RenameMemberRequest, db: Session = Depends(get_db)) -> RenameMemberResponse:
    """POST /rename_member: 登録名を変更する

    Args:
        request (RenameMemberRequest): 名前を変える人のuser_idと、変更後の名前
        db (Session): DBのセッション

    Returns:
        RenameMemberResponse: 変更前と変更後の名前

    Raises:
        AppError: 変更できない時(member_service.rename_memberと同じ)

    Note:
        AppErrorは、main.pyの例外ハンドラーがエラーのレスポンスにする
    """
    old_name, member = member_service.rename_member(db, request.user_id, request.user_name)
    return RenameMemberResponse(old_name=old_name, new_name=member.user_name)
