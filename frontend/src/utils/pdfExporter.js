/**
 * PDF导出工具 - 使用html2canvas + jsPDF
 * 支持中文显示和智能分页，避免表格断裂
 */

import html2canvas from 'html2canvas'
import { jsPDF } from 'jspdf'
import MarkdownIt from 'markdown-it'

/**
 * 生成工单PDF（支持中文，智能分页）
 * @param {string} markdownContent - Markdown格式的工单内容
 * @param {string} workorderNumber - 工单编号
 * @param {string} solutionName - 方案名称
 * @returns {Promise<string>} 文件名
 */
export async function generateWorkorderPDF(markdownContent, workorderNumber, solutionName = 'AlTiN涂层性能优化') {
  // 获取当前时间
  const dateStr = new Date().toLocaleString('zh-CN')
  
  // 清理Markdown内容，移除重复的标题和工单信息
  let cleanedContent = markdownContent
    // 移除 "# 实验工单" 或 "## 实验工单" 标题
    .replace(/^#+ *实验工单\s*$/gm, '')
    // 移除 "工单编号: XXX" 行
    .replace(/^\*?\*?工单编号\*?\*?\s*[:：]\s*[^\n]+$/gm, '')
    // 移除 "**工单编号**: XXX" 格式
    .replace(/\*\*工单编号\*\*\s*[:：]\s*[^\n]+/g, '')
    // 移除空行（连续的换行符）
    .replace(/\n{3,}/g, '\n\n')
    // 移除开头的空白
    .trim()
  
  // 创建临时容器（优化尺寸以适应A4纸张）
  const container = document.createElement('div')
  container.style.cssText = `
    position: fixed;
    top: -9999px;
    left: -9999px;
    width: 700px;
    padding: 25px;
    background: white;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft YaHei', 'PingFang SC', sans-serif;
  `
  
  // 解析Markdown（使用清理后的内容）
  const md = new MarkdownIt()
  const htmlContent = md.render(cleanedContent)
  
  // 构建HTML内容
  container.innerHTML = `
    <style>
      * {
        box-sizing: border-box;
      }
      .pdf-header {
        text-align: center;
        margin-bottom: 25px;
        padding-bottom: 15px;
        border-bottom: 2px solid #3498db;
      }
      .pdf-header h1 {
        font-size: 22px;
        color: #2c3e50;
        margin: 0 0 12px 0;
        line-height: 1.2;
        font-weight: 700;
      }
      .pdf-header h2 {
        font-size: 15px;
        color: #3498db;
        margin: 0 0 12px 0;
        font-weight: 600;
        line-height: 1.3;
      }
      .pdf-header .meta-info {
        display: flex;
        justify-content: center;
        gap: 35px;
        margin-top: 10px;
      }
      .pdf-header .meta {
        font-size: 10px;
        color: #666;
      }
      .pdf-header .meta-label {
        color: #999;
        margin-right: 4px;
      }
      .pdf-content {
        font-size: 12px;
        line-height: 1.6;
        color: #333;
      }
      .pdf-content h1 {
        font-size: 18px;
        margin: 20px 0 10px 0;
        color: #2c3e50;
        page-break-after: avoid;
        break-after: avoid;
      }
      .pdf-content h2 {
        font-size: 16px;
        margin: 16px 0 8px 0;
        color: #2c3e50;
        page-break-after: avoid;
        break-after: avoid;
      }
      .pdf-content h3 {
        font-size: 14px;
        margin: 14px 0 8px 0;
        color: #2c3e50;
        page-break-after: avoid;
        break-after: avoid;
      }
      .pdf-content h4 {
        font-size: 13px;
        margin: 12px 0 6px 0;
        color: #2c3e50;
      }
      .pdf-content p {
        margin: 6px 0;
        line-height: 1.6;
      }
      .pdf-content ul, .pdf-content ol {
        margin: 8px 0;
        padding-left: 22px;
        page-break-inside: avoid;
        break-inside: avoid;
      }
      .pdf-content li {
        margin: 3px 0;
        line-height: 1.5;
      }
      .pdf-content table {
        width: 100%;
        border-collapse: collapse;
        margin: 12px 0 16px 0;
        font-size: 12px;
        page-break-inside: avoid;
        break-inside: avoid;
      }
      .pdf-content table th,
      .pdf-content table td {
        border: 1px solid #ddd;
        padding: 5px 8px;
        text-align: left;
        line-height: 1.4;
      }
      .pdf-content table th {
        background-color: #f5f5f5;
        font-weight: 600;
      }
      .pdf-content strong {
        font-weight: 600;
        color: #2c3e50;
      }
      .pdf-content code {
        background-color: #f5f5f5;
        padding: 2px 5px;
        border-radius: 3px;
        font-size: 11px;
      }
    </style>
    <div class="pdf-header">
      <h1>TopMat 实验工单</h1>
      <h2>${solutionName}</h2>
      <div class="meta-info">
        <div class="meta">
          <span class="meta-label">工单编号</span>
          <span>${workorderNumber}</span>
        </div>
        <div class="meta">
          <span class="meta-label">生成时间</span>
          <span>${dateStr}</span>
        </div>
      </div>
    </div>
    <div class="pdf-content">${htmlContent}</div>
  `
  
  // 添加到DOM
  document.body.appendChild(container)
  
  // 等待渲染
  await new Promise(resolve => setTimeout(resolve, 100))
  
  // 使用html2canvas截图（高质量）
  const canvas = await html2canvas(container, {
    scale: 2.8,
    useCORS: true,
    backgroundColor: '#ffffff',
    logging: false,
    windowWidth: container.scrollWidth,
    windowHeight: container.scrollHeight
  })
  
  // 移除临时容器
  document.body.removeChild(container)
  
  // 创建PDF
  const pdf = new jsPDF({
    orientation: 'portrait',
    unit: 'mm',
    format: 'a4',
    compress: true
  })
  
  // A4纸张尺寸
  const pdfWidth = 210
  const pdfHeight = 297
  const margin = 12
  const contentWidth = pdfWidth - 2 * margin
  const contentHeight = pdfHeight - 2 * margin
  
  // 计算图片尺寸
  const imgWidth = contentWidth
  const imgHeight = (canvas.height * contentWidth) / canvas.width
  
  // 转换为图片数据
  const imgData = canvas.toDataURL('image/jpeg', 0.95)
  
  // 如果内容在一页内
  if (imgHeight <= contentHeight) {
    pdf.addImage(imgData, 'JPEG', margin, margin, imgWidth, imgHeight)
  } else {
    // 智能分页：尽量避免在不合适的位置断页
    let yOffset = 0
    let pageNum = 0
    const pageBreakMargin = 15 // 页面底部预留空间，避免在边缘断开
    
    while (yOffset < imgHeight) {
      if (pageNum > 0) {
        pdf.addPage()
      }
      
      // 计算当前页可用高度
      let availableHeight = Math.min(contentHeight, imgHeight - yOffset)
      
      // 如果不是最后一页，尝试找到更好的断页位置
      if (yOffset + contentHeight < imgHeight) {
        // 在接近页面底部时，预留一些空间避免切断内容
        availableHeight = Math.min(contentHeight - pageBreakMargin, imgHeight - yOffset)
      }
      
      // 计算源图片裁剪位置（像素）
      const sourceY = (yOffset * canvas.width) / contentWidth
      const sourceHeight = (availableHeight * canvas.width) / contentWidth
      
      // 创建临时canvas裁剪
      const pageCanvas = document.createElement('canvas')
      pageCanvas.width = canvas.width
      pageCanvas.height = sourceHeight
      
      const ctx = pageCanvas.getContext('2d')
      ctx.fillStyle = '#ffffff'
      ctx.fillRect(0, 0, pageCanvas.width, pageCanvas.height)
      ctx.drawImage(
        canvas,
        0, sourceY,
        canvas.width, sourceHeight,
        0, 0,
        canvas.width, sourceHeight
      )
      
      // 添加到PDF
      const pageImgData = pageCanvas.toDataURL('image/jpeg', 0.95)
      pdf.addImage(pageImgData, 'JPEG', margin, margin, imgWidth, availableHeight)
      
      // 更新偏移
      yOffset += availableHeight
      pageNum++
      
      // 安全检查：避免无限循环
      if (pageNum > 20) {
        console.warn('PDF页数过多，强制结束分页')
        break
      }
    }
  }
  
  // 保存PDF（文件名中去除特殊字符）
  const cleanSolutionName = solutionName.replace(/[\/\\:*?"<>|]/g, '-').substring(0, 30)
  const fileName = `TopMat_${cleanSolutionName}_${workorderNumber}.pdf`
  pdf.save(fileName)
  
  return fileName
}
