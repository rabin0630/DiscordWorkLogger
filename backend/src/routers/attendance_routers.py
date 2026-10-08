"""出退勤のAPIのエンドポイント"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.dependencies import get_db, verify_bot_key
from src.schemas.attendance import StartWorkRequest, StartWorkResponse
from src.services import attendance_service

router = APIRouter(dependencies=[Depends(verify_bot_key)])


@router.post("/start_work", response_model=StartWorkResponse)
def start_work(request: StartWorkRequest, db: Session = Depends(get_db)) -> StartWorkResponse:
    """POST /start_work: 出勤を記録する

    Args:
        request (StartWorkRequest): 出勤する人のuser_idと、コマンドした時刻
        db (Session): DBのセッション

    Returns:
        StartWorkResponse: 登録名と、丸めた出勤時刻

    Raises:
        AppError: 出勤できない時(attendance_service.start_workと同じ)

    Note:
        AppErrorは、main.pyの例外ハンドラーがエラーのレスポンスにする
    """
    member, record = attendance_service.start_work(request.user_id, request.command_at, db)
    return StartWorkResponse(user_name=member.user_name, start_time=record.start_time)
