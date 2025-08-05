<template>
  <div class="analytics-container">
    <h2 class="card-title">Analytics</h2>
    
    <div class="analytics-controls">
      <button 
        class="nav-tab" 
        :class="{ active: analyticsView === 'week' }"
        @click="switchView('week')"
      >
        Week
      </button>
      <button 
        class="nav-tab" 
        :class="{ active: analyticsView === 'month' }"
        @click="switchView('month')"
      >
        Month
      </button>
      <button class="btn-small" @click="downloadCSV">Download CSV</button>
    </div>

    <div class="chart-container">
      <canvas 
        ref="analyticsChart" 
        v-show="chartsReady"
        width="400" 
        height="200"
      ></canvas>
    </div>

    <h3 class="card-title">Energy Usage Heatmap</h3>
    <div class="heatmap-container">
      <div 
        v-for="(hour, index) in 24" 
        :key="index"
        class="heatmap-cell"
        :style="{ backgroundColor: getHeatmapColor(heatmapData[index] || 0) }"
        :title="`${index}:00 - ${heatmapData[index] || 0} WH`"
      >
        {{ index }}
      </div>
    </div>

    <div class="doughnut-section">
      <h3 class="card-title">Daily Peak Hours</h3>
      <div class="doughnut-container">
        <canvas 
          ref="doughnutChart" 
          v-show="chartsReady"
          width="300" 
          height="150"
        ></canvas>
      </div>
    </div>
  </div>
</template>

<script>
import Chart from 'chart.js/auto'

export default {
  name: 'AnalyticsTabComponent',
  emits: ['load-analytics'],
  props: {
    analyticsData: {
      type: Array,
      required: true
    },
    heatmapData: {
      type: Array,
      required: true
    }
  },
  data() {
    return {
      analyticsView: 'week',
      analyticsChart: null,
      doughnutChart: null,
      chartsReady: false,
      weeklyData: [],
      monthlyData: [],
      updateTimeout: null
    }
  },
  mounted() {
    this.generateSampleData()
    // Use setTimeout to ensure DOM is fully rendered
    setTimeout(() => {
      this.chartsReady = true
      this.$nextTick(() => {
        this.initializeCharts()
      })
    }, 100)
  },
  beforeUnmount() {
    // Clear any pending timeouts
    if (this.updateTimeout) {
      clearTimeout(this.updateTimeout)
    }
    this.destroyCharts()
  },
  watch: {
    analyticsData: {
      handler() {
        if (this.chartsReady) {
          // Debounce updates to prevent multiple rapid calls
          clearTimeout(this.updateTimeout)
          this.updateTimeout = setTimeout(() => {
            this.$nextTick(() => {
              this.updateCharts()
            })
          }, 100)
        }
      },
      deep: true
    }
  },
  methods: {
    async switchView(view) {
  this.analyticsView = view
  
  // Load filtered data from API
  try {
    const response = await fetch(`http://127.0.0.1:5000/api/analytics?period=${view}`)
    if (response.ok) {
      const data = await response.json()
      // Emit to parent to update analyticsData
      this.$emit('load-analytics', view, data)
    }
  } catch (error) {
    console.error('Error loading analytics data:', error)
  }
  
  if (this.chartsReady) {
    this.updateCharts()
  }
},
    
    generateSampleData() {
      // Generate weekly data (7 days)
      this.weeklyData = Array.from({ length: 7 }, (_, i) => {
        const date = new Date()
        date.setDate(date.getDate() - (6 - i))
        return {
          timestamp: date.toISOString(),
          power: Math.random() * 500 + 200,
          current: Math.random() * 3 + 1
        }
      })
      
      // Generate monthly data (30 days)
      this.monthlyData = Array.from({ length: 30 }, (_, i) => {
        const date = new Date()
        date.setDate(date.getDate() - (29 - i))
        return {
          timestamp: date.toISOString(),
          power: Math.random() * 800 + 300,
          current: Math.random() * 4 + 1.5
        }
      })
    },
    
    getCurrentData() {
  // Always use real data from props if available
  if (this.analyticsData && this.analyticsData.length > 0) {
    const data = JSON.parse(JSON.stringify(this.analyticsData))
    
    // Apply aggregation based on view
    if (this.analyticsView === 'week') {
      return this.aggregateByDay(data)
    } else {
      return this.aggregateByWeek(data)
    }
  }
  
  // Fallback to sample data
  const data = this.analyticsView === 'week' ? this.weeklyData : this.monthlyData
  return JSON.parse(JSON.stringify(data))
},
    
    
    aggregateByDay(data) {
  const dailyData = new Map()
  
  data.forEach(entry => {
    const date = new Date(entry.timestamp)
    // Create a date key using just year-month-day
    const dateKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
    
    if (!dailyData.has(dateKey)) {
      dailyData.set(dateKey, {
        timestamp: new Date(date.getFullYear(), date.getMonth(), date.getDate(), 12).toISOString(),
        power: 0,
        current: 0,
        count: 0,
        date: dateKey
      })
    }
    
    const dayData = dailyData.get(dateKey)
    dayData.power += parseFloat(entry.power) || 0
    dayData.current += parseFloat(entry.current) || 0
    dayData.count += 1
  })
  const result = Array.from(dailyData.values())
    .map(day => ({
      timestamp: day.timestamp,
      power: Math.round(day.power), // Total power for the day
      current: Math.round(day.current / day.count * 100) / 100, // Average current
      date: day.date
    }))
    .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))
  
  console.log('Daily aggregated data:', result) // Debug log
  return result
},

    
    aggregateByWeek(data) {
  const weeklyData = new Map()
  
  data.forEach(entry => {
    const date = new Date(entry.timestamp)
    // Get week start (Monday instead of Sunday for better grouping)
    const weekStart = new Date(date)
    const day = date.getDay()
    const diff = date.getDate() - day + (day === 0 ? -6 : 1) // Adjust for Monday start
    weekStart.setDate(diff)
    weekStart.setHours(0, 0, 0, 0)
    
    const weekKey = weekStart.toISOString().split('T')[0] // Use date string as key
    
    if (!weeklyData.has(weekKey)) {
      weeklyData.set(weekKey, {
        timestamp: weekStart.toISOString(),
        power: 0,
        current: 0,
        count: 0
      })
    }
    const weekData = weeklyData.get(weekKey)
    weekData.power += parseFloat(entry.power) || 0
    weekData.current += parseFloat(entry.current) || 0
    weekData.count += 1
  })
  
  const result = Array.from(weeklyData.values())
    .map(week => ({
      timestamp: week.timestamp,
      power: Math.round(week.power), // Total power for the week
      current: Math.round(week.current / week.count * 100) / 100 // Average current
    }))
    .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))
  
  console.log('Weekly aggregated data:', result) // Debug log
  return result
},

        
    
    initializeCharts() {
      this.createAnalyticsChart()
      this.createDoughnutChart()
    },
    
    updateCharts() {
      this.updateAnalyticsChart()
      this.updateDoughnutChart()
    },
    
    destroyCharts() {
      if (this.analyticsChart) {
        this.analyticsChart.destroy()
        this.analyticsChart = null
      }
      if (this.doughnutChart) {
        this.doughnutChart.destroy()
        this.doughnutChart = null
      }
    },
    
    createAnalyticsChart() {
      const canvas = this.$refs.analyticsChart
      if (!canvas) {
        console.warn('Analytics chart canvas not found')
        return
      }

      // Destroy existing chart if it exists
      if (this.analyticsChart) {
        this.analyticsChart.destroy()
        this.analyticsChart = null
      }

      const data = this.getCurrentData()
      if (!data || data.length === 0) {
        console.warn('No data available for analytics chart')
        return
      }

      const labels = data.map(d => {
        const date = new Date(d.timestamp)
        if (this.analyticsView === 'week') {
          // For week view, show day names
          return date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
        } else {
          // For month view, show week ranges
          const weekEnd = new Date(date)
          weekEnd.setDate(date.getDate() + 6)
          return `${date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} - ${weekEnd.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}`
        }
      })
      const values = data.map(d => parseFloat(d.power) || 0)

      this.analyticsChart = new Chart(canvas, {
        type: 'bar',
        data: {
          labels: labels,
          datasets: [{
            label: 'Energy Usage (WH)',
            data: values,
            backgroundColor: 'rgba(102, 126, 234, 0.8)',
            borderColor: '#667eea',
            borderWidth: 1
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          interaction: {
            intersect: false,
            mode: 'index'
          },
          plugins: {
            legend: {
              display: true,
              position: 'top'
            },
            title: {
              display: true,
              text: `${this.analyticsView === 'week' ? 'Weekly' : 'Monthly'} Energy Usage`
            }
          },
          scales: {
            x: {
              display: true,
              title: {
                display: true,
                text: 'Date'
              }
            },
            y: {
              display: true,
              beginAtZero: true,
              title: {
                display: true,
                text: 'Power (WH)'
              }
            }
          },
          layout: {
            padding: {
              top: 10,
              bottom: 10,
              left: 10,
              right: 10
            }
          }
        }
      })
    },
    
    updateAnalyticsChart() {
      // Always recreate the chart to avoid configuration issues
      this.createAnalyticsChart()
    },
    
    createDoughnutChart() {
      const canvas = this.$refs.doughnutChart
      if (!canvas) {
        console.warn('Doughnut chart canvas not found')
        return
      }

      // Destroy existing chart if it exists
      if (this.doughnutChart) {
        this.doughnutChart.destroy()
        this.doughnutChart = null
      }

      const data = this.getCurrentData()
      if (!data || data.length === 0) {
        console.warn('No data available for doughnut chart')
        return
      }

      const peakHours = {
        'Morning (6-12)': 0,
        'Afternoon (12-18)': 0,
        'Evening (18-24)': 0,
        'Night (0-6)': 0
      }
      
      data.forEach(d => {
        const hour = new Date(d.timestamp).getHours()
        const power = parseFloat(d.power) || 0
        if (hour >= 6 && hour < 12) peakHours['Morning (6-12)'] += power
        else if (hour >= 12 && hour < 18) peakHours['Afternoon (12-18)'] += power
        else if (hour >= 18 && hour < 24) peakHours['Evening (18-24)'] += power
        else peakHours['Night (0-6)'] += power
      })
      
      this.doughnutChart = new Chart(canvas, {
        type: 'doughnut',
        data: {
          labels: Object.keys(peakHours),
          datasets: [{
            data: Object.values(peakHours).map(v => Math.round(v)),
            backgroundColor: [
              '#FF6384',
              '#36A2EB',
              '#FFCE56',
              '#4BC0C0'
            ],
            borderWidth: 2,
            borderColor: '#fff'
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          interaction: {
            intersect: false
          },
          plugins: {
            legend: {
              position: 'right',
              labels: {
                boxWidth: 12,
                padding: 15,
                usePointStyle: true
              }
            },
            title: {
              display: true,
              text: `${this.analyticsView === 'week' ? 'Weekly' : 'Monthly'} Peak Hours Distribution`
            }
          },
          layout: {
            padding: {
              top: 10,
              bottom: 10,
              left: 10,
              right: 10
            }
          }
        }
      })
    },
    
    updateDoughnutChart() {
      // Always recreate the chart to avoid configuration issues
      this.createDoughnutChart()
    },
    
    getHeatmapColor(value) {
      const intensity = Math.min(value / 1000, 1)
      const red = Math.floor(255 * intensity)
      const green = Math.floor(255 * (1 - intensity))
      return `rgb(${red}, ${green}, 0)`
    },
    
    downloadCSV() {
      const data = this.getCurrentData()
      
      if (data.length === 0) {
        alert('No data available to download')
        return
      }
      
      const csvContent = "data:text/csv;charset=utf-8," 
        + "Timestamp,Current,Power\n"
        + data.map(d => 
            `${d.timestamp},${d.current},${d.power}`
          ).join("\n")
      
      const encodedUri = encodeURI(csvContent)
      const link = document.createElement("a")
      link.setAttribute("href", encodedUri)
      link.setAttribute("download", `power_data_${this.analyticsView}.csv`)
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    }
  }
}
</script>