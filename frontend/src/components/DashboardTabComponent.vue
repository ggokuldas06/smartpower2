<template>
  <div>
    <div class="dashboard-grid">
      <!-- Real-time Usage -->
      <div class="dashboard-card">
        <h3 class="card-title">Realtime Usage</h3>
        <div class="usage-stats">
          <div class="stat">
            <div class="stat-value">{{ currentUsage }} WH</div>
            <div class="stat-label">Current Usage</div>
          </div>
          <div class="stat">
            <div class="stat-value">Rs. {{ currentCost }}</div>
            <div class="stat-label">Cost</div>
          </div>
        </div>
      </div>

      <!-- 24 Hour Chart -->
      <div class="dashboard-card">
        <h3 class="card-title">Usage in last 24 hrs</h3>
        <div class="fixed-chart">
          <canvas ref="usage24Chart"></canvas>
        </div>
      </div>

      <!-- Budget Monitor -->
      <div class="dashboard-card">
        <h3 class="card-title">Budget Monitor</h3>
        <div class="budget-container">
          <div class="budget-bar">
            <div 
              class="budget-fill" 
              :class="{ 'over-budget': budgetData.over_budget }"
              :style="{ width: budgetPercentage + '%' }"
            ></div>
          </div>
          <div class="budget-info">
            <span>Spent: Rs. {{ budgetData.spent }}</span>
            <span>Budget: Rs. {{ budgetData.budget }}</span>
          </div>
          <div class="budget-input-group">
            <input 
              type="number" 
              v-model="newBudget" 
              placeholder="Set new budget"
              step="0.01"
            >
            <button class="btn-small" @click="updateBudget">Update</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import Chart from 'chart.js/auto'

export default {
  name: 'DashboardTabComponent',
  emits: ['update-budget'],
  props: {
    currentUsage: {
      type: Number,
      required: true
    },
    currentCost: {
      type: Number,
      required: true
    },
    budgetData: {
      type: Object,
      required: true
    },
    budgetPercentage: {
      type: Number,
      required: true
    }
  },
  data() {
    return {
      newBudget: '',
      usage24Chart: null,
      chartReady: false
    }
  },
  mounted() {
    this.chartReady = true
    this.$nextTick(() => {
      this.loadAnalyticsForChart()
    })
  },
  beforeUnmount() {
    if (this.usage24Chart) {
      this.usage24Chart.destroy()
    }
  },
  methods: {
    updateBudget() {
      this.$emit('update-budget', this.newBudget)
      this.newBudget = ''
    },
    
    async loadAnalyticsForChart() {
      try {
        const response = await fetch('http://127.0.0.1:5000/api/analytics')
        if (response.ok) {
          const data = await response.json()
          this.updateUsage24Chart(data)
        }
      } catch (err) {
        console.error('Error loading analytics for chart:', err)
      }
    },
    
    updateUsage24Chart(data) {
      if (!this.chartReady) return
      
      const ctx = this.$refs.usage24Chart
      if (!ctx) {
        console.warn('Usage 24h chart canvas not found')
        return
      }
      
      if (this.usage24Chart) {
        this.usage24Chart.destroy()
        this.usage24Chart = null
      }
      
      if (!data || data.length === 0) {
        console.warn('No data available for 24h chart')
        return
      }
      
      const last24Hours = data.slice(-24)
      
      this.usage24Chart = new Chart(ctx, {
        type: 'line',
        data: {
          labels: last24Hours.map(d => new Date(d.timestamp).getHours() + ':00'),
          datasets: [{
            label: 'Power Usage (WH)',
            data: last24Hours.map(d => d.power),
            borderColor: '#667eea',
            backgroundColor: 'rgba(102, 126, 234, 0.1)',
            fill: true,
            tension: 0.4
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: false
            }
          },
          scales: {
            y: {
              beginAtZero: true
            }
          }
        }
      })
    }
  }
}
</script>