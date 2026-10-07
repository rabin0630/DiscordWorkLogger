"""名前のAPIのエンドポイント"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.dependencies import get_db, verify_bot_key
from src.schemas.members import RegisterMemberRequest, RegisterMemberResponse
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
