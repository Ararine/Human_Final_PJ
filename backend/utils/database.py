import os
from sqlalchemy import create_engine

user_id=os.getenv("USER_ID")
password=os.getenv("DB_PASSWORD")
host=os.getenv("DB_HOST")
db_info = f"mysql+pymysql://{user_id}:{password}@{host}"

engine = create_engine(
    db_info,connect_args={}) 
