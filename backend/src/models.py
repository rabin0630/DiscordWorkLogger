"""データベースのテーブル設計"""
from sqlalchemy import BigInteger, Column, Date, String

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
