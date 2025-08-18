<template>
  <div class="alerts-container">
    <h2 class="card-title">Alerts</h2>
    
    <div v-if="visibleAlerts.length === 0" class="no-alerts">
      <p>✅ No alerts at the moment</p>
    </div>
    
    <div 
      v-for="alert in visibleAlerts" 
      :key="alert.id" 
      class="alert-item theft"
    >
      <div class="alert-content">
        <div class="alert-time">{{ formatDate(alert.timestamp) }}</div>
        <div class="alert-type">⚠️ {{alert.message}}</div>
        <div>Power: {{ alert.power }} WH, Current: {{ alert.current }} A</div>
      </div>
      <div class="alert-actions">
        <button class="btn-ignore" @click="ignoreAlert(alert.id)">
          Ignore
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AlertsTabComponent',
  emits: ['ignore-alert'],
  props: {
    alerts: {
      type: Array,
      required: true
    }
  },
  computed: {
    visibleAlerts() {
      return this.alerts.filter(alert => !alert.ignored)
    }
  },
  methods: {
    ignoreAlert(alertId) {
      this.$emit('ignore-alert', alertId)
    },
    
    formatDate(dateString) {
      const date = new Date(dateString)
      return date.toLocaleString()
    }
  }
}
</script>