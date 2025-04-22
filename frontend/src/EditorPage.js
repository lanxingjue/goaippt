import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import styles from './App.module.css';

const deepCopy = (obj) => {
    try {
        return JSON.parse(JSON.stringify(obj));
    } catch (e) {
        console.error("Failed to deep copy object:", e);
        return obj;
    }
};

// --- EditorPage 组件定义 ---
function EditorPage() {
  const { presentationId } = useParams();
  const navigate = useNavigate();

  // --- 状态管理 ---
  const [presentation, setPresentation] = useState(null);
  const [currentSlideIndex, setCurrentSlideIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [templates, setTemplates] = useState([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState(null);


  const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

   // --- 辅助函数：根据本地图片路径构建可访问的 URL ---
   // 后端静态文件服务挂载在 /static
   const buildStaticImageUrl = useCallback((localImagePath) => {
       if (!localImagePath) {
           // 如果没有匹配到本地图片，可以返回一个前端默认的“无图片”占位符 URL
           // 例如：'/images/no-image-placeholder.png' (放在 frontend/public 目录下)
           // 或者返回 null，在渲染时判断不显示图片
           return null; // MVP 阶段没有匹配到图片则不显示图片
       }
       // localImagePath 是相对于 backend/static 的路径，例如 "images/tech1.jpg"
       // 后端静态服务挂载在 /static
       return `${API_BASE_URL}/static/${localImagePath}`; // <--- 构建本地图片的可访问 URL
   }, [API_BASE_URL]); // 依赖项，API_BASE_URL 变化时重新创建


  // --- 副作用：页面加载时获取数据 ---
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        console.log(`Fetching presentation with ID: ${presentationId}`);
        // 向后端发送 GET 请求获取演示文稿数据
        const presentationResponse = await fetch(`${API_BASE_URL}/api/presentations/${presentationId}`);
        if (!presentationResponse.ok) {
          const errorData = await presentationResponse.json();
          throw new Error(errorData.detail || 'Failed to fetch presentation');
        }
        const presentationData = await presentationResponse.json();
        setPresentation(presentationData);
        console.log("Fetched presentation data:", presentationData);

        // 设置当前选中的模板ID
        setSelectedTemplateId(presentationData.template_id);

        // 如果获取的数据中没有幻灯片，或者幻灯片列表为空，创建一个默认空幻灯片
        if (!presentationData || !presentationData.slides || presentationData.slides.length === 0) {
           console.warn("No slides found for this presentation. Creating a default empty slide.");
           const updatedPresentation = deepCopy(presentationData || {}); // 如果presentationData是null或undefined，创建一个空对象
           updatedPresentation.slides = [{
                id: 'temp-' + Date.now(),
                order: 0,
                title: "First Slide",
                content: "",
                notes: "",
                visual_keywords: [],
                local_image_path: null 
           }];
           setPresentation(updatedPresentation);
           setCurrentSlideIndex(0);
        } else {
           // 如果有幻灯片，默认选中第一页 (索引 0)
           setCurrentSlideIndex(0);
        }


        // 获取可用模板列表
        console.log("Fetching templates list...");
        const templatesResponse = await fetch(`${API_BASE_URL}/api/templates`);
         if (!templatesResponse.ok) {
             const errorData = await templatesResponse.json();
             throw new Error(errorData.detail || 'Failed to fetch templates list');
         }
         const templatesData = await templatesResponse.json();
         setTemplates(templatesData);
         console.log("Fetched templates list:", templatesData);

      } catch (err) {
        console.error("Fetch error:", err);
        setError(err.message);
         if (presentationId) {
            // 可以在这里设置一个状态来控制显示“返回”按钮
         }
      } finally {
        setLoading(false);
      }
    };

    if (presentationId) {
      fetchData();
    } else {
        setError("No presentation ID provided in URL.");
        setLoading(false);
        setTimeout(() => {
            navigate('/');
        }, 3000);
    }

  }, [presentationId, API_BASE_URL, navigate]);


  // --- 处理内容编辑 (包括视觉关键词和本地图片路径 - 虽然UI还没编辑) ---
  const handleContentChange = (field, value) => {
    if (!presentation || !presentation.slides || currentSlideIndex < 0) return;

    const updatedPresentation = deepCopy(presentation);
    const slideToUpdate = updatedPresentation.slides[currentSlideIndex];

    if (!slideToUpdate) return;

    if (field === 'visual_keywords_string') {
        slideToUpdate['visual_keywords'] = value.split(/[,\s]+/).map(k => k.trim()).filter(k => k);
    } else {
        slideToUpdate[field] = value;
    }


    setPresentation(updatedPresentation);
    setSaveSuccess(false);
  };

   // --- 处理模板选择变化 ---
   const handleTemplateChange = (event) => {
       setSelectedTemplateId(event.target.value);
       setSaveSuccess(false);
   };

  // --- 切换当前编辑的幻灯片 ---
  const handleSelectSlide = (index) => {
    if (presentation && presentation.slides && index >= 0 && index < presentation.slides.length && index !== currentSlideIndex) {
        setCurrentSlideIndex(index);
        setSaveSuccess(false);
    }
  };

  // --- 处理新增幻灯片 ---
  const handleAddSlide = () => {
    if (!presentation) return;

    const updatedPresentation = deepCopy(presentation);
    const newSlide = {
        id: 'temp-' + Date.now() + Math.random(),
        order: updatedPresentation.slides.length,
        title: "New Slide",
        content: "",
        notes: "",
        visual_keywords: [],
        local_image_path: null 
    };
    updatedPresentation.slides.push(newSlide);

    updatedPresentation.slides.forEach((slide, index) => {
        slide.order = index;
    });


    setPresentation(updatedPresentation);
    setCurrentSlideIndex(updatedPresentation.slides.length - 1);
    setSaveSuccess(false);
  };

  // --- 处理删除幻灯片 ---
  const handleDeleteSlide = (indexToDelete) => {
    if (!presentation || !presentation.slides || presentation.slides.length <= 1) {
        console.warn("Cannot delete the last slide. A presentation must have at least one slide.");
        setError("Cannot delete the last slide.");
        setTimeout(() => setError(null), 3000);
        return;
    }
    if (!window.confirm(`Are you sure you want to delete slide ${indexToDelete + 1} "${presentation.slides[indexToDelete].title || 'Untitled'}"?`)) {
        return;
    }

    const updatedPresentation = deepCopy(presentation);
    updatedPresentation.slides.splice(indexToDelete, 1);

    updatedPresentation.slides.forEach((slide, index) => {
        slide.order = index;
    });

    setPresentation(updatedPresentation);

    if (indexToDelete === currentSlideIndex) {
        setCurrentSlideIndex(Math.max(0, currentSlideIndex - 1));
    } else if (indexToDelete < currentSlideIndex) {
        setCurrentSlideIndex(currentSlideIndex - 1);
    }

    setSaveSuccess(false);
  };


  // --- 处理保存修改 ---
  const handleSave = async () => {
    if (!presentation || saving) return;

    setSaving(true);
    setError(null);
    setSaveSuccess(false);

    try {
      const dataToSend = {
            id: presentation.id,
            slides: presentation.slides.map(slide => ({
                // MVP 先删后插，只发送需要保存到数据库的字段
                order: slide.order,
                title: slide.title,
                content: slide.content,
                notes: slide.notes,
                visual_keywords: slide.visual_keywords,
                 local_image_path: slide.local_image_path, // <--- 发送本地图片路径给后端保存
            })),
            template_id: selectedTemplateId,
      };

      console.log("Saving data:", dataToSend);

      const response = await fetch(`${API_BASE_URL}/api/presentations/${presentationId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(dataToSend),
      });

      if (!response.ok) {
        const errorData = await response.json();
        const errorMessage = typeof errorData.detail === 'string' ? errorData.detail : 'Failed to save presentation';
        throw new Error(errorMessage);
      }

      console.log("Presentation saved successfully.");
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);

    } catch (err) {
      console.error("Save error:", err);
      setError(err.message);
      setSaveSuccess(false);
    } finally {
      setSaving(false);
    }
  };

    // --- 处理下载 PPTX ---
   const handleDownload = () => {
        if (presentationId && !saving) {
            const downloadUrl = `${API_BASE_URL}/api/presentations/${presentationId}/download`;
            window.open(downloadUrl, '_blank');
        }
   };


  // --- 条件渲染：根据状态显示不同内容 ---

  if (loading) {
    return (
        <div className={styles.app}>
            <header className={styles.header}><h1>Loading Presentation...</h1></header>
            <main><div className={styles.messageArea}>
                <p className={styles.loadingMessage}>
                    Establishing Neural Link: Fetching Data Stream...
                    <span className={styles.pulsingDots}>. . .</span>
                </p>
            </div></main>
        </div>
    );
  }

  if (error || !presentation || !presentation.slides) {
    return (
         <div className={styles.app}>
            <header className={styles.header}><h1>Error</h1></header>
             <main><div className={styles.messageArea}>
                <p className={styles.errorMessage}>Error: {error || "Presentation data not found."}</p>
                <button className={styles.neonButton} onClick={() => navigate('/')}>Go Back to Generator</button>
             </div></main>
        </div>
    );
  }

  const currentSlide = (presentation && presentation.slides && currentSlideIndex >= 0 && currentSlideIndex < presentation.slides.length) ? presentation.slides[currentSlideIndex] : null;

  // 生成当前幻灯片预览图的 URL (使用匹配到的本地图片路径)
  const currentSlideImageUrl = currentSlide ? buildStaticImageUrl(currentSlide.local_image_path) : null;


  // --- 主要编辑界面渲染 ---
  return (
    <div className={styles.app}>
      <header className={styles.header}>
        <h1>Edit Presentation</h1>
      </header>

      <main className={styles.editorLayout}>

        {/* 左侧：幻灯片列表区域 */}
        <div className={styles.slideList}>
          <h3>Slides ({presentation.slides.length})</h3>
          <ul>
            {presentation.slides.map((slide, index) => (
              <li
                key={slide.id || `temp-${index}`}
                className={`${styles.slideListItem} ${index === currentSlideIndex ? styles.activeSlide : ''}`}
                onClick={() => handleSelectSlide(index)}
              >
                <span className={styles.slideOrder}>[{index + 1}]</span>
                <span>{slide.title || 'Untitled'}</span>
                 {presentation.slides.length > 1 && (
                     <button
                         className={styles.deleteSlideButton}
                         onClick={(e) => {
                             e.stopPropagation();
                             handleDeleteSlide(index);
                         }}
                         disabled={saving}
                     >
                         ×
                     </button>
                 )}
              </li>
            ))}
          </ul>
           <button className={styles.addSlideButton} onClick={handleAddSlide} disabled={saving}>
               + Add Slide
           </button>

        </div>

        {/* 右侧：当前幻灯片详细编辑区域 */}
        <div className={styles.slideEditor}>
          {currentSlide ? (
            <>
              <h3>Slide {currentSlideIndex + 1} / {presentation.slides.length}</h3>

              {/* --- 模拟幻灯片预览区域 --- */}
              <div className={styles.slidePreview}>
                  {/* 图片预览 - 只有当 local_image_path 存在时才显示图片 */}
                   {currentSlideImageUrl && (
                       <div className={styles.previewImageContainer}>
                           {/* 使用后端静态文件服务的 URL 加载图片 */}
                           <img src={currentSlideImageUrl} alt="Slide Visual Suggestion" className={styles.previewImage} />
                       </div>
                   )}
                   {/* 如果没有图片，可以显示一个占位符或者提示 */}
                   {!currentSlideImageUrl && (
                       <div className={styles.previewNoImage}>
                           No Image Matched or Available
                       </div>
                   )}


                  {/* 标题预览 */}
                  {/* 根据是否有图片调整标题位置 */}
                  <div className={`${styles.previewTitle} ${!currentSlideImageUrl ? styles.previewTitleNoImage : ''}`}>
                       {currentSlide.title || 'Untitled Slide'}
                  </div>


                  {/* 内容（要点）预览 */}
                  {/* 根据是否有图片调整内容位置和宽度 */}
                  <ul className={`${styles.previewContent} ${!currentSlideImageUrl ? styles.previewContentNoImage : ''}`}>
                      {currentSlide.content && currentSlide.content.split('\n').map((point, idx) =>
                           point.trim() && <li key={idx} className={styles.previewPoint}>{point.trim()}</li>
                      )}
                  </ul>

              </div>


              {/* --- 编辑表单区域 --- */}

              {/* 模板选择下拉框 */}
              <div className={styles.editorField}>
                  <label htmlFor="template-select">Select Template:</label>
                   <select
                       id="template-select"
                       value={selectedTemplateId || ''}
                       onChange={handleTemplateChange}
                       className={styles.editorSelect}
                       disabled={templates.length === 0 || saving || loading}
                   >
                       {!selectedTemplateId && <option value="">-- Select a Template --</option>}
                       {templates.map(template => (
                           <option key={template.id} value={template.id}>
                               {template.name}
                           </option>
                       ))}
                       {templates.length === 0 && <option value="" disabled>No templates available</option>}
                   </select>
              </div>


              {/* 标题编辑字段 */}
              <div className={styles.editorField}>
                <label>Title:</label>
                <input
                  type="text"
                  value={currentSlide.title || ''}
                  onChange={(e) => handleContentChange('title', e.target.value)}
                  className={styles.editorInput}
                />
              </div>

              {/* 内容要点编辑字段 */}
              <div className={styles.editorField}>
                <label>Content (Points per line):</label>
                <textarea
                  rows="10"
                  value={currentSlide.content || ''}
                  onChange={(e) => handleContentChange('content', e.target.value)}
                  className={styles.editorTextarea}
                />
              </div>

              {/* 备注编辑字段 */}
              <div className={styles.editorField}>
                <label>Notes:</label>
                <textarea
                  rows="10"
                  value={currentSlide.notes || ''}
                  onChange={(e) => handleContentChange('notes', e.target.value)}
                  className={styles.editorTextarea}
                />
              </div>

              {/* 视觉关键词编辑字段 (目前仅展示 AI 生成的关键词，作为手动编辑的准备) */}
              {/* 未来这里可能提供 UI 让用户修改关键词或直接上传图片 */}
              <div className={styles.editorField}>
                <label>Visual Keywords:</label>
                 {/* 使用输入框或简单的文本展示关键词数组 */}
                 {/* 暂时使用输入框，但禁用编辑，只用于展示 */}
                 <input
                    type="text"
                    value={currentSlide.visual_keywords ? currentSlide.visual_keywords.join(', ') : 'No keywords generated'}
                    className={styles.editorInput}
                    readOnly // 设置为只读
                    disabled={true} // 禁用编辑
                 />
              </div>

               {/* 操作按钮区域 */}
               <div className={styles.editorActions}>
                   <button
                       className={styles.neonButton}
                       onClick={handleSave}
                       disabled={saving}
                   >
                       {saving ? 'Synchronizing Data...' : 'Save Changes'}
                   </button>
                    <button
                       className={styles.downloadButton}
                       onClick={handleDownload}
                       disabled={saving}
                   >
                       Download Edited PPTX File
                   </button>
                    {saveSuccess && <span className={styles.saveSuccessMessage}>Data Synchronized!</span>}
               </div>

            </>
          ) : (
            <div className={styles.messageArea}>
                <p>Select a slide from the left panel to edit.</p>
                {presentation && presentation.slides && presentation.slides.length === 0 && (
                    <button className={`${styles.addSlideButton} ${styles.messageAreaAddButton}`} onClick={handleAddSlide} disabled={saving}>
                       + Add First Slide
                   </button>
                )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default EditorPage;