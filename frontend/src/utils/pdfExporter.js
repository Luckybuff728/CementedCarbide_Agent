/**
 * 实验工单 PDF 导出工具
 * 
 * 专门处理实验工单的 Markdown 格式，手动解析并转换为格式化 HTML
 * 支持：标题、表格、列表、粗体等格式
 */

import html2canvas from 'html2canvas'
import { jsPDF } from 'jspdf'

/**
 * 手动解析 Markdown 为 HTML（专门针对实验工单格式）
 * @param {string} markdown - Markdown 文本
 * @returns {string} HTML 字符串
 */
function parseMarkdownToHTML(markdown) {
  if (!markdown) return ''
  
  let html = markdown
  
  // 1. 处理表格（必须在其他处理之前）
  html = html.replace(/\|(.+)\|\n\|[-:\s|]+\|\n((?:\|.+\|\n?)+)/g, (match, header, body) => {
    const headerCells = header.split('|').map(cell => cell.trim()).filter(Boolean)
    const headerRow = headerCells.map(cell => `<th>${cell}</th>`).join('')
    
    const bodyRows = body.trim().split('\n').map(row => {
      const cells = row.split('|').map(cell => cell.trim()).filter(Boolean)
      return `<tr>${cells.map(cell => `<td>${cell}</td>`).join('')}</tr>`
    }).join('')
    
    return `<table><thead><tr>${headerRow}</tr></thead><tbody>${bodyRows}</tbody></table>`
  })
  
  // 2. 处理标题
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>')
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>')
  html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>')
  
  // 3. 处理粗体
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
  
  // 4. 处理有序列表（数字开头）
  html = html.replace(/^(\d+)\.\s+(.+)$/gm, '<li class="ordered">$2</li>')
  
  // 5. 处理无序列表（- 开头）
  html = html.replace(/^-\s+(.+)$/gm, '<li>$1</li>')
  
  // 6. 处理缩进的子列表项（以空格或 tab 开头的 -）
  html = html.replace(/^\s+-\s+(.+)$/gm, '<li class="sub">$1</li>')
  
  // 7. 将连续的 li 包装成 ul/ol
  html = html.replace(/((?:<li[^>]*>.*?<\/li>\s*)+)/g, (match) => {
    if (match.includes('class="ordered"')) {
      return `<ol>${match.replace(/ class="ordered"/g, '')}</ol>`
    }
    return `<ul>${match}</ul>`
  })
  
  // 8. 处理段落（非空行且不是已处理的标签）
  const lines = html.split('\n')
  html = lines.map(line => {
    const trimmed = line.trim()
    if (!trimmed) return ''
    if (trimmed.startsWith('<')) return line  // 已经是 HTML 标签
    return `<p>${trimmed}</p>`
  }).join('\n')
  
  // 9. 清理多余空行
  html = html.replace(/\n{2,}/g, '\n')
  
  return html
}

/**
 * 生成工单 PDF（支持中文，智能分页）
 * @param {string} markdownContent - Markdown 格式的工单内容
 * @param {string} workorderNumber - 工单编号（系统自动生成）
 * @param {string} solutionName - 方案名称
 * @returns {Promise<string>} 文件名
 */
export async function generateWorkorderPDF(markdownContent, workorderNumber, solutionName = 'AlTiN涂层性能优化') {
  // 获取当前时间
  const dateStr = new Date().toLocaleString('zh-CN')
  
  // 清理 Markdown 内容，移除会在 PDF 头部重复显示的信息
  let cleanedContent = markdownContent
    // 移除代码块标记 ```markdown 和 ```
    .replace(/```markdown\s*/gi, '')
    .replace(/```\s*/g, '')
    // 移除 "# 实验工单" 标题
    .replace(/^#\s*实验工单\s*$/gm, '')
    // 移除整个基本信息章节
    .replace(/^##\s*基本信息[\s\S]*?(?=##\s*实验目的|##\s*涂层配方|$)/m, '')
    // 移除单独的优化方案和方案名称行（已在头部显示）
    .replace(/^-\s*优化方案[：:]\s*.+$/gm, '')
    .replace(/^-\s*方案名称[：:]\s*.+$/gm, '')
    // 移除"数据记录"章节（不需要打印）
    .replace(/^##\s*数据记录[\s\S]*$/m, '')
    // 移除空行
    .replace(/\n{3,}/g, '\n\n')
    .trim()
  
  // 手动解析 Markdown 为 HTML
  const htmlContent = parseMarkdownToHTML(cleanedContent)
  
  console.log('[PDF] 转换后 HTML:', htmlContent.substring(0, 500))
  
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
  
  // 构建 HTML 内容（头部 + 渲染后的 Markdown）
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
      .pdf-content li.sub {
        margin-left: 20px;
        list-style-type: circle;
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
      <h2>${solutionName || '涂层优化实验'}</h2>
      <div class="meta-info">
        <div class="meta">
          <span class="meta-label">工单编号</span>
          <span style="font-family: Consolas, monospace; color: #2980b9;">${workorderNumber}</span>
        </div>
        <div class="meta">
          <span class="meta-label">生成时间</span>
          <span>${dateStr}</span>
        </div>
      </div>
    </div>
    <div class="pdf-content">${htmlContent}</div>
  `
  
  // 添加到 DOM
  document.body.appendChild(container)
  
  // 等待渲染完成（增加等待时间确保复杂内容渲染完毕）
  await new Promise(resolve => setTimeout(resolve, 300))
  
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
