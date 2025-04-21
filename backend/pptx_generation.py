# backend/pptx_generation.py
# 使用 python-pptx 库生成 .pptx 文件

import os

from pptx import Presentation as PPTXPresentation
from pptx.util import Inches, Pt
# from pptx.enum.shapes import MSO_SHAPE
# from pptx.dml.color import RGBColor

# --- 简单的样式配置 (MVP阶段，后续通过模板管理) ---
TITLE_FONT_SIZE = Pt(30)
BODY_FONT_SIZE = Pt(18)
NOTES_FONT_SIZE = Pt(10)
BULLET_CHAR = '•' # 或 '-'

# --- PPTX 生成核心函数 ---
# 添加 template_path 参数
def create_presentation_file(presentation_id: str, slides_data: list, template_path: str | None = None): # <--- 新增 template_path 参数
    """
    根据幻灯片数据生成 PPTX 文件，可选择加载模板。

    Args:
        presentation_id (str): 演示文稿的唯一 ID。
        slides_data (list): 包含每个幻灯片数据的列表。
        template_path (str | None): 可选的模板文件物理路径。如果为 None，则创建空白演示文稿。

    Returns:
        str: 生成的 PPTX 文件的完整文件路径。
    """
    # 根据 template_path 创建或加载演示文稿对象
    if template_path and os.path.exists(template_path):
        prs = PPTXPresentation(template_path) # 加载模板
        print(f"Loaded presentation template from: {template_path}")
    else:
        prs = PPTXPresentation() # 创建空白演示文稿
        print("Created a blank presentation (no valid template found or specified).")


    # --- 幻灯片布局选择 ---
    # 尝试使用“标题和内容”布局。如果模板中有，就用模板的；如果没有或没加载模板，就用默认的。
    title_content_layout = None
    # 先尝试通过布局名称查找 (更稳定，不同模板/PowerPoint版本索引可能不同)
    for layout in prs.slide_layouts:
        # 检查布局名称，通常标题和内容布局名称包含 "Title and Content" 或 "标题和内容"
        # 需要更鲁棒的匹配或者依赖模板约定
        # MVP 简单处理：尝试找索引 1 或 索引 0
        pass # 在循环后通过索引尝试

    # 如果按名称找不到，或不确定名称，回退到按索引查找常见布局
    try:
        # 尝试索引 1 (常见的内容布局)
        title_content_layout = prs.slide_layouts[1]
        print("Using slide layout: Index 1")
    except IndexError:
         try:
              # 尝试索引 0 (常见的主标题布局)
              title_content_layout = prs.slide_layouts[0]
              print("Using slide layout: Index 0")
         except IndexError:
              # 如果模板中连索引 0 也没有（不太可能），或者空白演示文稿没有默认布局，则报错
              raise RuntimeError("No usable slide layout found in the presentation or template.")


    # --- 遍历幻灯片数据，创建每一页幻灯片 ---
    for slide_info in slides_data:
        # 使用选定的布局添加一页新的幻灯片
        slide = prs.slides.add_slide(title_content_layout)

        # --- 添加标题 ---
        if slide.shapes.title:
             title_shape = slide.shapes.title
             title_shape.text = slide_info.get("title", "Untitled Slide")
             # TODO: 可以考虑应用模板的标题样式
        else:
             print(f"Warning: Slide layout '{title_content_layout.name}' has no title placeholder. Title '{slide_info.get('title', 'Untitled')}' will not be added.")


        # --- 添加内容要点 ---
        content_placeholder = None
        for shape in slide.placeholders:
            if shape.is_placeholder and shape.placeholder_format.idx == 1: # Index 1 通常是内容占位符
                 content_placeholder = shape
                 break

        if content_placeholder:
            tf = content_placeholder.text_frame
            tf.clear() # 清除默认文本

            points = slide_info.get("points", [])

            if points:
                 # 添加第一个要点
                 p = tf.add_paragraph()
                 p.text = points[0]
                 p.level = 0 # 顶级要点

                 # 添加剩余的要点
                 for point in points[1:]:
                    p = tf.add_paragraph()
                    p.text = point
                    p.level = 0 # 顶级要点

            # TODO: 可以考虑应用模板的要点样式（如字体、大小、bullet 符号等）
            # 例如:
            # for p in tf.paragraphs:
            #      for run in p.runs:
            #           font = run.font
            #           font.size = Pt(18) # 设置字号


        else:
             print(f"Warning: Slide layout '{title_content_layout.name}' has no content placeholder. Points will not be added.")


        # --- 添加演讲者备注 ---
        # 获取或创建备注幻灯片
        notes_slide = slide.notes_slide
        # 获取备注文本框
        text_frame = notes_slide.notes_text_frame
        text_frame.clear() # 清除默认内容
        text_frame.text = slide_info.get("notes", "") # 设置备注内容
        # TODO: 备注样式通常在备注母版中定义，无需代码设置，但如果模板没有，可以尝试设置默认样式。


    # --- 保存 PPTX 文件 ---
    output_dir = "generated_pptx"
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, f"presentation_{presentation_id}.pptx")
    prs.save(filepath)

    return filepath

# --- 用于本地测试此模块的代码 (可选) ---
if __name__ == "__main__":
    # 假设的幻灯片数据
    test_slides_data = [
        {"title": "测试模板应用", "points": ["这是一个带模板的要点"], "notes": "这页使用模板生成。"},
    ]
    test_id = "test_template_pptx"
    # 需要指定一个实际存在的模板文件路径进行测试
    # 例如，如果你的模板文件是 backend/templates/simple_template.pptx
    import os
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    TEST_TEMPLATE_PATH = os.path.join(BASE_DIR, "templates", "simple_template.pptx") # <--- **请检查并修改路径**

    print("Running PPTX generation test with template...")
    try:
        # 调用函数生成 PPTX 文件，传入模板路径
        generated_filepath = create_presentation_file(test_id, test_slides_data, template_path=TEST_TEMPLATE_PATH)
        print(f"Test PPTX generated at: {generated_filepath}")
        # 您可以在文件浏览器中找到这个文件并打开检查，看是否应用了模板样式。
    except FileNotFoundError:
         print(f"Error: Test template file not found at {TEST_TEMPLATE_PATH}. Cannot run test.")
    except Exception as e:
        print(f"PPTX test failed: {e}")