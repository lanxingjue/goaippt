import React, { useState } from 'react';
// 导入 React Router 的核心组件和 Hook
import { Routes, Route, useNavigate } from 'react-router-dom';
// 导入我们创建的编辑器页面组件
import EditorPage from './EditorPage';

// 导入 CSS Modules 样式文件
import styles from './App.module.css';
// 不再需要导入 ./App.css

function App() {
  // App 组件现在主要作为应用的顶级容器和路由配置中心，
  // 同时也包含了主页（生成页面）的逻辑。

  // --- 状态管理 (仅用于主页生成功能) ---
  const [inputText, setInputText] = useState(''); // 存储文本输入框的内容
  const [loading, setLoading] = useState(false); // 存储是否正在加载/生成中
  const [error, setError] = useState(null); // 存储发生的错误信息

  // 从环境变量中读取后端API的基础URL。这是我们在 frontend/.env 文件中设置的。
  const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

  // 获取 navigate 函数，用于在代码中进行页面跳转
  const navigate = useNavigate();

  // --- 事件处理函数 (仅用于主页生成按钮) ---
  const handleGenerate = async () => {
    // 输入校验
    if (!inputText.trim()) {
      setError("Please enter some text.");
      return;
    }

    // 重置状态，开始加载
    setLoading(true);
    setError(null);

    try {
      // 向后端发送 POST 请求，触发 PPT 生成 API
      // 后端现在直接返回生成的演示文稿数据，而不是只返回ID
      const response = await fetch(`${API_BASE_URL}/api/presentations/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: inputText }), // 将输入的文本作为 JSON 数据发送
      });

      // 检查 HTTP 响应状态码
      if (!response.ok) {
        const errorData = await response.json();
        // 尝试从 detail 中获取更具体的错误信息
        const errorMessage = typeof errorData.detail === 'string' ? errorData.detail : 'Generation failed';
        throw new Error(errorMessage);
      }

      // 解析后端返回的 JSON 数据，获取整个演示文稿对象
      const presentationData = await response.json();
      console.log("Generated presentation data received:", presentationData);
      // 生成成功后，使用 navigate 函数跳转到编辑器页面，并将 PPT ID 作为 URL 参数传递。
      // 例如，ID 为 "abc" 的演示文稿会跳转到 "/edit/abc"。
      // EditorPage 会通过 URL 参数获取 ID，并发送 GET 请求加载数据。
      if(presentationData && presentationData.id) {
         navigate(`/edit/${presentationData.id}`);
      } else {
         // 如果后端没有返回ID，说明生成失败
         throw new Error("Generation succeeded but no presentation ID returned.");
      }


    } catch (err) {
      // 捕获并处理生成过程中的错误
      console.error("Generation error:", err);
      setError(err.message); // 设置错误信息以便在界面上显示
    } finally {
      // 无论成功或失败，结束加载状态
      setLoading(false);
    }
  };

  // --- 组件渲染 ---
  // App 组件的 render 方法主要用来定义路由规则。
  // 不同的 URL 路径将渲染不同的组件（例如 App 的主页内容或 EditorPage）。
  return (
     // 使用 styles.app 类来包裹整个应用内容，以便应用全局的赛博朋克样式、背景等。
     // 这个 div 是路由渲染内容的容器。
     <div className={styles.app}>
        {/* Routes 组件用于包裹所有的 Route 定义 */}
        <Routes>
            {/* Route 定义：当 URL 路径是 "/" 时，渲染主页内容 */}
            <Route path="/" element={
                <> {/* 使用 Fragment 来包裹多个同级元素，避免额外的 DOM 节点 */}
                    {/* 主页头部 */}
                    <header className={styles.header}> {/* 应用 header 类的样式 */}
                        <h1>AI Presentation Generator</h1> {/* 应用头部样式和标题样式 */}
                    </header>
                     {/* 主页主要内容区域 */}
                     <main>
                        {/* 输入区域容器 */}
                        <div className={styles.inputSection}> {/* 应用 inputSection 类的样式 */}
                            <h2>Enter your text or outline</h2> {/* 输入区域标题 */}
                            <textarea
                                rows="10"
                                cols="80"
                                value={inputText} // 绑定到状态
                                onChange={(e) => setInputText(e.target.value)} // 状态更新
                                placeholder="Paste your document, report, or outline here..." // 占位符文本
                                disabled={loading} // 根据加载状态禁用
                            />
                            {/* 生成按钮 */}
                            <button
                                className={styles.neonButton} // 应用赛博朋克按钮样式
                                onClick={handleGenerate} // 绑定点击事件
                                disabled={loading} // 根据加载状态禁用
                                data-loading={loading ? "true" : "false"} // 添加数据属性用于CSS动画
                            >
                                {loading ? 'Processing Data...' : 'Generate Presentation'} {/* 根据加载状态显示不同文本 */}
                            </button>
                            {/* 消息显示区域 */}
                            <div className={styles.messageArea}> {/* 应用 messageArea 类的样式 */}
                                {/* 加载中提示 */}
                                {loading && (
                                     <p className={styles.loadingMessage}>
                                         Processing Data: Analyzing Inputs...
                                         {/* 添加闪烁点元素，应用 styles.pulsingDots 类 */}
                                         <span className={styles.pulsingDots}>. . .</span>
                                     </p>
                                )}
                                {/* 错误提示 */}
                                {error && <p className={styles.errorMessage}>Error: {error}</p>}
                            </div>
                        </div>
                     </main>
                </>
            } />

            {/* Route 定义：当 URL 路径匹配 "/edit/:presentationId" 模式时，渲染 EditorPage 组件 */}
            <Route path="/edit/:presentationId" element={<EditorPage />} />

            {/* TODO: 可以添加一个匹配所有未定义路径的 404 Not Found 页面路由 */}
            {/* <Route path="*" element={<NotFoundPage />} /> */}
        </Routes>
     </div>
  );
}

export default App; // 导出 App 组件