# backend/models.py
# 定义数据库模型，使用 SQLAlchemy ORM

from sqlalchemy import create_engine, Column, String, Integer, Text, DateTime, ForeignKey
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
    __tablename__ = "presentations" # 数据库中的表名

    # 主键，使用 UUID 作为唯一标识符
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    # 存储用户输入的原始文本内容
    input_text = Column(Text)
    # 记录创建时间，使用数据库函数 func.now() 获取当前时间
    created_at = Column(DateTime, server_default=func.now())


    # --- 新增字段：存储使用的模板 ID ---
    # 默认使用 templates 模块中定义的第一个模板的 ID 作为默认值
    # 确保 templates 模块和 TEMPLATES 列表已定义
    # from .templates import TEMPLATES # 确保正确导入 TEMPLATES
    # default_template_id = TEMPLATES[0]["id"] if TEMPLATES else None # 获取第一个模板的ID作为默认值
    # template_id = Column(String, default=default_template_id, nullable=True) # <--- 简单版本，直接使用字符串，默认值为 None
    # 为了避免跨模块引用带来的复杂性，我们不在模型中设置默认值，而是在 main.py 生成时指定。
    template_id = Column(String, nullable=True) # 存储使用的模板 ID，允许为空
    # 与 Slide 表建立一对多关系。一个 Presentation 可以有多个 Slides。
    # 'slides' 是 Presentation 对象上的一个属性，通过它可以访问关联的 Slide 对象列表。
    # back_populates="presentation" 指明在 Slide 模型中对应的关系属性名。
    # cascade="all, delete-orphan" 意味着当删除一个 Presentation 对象时，关联的 Slides 会被自动删除。
    # order_by="Slide.order" 保证在查询时 Slides 按照 order 字段排序。
    slides = relationship("Slide", back_populates="presentation", cascade="all, delete-orphan", order_by="Slide.order")

class Slide(Base):
    """
    单个幻灯片表模型。
    """
    __tablename__ = "slides" # 数据库中的表名

    # 主键，使用 UUID 作为唯一标识符
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    # 外键，关联到 presentations 表的 id 字段。表示这个幻灯片属于哪个演示文稿。
    presentation_id = Column(String, ForeignKey("presentations.id"), index=True)
    # 幻灯片在演示文稿中的顺序
    order = Column(Integer)
    # 幻灯片标题，允许为空
    title = Column(String, nullable=True)
    # 幻灯片主要内容（在 MVP 阶段存储为包含要点的文本字符串）
    content = Column(Text, nullable=True)
    # 演讲者的备注，允许为空
    notes = Column(Text, nullable=True)

    # 与 Presentation 表建立多对一关系。多个 Slides 可以属于同一个 Presentation。
    # 'presentation' 是 Slide 对象上的一个属性，通过它可以访问所属的 Presentation 对象。
    # back_populates="slides" 指明在 Presentation 模型中对应的关系属性名。
    presentation = relationship("Presentation", back_populates="slides")

# --- 数据库初始化函数 ---
# 这个函数将在应用启动时被调用，用于在数据库中创建定义的所有表（如果不存在的话）。
# 这个函数的实际实现将在 database.py 中使用，以便复用 engine。
# 我们在这里保留一个同名函数，虽然在 database.py 中会被覆盖，但这是一种组织方式。
# 实际上 database.py 中的 init_db 函数会使用这里定义的 Base。
# def init_db():
#     """
#     创建数据库表（如果不存在）。
#     注意：这个函数在 database.py 中会有具体实现并被调用。
#     """
#     # 这里只是定义了函数的存在，具体实现依赖于 database.py 中的 engine
#     print("Models defined.")