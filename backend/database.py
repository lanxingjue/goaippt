# backend/database.py
# 负责数据库引擎创建、会话管理和初始化表

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session # 导入 Session 类用于类型提示
# 导入 models.py 中定义的 Base 和 DATABASE_URL
from .models import Base, DATABASE_URL

# --- 数据库引擎和会话 ---

# 创建数据库引擎。engine 是与数据库交互的入口点，它管理数据库连接池。
# echo=True 会打印所有执行的SQL语句，方便调试（生产环境通常关闭）。
engine = create_engine(DATABASE_URL, echo=False)

# 创建一个 Session 工厂。通过这个工厂可以创建数据库会话 (Session 对象)。
# autocommit=False: 默认不自动提交事务，需要显式调用 db.commit()。
# autoflush=False: 默认不自动刷新会话到数据库，在 commit() 或 flush() 时进行。
# bind=engine: 将会话工厂绑定到上面创建的 engine。
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- 数据库初始化函数 ---
# 在应用启动时调用此函数，使用 engine 创建数据库表。
def init_db():
    """
    创建数据库表（如果不存在）。在应用启动时调用。
    """
    print("Attempting to create database tables...")
    # 使用 Base.metadata.create_all(bind=engine) 来创建所有继承自 Base 的模型对应的表。
    # bind=engine 参数是必需的，告诉 SQLAlchemy 连接哪个数据库。
    Base.metadata.create_all(bind=engine)
    print("Database tables created (if not exist).")

# --- 依赖注入函数 ---
# 这个函数用于 FastAPI 的 Depends()，为每个请求创建一个独立的数据库会话。
def get_db():
    """
    获取一个数据库会话，用于 FastAPI 依赖注入。
    使用 try...finally 块确保会话在使用完毕后被关闭。
    """
    db = SessionLocal() # 从工厂创建一个新的会话
    try:
        yield db # 使用 yield 将会话提供给请求处理函数
    finally:
        db.close() # 请求处理完成后，关闭会话，释放连接回连接池