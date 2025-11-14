<template>
  <div class="performance-comparison-chart">
    <div class="chart-header">
      <div class="header-left">
        <n-icon :component="BarChartOutline" size="24" color="#6366f1" />
        <h4>性能对比图</h4>
      </div>
      <div class="chart-legend">
        <div class="legend-item">
          <span class="legend-dot experiment"></span>
          <span>实验数据</span>
        </div>
        <div class="legend-item">
          <span class="legend-dot prediction"></span>
          <span>ML预测</span>
        </div>
        <div class="legend-item">
          <span class="legend-dot historical"></span>
          <span>历史最优</span>
        </div>
      </div>
    </div>
    
    <!-- Plotly散点图容器 -->
    <div ref="plotlyChartRef" class="chart-container"></div>
    
    <!-- 切换按钮 -->
    <div class="chart-actions">
      <el-button-group>
        <el-button 
          :type="chartType === 'facet' ? 'primary' : ''" 
          size="small"
          @click="chartType = 'facet'"
        >
          分面散点图（推荐）
        </el-button>
        <el-button 
          :type="chartType === 'bar' ? 'primary' : ''" 
          size="small"
          @click="chartType = 'bar'"
        >
          分组条形图
        </el-button>
      </el-button-group>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { NIcon } from 'naive-ui'
import { BarChartOutline } from '@vicons/ionicons5'
import Plotly from 'plotly.js-dist-min'

const props = defineProps({
  // 实验数据
  experimentData: {
    type: Object,
    required: true
  },
  // ML预测数据
  predictionData: {
    type: Object,
    default: null
  },
  // 历史最优数据
  historicalBest: {
    type: Object,
    default: null
  }
})

const chartType = ref('facet') // 'facet' | 'bar'
const plotlyChartRef = ref(null)
const resizeObserver = ref(null)

// 性能指标配置（统一为4个核心指标）
const metricsConfig = [
  { key: 'hardness', label: '硬度', unit: 'GPa', color: '#8b5cf6' },
  { key: 'elastic_modulus', label: '弹性模量', unit: 'GPa', color: '#3b82f6' },
  { key: 'wear_rate', label: '磨损率', unit: 'mm³/Nm', color: '#f59e0b' },
  { key: 'adhesion_strength', label: '结合力', unit: 'N', color: '#10b981' }
]

// 创建分面散点图（专业实验数据可视化）
const createFacetScatterChart = () => {
  if (!plotlyChartRef.value) return
  
  const traces = []
  // 存储每个指标的Y轴范围，用于自适应调整
  const yRanges = {}
  
  // 为每个指标创建独立的子图
  metricsConfig.forEach((metric, index) => {
    const dataTypes = ['实验', '预测', '历史']
    const colors = ['rgb(99, 102, 241)', 'rgb(16, 185, 129)', 'rgb(245, 158, 11)']
    const symbols = ['circle', 'diamond', 'square']
    const dataSources = [
      props.experimentData,
      props.predictionData,
      props.historicalBest
    ]
    
    // 收集当前指标的所有数值，用于计算Y轴范围
    const values = []
    
    dataSources.forEach((dataSource, dataIndex) => {
      if (!dataSource) return
      
      const value = dataSource[metric.key]
      // 安全检查：value必须是有效数字
      if (value === null || value === undefined || isNaN(value)) return
      
      values.push(value)
      const dataType = dataTypes[dataIndex]
      
      // 根据数值大小智能格式化
      const formatValue = (val) => {
        if (val < 1) return val.toFixed(3)
        return val.toFixed(1)
      }
      
      traces.push({
        x: [dataType],
        y: [value],
        name: dataType,
        legendgroup: dataType,
        showlegend: index === 0, // 只在第一个子图显示图例
        type: 'scatter',
        mode: 'markers+text',
        text: [formatValue(value)],
        textposition: 'top center',
        textfont: {
          size: 12,
          color: colors[dataIndex],
          family: 'Arial, sans-serif',
          weight: 'bold'
        },
        marker: {
          size: 20,
          color: colors[dataIndex],
          symbol: symbols[dataIndex],
          line: {
            color: 'white',
            width: 2.5
          }
        },
        xaxis: `x${index + 1}`,
        yaxis: `y${index + 1}`,
        hovertemplate: `<b>${dataType}数据</b><br>${metric.label}: <b>%{y} ${metric.unit}</b><extra></extra>`
      })
    })
    
    // 计算Y轴范围：给标注留出20%的上方空间
    if (values.length > 0) {
      const minVal = Math.min(...values)
      const maxVal = Math.max(...values)
      const range = maxVal - minVal
      
      // 如果所有值相同，给一个默认范围
      if (range === 0) {
        yRanges[index + 1] = [minVal * 0.8, minVal * 1.3]
      } else {
        // 下界：留出5%的空间，但不低于0（除非有负数）
        const yMin = minVal > 0 ? Math.max(0, minVal - range * 0.05) : minVal - range * 0.05
        // 上界：留出20%的空间给文字标注
        const yMax = maxVal + range * 0.20
        yRanges[index + 1] = [yMin, yMax]
      }
    }
  })
  
  // 创建布局：2行3列排列（更舒适）
  const layout = {
    title: {
      text: '性能指标对比分析',
      font: {
        size: 17,
        family: 'Arial, sans-serif',
        weight: 'bold'
      }
    },
    showlegend: true,
    legend: {
      x: 0.5,
      xanchor: 'center',
      y: 1.08,
      yanchor: 'top',
      orientation: 'h',
      font: {
        size: 14,
        family: 'Arial, sans-serif'
      }
    },
    grid: {
      rows: 2,
      columns: 3,
      pattern: 'independent',
      xgap: 0.12,
      ygap: 0.15,
      roworder: 'top to bottom'
    },
    margin: {
      l: 60,
      r: 60,
      t: 90,
      b: 60
    },
    autosize: true,
    hovermode: 'closest'
  }
  
  // 为每个子图设置独立的坐标轴
  metricsConfig.forEach((metric, index) => {
    const axisNum = index + 1
    
    // X轴配置
    layout[`xaxis${axisNum}`] = {
      title: {
        text: `<b>${metric.label}</b><br><span style="font-size:12px">(${metric.unit})</span>`,
        font: {
          size: 14,
          family: 'Arial, sans-serif'
        },
        standoff: 15
      },
      tickfont: {
        size: 12
      },
      showgrid: false,
      fixedrange: false
    }
    
    // Y轴配置（自适应范围）
    layout[`yaxis${axisNum}`] = {
      tickfont: {
        size: 12
      },
      gridcolor: 'rgba(0,0,0,0.08)',
      fixedrange: false,
      // 应用计算好的Y轴范围，确保文字标注不被裁剪
      range: yRanges[axisNum] || undefined
    }
  })
  
  const config = {
    responsive: true,
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
    autosizable: true
  }
  
  Plotly.newPlot(plotlyChartRef.value, traces, layout, config)
}

// 创建分组条形图（更清晰）
const createBarChart = () => {
  if (!plotlyChartRef.value) return
  
  const traces = []
  const dataTypes = ['实验数据', 'ML预测', '历史最优']
  const colors = ['rgb(99, 102, 241)', 'rgb(16, 185, 129)', 'rgb(245, 158, 11)']
  const dataSources = [props.experimentData, props.predictionData, props.historicalBest]
  
  // 为每种数据来源创建一个系列
  dataTypes.forEach((dataType, index) => {
    const dataSource = dataSources[index]
    if (!dataSource) return
    
    const xValues = []
    const yValues = []
    const textValues = []
    const hoverTexts = []
    
    metricsConfig.forEach(metric => {
      const value = dataSource[metric.key]
      if (value !== null && value !== undefined) {
        xValues.push(`${metric.label}<br>(${metric.unit})`)
        yValues.push(value)
        textValues.push(value)
        hoverTexts.push(`<b>${dataType}</b><br>${metric.label}: <b>${value} ${metric.unit}</b>`)
      }
    })
    
    traces.push({
      x: xValues,
      y: yValues,
      name: dataType,
      type: 'bar',
      text: textValues,
      textposition: 'outside',
      textfont: {
        size: 14,
        family: 'Arial, sans-serif',
        color: colors[index]
      },
      marker: {
        color: colors[index],
        opacity: 0.8,
        line: {
          color: colors[index],
          width: 1.5
        }
      },
      hovertemplate: '%{hovertext}<extra></extra>',
      hovertext: hoverTexts
    })
  })
  
  const layout = {
    title: {
      text: '性能指标对比',
      font: {
        size: 18,
        family: 'Arial, sans-serif',
        weight: 'bold'
      },
      y: 0.98,
      yanchor: 'top'
    },
    xaxis: {
      tickfont: {
        size: 13,
        family: 'Arial, sans-serif'
      },
      tickangle: 0
    },
    yaxis: {
      title: '数值',
      titlefont: {
        size: 15
      },
      tickfont: {
        size: 13
      },
      gridcolor: 'rgba(0,0,0,0.08)'
    },
    barmode: 'group',
    bargap: 0.15,
    bargroupgap: 0.1,
    showlegend: true,
    legend: {
      x: 0.5,
      xanchor: 'center',
      y: 1.12,
      yanchor: 'top',
      orientation: 'h',
      font: {
        size: 14,
        family: 'Arial, sans-serif'
      },
      bgcolor: 'rgba(255,255,255,0.9)',
      bordercolor: 'rgba(0,0,0,0.1)',
      borderwidth: 1
    },
    margin: {
      l: 70,
      r: 40,
      t: 120,
      b: 80
    },
    autosize: true,
    hovermode: 'closest'
  }
  
  const config = {
    responsive: true,
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d', 'zoom2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d'],
    autosizable: true
  }
  
  Plotly.newPlot(plotlyChartRef.value, traces, layout, config)
}



// 监听图表类型变化
watch(chartType, async (newType) => {
  await nextTick()
  if (newType === 'facet') {
    createFacetScatterChart()
  } else {
    createBarChart()
  }
})

// 监听数据变化
watch(
  () => [props.experimentData, props.predictionData, props.historicalBest],
  async () => {
    await nextTick()
    if (chartType.value === 'facet') {
      createFacetScatterChart()
    } else {
      createBarChart()
    }
  },
  { deep: true }
)

onMounted(async () => {
  await nextTick()
  createFacetScatterChart()
  
  // 设置ResizeObserver监听容器大小变化（防抖处理）
  if (plotlyChartRef.value) {
    let resizeTimer = null
    resizeObserver.value = new ResizeObserver(() => {
      if (plotlyChartRef.value) {
        // 防抖：避免频繁resize
        clearTimeout(resizeTimer)
        resizeTimer = setTimeout(() => {
          Plotly.Plots.resize(plotlyChartRef.value)
        }, 100)
      }
    })
    resizeObserver.value.observe(plotlyChartRef.value)
  }
})

// 组件卸载时清理ResizeObserver
onUnmounted(() => {
  if (resizeObserver.value) {
    resizeObserver.value.disconnect()
    resizeObserver.value = null
  }
})
</script>

<style scoped>
.performance-comparison-chart {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-top: 16px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 2px solid #e5e7eb;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-left h4 {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: #1f2937;
}

.chart-legend {
  display: flex;
  gap: 16px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #4b5563;
}

.legend-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  flex-shrink: 0;
}

.legend-dot.experiment {
  background: rgb(99, 102, 241);
}

.legend-dot.prediction {
  background: rgb(16, 185, 129);
}

.legend-dot.historical {
  background: rgb(245, 158, 11);
}

.chart-container {
  width: 100%;
  height: 650px;
  position: relative;
  padding: 0;
}


.chart-actions {
  display: flex;
  justify-content: center;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #e5e7eb;
}
</style>
