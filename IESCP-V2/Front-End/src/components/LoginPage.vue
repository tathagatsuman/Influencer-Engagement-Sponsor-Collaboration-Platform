<template>
  <div class="body">
    <nav>
      <div class="nav-left">
        <router-link to="/" class="nav-link">Home</router-link>
      </div>
    </nav>

    <div class="login-container">
      <div class="imgbox">
        <img src="@/assets/photo.svg" alt="Background Image">
      </div>

      <div class="contentbox">
        <div class="formbox card">
          <h2>Login</h2>
          <form @submit.prevent="validateForm">
            <div class="inputbox">
              <label for="username">Username</label>
              <input type="text" v-model="form.username" id="username" required>
              <span v-if="errors.username" class="error-message">{{ errors.username }}</span>
            </div>
            <div class="inputbox">
              <label for="password">Password</label>
              <input type="password" v-model="form.password" id="password" required>
              <span v-if="errors.password" class="error-message">{{ errors.password }}</span>
            </div>
            <div class="inputbox">
              <input type="submit" value="Sign in">
            </div>
            <div class="inputbox">
              <p>Don't have an account...? <router-link to="/register">Sign Up</router-link></p>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
data() {
  return {
    form: {
      username: '',
      password: ''
    },
    errors: {}
  };
},
methods: {
  validateForm() {
    this.errors = {};
    
    // Email validation
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!this.form.username) {
      this.errors.username = 'Username is required.';
    } else if (!emailPattern.test(this.form.username)) {
      this.errors.username = 'Please enter a valid email address.';
    }

    // Password validation
    const passwordPattern = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{8,}$/;
    if (!this.form.password) {
      this.errors.password = 'Password is required.';
    } else if (!passwordPattern.test(this.form.password)) {
      this.errors.password = 'Password must be at least 8 characters long and include at least one uppercase letter, one lowercase letter, one digit, and one special character.';
    }

    if (Object.keys(this.errors).length === 0) {
      this.loginUser();
      console.log('Form submitted successfully');
    }
  },
  async loginUser() {
    try {
      const response = await axios.post('http://127.0.0.1:5000/login', {
        username: this.form.username,
        password: this.form.password
      });
      
      const { user, access_token, refresh_token } = response.data;
      
      // Store tokens in localStorage
      localStorage.setItem('user', JSON.stringify(user));
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      console.log('Form submitted successfully');
      
      // Redirect to dashboard or another route
      if (user.role === 'influencer') {
        this.$router.push(`/influencer/${user.name}`);
      } else if (user.role === 'sponsor') {
        this.$router.push(`/sponsor/${user.name}`);
      } else if (user.role === 'admin') {
        this.$router.push(`/admin/dashboard/${user.name}`);
      }
      
    } catch (error) {
      if (error.response && error.response.data) {
        this.errors.server = error.response.data.error || 'Login failed. Please try again.';
      } else {
        this.errors.server = 'An error occurred. Please try again.';
      }
    }
  }    
}
};
</script>

<style scoped>
@import '@/assets/navBar.css';
@import '@/assets/loginRegister.css';
</style>
