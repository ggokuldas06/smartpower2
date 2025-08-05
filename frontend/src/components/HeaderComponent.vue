<template>
  <div class="header">
    <div class="logo">
      <h1>⚡ SmartPower Guard</h1>
    </div>
    
    <div class="nav-tabs">
      <button 
        class="nav-tab" 
        :class="{ active: activeTab === 'dashboard' }"
        @click="$emit('tab-change', 'dashboard')"
      >
        Dashboard
      </button>
      <button 
        class="nav-tab" 
        :class="{ active: activeTab === 'analytics' }"
        @click="$emit('tab-change', 'analytics')"
      >
        Analytics
      </button>
      <button 
        class="nav-tab" 
        :class="{ active: activeTab === 'alerts' }"
        @click="$emit('tab-change', 'alerts')"
      >
        Alerts
      </button>
    </div>

    <button class="logout-btn" @click="$emit('logout')">Logout</button>
  </div>
</template>

<script>
export default {
  name: 'HeaderComponent',
  emits: ['tab-change', 'logout'],
  props: {
    activeTab: {
      type: String,
      required: true
    }
  }
}
</script>