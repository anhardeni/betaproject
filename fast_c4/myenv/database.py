from sqlmodel import SQLModel, create_engine 
import os

BASE_DIR=os.path.dirname(os.path.realpath(__file__))
url_db_erp= '_aad86d4a36e7fb50'
url_db='test'
conn_str='mysql+pymysql://root:qwerty2022@127.0.0.1/test'
#conn_str='sqlite:///'+os.path.join(BASE_DIR,'books.db')

connect_args = {"check_same_thread": False}

engine=create_engine(conn_str, echo=True)