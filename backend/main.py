# backend/main.py
# FastAPI 应用主文件，包含所有的 API 路由和应用配置

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
import os

# 导入我们自己定义的模块
from sqlalchemy.orm import Session
from .database import init_db, get_db
from .models import Presentation, Slide
from .ai_generation import generate_presentation_data
from .pptx_generation import create_presentation_file
from . import templates # 导入 templates 包

# --- 初始化 FastAPI 应用 ---
app = FastAPI()

# --- 配置 CORS --- (保持不变)
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    # ...
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 应用启动事件处理 --- (保持不变)
@app.on_event("startup")
def on_startup():
    init_db()
    templates.check_templates_exist()

# --- Pydantic 模型定义 --- (保持不变)
class TextRequest(BaseModel):
    text: str

class SlideUpdate(BaseModel):
    # id: str # MVP简化处理
    order: int
    title: str | None = None
    content: str | None = None
    notes: str | None = None

class PresentationUpdate(BaseModel):
    id: str
    slides: list[SlideUpdate]
    template_id: str | None = None

class TemplateItem(BaseModel):
    id: str
    name: str

# --- API Endpoints ---

# POST /api/presentations/generate (修改默认模板ID)
@app.post("/api/presentations/generate")
async def generate_presentation(request: TextRequest, db: Session = Depends(get_db)):
    # --- 调整默认模板 ID ---
    # 查找暗黑科技模板的 ID，如果找不到则回退到列表第一个或 None
    dark_tech_template = next((t for t in templates.TEMPLATES if t["id"] == "dark_tech"), None)
    default_template_id = dark_tech_template["id"] if dark_tech_template else (templates.TEMPLATES[0]["id"] if templates.TEMPLATES else None)

    if not default_template_id:
         raise HTTPException(status_code=500, detail="No template defined.")

    presentation_id = str(uuid.uuid4())
    new_presentation = Presentation(
        id=presentation_id,
        input_text=request.text,
        template_id=default_template_id # <--- 使用调整后的默认模板 ID
    )
    db.add(new_presentation)
    db.commit()
    db.refresh(new_presentation)

    try:
        print(f"开始为演示文稿 ID: {presentation_id} 生成数据 (使用模板: {default_template_id})")
        slide_data = generate_presentation_data(request.text)

        # --- MVP 阶段改进：检查并丢弃第一页的介绍性内容 --- (保持不变)
        if slide_data and len(slide_data) > 1:
            first_slide = slide_data[0]
            first_slide_text = (first_slide.get("title", "") + " " + '\n'.join(first_slide.get("points", []))).lower()
            # 根据您实际观察到的 AI 输出调整关键词
            intro_keywords = ["大纲", "基于", "以下", "生成", "演示文稿"] # 增加关键词
            if any(keyword in first_slide_text for keyword in intro_keywords):
                print(f"检测到第一页 (ID: {presentation_id}) 可能是介绍性内容，正在丢弃。")
                slide_data = slide_data[1:] # 丢弃第一页
                # 调整剩余幻灯片的顺序
                for i, slide_info in enumerate(slide_data):
                     slide_info["order"] = i
                print(f"丢弃介绍页后，剩余 {len(slide_data)} 页。")
            else:
                print("第一页未检测到介绍性内容，保留。")


        if not slide_data:
             # 如果丢弃后没有剩余幻灯片
             raise ValueError("AI generated only introductory content or no content.")


        # 遍历并保存到数据库
        for i, slide_info in enumerate(slide_data):
            slide = Slide(
                presentation_id=presentation_id,
                order=i,
                title=slide_info.get("title", "Untitled Slide"),
                content='\n'.join(slide_info.get("points", [])),
                notes=slide_info.get("notes", "")
            )
            db.add(slide)

        db.commit()
        print(f"演示文稿 {presentation_id} 数据已成功保存到数据库。")

    except Exception as e:
        db.rollback()
        print(f"为演示文稿 {presentation_id} 生成或保存数据时发生错误: {e}")
        # TODO: 更好的错误处理
        raise HTTPException(status_code=500, detail=f"Presentation generation failed: {e}") # 返回 AI 生成的具体错误信息给用户


    return {"id": presentation_id, "status": "completed", "template_id": default_template_id}


# GET /api/presentations/{presentation_id} (保持不变)
@app.get("/api/presentations/{presentation_id}")
async def get_presentation(presentation_id: str, db: Session = Depends(get_db)):
    # ... (获取数据并返回，已包含 template_id) ...
    presentation = db.query(Presentation).filter(Presentation.id == presentation_id).first()
    if not presentation:
        raise HTTPException(status_code=404, detail="Presentation not found")

    slides = db.query(Slide).filter(Slide.presentation_id == presentation_id).order_by(Slide.order).all()

    return {
        "id": presentation.id,
        "input_text": presentation.input_text,
        "created_at": presentation.created_at,
        "template_id": presentation.template_id,
        "slides": [
            {
                "id": slide.id,
                "order": slide.order,
                "title": slide.title,
                "content": slide.content,
                "notes": slide.notes
            } for slide in slides
        ]
    }


# PUT /api/presentations/{presentation_id} (保持不变)
@app.put("/api/presentations/{presentation_id}")
async def update_presentation(presentation_id: str, updated_presentation: PresentationUpdate, db: Session = Depends(get_db)):
    # ... (更新数据和模板 ID) ...
    presentation = db.query(Presentation).filter(Presentation.id == presentation_id).first()
    if not presentation:
        raise HTTPException(status_code=404, detail="Presentation not found")

    if presentation_id != updated_presentation.id:
         raise HTTPException(status_code=400, detail="Presentation ID mismatch in URL and body.")

    try:
        # 更新演示文稿主记录的模板 ID
        presentation.template_id = updated_presentation.template_id

        # 删除旧的 slides
        db.query(Slide).filter(Slide.presentation_id == presentation_id).delete()

        # 插入新的 slides，确保顺序正确
        # 前端在编辑后应该会发送包含正确 order 的 slides 列表
        for slide_info in updated_presentation.slides:
             slide = Slide(
                 presentation_id=presentation_id,
                 order=slide_info.order,
                 title=slide_info.title,
                 content=slide_info.content,
                 notes=slide_info.notes
             )
             db.add(slide)

        db.commit()
        print(f"演示文稿 {presentation_id} 数据已成功更新 (包括模板 ID: {presentation.template_id})。")

    except Exception as e:
        db.rollback()
        print(f"更新演示文稿 {presentation_id} 时发生错误: {e}")
        raise HTTPException(status_code=500, detail="Failed to update presentation.")

    return {"id": presentation_id, "status": "updated", "template_id": presentation.template_id}


# GET /api/presentations/{presentation_id}/download (保持不变，它会使用 DB 中的 template_id)
@app.get("/api/presentations/{presentation_id}/download")
async def download_presentation(presentation_id: str, db: Session = Depends(get_db)):
    # ... (下载逻辑，使用 DB 中的 template_id 获取模板路径) ...
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
                 template_path = None

    slide_data_for_pptx = []
    for slide in slides:
         points = slide.content.split('\n') if slide.content else []
         slide_data_for_pptx.append({
              "title": slide.title,
              "points": points,
              "notes": slide.notes
         })

    try:
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