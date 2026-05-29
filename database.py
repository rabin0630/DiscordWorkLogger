from database_config import MYSQL_INFO

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


# 接続用コードへの適用
user = MYSQL_INFO['user']
password = MYSQL_INFO['password']
host = MYSQL_INFO['host']
db_name = MYSQL_INFO['database']

engine = create_engine(f"mysql+mysqlconnector://{user}:{password}@{host}/{db_name}")
Base = declarative_base()
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = Session()