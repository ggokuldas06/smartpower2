// Complete DashboardTabComponent.vue with robust Chart.js handling

<template>
  <div class="dashboard-tab">
    <div class="stats-grid">
      <div class="stat-card">
        <h3>Current Usage</h3>
        <div class="stat-value">{{ currentUsage }} WH</div>
      </div>
      <div class="stat-card">
        <h3>Current Cost</h3>
        <div class="stat-value">₹{{ currentCost }}</div>
      </div>
      <div class="stat-card">
        <h3>Budget Status</h3>
        <div class="budget-progress">
          <div class="progress-bar">
            <div 
              class="progress-fill" 
              :style="{ width: budgetPercentage + '%' }"
              :class="{ 'over-budget': budgetData.over_budget }"
            ></div>
          </div>
          <div class="budget-text">
            ₹{{ budgetData.spent }} / ₹{{ budgetData.budget }}
          </div>
        </div>
      </div>
    </div>

    <div class="chart-section">
      <div class="chart-header">
        <h3>Last 24 Hours Usage</h3>
        <button @click="refreshChart" class="refresh-btn">Refresh</button>
      </div>
      
      <div class="chart-container" :class="{ 'chart-loading': !chartReady }">
        <canvas 
          ref="chart24h" 
          v-show="chartReady && hasData"
          :width="chartWidth" 
          :height="chartHeight"
        ></canvas>
        
        <div v-if="!chartReady" class="chart-placeholder">
          <div class="loading-spinner"></div>
          <p>Loading chart...</p>
        </div>
        
        <div v-else-if="!hasData" class="chart-placeholder">
          <p>No data available for the last 24 hours</p>
          <button @click="generateSampleData" class="btn-secondary">Generate Sample Data</button>
        </div>
      </div>
    </div>

    <div class="budget-update">
      <h3>Update Budget</h3>
      <div class="budget-form">
        <input 
          type="number" 
          v-model="newBudget" 
          placeholder="Enter new budget"
          min="1"
          step="1"
        >
        <button @click="updateBudget" :disabled="!newBudget || newBudget <= 0">
          Update Budget
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import Chart from 'chart.js/auto'

export default {
  name: 'DashboardTabComponent',
  props: {
    currentUsage: {
      type: Number,
      default: 0
    },
    currentCost: {
      type: Number,
      default: 0
    },
    budgetData: {
      type: Object,
      default: () => ({
        budget: 1000,
        spent: 0,
        remaining: 1000,
        over_budget: false
      })
    },
    budgetPercentage: {
      type: Number,
      default: 0
    },
    analyticsData: {
      type: Array,
      default: () => []
    }
  },
  emits: ['update-budget'],
  data() {
    return {
      chart: null,
      chartReady: false,
      newBudget: '',
      chartWidth: 800,
      chartHeight: 400,
      initializationAttempts: 0,
      maxInitAttempts: 3,
      chartData: []
    }
  },
  computed: {
    hasData() {
      return this.chartData && this.chartData.length > 0
    }
  },
  mounted() {
    this.initializeComponent()
  },
  beforeUnmount() {
    this.cleanupChart()
  },
  watch: {
    analyticsData: {
      handler(newData) {
        console.log('Analytics data received:', newData?.length || 0, 'items')
        this.processAnalyticsData(newData)
      },
      immediate: true,
      deep: true
    }
  },
  methods: {
    async initializeComponent() {
      // Wait for DOM to be fully ready
      await this.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 200))
      
      this.processAnalyticsData(this.analyticsData)
      this.initializeChart()
    },

    processAnalyticsData(data) {
      if (!data || !Array.isArray(data)) {
        this.chartData = []
        return
      }

      // Filter last 24 hours and validate data
      const twentyFourHoursAgo = new Date()
      twentyFourHoursAgo.setHours(twentyFourHoursAgo.getHours() - 24)

      this.chartData = data
        .filter(item => {
          // Validate data structure
          if (!item || !item.timestamp) return false
          
          const itemDate = new Date(item.timestamp)
          return itemDate >= twentyFourHoursAgo && 
                 !isNaN(itemDate.getTime()) &&
                 typeof item.power !== 'undefined'
        })
        .map(item => ({
          timestamp: item.timestamp,
          power: parseFloat(item.power) || 0,
          current: parseFloat(item.current) || 0
        }))
        .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))

      console.log('Processed chart data:', this.chartData.length, 'items')

      // Update chart if it exists
      if (this.chart && this.chartReady) {
        this.updateChartData()
      }
    },

    async initializeChart() {
      if (this.initializationAttempts >= this.maxInitAttempts) {
        console.error('Max chart initialization attempts reached')
        return
      }

      this.initializationAttempts++
      
      const canvas = this.$refs.chart24h
      if (!canvas) {
        console.warn('Chart canvas not found, attempt:', this.initializationAttempts)
        setTimeout(() => this.initializeChart(), 300)
        return
      }

      // Clean up existing chart
      this.cleanupChart()

      try {
        const ctx = canvas.getContext('2d')
        if (!ctx) {
          throw new Error('Could not get 2D context from canvas')
        }

        // Prepare chart data
        const { labels, datasets } = this.prepareChartData()

        // Create chart with complete configuration
        this.chart = new Chart(ctx, {
          type: 'line',
          data: {
            labels: labels,
            datasets: datasets
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: {
              duration: 750,
              easing: 'easeInOutQuart'
            },
            interaction: {
              mode: 'index',
              intersect: false
            },
            plugins: {
              legend: {
                display: true,
                position: 'top',
                labels: {
                  boxWidth: 12,
                  padding: 15,
                  usePointStyle: true
                }
              },
              title: {
                display: true,
                text: 'Power Usage - Last 24 Hours',
                font: {
                  size: 16,
                  weight: 'bold'
                },
                padding: {
                  top: 10,
                  bottom: 30
                }
              },
              tooltip: {
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                titleColor: 'white',
                bodyColor: 'white',
                borderColor: '#667eea',
                borderWidth: 1,
                displayColors: true,
                callbacks: {
                  title: function(context) {
                    return 'Time: ' + context[0].label
                  },
                  label: function(context) {
                    return `Power: ${context.parsed.y} WH`
                  }
                }
              }
            },
            scales: {
              x: {
                type: 'category',
                display: true,
                title: {
                  display: true,
                  text: 'Time',
                  font: {
                    weight: 'bold'
                  }
                },
                grid: {
                  display: true,
                  color: 'rgba(0, 0, 0, 0.1)',
                  lineWidth: 1
                },
                ticks: {
                  maxTicksLimit: 12,
                  maxRotation: 45
                }
              },
              y: {
                type: 'linear',
                display: true,
                beginAtZero: true,
                title: {
                  display: true,
                  text: 'Power (WH)',
                  font: {
                    weight: 'bold'
                  }
                },
                grid: {
                  display: true,
                  color: 'rgba(0, 0, 0, 0.1)',
                  lineWidth: 1
                },
                ticks: {
                  callback: function(value) {
                    return value + ' WH'
                  }
                }
              }
            },
            elements: {
              line: {
                tension: 0.4,
                borderWidth: 2,
                fill: true
              },
              point: {
                radius: 3,
                hoverRadius: 6,
                borderWidth: 2,
                backgroundColor: '#667eea',
                borderColor: '#ffffff'
              }
            },
            layout: {
              padding: {
                top: 10,
                right: 10,
                bottom: 10,
                left: 10
              }
            }
          }
        })

        // Mark chart as ready
        this.chartReady = true
        this.initializationAttempts = 0
        
        console.log('Chart initialized successfully with', labels.length, 'data points')

      } catch (error) {
        console.error('Chart initialization error:', error)
        this.chartReady = false
        
        // Retry initialization
        if (this.initializationAttempts < this.maxInitAttempts) {
          setTimeout(() => this.initializeChart(), 500)
        }
      }
    },

    prepareChartData() {
      let labels = []
      let dataPoints = []

      if (this.hasData) {
        labels = this.chartData.map(item => {
          const date = new Date(item.timestamp)
          return date.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            hour12: false
          })
        })
        
        dataPoints = this.chartData.map(item => parseFloat(item.power) || 0)
      } else {
        // Fallback data
        labels = ['No Data']
        dataPoints = [0]
      }

      const datasets = [{
        label: 'Power Usage (WH)',
        data: dataPoints,
        borderColor: '#667eea',
        backgroundColor: 'rgba(102, 126, 234, 0.1)',
        borderWidth: 2,
        fill: true,
        tension: 0.4,
        pointBackgroundColor: '#667eea',
        pointBorderColor: '#ffffff',
        pointBorderWidth: 2,
        pointRadius: 3,
        pointHoverRadius: 6,
        pointHoverBackgroundColor: '#667eea',
        pointHoverBorderColor: '#ffffff'
      }]

      return { labels, datasets }
    },

    updateChartData() {
      if (!this.chart || !this.chartReady) {
        console.log('Chart not ready for update')
        return
      }

      try {
        const { labels, datasets } = this.prepareChartData()
        
        this.chart.data.labels = labels
        this.chart.data.datasets = datasets
        
        this.chart.update('none')
        
        console.log('Chart updated successfully')
      } catch (error) {
        console.error('Chart update error:', error)
        // Reinitialize on update error
        this.initializeChart()
      }
    },

    refreshChart() {
      console.log('Refreshing chart...')
      this.cleanupChart()
      setTimeout(() => {
        this.initializeChart()
      }, 100)
    },

    cleanupChart() {
      if (this.chart) {
        try {
          this.chart.destroy()
        } catch (error) {
          console.warn('Error destroying chart:', error)
        }
        this.chart = null
      }
      this.chartReady = false
    },

    updateBudget() {
      if (!this.newBudget || this.newBudget <= 0) {
        alert('Please enter a valid budget amount')
        return
      }

      this.$emit('update-budget', parseFloat(this.newBudget))
      this.newBudget = ''
    },

    async generateSampleData() {
      try {
        const response = await fetch('http://127.0.0.1:5000/api/fake_data', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ count: 50 })
        })

        if (response.ok) {
          alert('Sample data generated! Refreshing...')
          // Emit event to parent to reload data
          this.$emit('data-generated')
        }
      } catch (error) {
        console.error('Error generating sample data:', error)
        alert('Error generating sample data')
      }
    }
  }
}
</script>

<style scoped>
.dashboard-tab {
  padding: 20px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.stat-card {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.stat-card h3 {
  margin: 0 0 10px 0;
  color: #666;
  font-size: 14px;
  text-transform: uppercase;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #333;
}

.budget-progress {
  margin-top: 10px;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #e5e5e5;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #667eea;
  transition: width 0.3s ease;
}

.progress-fill.over-budget {
  background: #e53e3e;
}

.budget-text {
  margin-top: 8px;
  font-size: 14px;
  color: #666;
}

.chart-section {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  margin-bottom: 30px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.chart-header h3 {
  margin: 0;
  color: #333;
}

.refresh-btn {
  padding: 8px 16px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.refresh-btn:hover {
  background: #5a67d8;
}

.chart-container {
  position: relative;
  height: 400px;
  width: 100%;
}

.chart-container.chart-loading {
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #666;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 15px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.budget-update {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.budget-update h3 {
  margin: 0 0 15px 0;
  color: #333;
}

.budget-form {
  display: flex;
  gap: 10px;
  align-items: center;
}

.budget-form input {
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  flex: 1;
  max-width: 200px;
}

.budget-form button {
  padding: 10px 20px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.budget-form button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.budget-form button:not(:disabled):hover {
  background: #5a67d8;
}

.btn-secondary {
  padding: 10px 20px;
  background: #e2e8f0;
  color: #4a5568;
  border: 1px solid #cbd5e0;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 10px;
}

.btn-secondary:hover {
  background: #cbd5e0;
}
</style>