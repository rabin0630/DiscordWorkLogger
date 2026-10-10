"""出退勤のAPIのエンドポイント"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.dependencies import get_db, verify_bot_key
from src.schemas.attendance import StartWorkRequest, StartWorkResponse, StopWorkRequest, StopWorkResponse
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


@router.post("/stop_work", response_model=StopWorkResponse)
def stop_work(request: StopWorkRequest, db: Session = Depends(get_db)) -> StopWorkResponse:
    """POST /stop_work: 退勤を記録する

    Args:
        request (StopWorkRequest): 退勤する人のuser_idと、コマンドした時刻
        db (Session): DBのセッション

    Returns:
        StopWorkResponse: 登録名と、丸めた出勤時刻・退勤時刻と、勤務時間(分)

    Raises:
        AppError: 退勤できない時(attendance_service.stop_workと同じ)

    Note:
        AppErrorは、main.pyの例外ハンドラーがエラーのレスポンスにする
    """
    member, record, work_minutes = attendance_service.stop_work(request.user_id, request.command_at, db)
    return StopWorkResponse(
        user_name=member.user_name, start_time=record.start_time, end_time=record.end_time,
        work_minutes=work_minutes)
