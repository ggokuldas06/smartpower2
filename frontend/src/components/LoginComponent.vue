<template>
  <div class="login-container">
    <div class="login-card">
      <div class="logo">
        <h1>⚡ SmartPower</h1>
        <span>Guard</span>
      </div>
      
      <div v-if="!showRegister">
        <h2 style="text-align: center; margin-bottom: 30px;">LOGIN</h2>
        <form @submit.prevent="login">
          <div class="form-group">
            <label>Email</label>
            <input type="text" v-model="loginForm.username" required>
          </div>
          <div class="form-group">
            <label>Password</label>
            <input type="password" v-model="loginForm.password" required>
          </div>
          <button type="submit" class="btn" :disabled="loading">
            {{ loading ? 'Logging in...' : 'LOGIN' }}
          </button>
          <button type="button" class="btn btn-secondary" @click="showRegister = true">
            Create a new account
          </button>
        </form>
      </div>

      <div v-else>
        <h2 style="text-align: center; margin-bottom: 30px;">REGISTER</h2>
        <form @submit.prevent="register">
          <div class="form-group">
            <label>Username</label>
            <input type="text" v-model="registerForm.username" required>
          </div>
          <div class="form-group">
            <label>Password</label>
            <input type="password" v-model="registerForm.password" required>
          </div>
          <button type="submit" class="btn" :disabled="loading">
            {{ loading ? 'Registering...' : 'REGISTER' }}
          </button>
          <button type="button" class="btn btn-secondary" @click="showRegister = false">
            Back to Login
          </button>
        </form>
      </div>

      <div v-if="error" class="error" style="margin-top: 15px; text-align: center;">
        {{ error }}
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'LoginComponent',
  emits: ['login-success'],
  data() {
    return {
      showRegister: false,
      loading: false,
      error: '',
      loginForm: {
        username: '',
        password: ''
      },
      registerForm: {
        username: '',
        password: ''
      }
    }
  },
  methods: {
    async login() {
      this.loading = true
      this.error = ''
      
      try {
        const response = await fetch('http://127.0.0.1:5000/api/login', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(this.loginForm)
        })
        
        const data = await response.json()
        
        if (response.ok) {
          localStorage.setItem('user_id', data.user_id)
          this.$emit('login-success')
        } else {
          this.error = data.error || 'Login failed'
        }
      } catch (err) {
        this.error = 'Connection error. Please try again.'
      }
      
      this.loading = false
    },
    
    async register() {
      this.loading = true
      this.error = ''
      
      try {
        const response = await fetch('http://127.0.0.1:5000/api/register', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(this.registerForm)
        })
        
        const data = await response.json()
        
        if (response.ok) {
          this.showRegister = false
          alert('Registration successful! Please login.')
        } else {
          this.error = data.error || 'Registration failed'
        }
      } catch (err) {
        this.error = 'Connection error. Please try again.'
      }
      
      this.loading = false
    }
  }
}
</script>