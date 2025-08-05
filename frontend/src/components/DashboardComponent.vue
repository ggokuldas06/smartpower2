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
      :analyticsData="dashboardAnalyticsData"
      :key="dashboardKey"
      @update-budget="updateBudget"
    />

    <!-- Analytics Tab -->
    <AnalyticsTabComponent 
      v-if="activeTab === 'analytics'"
      :analyticsData="analyticsData"
      :heatmapData="heatmapData"
      :key="analyticsKey"
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
      dashboardAnalyticsData: [], // Separate data for dashboard
      alerts: [],
      heatmapData: Array(24).fill(0),
      dashboardKey: 0, // Force re-render key for dashboard
      analyticsKey: 0, // Force re-render key for analytics
      dataLoading: false
    }
  },
  computed: {
    budgetPercentage() {
      if (this.budgetData.budget === 0) return 0
      return Math.min((this.budgetData.spent / this.budgetData.budget) * 100, 100)
    }
  },
  mounted() {
    this.initializeDashboard()
    
    // Set up periodic updates
    setInterval(() => {
      if (!this.dataLoading) {
        this.loadDashboardData()
      }
    }, 30000) // Update every 30 seconds
  },
  methods: {
    async initializeDashboard() {
      // Initial load with some delay to ensure DOM is ready
      await this.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 100))
      await this.loadDashboardData()
    },

    async loadDashboardData() {
      if (this.dataLoading) return
      this.dataLoading = true

      try {
        console.log('Loading dashboard data...')
        
        // Load all data in parallel
        const [budgetData, analyticsData, alertsData, heatmapData] = await Promise.allSettled([
          this.fetchBudgetData(),
          this.fetchAnalyticsData(),
          this.fetchAlertsData(),
          this.fetchHeatmapData()
        ])

        // Process budget data
        if (budgetData.status === 'fulfilled' && budgetData.value) {
          this.budgetData = budgetData.value
        }

        // Process analytics data for dashboard (last 24 hours)
        if (analyticsData.status === 'fulfilled' && analyticsData.value) {
          this.analyticsData = analyticsData.value
          this.dashboardAnalyticsData = this.filterLast24Hours(analyticsData.value)
          
          // Update current usage from latest data point
          if (this.dashboardAnalyticsData.length > 0) {
            const latest = this.dashboardAnalyticsData[this.dashboardAnalyticsData.length - 1]
            this.currentUsage = Math.round(parseFloat(latest.power) || 0)
            this.currentCost = Math.round((parseFloat(latest.power) || 0) * 0.27)
          }
        }

        // Process alerts data
        if (alertsData.status === 'fulfilled' && alertsData.value) {
          this.alerts = alertsData.value
        }

        // Process heatmap data
        if (heatmapData.status === 'fulfilled' && heatmapData.value) {
          this.heatmapData = heatmapData.value
        }

        // Force re-render of dashboard component to fix chart issues
        this.dashboardKey++

        console.log('Dashboard data loaded successfully')
        
      } catch (err) {
        console.error('Error loading dashboard data:', err)
      } finally {
        this.dataLoading = false
      }
    },

    filterLast24Hours(data) {
      if (!data || !Array.isArray(data)) return []
      
      const twentyFourHoursAgo = new Date()
      twentyFourHoursAgo.setHours(twentyFourHoursAgo.getHours() - 24)
      
      return data.filter(entry => {
        const entryDate = new Date(entry.timestamp)
        return entryDate >= twentyFourHoursAgo
      }).sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))
    },

    async fetchBudgetData() {
      try {
        const response = await fetch('http://127.0.0.1:5000/api/budget')
        if (response.ok) {
          const data = await response.json()
          return {
            budget: parseFloat(data.budget) || 0,
            spent: parseFloat(data.spent) || 0,
            remaining: parseFloat(data.remaining) || 0,
            over_budget: data.over_budget || false
          }
        } else {
          console.error('Failed to load budget data:', response.status)
          return null
        }
      } catch (err) {
        console.error('Error fetching budget data:', err)
        return null
      }
    },

    async fetchAnalyticsData() {
      try {
        const response = await fetch('http://127.0.0.1:5000/api/analytics')
        if (response.ok) {
          const data = await response.json()
          return Array.isArray(data) ? data : []
        } else {
          console.error('Failed to load analytics data:', response.status)
          return []
        }
      } catch (err) {
        console.error('Error fetching analytics data:', err)
        return []
      }
    },

    async fetchAlertsData() {
      try {
        const response = await fetch('http://127.0.0.1:5000/api/alerts')
        if (response.ok) {
          const data = await response.json()
          return Array.isArray(data) ? data : []
        } else {
          console.error('Failed to load alerts data:', response.status)
          return []
        }
      } catch (err) {
        console.error('Error fetching alerts data:', err)
        return []
      }
    },

    async fetchHeatmapData() {
      try {
        const response = await fetch('http://127.0.0.1:5000/api/heatmap')
        if (response.ok) {
          const data = await response.json()
          return Array.isArray(data) ? data : Array(24).fill(0)
        } else {
          console.error('Failed to load heatmap data:', response.status)
          return this.generateFallbackHeatmapData()
        }
      } catch (err) {
        console.error('Error fetching heatmap data:', err)
        return this.generateFallbackHeatmapData()
      }
    },

    generateFallbackHeatmapData() {
      return Array.from({ length: 24 }, (_, i) => {
        if (i >= 6 && i <= 9) return Math.round(Math.random() * 800 + 200) // Morning peak
        if (i >= 18 && i <= 22) return Math.round(Math.random() * 1000 + 300) // Evening peak
        return Math.round(Math.random() * 400 + 50) // Normal hours
      })
    },
    
    async updateBudget(newBudget) {
      if (!newBudget || isNaN(newBudget) || parseFloat(newBudget) <= 0) {
        console.warn('Invalid budget value:', newBudget)
        alert('Please enter a valid budget amount')
        return
      }
      
      try {
        console.log('Updating budget to:', newBudget)
        
        const response = await fetch('http://127.0.0.1:5000/api/budget', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ budget: parseFloat(newBudget) })
        })
        
        if (response.ok) {
          const updatedData = await response.json()
          console.log('Budget update response:', updatedData)
          
          // Update the budget data directly from the response
          if (updatedData.budget !== undefined) {
            this.budgetData = {
              budget: parseFloat(updatedData.budget) || 0,
              spent: parseFloat(updatedData.spent) || 0,
              remaining: parseFloat(updatedData.remaining) || 0,
              over_budget: updatedData.over_budget || false
            }
            
            // Force dashboard re-render
            this.dashboardKey++
            
            console.log('Budget updated successfully:', this.budgetData)
          } else {
            // Fallback: reload dashboard data
            await this.loadDashboardData()
          }
        } else {
          const errorData = await response.json()
          console.error('Failed to update budget:', response.status, errorData)
          alert('Failed to update budget: ' + (errorData.error || 'Unknown error'))
        }
      } catch (err) {
        console.error('Error updating budget:', err)
        alert('Error updating budget: ' + err.message)
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
          const responseData = await response.json()
          this.analyticsData = Array.isArray(responseData) ? responseData : []
          
          // Force analytics re-render
          this.analyticsKey++
        } else {
          console.error('Failed to load analytics:', response.status)
        }
      } catch (err) {
        console.error('Error loading analytics:', err)
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
          // Just reload alerts data instead of all dashboard data
          const alertsData = await this.fetchAlertsData()
          if (alertsData) {
            this.alerts = alertsData
          }
        } else {
          console.error('Failed to ignore alert:', response.status)
        }
      } catch (err) {
        console.error('Error ignoring alert:', err)
      }
    }
  },
  
  watch: {
    activeTab: {
      handler(newTab, oldTab) {
        console.log(`Tab changed from ${oldTab} to ${newTab}`)
        
        this.$nextTick(() => {
          if (newTab === 'analytics') {
            this.loadAnalytics()
          } else if (newTab === 'dashboard') {
            this.loadDashboardData()
          }
        })
      },
      immediate: false
    }
  }
}
</script>