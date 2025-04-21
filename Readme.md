创建项目目录和文件结构: 确保你的项目目录结构如最上方所示，特别是 backend 文件夹中有一个空的 __init__.py 文件。
后端文件创建与粘贴: 在 backend 文件夹中创建 main.py, database.py, models.py, ai_generation.py, pptx_generation.py 这五个文件，并将上面对应的代码复制粘贴进去。务必修改 backend/models.py 中的 DATABASE_URL 和 backend/ai_generation.py 中的 DeepSeek API 配置。
数据库设置: 按照之前给出的步骤，安装并运行 PostgreSQL，创建 presentation_db 数据库。
后端依赖安装: 在终端中进入项目根目录 (goaippt)，激活虚拟环境 (.venv\Scripts\activate 或 source .venv/bin/activate)，然后运行 pip install fastapi uvicorn python-pptx sqlalchemy psycopg2-binary openai pydantic。
后端环境变量: 如果使用环境变量配置 DeepSeek API，请在终端中设置好 DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL_NAME。
前端项目创建: 在终端中进入项目根目录 (goaippt)，运行 npx create-react-app frontend。如果 frontend 目录已存在，按照之前的方法先删除再创建，确保项目结构完整。
前端依赖安装: 在终端中进入 frontend 目录 (cd frontend)，运行 npm install react-router-dom (或者 yarn add react-router-dom)。React 脚手架创建项目时已经安装了其他基础依赖。
前端环境变量: 在 frontend 目录下创建 .env 文件，内容为 REACT_APP_API_BASE_URL=http://localhost:8000。
前端文件创建与粘贴: 在 frontend/src/ 目录下，创建 EditorPage.js 和 App.module.css 这两个文件，并将上面对应的代码复制粘贴进去。
修改前端现有文件: 打开 frontend/src/index.js 和 frontend/src/App.js 文件，将上面对应的代码复制粘贴进去，覆盖原有内容。
添加字体 (可选): 在 frontend/public/index.html 的 <head> 中添加 Google Fonts 链接，或者在 App.module.css 中使用 @import 导入字体（推荐使用 @import 并确保在 CSS 变量前）。
启动后端: 在终端中进入项目根目录 (goaippt)，确保虚拟环境激活，运行 uvicorn backend.main:app --reload。检查终端输出，确保数据库初始化和应用启动成功。
启动前端: 在终端中进入 frontend 目录 (cd frontend)，运行 npm start (或 yarn start)。浏览器应该会自动打开 http://localhost:3000。
测试: 在浏览器中访问 http://localhost:3000，输入文本，点击生成，应该会跳转到编辑器页面，然后可以在编辑器中修改并保存，最后下载。

pip install fastapi uvicorn python-pptx sqlalchemy psycopg2-binary openai pydantic