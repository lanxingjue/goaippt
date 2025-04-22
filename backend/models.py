# backend/models.py
# 定义数据库模型，使用 SQLAlchemy ORM

from sqlalchemy import create_engine, Column, String, Integer, Text, DateTime, ForeignKey,JSON
from sqlalchemy.orm import relationship, declarative_base # 导入 declarative_base 用于ORM基类
from sqlalchemy.sql import func # 导入 func 用于数据库函数，如 now()
import uuid # 导入 uuid 用于生成唯一ID

# --- 数据库连接配置 ---
# 数据库连接字符串。请根据您的实际 PostgreSQL 配置进行修改。
# 格式: "postgresql://用户名:密码@主机名:端口号/数据库名"
# 如果使用Docker，主机名可能是容器名 (例如 'db') 或 localhost
# 如果本地安装，主机名通常是 'localhost'
# 默认端口是 5432
# 示例: postgresql://user:mypassword@localhost:5432/presentation_db
DATABASE_URL = "postgresql://root:wang@localhost:5432/presentation_db" # <--- **请修改为您的实际配置**

# 创建一个声明性映射的基类。我们的所有ORM模型都将继承自它。
Base = declarative_base()

# --- 数据库表模型定义 ---

class Presentation(Base):
    """
    演示文稿主表模型。
    每个演示文稿包含多个幻灯片。
    """
    __tablename__ = "presentations"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    input_text = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    template_id = Column(String, nullable=True)

    # 与 Slide 表建立一对多关系。'slides' 是 Presentation 对象上的属性。
    # back_populates="presentation" 指明在 Slide 模型中对应的属性名是 'presentation'。
    slides = relationship("Slide", back_populates="presentation", cascade="all, delete-orphan", order_by="Slide.order")

class Slide(Base):
    """
    单个幻灯片表模型。
    """
    __tablename__ = "slides"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    presentation_id = Column(String, ForeignKey("presentations.id"), index=True)
    order = Column(Integer)
    title = Column(String, nullable=True)
    content = Column(Text, nullable=True) # 幻灯片主要内容（要点）
    notes = Column(Text, nullable=True) # 演讲者备注

    # --- 新增字段：存储 AI 生成的视觉关键词 ---
    visual_keywords = Column(JSON, nullable=True)

    # --- 新增字段：存储匹配到的本地图片文件路径（相对于 static 目录） ---
    # 例如: "images/tech1.jpg"
    local_image_path = Column(String, nullable=True) # <--- 新增字段

    # 与 Presentation 表建立多对一关系。'presentation' 是 Slide 对象上的属性。
    # back_populates="slides" 指明在 Presentation 模型中对应的属性名是 'slides'。
    # 注意：这里的 back_populates 必须引用 Presentation 模型中的 slides 属性名。
    presentation = relationship("Presentation", back_populates="slides") # <--- **已修正 back_populates="slides"**

# --- 数据库初始化函数 ---
# 这个函数将在应用启动时被调用，用于在数据库中创建定义的所有表（如果不存在的话）。
# 这个函数的实际实现将在 database.py 中使用，以便复用 engine。
# def init_db():
#     print("Models defined.")