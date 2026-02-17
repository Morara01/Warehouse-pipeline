from sqlalchemy import create_engine

def get_engine():
    return create_engine(
        "mysql+mysqlconnector://username:password@localhost:3306/warehouse_db"
    )
