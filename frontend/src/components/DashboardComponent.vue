<template>
  <div class="container">
    <HeaderComponent 
      :activeTab="activeTab"
      @tab-change="activeTab = $event"
      @logout="$emit('logout')"
    />

    <!-- Dashboard Tab -->
    <DashboardTabComponent 
      v-if="activeTab === 'dashboard'"
      :currentUsage="currentUsage"
      :currentCost="currentCost"
      :budgetData="budgetData"
      :budgetPercentage="budgetPercentage"
      @update-budget="updateBudget"
    />

    <!-- Analytics Tab -->
    <AnalyticsTabComponent 
      v-if="activeTab === 'analytics'"
      :analyticsData="analyticsData"
      :heatmapData="heatmapData"
      @load-analytics="loadAnalytics"
    />

    <!-- Alerts Tab -->
    <AlertsTabComponent 
      v-if="activeTab === 'alerts'"
      :alerts="alerts"
      @ignore-alert="ignoreAlert"
    />
  </div>
</template>

<script>
import HeaderComponent from './HeaderComponent.vue'
import DashboardTabComponent from './DashboardTabComponent.vue'
import AnalyticsTabComponent from './AnalyticsTabComponent.vue'
import AlertsTabComponent from './AlertsTabComponent.vue'

export default {
  name: 'DashboardComponent',
  emits: ['logout'],
  components: {
    HeaderComponent,
    DashboardTabComponent,
    AnalyticsTabComponent,
    AlertsTabComponent
  },
  data() {
    return {
      activeTab: 'dashboard',
      currentUsage: 1853,
      currentCost: 516,
      budgetData: {
        budget: 1000,
        spent: 516,
        remaining: 484,
        over_budget: false
      },
      analyticsData: [],
      alerts: [],
      heatmapData: []
    }
  },
  computed: {
    budgetPercentage() {
      if (this.budgetData.budget === 0) return 0
      return Math.min((this.budgetData.spent / this.budgetData.budget) * 100, 100)
    }
  },
  mounted() {
    this.loadDashboardData()
    this.loadHeatmapData() // Load from API instead of generating
    setInterval(() => {
      this.loadDashboardData()
      if (this.activeTab === 'dashboard') {
        this.loadHeatmapData() // Update heatmap periodically
      }
    }, 30000) // Update every 30 seconds
  },
  methods: {
    async loadDashboardData() {
      try {
        // Load budget data
        const budgetResponse = await fetch('http://127.0.0.1:5000/api/budget')
        if (budgetResponse.ok) {
          const budgetData = await budgetResponse.json()
          this.budgetData = {
            budget: parseFloat(budgetData.budget) || 0,
            spent: parseFloat(budgetData.spent) || 0,
            remaining: parseFloat(budgetData.remaining) || 0,
            over_budget: budgetData.over_budget || false
          }
        } else {
          console.error('Failed to load budget data:', budgetResponse.status)
        }
        
        // Load analytics for dashboard chart (recent data)
        const analyticsResponse = await fetch('http://127.0.0.1:5000/api/analytics')
        if (analyticsResponse.ok) {
          const data = await analyticsResponse.json()
          this.analyticsData = data || []
          
          // Update current usage from latest data point
          if (this.analyticsData.length > 0) {
            const latest = this.analyticsData[this.analyticsData.length - 1]
            this.currentUsage = Math.round(parseFloat(latest.power) || 0)
            this.currentCost = Math.round((parseFloat(latest.power) || 0) * 0.27) // Assuming 0.27 Rs per WH
          }
        } else {
          console.error('Failed to load analytics data:', analyticsResponse.status)
        }
        
        // Load alerts
        const alertsResponse = await fetch('http://127.0.0.1:5000/api/alerts')
        if (alertsResponse.ok) {
          this.alerts = await alertsResponse.json() || []
        } else {
          console.error('Failed to load alerts:', alertsResponse.status)
        }
        
      } catch (err) {
        console.error('Error loading dashboard data:', err)
        // Fallback to prevent breaking the UI
        this.budgetData = {
          budget: 1000,
          spent: 516,
          remaining: 484,
          over_budget: false
        }
      }
    },
    
    async updateBudget(newBudget) {
      if (!newBudget || newBudget <= 0) {
        console.warn('Invalid budget value:', newBudget)
        return
      }
      
      try {
        const response = await fetch('http://127.0.0.1:5000/api/budget', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ budget: parseFloat(newBudget) })
        })
        
        if (response.ok) {
          const updatedBudgetData = await response.json()
          // Reload dashboard data to get updated budget info
          await this.loadDashboardData()
        } else {
          console.error('Failed to update budget:', response.status)
          const errorData = await response.json()
          console.error('Error details:', errorData)
        }
      } catch (err) {
        console.error('Error updating budget:', err)
      }
    },
    
    async loadAnalytics(period = null) {
      try {
        let url = 'http://127.0.0.1:5000/api/analytics'
        if (period) {
          url += `?period=${period}`
        }
        
        const response = await fetch(url)
        if (response.ok) {
          const data = await response.json()
          this.analyticsData = data || []
        } else {
          console.error('Failed to load analytics:', response.status)
        }
      } catch (err) {
        console.error('Error loading analytics:', err)
      }
    },
    
    async loadHeatmapData() {
      try {
        const response = await fetch('http://127.0.0.1:5000/api/heatmap')
        if (response.ok) {
          const data = await response.json()
          this.heatmapData = data || Array(24).fill(0)
        } else {
          console.error('Failed to load heatmap data:', response.status)
          // Fallback to generated data
          this.generateHeatmapData()
        }
      } catch (err) {
        console.error('Error loading heatmap data:', err)
        // Fallback to generated data
        this.generateHeatmapData()
      }
    },
    
    async ignoreAlert(alertId) {
      try {
        const response = await fetch('http://127.0.0.1:5000/api/alerts', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ alert_id: alertId })
        })
        
        if (response.ok) {
          await this.loadDashboardData()
        } else {
          console.error('Failed to ignore alert:', response.status)
        }
      } catch (err) {
        console.error('Error ignoring alert:', err)
      }
    },
    
    generateHeatmapData() {
      // Generate sample heatmap data for 24 hours (fallback)
      this.heatmapData = Array.from({ length: 24 }, (_, i) => {
        // Simulate higher usage during peak hours
        if (i >= 6 && i <= 9) return Math.round(Math.random() * 800 + 200) // Morning peak
        if (i >= 18 && i <= 22) return Math.round(Math.random() * 1000 + 300) // Evening peak
        return Math.round(Math.random() * 400 + 50) // Normal hours
      })
    }
  },
  
  watch: {
    activeTab(newTab) {
      this.$nextTick(() => {
        if (newTab === 'analytics') {
          this.loadAnalytics()
          this.loadHeatmapData()
        } else if (newTab === 'dashboard') {
          this.loadDashboardData()
        }
      })
    }
  }
}
</script>