# backend/main.py
# FastAPI 应用主文件，包含所有的 API 路由和应用配置

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles # <--- 导入 StaticFiles
from pydantic import BaseModel, Field
import uuid
import os

# 导入我们自己定义的模块
from sqlalchemy.orm import Session
from .database import init_db, get_db
from .models import Presentation, Slide # <--- Slide 模型已更新
# 导入 AI 生成函数和相关的常量
from .ai_generation import generate_presentation_data, STATIC_DIR_RELATIVE, IMAGES_SUBDIR # <--- 已修正，导入 IMAGES_SUBDIR
from .pptx_generation import create_presentation_file # <--- PPTX 生成函数已更新
from . import templates

# --- 初始化 FastAPI 应用 ---
app = FastAPI()

# --- 配置静态文件服务 ---
# 获取 backend 目录的绝对路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 构建静态文件目录的完整物理路径
STATIC_FILES_DIR = os.path.join(BASE_DIR, STATIC_DIR_RELATIVE)

# 将静态文件目录挂载到 /static 路径
# 这意味着访问 /static/images/tech1.jpg 会去 STATIC_FILES_DIR/images/tech1.jpg 查找文件
app.mount(f"/{STATIC_DIR_RELATIVE}", StaticFiles(directory=STATIC_FILES_DIR), name=STATIC_DIR_RELATIVE) # <--- 挂载静态文件目录

# --- 配置 CORS --- (保持不变)
origins = [
    "http://localhost:3000",
    "http://127.0.0.0/8",
    # "http://192.168.1.0/24", # 示例：如果前端在局域网的其他机器上运行
    # 添加您前端部署后的地址...
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 应用启动事件处理 ---
@app.on_event("startup")
def on_startup():
    init_db()
    templates.check_templates_exist()
    # 确保静态图片目录存在
    # 使用直接导入的 IMAGES_SUBDIR
    images_dir = os.path.join(STATIC_FILES_DIR, IMAGES_SUBDIR) # <--- 已修正
    os.makedirs(images_dir, exist_ok=True)
    print(f"Ensured static images directory exists: {images_dir}")
    # TODO: 检查是否有图片文件在目录中，如果没有则警告用户

# --- Pydantic 模型定义 ---
class TextRequest(BaseModel):
    text: str

# --- 响应模型：包含本地图片路径 ---
class SlideResponse(BaseModel):
    id: str
    order: int
    title: str | None = None
    content: str | None = None
    notes: str | None = None
    visual_keywords: list[str] | None = None
    local_image_path: str | None = None # <--- 新增字段，存储匹配到的本地图片路径（相对于 static 目录）

class PresentationResponse(BaseModel):
    id: str
    input_text: str
    created_at: str
    template_id: str | None = None
    slides: list[SlideResponse]

# --- 请求模型：接收本地图片路径 ---
class SlideUpdate(BaseModel):
    id: str | None = None
    order: int
    title: str | None = None
    content: str | None = None
    notes: str | None = None
    visual_keywords: list[str] | None = None
    local_image_path: str | None = None # <--- 新增字段，允许前端在保存时发送

class PresentationUpdate(BaseModel):
    id: str
    slides: list[SlideUpdate]
    template_id: str | None = None


class TemplateItem(BaseModel):
    id: str
    name: str

# --- API Endpoints ---

# POST /api/presentations/generate (保存本地图片路径，返回完整数据)
# response_model 暂时不指定，因为返回的数据结构包含 SlideResponse，但不是 PresentationResponse 根对象
# 生产环境应该返回更简单的任务状态
@app.post("/api/presentations/generate")
async def generate_presentation(request: TextRequest, db: Session = Depends(get_db)):
    """
    根据输入的文本生成PPT数据（含视觉关键词和本地图片路径），并保存到数据库。
    """
    dark_tech_template = next((t for t in templates.TEMPLATES if t["id"] == "dark_tech"), None)
    default_template_id = dark_tech_template["id"] if dark_tech_template else (templates.TEMPLATES[0]["id"] if templates.TEMPLATES else None)

    if not default_template_id:
         raise HTTPException(status_code=500, detail="No presentation template defined on the server.")

    presentation_id = str(uuid.uuid4())
    new_presentation = Presentation(
        id=presentation_id,
        input_text=request.text,
        template_id=default_template_id
    )
    db.add(new_presentation)
    db.commit()
    db.refresh(new_presentation)

    try:
        print(f"开始为演示文稿 ID: {presentation_id} 生成数据 (使用模板: {default_template_id})")
        # generate_presentation_data 现在返回包含 'visual_keywords' 和 'local_image_path' 的数据
        slide_data = generate_presentation_data(request.text)

        for i, slide_info in enumerate(slide_data):
            slide = Slide(
                presentation_id=presentation_id,
                order=i,
                title=slide_info.get("title", f"幻灯片 {i+1}"),
                content='\n'.join(slide_info.get("points", [])),
                notes=slide_info.get("notes", ""),
                visual_keywords=slide_info.get("visual_keywords"),
                local_image_path=slide_info.get("local_image_path") # <--- 保存本地图片路径到数据库
            )
            db.add(slide)

        db.commit()
        print(f"演示文稿 {presentation_id} 数据（含视觉关键词和本地图片路径）已成功保存到数据库。")

        # 构建响应数据，包含本地图片路径
        response_slides_data = []
        # 这里的 slide_data 包含了 generate_presentation_data 返回的所有信息，包括 local_image_path
        for slide_info in slide_data:
             response_slides_data.append({
                  # 前端需要一个 ID 来标识列表项，这里先用 uuid 临时生成
                  # TODO: 更好的做法是从DB加载后，使用DB分配的ID
                  # 但因为是同步生成立即返回，DB分配的ID在commit后才确定，需要refresh或重新查询
                  # 为了与 EditorPage 的期望数据结构一致，手动构造一个包含所有字段的字典
                  "id": str(uuid.uuid4()), # 临时前端 ID
                  "order": slide_info.get("order", 0),
                  "title": slide_info.get("title", f"幻灯片 {slide_info.get('order',0)+1}"),
                  "content": '\n'.join(slide_info.get("points", [])),
                  "notes": slide_info.get("notes", ""),
                  "visual_keywords": slide_info.get("visual_keywords"),
                  "local_image_path": slide_info.get("local_image_path") # <--- 返回本地图片路径给前端
             })


        created_presentation = db.query(Presentation).filter(Presentation.id == presentation_id).first()
        response_data = {
            "id": presentation_id,
            "input_text": request.text,
            "created_at": created_presentation.created_at.isoformat() if created_presentation.created_at else None,
            "template_id": default_template_id,
            "slides": response_slides_data
        }

        return response_data # <--- 直接返回完整数据


    except ValueError as ve:
         db.rollback()
         print(f"AI generation specific error for {presentation_id}: {ve}")
         raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        db.rollback()
        print(f"为演示文稿 {presentation_id} 生成或保存数据时发生错误: {e}")
        raise HTTPException(status_code=500, detail=f"Presentation generation failed: {e}")


# GET /api/presentations/{presentation_id} (返回本地图片路径)
@app.get("/api/presentations/{presentation_id}", response_model=PresentationResponse)
async def get_presentation(presentation_id: str, db: Session = Depends(get_db)):
    """
    获取指定ID的PPT数据，包含视觉关键词和本地图片路径。
    """
    presentation = db.query(Presentation).filter(Presentation.id == presentation_id).first()
    if not presentation:
        raise HTTPException(status_code=404, detail="Presentation not found")

    slides = db.query(Slide).filter(Slide.presentation_id == presentation_id).order_by(Slide.order).all()

    slides_response = []
    for slide in slides:
         slides_response.append({
              "id": slide.id,
              "order": slide.order,
              "title": slide.title,
              "content": slide.content,
              "notes": slide.notes,
              "visual_keywords": slide.visual_keywords,
              "local_image_path": slide.local_image_path, # <--- 从数据库返回本地图片路径
         })

    return {
        "id": presentation.id,
        "input_text": presentation.input_text,
        "created_at": presentation.created_at.isoformat() if presentation.created_at else None,
        "template_id": presentation.template_id,
        "slides": slides_response
    }


# PUT /api/presentations/{presentation_id} (接收并更新本地图片路径)
@app.put("/api/presentations/{presentation_id}")
async def update_presentation(presentation_id: str, updated_presentation: PresentationUpdate, db: Session = Depends(get_db)):
    """
    更新演示文稿数据，包括幻灯片内容、顺序、备注、视觉关键词和本地图片路径。
    """
    presentation = db.query(Presentation).filter(Presentation.id == presentation_id).first()
    if not presentation:
        raise HTTPException(status_code=404, detail="Presentation not found")

    if presentation_id != updated_presentation.id:
         raise HTTPException(status_code=400, detail="Presentation ID mismatch in URL and body.")

    try:
        presentation.template_id = updated_presentation.template_id

        # 先删后插的简化逻辑 (注意其局限性)
        db.query(Slide).filter(Slide.presentation_id == presentation_id).delete()
        db.commit()

        for slide_info in updated_presentation.slides:
             slide = Slide(
                 presentation_id=presentation_id,
                 order=slide_info.order,
                 title=slide_info.title,
                 content=slide_info.content,
                 notes=slide_info.notes,
                 visual_keywords=slide_info.visual_keywords,
                 local_image_path=slide_info.local_image_path # <--- 接收并保存本地图片路径
             )
             db.add(slide)

        db.commit()
        print(f"演示文稿 {presentation_id} 数据已成功更新（包括本地图片路径和模板 ID: {presentation.template_id}）。")

    except Exception as e:
        db.rollback()
        print(f"更新演示文稿 {presentation_id} 时发生错误: {e}")
        raise HTTPException(status_code=500, detail="Failed to update presentation.")

    # 重新获取更新后的数据返回
    updated_presentation_data = db.query(Presentation).filter(Presentation.id == presentation_id).first()
    slides_response = []
    for slide in updated_presentation_data.slides:
         slides_response.append({
              "id": slide.id,
              "order": slide.order,
              "title": slide.title,
              "content": slide.content,
              "notes": slide.notes,
              "visual_keywords": slide.visual_keywords,
              "local_image_path": slide.local_image_path,
         })

    return {
        "id": updated_presentation_data.id,
        "input_text": updated_presentation_data.input_text,
        "created_at": updated_presentation_data.created_at.isoformat() if updated_presentation_data.created_at else None,
        "template_id": updated_presentation_data.template_id,
        "slides": slides_response
    }


# GET /api/presentations/{presentation_id}/download (使用 DB 中的 template_id 和本地图片路径生成 PPTX)
@app.get("/api/presentations/{presentation_id}/download")
async def download_presentation(presentation_id: str, db: Session = Depends(get_db)):
    """
    生成 PPTX 文件并提供下载。使用数据库中的数据（包括本地图片路径）和模板 ID。
    """
    presentation = db.query(Presentation).filter(Presentation.id == presentation_id).first()
    if not presentation:
        raise HTTPException(status_code=404, detail="Presentation not found")

    slides = db.query(Slide).filter(Slide.presentation_id == presentation_id).order_by(Slide.order).all()
    if not slides:
         raise HTTPException(status_code=400, detail="No slides found for this presentation")

    template_id = presentation.template_id
    template_path = None
    if template_id:
        template_path = templates.get_template_path(template_id)
        if not template_path:
             print(f"Warning: Template file not found for ID: {template_id}. Falling back to default template.")
             default_template = templates.TEMPLATES[0] if templates.TEMPLATES else None
             if default_template:
                  template_path = default_template["path"]
                  if not os.path.exists(template_path):
                       template_path = None
                  else:
                       print(f"Using default template file: {template_path}")
             else:
                 template_path = None

    slide_data_for_pptx = []
    for slide in slides:
         points = slide.content.split('\n') if slide.content else []

         # 构建本地图片的完整物理路径，用于 PPTX 生成
         # local_image_path 字段存储的是相对于 STATIC_DIR_RELATIVE 的路径
         local_image_relative_path = slide.local_image_path
         local_image_full_path = None
         if local_image_relative_path:
             # 使用在 main.py 中定义的 STATIC_FILES_DIR 构建完整路径
             local_image_full_path = os.path.join(STATIC_FILES_DIR, local_image_relative_path) # <--- 使用 STATIC_FILES_DIR
             # 再次检查文件是否存在
             if not os.path.exists(local_image_full_path):
                 print(f"Warning: Local image file not found for PPTX generation: {local_image_full_path}")
                 local_image_full_path = None # 文件不存在则不插入图片

         slide_data_for_pptx.append({
              "title": slide.title,
              "points": points, # 在 pptx_generation 中解析为要点
              "notes": slide.notes,
              "local_image_path": local_image_full_path # <--- 传递完整物理路径给 PPTX 生成模块
         })

    try:
        # 调用 PPTX 生成函数
        filepath = create_presentation_file(presentation_id, slide_data_for_pptx, template_path=template_path)
        print(f"PPTX 文件已生成在: {filepath} (使用模板 ID: {template_id or 'default'})")

        from fastapi.responses import FileResponse
        return FileResponse(
            filepath,
            media_type='application/vnd.openxmlformats-officedocument.presentationml.presentation',
            filename=f"presentation_{presentation_id[:8]}.pptx"
        )
    except Exception as e:
         print(f"生成 PPTX 文件时发生错误: {e}")
         raise HTTPException(status_code=500, detail="Error generating PPTX file.")
    finally:
        pass


# GET /api/templates (保持不变)
@app.get("/api/templates", response_model=list[TemplateItem])
async def get_templates():
    """
    获取可用 PPT 模板的列表。
    """
    return templates.get_templates_list()


# --- 健康检查或根路径 --- (保持不变)
@app.get("/")
async def read_root():
    return {"message": "AI Presentation Generator Backend is running"}

# --- 运行 FastAPI (本地开发用) ---
# 在项目根目录终端中使用命令启动: uvicorn backend.main:app --reload