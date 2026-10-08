"""データベースのテーブル設計"""
from sqlalchemy import BigInteger, Column, Date, DateTime, ForeignKey, Index, Integer, String

from src.database import Base


class Member(Base):
    """Member_table。メンバーを1人1行で管理する

    Attributes:
        user_id (int): 主キー。DiscordのユーザーID
        user_name (str): 登録名。UNIQUE。入力した大文字・小文字のまま保存する
        created_date (date): 登録日(日本時間)
        retirement_date (date | None): 退職日。今回は使わない
    """
    __tablename__ = "Member_table"
    # テーブル全体の設定。create_allでテーブルを新しく作る時だけ使われる
    __table_args__ = {
        "mysql_charset": "utf8mb4",              # 文字コード。日本語や絵文字も保存できる
        "mysql_collate": "utf8mb4_0900_ai_ci",   # 照合順序。大文字・小文字を区別しないので、UNIQUE制約がJunとjunを同じ名前とみなす
    }

    user_id = Column(BigInteger, primary_key=True, autoincrement=False)
    user_name = Column(String(10), nullable=False, unique=True)
    created_date = Column(Date, nullable=False)
    retirement_date = Column(Date, nullable=True)


class AttendanceRecord(Base):
    """attendance_records。1回の出退勤を1行で管理する

    Attributes:
        index (int): 主キー。自動採番
        member_id (int): Member_table.user_idの外部キー
        date (date): 出勤日。丸めた後の出勤時刻の日付
        start_time (datetime): 出勤時刻(丸めた後、日本時間)
        end_time (datetime | None): 退勤時刻(丸めた後、日本時間)。出勤中はNone
        raw_start_time (datetime | None): 打刻した本当の出勤時刻。社長がWebで追加した記録はNone
        raw_end_time (datetime | None): 打刻した本当の退勤時刻。出勤中と、社長がWebで退勤時間を入れた記録はNone
    """
    __tablename__ = "attendance_records"
    __table_args__ = (
        # 出勤中の行の検索、月の一覧、重なりの確認に使う
        Index("ix_attendance_records_member_id_start_time", "member_id", "start_time"),
        {
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_0900_ai_ci",
        },
    )

    index = Column(Integer, primary_key=True, autoincrement=True)
    member_id = Column(BigInteger, ForeignKey("Member_table.user_id"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    raw_start_time = Column(DateTime, nullable=True)
    raw_end_time = Column(DateTime, nullable=True)
