import React, { useState, useEffect } from 'react';
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

  // --- 副作用：页面加载时获取数据 --- (保持不变)
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        console.log(`Fetching presentation with ID: ${presentationId}`);
        const presentationResponse = await fetch(`${API_BASE_URL}/api/presentations/${presentationId}`);
        if (!presentationResponse.ok) {
          const errorData = await presentationResponse.json();
          throw new Error(errorData.detail || 'Failed to fetch presentation');
        }
        const presentationData = await presentationResponse.json();
        setPresentation(presentationData);
        console.log("Fetched presentation data:", presentationData);

        setSelectedTemplateId(presentationData.template_id);

        if (presentationData && presentationData.slides && presentationData.slides.length > 0) {
           setCurrentSlideIndex(0);
        } else {
           // 如果没有幻灯片，创建一个默认空幻灯片
           console.warn("No slides found for this presentation. Creating a default empty slide.");
           const updatedPresentation = deepCopy(presentationData);
           updatedPresentation.slides = [{
                id: 'temp-' + Date.now(), // 临时ID，保存到后端会被替换
                order: 0,
                title: "First Slide",
                content: "",
                notes: ""
           }];
           setPresentation(updatedPresentation);
           setCurrentSlideIndex(0);
        }

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
      } finally {
        setLoading(false);
      }
    };

    if (presentationId) {
      fetchData();
    } else {
        setError("No presentation ID provided in URL.");
        setLoading(false);
    }

  }, [presentationId, API_BASE_URL]);


  // --- 处理内容编辑 --- (保持不变)
  const handleContentChange = (field, value) => {
    if (!presentation || !presentation.slides || currentSlideIndex < 0) return;

    const updatedPresentation = deepCopy(presentation);
    const slideToUpdate = updatedPresentation.slides[currentSlideIndex];

    if (!slideToUpdate) return;

    slideToUpdate[field] = value;
    setPresentation(updatedPresentation);
    setSaveSuccess(false);
  };

   // --- 处理模板选择变化 --- (保持不变)
   const handleTemplateChange = (event) => {
       setSelectedTemplateId(event.target.value);
       setSaveSuccess(false);
   };

  // --- 切换当前编辑的幻灯片 --- (保持不变)
  const handleSelectSlide = (index) => {
    if (presentation && presentation.slides && index >= 0 && index < presentation.slides.length) {
        setCurrentSlideIndex(index);
    }
  };

  // --- 处理新增幻灯片 ---
  const handleAddSlide = () => {
    if (!presentation) return;

    const updatedPresentation = deepCopy(presentation);
    const newSlide = {
        // 使用临时 ID，保存到后端时数据库会分配新的永久 ID
        id: 'temp-' + Date.now() + Math.random(),
        order: updatedPresentation.slides.length, // 新幻灯片放在最后
        title: "New Slide",
        content: "",
        notes: ""
    };
    updatedPresentation.slides.push(newSlide); // 添加到列表末尾

    // 重新给所有幻灯片按在列表中的位置赋予 order
    updatedPresentation.slides.forEach((slide, index) => {
        slide.order = index;
    });


    setPresentation(updatedPresentation);
    setCurrentSlideIndex(updatedPresentation.slides.length - 1); // 选中新添加的幻灯片
    setSaveSuccess(false);
  };

  // --- 处理删除幻灯片 ---
  const handleDeleteSlide = (indexToDelete) => {
    if (!presentation || !presentation.slides || presentation.slides.length <= 1) {
        // 不允许删除最后一页
        console.warn("Cannot delete the last slide.");
        return;
    }
     // 确认删除
    if (!window.confirm(`Are you sure you want to delete slide ${indexToDelete + 1}?`)) {
        return; // 用户取消删除
    }


    const updatedPresentation = deepCopy(presentation);
    // 从列表中移除指定索引的幻灯片
    updatedPresentation.slides.splice(indexToDelete, 1);

    // 重新给剩余幻灯片按在列表中的位置赋予 order
    updatedPresentation.slides.forEach((slide, index) => {
        slide.order = index;
    });

    // 更新状态
    setPresentation(updatedPresentation);

    // 更新当前选中幻灯片的索引
    if (indexToDelete === currentSlideIndex) {
        // 如果删除了当前页，选中前一页或第一页
        setCurrentSlideIndex(Math.max(0, currentSlideIndex - 1));
    } else if (indexToDelete < currentSlideIndex) {
        // 如果删除了当前页之前的页，当前页的索引需要减 1
        setCurrentSlideIndex(currentSlideIndex - 1);
    }
    // 如果删除了当前页之后的页，当前页索引不变

    setSaveSuccess(false);
  };


  // --- 处理保存修改 --- (保持不变)
  const handleSave = async () => {
    if (!presentation || saving) return;

    setSaving(true);
    setError(null);
    setSaveSuccess(false);

    try {
      const response = await fetch(`${API_BASE_URL}/api/presentations/${presentationId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            id: presentation.id,
            slides: presentation.slides,
            template_id: selectedTemplateId,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to save presentation');
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

    // --- 处理下载 PPTX --- (保持不变)
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
                <p className={styles.loadingMessage}>Establishing Neural Link: Fetching Data Stream...</p>
            </div></main>
        </div>
    );
  }

  if (error || !presentation) {
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


  return (
    <div className={styles.app}>
      <header className={styles.header}>
        <h1>Edit Presentation</h1>
      </header>

      <main className={styles.editorLayout}>

        {/* 左侧：幻灯片列表区域 */}
        <div className={styles.slideList}>
          <h3>Slides ({presentation.slides ? presentation.slides.length : 0})</h3>
          <ul>
            {presentation.slides && Array.isArray(presentation.slides) && presentation.slides.map((slide, index) => (
              <li
                key={slide.id || `temp-${index}`} // 使用 slide.id 作为 key，如果 AI 生成的没有 ID 或为 null，使用临时 index-based key
                className={`${styles.slideListItem} ${index === currentSlideIndex ? styles.activeSlide : ''}`}
                onClick={() => handleSelectSlide(index)}
              >
                <span className={styles.slideOrder}>[{index + 1}]</span> {slide.title || 'Untitled'}
                {/* 删除幻灯片按钮 */}
                {/* 不允许删除最后一页 */}
                 {presentation.slides.length > 1 && (
                     <button
                         className={styles.deleteSlideButton} // 应用删除按钮样式
                         onClick={(e) => {
                             e.stopPropagation(); // 阻止事件冒泡到 li 的 onClick，避免切换幻灯片
                             handleDeleteSlide(index); // 调用删除函数
                         }}
                         disabled={saving} // 保存中禁用删除
                     >
                         ×
                     </button>
                 )}
              </li>
            ))}
          </ul>
           {/* 新增幻灯片按钮 */}
           <button className={styles.addSlideButton} onClick={handleAddSlide} disabled={saving}>
               + Add Slide
           </button>

        </div>

        {/* 右侧：当前幻灯片详细编辑区域 */}
        <div className={styles.slideEditor}>
          {currentSlide ? (
            <> {/* Fragment 开始 */}
              <h3>Slide {currentSlideIndex + 1} / {presentation.slides.length}</h3>

              {/* 模板选择下拉框 */}
              <div className={styles.editorField}>
                  <label htmlFor="template-select">Select Template:</label>
                   <select
                       id="template-select"
                       value={selectedTemplateId || ''}
                       onChange={handleTemplateChange}
                       className={styles.editorSelect} // 应用 Select 样式
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

               {/* 操作按钮区域 */}
               <div className={styles.editorActions}>
                   {/* 保存按钮 */}
                   <button
                       className={styles.neonButton}
                       onClick={handleSave}
                       disabled={saving}
                   >
                       {saving ? 'Saving Changes...' : 'Save Changes'}
                   </button>
                   {/* 下载按钮 */}
                    <button
                       className={styles.downloadButton}
                       onClick={handleDownload}
                       disabled={saving}
                   >
                       Download Edited PPTX File
                   </button>
                    {/* 保存成功提示 */}
                    {saveSuccess && <span className={styles.saveSuccessMessage}>Data Synchronized!</span>}
               </div>

            </> // Fragment 结束
          ) : (
            // 如果当前幻灯片对象不存在，显示提示或添加第一页按钮
            <div className={styles.messageArea}> {/* 用 div 包裹，以便添加按钮 */}
                <p>Select a slide to edit or check if presentation has slides.</p>
                {/* 如果没有幻灯片（例如删除到只剩一个后又删了），提供添加按钮 */}
                {presentation && presentation.slides && presentation.slides.length === 0 && (
                    <button className={styles.addSlideButton} onClick={handleAddSlide} disabled={saving}>
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