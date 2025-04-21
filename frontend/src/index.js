import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css'; // 导入全局 CSS 文件 (create-react-app 默认生成)
import App from './App';
// 导入 BrowserRouter，它是 React Router 的一个路由容器组件
import { BrowserRouter } from 'react-router-dom';

// 获取应用的根 DOM 元素
const root = ReactDOM.createRoot(document.getElementById('root'));

// 使用 root.render 方法渲染 React 应用
root.render(
  // <React.StrictMode> 是一个开发者工具，用于检测代码中的潜在问题，在生产环境中会自动禁用。
  <React.StrictMode>
    {/* 将整个 App 组件包裹在 <BrowserRouter> 中。
        这是使用 React Router 进行客户端路由所必需的。
        它使得 App 组件及其内部的组件可以使用路由功能（如 <Route>, useNavigate, useParams 等）。 */}
    <BrowserRouter>
      <App /> {/* App 组件是应用的入口 */}
    </BrowserRouter>
  </React.StrictMode>
);

// 如果您的项目中有报告性能或分析相关的代码，可以保留或移除。
// import reportWebVitals from './reportWebVitals';
// reportWebVitals();