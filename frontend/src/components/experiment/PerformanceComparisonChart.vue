<template>
  <div class="performance-comparison-chart">
    <!-- 简化的图例 -->
    <div class="chart-legend">
      <div class="legend-item">
        <span class="legend-dot experiment"></span>
        <span>实验</span>
      </div>
      <div class="legend-item">
        <span class="legend-dot prediction"></span>
        <span>预测</span>
      </div>
      <div class="legend-item" v-if="historicalBest">
        <span class="legend-dot historical"></span>
        <span>历史最优</span>
      </div>
      <!-- 图表类型切换 -->
      <div class="chart-toggle">
        <el-button-group size="small">
          <el-button :type="chartType === 'facet' ? 'primary' : ''" @click="chartType = 'facet'">散点</el-button>
          <el-button :type="chartType === 'bar' ? 'primary' : ''" @click="chartType = 'bar'">柱状</el-button>
        </el-button-group>
      </div>
    </div>
    
    <!-- Plotly 图表容器 -->
    <div ref="plotlyChartRef" class="chart-container"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { ElIcon } from 'element-plus'
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

// 创建散点图 - 2x2 独立子图布局
const createFacetScatterChart = () => {
  if (!plotlyChartRef.value) return
  
  const dataTypes = ['实验', '预测', '历史']
  const colors = ['#6366f1', '#10b981', '#f59e0b']
  const symbols = ['circle', 'diamond', 'square']
  const dataSources = [props.experimentData, props.predictionData, props.historicalBest]
  
  const traces = []
  
  // 为每个指标创建独立子图
  metricsConfig.forEach((metric, mIdx) => {
    dataSources.forEach((src, dIdx) => {
      if (!src) return
      const val = src[metric.key]
      if (val === null || val === undefined || isNaN(val)) return
      
      traces.push({
        x: [dataTypes[dIdx]],
        y: [val],
        name: dataTypes[dIdx],
        legendgroup: dataTypes[dIdx],
        showlegend: mIdx === 0,
        type: 'scatter',
        mode: 'markers',
        marker: { 
          size: 12, 
          color: colors[dIdx],
          symbol: symbols[dIdx],
          line: { width: 1, color: 'white' }
        },
        xaxis: mIdx === 0 ? 'x' : `x${mIdx + 1}`,
        yaxis: mIdx === 0 ? 'y' : `y${mIdx + 1}`,
        hovertemplate: `<b>${dataTypes[dIdx]}</b><br>${val < 0.01 ? val.toExponential(2) : val.toFixed(2)}<extra></extra>`
      })
    })
  })
  
  // 2x2 布局
  const layout = {
    showlegend: true,
    legend: { orientation: 'h', x: 0.5, xanchor: 'center', y: 1.12 },
    grid: { rows: 2, columns: 2, pattern: 'independent', xgap: 0.1, ygap: 0.15 },
    margin: { l: 60, r: 30, t: 60, b: 40 },
    height: 400,
    autosize: true,
    hovermode: 'closest',
    plot_bgcolor: '#fafafa',
    paper_bgcolor: 'rgba(0,0,0,0)'
  }
  
  // 配置每个子图坐标轴
  metricsConfig.forEach((metric, idx) => {
    const xKey = idx === 0 ? 'xaxis' : `xaxis${idx + 1}`
    const yKey = idx === 0 ? 'yaxis' : `yaxis${idx + 1}`
    
    layout[xKey] = {
      title: { text: `${metric.label} (${metric.unit})`, font: { size: 12 }, standoff: 5 },
      tickfont: { size: 10 },
      showgrid: false,
      showline: true,
      linecolor: '#e0e0e0'
    }
    layout[yKey] = {
      tickfont: { size: 10 },
      gridcolor: '#f0f0f0',
      showline: true,
      linecolor: '#e0e0e0',
      zeroline: false
    }
  })
  
  Plotly.newPlot(plotlyChartRef.value, traces, layout, {
    responsive: true,
    displayModeBar: true,
    modeBarButtonsToRemove: ['lasso2d', 'select2d', 'sendDataToCloud']
  })
}

// 创建柱状图 - 2x2 独立子图布局
const createBarChart = () => {
  if (!plotlyChartRef.value) return
  
  const dataTypes = ['实验', '预测', '历史']
  const colors = ['#6366f1', '#10b981', '#f59e0b']
  const dataSources = [props.experimentData, props.predictionData, props.historicalBest]
  
  const traces = []
  
  // 为每个指标创建独立子图
  metricsConfig.forEach((metric, mIdx) => {
    dataSources.forEach((src, dIdx) => {
      if (!src) return
      const val = src[metric.key]
      if (val === null || val === undefined || isNaN(val)) return
      
      traces.push({
        x: [dataTypes[dIdx]],
        y: [val],
        name: dataTypes[dIdx],
        legendgroup: dataTypes[dIdx],
        showlegend: mIdx === 0,
        type: 'bar',
        marker: { color: colors[dIdx], opacity: 0.85 },
        xaxis: mIdx === 0 ? 'x' : `x${mIdx + 1}`,
        yaxis: mIdx === 0 ? 'y' : `y${mIdx + 1}`,
        hovertemplate: `<b>${dataTypes[dIdx]}</b><br>${val < 0.01 ? val.toExponential(2) : val.toFixed(2)}<extra></extra>`
      })
    })
  })
  
  // 2x2 布局
  const layout = {
    showlegend: true,
    legend: { orientation: 'h', x: 0.5, xanchor: 'center', y: 1.12 },
    grid: { rows: 2, columns: 2, pattern: 'independent', xgap: 0.1, ygap: 0.15 },
    margin: { l: 60, r: 30, t: 60, b: 40 },
    height: 400,
    autosize: true,
    hovermode: 'closest',
    plot_bgcolor: '#fafafa',
    paper_bgcolor: 'rgba(0,0,0,0)',
    bargap: 0.3
  }
  
  // 配置每个子图坐标轴
  metricsConfig.forEach((metric, idx) => {
    const xKey = idx === 0 ? 'xaxis' : `xaxis${idx + 1}`
    const yKey = idx === 0 ? 'yaxis' : `yaxis${idx + 1}`
    
    layout[xKey] = {
      title: { text: `${metric.label} (${metric.unit})`, font: { size: 12 }, standoff: 5 },
      tickfont: { size: 10 },
      showgrid: false,
      showline: true,
      linecolor: '#e0e0e0'
    }
    layout[yKey] = {
      tickfont: { size: 10 },
      gridcolor: '#f0f0f0',
      showline: true,
      linecolor: '#e0e0e0',
      zeroline: false
    }
  })
  
  Plotly.newPlot(plotlyChartRef.value, traces, layout, {
    responsive: true,
    displayModeBar: true,
    modeBarButtonsToRemove: ['lasso2d', 'select2d', 'sendDataToCloud']
  })
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
  padding: 16px;
}

/* 图例和切换按钮 */
.chart-legend {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-secondary, #6b7280);
}

.legend-dot {
  width: 10px;
  height: 10px;
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

.chart-toggle {
  margin-left: auto;
}

.chart-toggle :deep(.el-button) {
  font-size: 12px;
  padding: 4px 10px;
}

/* 图表容器 */
.chart-container {
  width: 100%;
  height: 400px;
  position: relative;
  background: var(--bg-secondary, #f9fafb);
  border-radius: 8px;
}
</style>
