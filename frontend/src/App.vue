<template>
  <div id="app">
    <!-- Login Screen -->
    <LoginComponent 
      v-if="!isLoggedIn" 
      @login-success="handleLoginSuccess"
    />

    <!-- Main Dashboard -->
    <DashboardComponent 
      v-else 
      @logout="handleLogout"
    />
  </div>
</template>

<script>
import LoginComponent from './components/LoginComponent.vue'
import DashboardComponent from './components/DashboardComponent.vue'

export default {
  name: 'App',
  components: {
    LoginComponent,
    DashboardComponent
  },
  data() {
    return {
      isLoggedIn: false
    }
  },
  mounted() {
    this.checkAuth()
  },
  methods: {
    checkAuth() {
      const userId = localStorage.getItem('user_id')
      if (userId) {
        this.isLoggedIn = true
      }
    },
    handleLoginSuccess() {
      this.isLoggedIn = true
    },
    async handleLogout() {
      this.isLoggedIn = false
      localStorage.removeItem('user_id')
      const res = await fetch("http://localhost:5000/api/logout", {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          }
        });
    }
  }
}
</script>