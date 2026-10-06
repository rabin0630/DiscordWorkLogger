from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import declarative_base, sessionmaker

from src import config


def make_database_url(database: str | None) -> URL:
    """MySQLの接続先のURLを作る

    パスワードに記号が入っていても壊れないよう、URL.createで組み立てる。

    Args:
        database (str | None): つなぐデータベースの名前

    Returns:
        URL: mysql+mysqlconnector://{user}:{password}@{host}/{database}?charset=utf8mb4
    """
    return URL.create(
        drivername="mysql+mysqlconnector",
        username=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD,
        host=config.MYSQL_HOST,
        database=database,
        query={"charset": "utf8mb4"},
    )


engine = create_engine(make_database_url(config.MYSQL_DATABASE), pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
