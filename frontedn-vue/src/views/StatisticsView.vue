<template>
  <div class="statistics-container">
    <h1>数据统计</h1>
    <el-card class="statistics-card">
      <div class="statistics-content">
        <el-row :gutter="20">
          <el-col :span="6">
            <el-card class="stat-item">
              <template #header>
                <div class="stat-header">
                  <el-icon><DataLine /></el-icon>
                  <span>总提供脚本生成服务次数</span>
                </div>
              </template>
              <div class="stat-value">{{ stats.totalGenerations }}</div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="stat-item">
              <template #header>
                <div class="stat-header">
                  <el-icon><User /></el-icon>
                  <span>使用服务的用户数</span>
                </div>
              </template>
              <div class="stat-value">{{ stats.activeUsers }}</div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="stat-item">
              <template #header>
                <div class="stat-header">
                  <el-icon><Calendar /></el-icon>
                  <span>今日提供生成服务次数</span>
                </div>
              </template>
              <div class="stat-value">{{ stats.todayGenerations }}</div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="stat-item">
              <template #header>
                <div class="stat-header">
                  <el-icon><Download /></el-icon>
                  <span>提供下载服务次数</span>
                </div>
              </template>
              <div class="stat-value">{{ stats.totalDownloads }}</div>
            </el-card>
          </el-col>
        </el-row>

        <div class="chart-section">
          <h2>生成趋势</h2>
          <div class="chart-filter">
            <el-radio-group v-model="trendTimeRange" @change="handleTrendRangeChange">
              <el-radio-button label="7">最近7天</el-radio-button>
              <el-radio-button label="30">最近30天</el-radio-button>
              <el-radio-button label="90">最近90天</el-radio-button>
              <el-radio-button label="monthly">按月统计</el-radio-button>
            </el-radio-group>
          </div>
          <div class="chart-container" ref="trendChartRef"></div>
        </div>

        <div class="chart-section">
          <h2>模板使用分布</h2>
          <div class="chart-container" ref="templateChartRef"></div>
        </div>

        <div class="chart-section">
          <h2>下载趋势</h2>
          <div class="chart-filter">
            <el-radio-group v-model="downloadTimeRange" @change="handleDownloadRangeChange">
              <el-radio-button label="7">最近7天</el-radio-button>
              <el-radio-button label="30">最近30天</el-radio-button>
              <el-radio-button label="90">最近90天</el-radio-button>
              <el-radio-button label="monthly">按月统计</el-radio-button>
            </el-radio-group>
          </div>
          <div class="chart-container" ref="downloadTrendChartRef"></div>
        </div>

        <div class="chart-section">
          <h2>用户行为分析</h2>
          <div class="chart-filter">
            <el-radio-group v-model="behaviorTimeRange" @change="handleBehaviorRangeChange">
              <el-radio-button label="7">最近7天</el-radio-button>
              <el-radio-button label="30">最近30天</el-radio-button>
              <el-radio-button label="90">最近90天</el-radio-button>
            </el-radio-group>
          </div>
          <el-row :gutter="20">
            <el-col :span="12">
              <h3>日内使用频率分布</h3>
              <div class="chart-container" ref="dailyHeatmapRef"></div>
            </el-col>
            <el-col :span="12">
              <h3>周内使用频率分布</h3>
              <div class="chart-container" ref="weeklyHeatmapRef"></div>
            </el-col>
          </el-row>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { DataLine, User, Calendar, Download } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import apiClient from '../api/config'

const trendChartRef = ref<HTMLElement | null>(null)
const templateChartRef = ref<HTMLElement | null>(null)
const downloadTrendChartRef = ref<HTMLElement | null>(null)
const dailyHeatmapRef = ref<HTMLElement | null>(null)
const weeklyHeatmapRef = ref<HTMLElement | null>(null)
let trendChart: echarts.ECharts | null = null
let templateChart: echarts.ECharts | null = null
let downloadTrendChart: echarts.ECharts | null = null
let dailyHeatmapChart: echarts.ECharts | null = null
let weeklyHeatmapChart: echarts.ECharts | null = null

// 默认显示最近7天的数据
const trendTimeRange = ref('7')
const downloadTimeRange = ref('7')
const behaviorTimeRange = ref('7')

interface TemplateData {
  template_name: string
  usage_count: number
}

const stats = reactive({
  totalGenerations: 0,
  activeUsers: 0,
  todayGenerations: 0,
  totalDownloads: 0
})

const trendData = reactive({
  dates: [] as string[],
  counts: [] as number[]
})

const downloadTrendData = reactive({
  dates: [] as string[],
  counts: [] as number[]
})

const behaviorData = reactive({
  dailyHeatmap: [] as Array<[number, number, number]>,
  weeklyHeatmap: [] as Array<[number, number, number]>
})

const handleTrendRangeChange = (value: string) => {
  fetchTrendData(value)
}

const handleDownloadRangeChange = (value: string) => {
  fetchDownloadData(value)
}

const handleBehaviorRangeChange = (value: string) => {
  fetchBehaviorData(value)
}

const fetchBehaviorData = async (timeRange: string) => {
  try {
    const token = localStorage.getItem('token')
    if (!token) {
      ElMessage.error('未登录或会话已过期')
      return
    }

    const params = { time_range: timeRange }
    const response = await apiClient.get('/statistics/behavior', {
      headers: { Authorization: `Bearer ${token}` },
      params
    })

    // 处理日内热力图数据
    if (response.data.hourly) {
      behaviorData.dailyHeatmap = response.data.hourly.map((item: any) => [
        parseInt(item.hour),
        0, // 固定为0，表示只有一行数据
        item.count
      ])
    }

    // 处理周内热力图数据
    if (response.data.weekday) {
      behaviorData.weeklyHeatmap = response.data.weekday.map((item: any) => [
        parseInt(item.weekday), // 星期（0-6）
        0, // 固定为0，表示只有一行数据
        item.count
      ])
    }

    initDailyHeatmap()
    initWeeklyHeatmap()
  } catch (error) {
    ElMessage.error('获取用户行为数据失败')
    console.error('获取用户行为数据失败:', error)
  }
}

const initDailyHeatmap = () => {
  if (dailyHeatmapRef.value) {
    dailyHeatmapChart = echarts.init(dailyHeatmapRef.value)
    
    const hours = Array.from({length: 24}, (_, i) => i + '时')
    const option = {
      tooltip: {
        position: 'top',
        formatter: (params: any) => {
          return `${params.data[0]}时: ${params.data[2]}次`
        }
      },
      grid: {
        top: '10%',
        bottom: '10%'
      },
      xAxis: {
        type: 'category',
        data: hours,
        splitArea: {
          show: true
        }
      },
      yAxis: {
        type: 'category',
        data: ['使用频率'],
        splitArea: {
          show: true
        }
      },
      visualMap: {
        min: 0,
        max: Math.max(...behaviorData.dailyHeatmap.map(item => item[2])),
        calculable: true,
        orient: 'horizontal',
        left: 'center',
        bottom: '0%'
      },
      series: [{
        name: '使用频率',
        type: 'heatmap',
        data: behaviorData.dailyHeatmap,
        label: {
          show: true
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }]
    }
    
    dailyHeatmapChart.setOption(option)
  }
}

const initWeeklyHeatmap = () => {
  if (weeklyHeatmapRef.value) {
    weeklyHeatmapChart = echarts.init(weeklyHeatmapRef.value)
    
    const hours = Array.from({length: 24}, (_, i) => i + '时')
    const days = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
    
    const option = {
      tooltip: {
        position: 'top',
        formatter: (params: any) => {
          return `${days[params.data[0]]} ${params.data[1]}时: ${params.data[2]}次`
        }
      },
      grid: {
        top: '10%',
        bottom: '10%'
      },
      xAxis: {
        type: 'category',
        data: hours,
        splitArea: {
          show: true
        }
      },
      yAxis: {
        type: 'category',
        data: days,
        splitArea: {
          show: true
        }
      },
      visualMap: {
        min: 0,
        max: Math.max(...behaviorData.weeklyHeatmap.map(item => item[2])),
        calculable: true,
        orient: 'horizontal',
        left: 'center',
        bottom: '0%'
      },
      series: [{
        name: '使用频率',
        type: 'heatmap',
        data: behaviorData.weeklyHeatmap,
        label: {
          show: true
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }]
    }
    
    weeklyHeatmapChart.setOption(option)
  }
}

const fetchStatistics = async () => {
  try {
    const token = localStorage.getItem('token')
    if (!token) {
      ElMessage.error('未登录或会话已过期')
      return
    }

    const response = await apiClient.get('/statistics', {
      headers: { Authorization: `Bearer ${token}` }
    })

    // 适配后端返回的数据格式
    stats.totalGenerations = response.data.generation_count || 0
    stats.activeUsers = response.data.user_count || 0
    stats.todayGenerations = response.data.today_generation_count || 0 // 更新为后端提供的今日数据
    stats.totalDownloads = response.data.download_count || 0

    // 处理模板使用数据
    const templateData: TemplateData[] = []
    if (response.data.branch_usage) {
      response.data.branch_usage.forEach((item: any) => {
        templateData.push({
          template_name: item.branch,
          usage_count: item.count
        })
      })
    }
    initTemplateChart(templateData)
    
    // 获取趋势数据和下载趋势数据
    fetchTrendData(trendTimeRange.value)
    fetchDownloadData(downloadTimeRange.value)
  } catch (error) {
    ElMessage.error('获取统计数据失败')
    console.error('获取统计数据失败:', error)
  }
}

const fetchTrendData = async (timeRange: string) => {
  try {
    const token = localStorage.getItem('token')
    if (!token) {
      ElMessage.error('未登录或会话已过期')
      return
    }

    // 根据选择的时间范围获取数据
    const params = { time_range: timeRange }
    const response = await apiClient.get('/statistics/trend', {
      headers: { Authorization: `Bearer ${token}` },
      params
    })

    // 清空之前的数据
    trendData.dates = []
    trendData.counts = []

    // 处理返回的趋势数据
    if (timeRange === 'monthly' && response.data.monthly) {
      // 处理月度数据
      response.data.monthly.forEach((item: any) => {
        trendData.dates.push(item.month)
        trendData.counts.push(item.count)
      })
    } else if (response.data.daily) {
      // 处理日数据
      response.data.daily.forEach((item: any) => {
        trendData.dates.push(item.date)
        trendData.counts.push(item.count)
      })
    }

    // 更新图表
    initTrendChart(trendData)
  } catch (error) {
    ElMessage.error('获取趋势数据失败')
    console.error('获取趋势数据失败:', error)
  }
}

const fetchDownloadData = async (timeRange: string) => {
  try {
    const token = localStorage.getItem('token')
    if (!token) {
      ElMessage.error('未登录或会话已过期')
      return
    }

    // 根据选择的时间范围获取数据
    const params = { time_range: timeRange }
    const response = await apiClient.get('/statistics/download', {
      headers: { Authorization: `Bearer ${token}` },
      params
    })

    // 清空之前的数据
    downloadTrendData.dates = []
    downloadTrendData.counts = []

    // 处理返回的下载趋势数据
    if (timeRange === 'monthly' && response.data.monthly) {
      // 处理月度数据
      response.data.monthly.forEach((item: any) => {
        downloadTrendData.dates.push(item.month)
        downloadTrendData.counts.push(item.count)
      })
    } else if (response.data.daily) {
      // 处理日数据
      response.data.daily.forEach((item: any) => {
        downloadTrendData.dates.push(item.date)
        downloadTrendData.counts.push(item.count)
      })
    }

    // 更新图表
    initDownloadTrendChart(downloadTrendData)
  } catch (error) {
    ElMessage.error('获取下载趋势数据失败')
    console.error('获取下载趋势数据失败:', error)
  }
}

const initTrendChart = (data: any) => {
  if (trendChartRef.value) {
    trendChart = echarts.init(trendChartRef.value)
    
    const option = {
      title: {
        text: '生成趋势'
      },
      tooltip: {
        trigger: 'axis'
      },
      xAxis: {
        type: 'category',
        data: data.dates,
        axisLabel: {
          rotate: data.dates.length > 10 ? 45 : 0,
          interval: data.dates.length > 20 ? 'auto' : 0
        }
      },
      yAxis: {
        type: 'value'
      },
      series: [{
        data: data.counts,
        type: 'line',
        smooth: true,
        itemStyle: {
          color: '#409EFF'
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [{
              offset: 0, color: 'rgba(64, 158, 255, 0.5)'
            }, {
              offset: 1, color: 'rgba(64, 158, 255, 0.1)'
            }]
          }
        }
      }]
    }
    
    trendChart.setOption(option)
  }
}

const initTemplateChart = (data: TemplateData[]) => {
  if (templateChartRef.value) {
    templateChart = echarts.init(templateChartRef.value)
    
    const option = {
      title: {
        text: '模板使用分布'
      },
      tooltip: {
        trigger: 'item',
        formatter: '{a} <br/>{b}: {c} ({d}%)'
      },
      series: [{
        name: '模板使用',
        type: 'pie',
        radius: '60%',
        data: data.map((item: any) => ({
          name: item.template_name,
          value: item.usage_count
        })),
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }]
    }
    
    templateChart.setOption(option)
  }
}

const initDownloadTrendChart = (data: any) => {
  if (downloadTrendChartRef.value) {
    downloadTrendChart = echarts.init(downloadTrendChartRef.value)
    
    const option = {
      title: {
        text: '下载趋势'
      },
      tooltip: {
        trigger: 'axis'
      },
      xAxis: {
        type: 'category',
        data: data.dates,
        axisLabel: {
          rotate: data.dates.length > 10 ? 45 : 0,
          interval: data.dates.length > 20 ? 'auto' : 0
        }
      },
      yAxis: {
        type: 'value'
      },
      series: [{
        data: data.counts,
        type: 'line',
        smooth: true,
        itemStyle: {
          color: '#67C23A'
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [{
              offset: 0, color: 'rgba(103, 194, 58, 0.5)'
            }, {
              offset: 1, color: 'rgba(103, 194, 58, 0.1)'
            }]
          }
        }
      }]
    }
    
    downloadTrendChart.setOption(option)
  }
}

onMounted(() => {
  fetchStatistics()
  fetchBehaviorData(behaviorTimeRange.value)
  
  // 窗口大小变化时重新调整图表大小
  window.addEventListener('resize', () => {
    trendChart?.resize()
    templateChart?.resize()
    downloadTrendChart?.resize()
    dailyHeatmapChart?.resize()
    weeklyHeatmapChart?.resize()
  })
})
</script>

<style scoped>
.statistics-container {
  padding: 20px;
  max-width: 2048px;
  margin: 0 auto;
}

.statistics-card {
  margin-top: 20px;
}

.statistics-content {
  padding: 10px;
}

.stat-item {
  text-align: center;
  margin-bottom: 20px;
}

.stat-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #409EFF;
  margin-top: 10px;
}

.chart-section {
  margin-top: 30px;
}

.chart-container {
  height: 400px;
  margin-top: 20px;
}
</style>