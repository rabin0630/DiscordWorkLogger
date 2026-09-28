from backend.database_config import MYSQL_INFO

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 接続用コードへの適用
user = MYSQL_INFO['USER']
password = MYSQL_INFO['PASSWORD']
host = MYSQL_INFO['HOST']
db_name = MYSQL_INFO['DATABASE']

engine = create_engine(f"mysql+mysqlconnector://{user}:{password}@{host}/{db_name}")
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = SessionLocal()