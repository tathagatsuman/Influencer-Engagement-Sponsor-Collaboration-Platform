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

      <div class="contentbox registerContentbox">
        <div class="formbox card">
          <h2>Register</h2>
          <form @submit.prevent="validateForm">
            <div class="scrollable">
              <div class="inputbox">
                <label for="name">Name:</label>
                <input type="text" id="name" v-model="form.name" required>
                <span v-if="errors.name" class="error-message">{{ errors.name }}</span>
              </div>
              <div class="inputbox">
                <label for="username">Username:</label>
                <input type="email" id="username" v-model="form.username" required>
                <span v-if="errors.username" class="error-message">{{ errors.username }}</span>
              </div>
              <div class="inputbox">
                <label for="password">Password:</label>
                <input type="password" id="password" v-model="form.password" required>
                <span v-if="errors.password" class="error-message">{{ errors.password }}</span>
              </div>
              <div class="inputbox">
                <label for="retype-password">Confirm Password:</label>
                <input type="password" id="retype-password" v-model="form.retypePassword" required>
                <span v-if="errors.retypePassword" class="error-message">{{ errors.retypePassword }}</span>
              </div>
              <div class="inputbox">
                <label for="niche">Niche:</label>
                <select id="niche" v-model="form.niche" required>
                  <option disabled value="">Niche/Category</option>
                  <option value="automobiles">Auto-Mobiles</option>
                  <option value="beverages">Beverages</option>
                  <option value="education">Education</option>
                  <option value="fashion">Fashion</option>
                  <option value="food">Food</option>
                  <option value="real-estates">Real Estates</option>
                  <option value="sports">Sports</option>
                  <option value="technology">Technology</option>
                </select>
                <span v-if="errors.niche" class="error-message">{{ errors.niche }}</span>
              </div>
              <div class="inputbox">
                <label for="role">Role:</label>
                <select id="role" v-model="form.role" required>
                  <option disabled value="">Role</option>
                  <option value="sponsor">Sponsor</option>
                  <option value="influencer">Influencer</option>
                </select>
                <span v-if="errors.role" class="error-message">{{ errors.role }}</span>
              </div>
              <div v-if="form.role === 'influencer'">
                <div class="inputbox">
                  <label for="reach">Reach:</label>
                  <input type="number" id="reach" v-model="form.reach" required>
                  <span v-if="errors.reach" class="error-message">{{ errors.reach }}</span>
                </div>
                <div class="inputbox">
                  <label for="active_status">Active Status:</label>
                  <select id="active_status" v-model="form.activeStatus" required>
                    <option disabled value="">Active-Status</option>
                    <option value="active">Active</option>
                    <option value="inactive">Inactive</option>
                  </select>
                  <span v-if="errors.activeStatus" class="error-message">{{ errors.activeStatus }}</span>
                </div>
              </div>
            </div>
            <div class="inputbox">
              <input type="submit" value="Register">
            </div>
            <div class="inputbox">
              <p>Already have an account...? <router-link to="/login">Log In</router-link></p>
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
        name: '',
        username: '',
        password: '',
        retypePassword: '',
        niche: '',  
        role: '',
        reach: '',        
        activeStatus: '' 
      },
      errors: {}
    };
  },
  methods: {
    validateForm() {
      this.errors = {};

      // Field-specific validations
      if (!this.form.name) {
        this.errors.name = 'Name is required.';
      }
      if (!this.form.username) {
        this.errors.username = 'Username is required.';
      }
      if (!this.form.password) {
        this.errors.password = 'Password is required.';
      }
      if (!this.form.retypePassword) {
        this.errors.retypePassword = 'Please confirm your password.';
      }
      if (!this.form.niche) {
        this.errors.niche = 'Niche is required.';
      }
      if (!this.form.role) {
        this.errors.role = 'Role is required.';
      }
      if (this.form.role === 'influencer' && !this.form.reach) {
        this.errors.reach = 'Reach is required for influencers.';
      }
      if (this.form.role === 'influencer' && !this.form.activeStatus) {
        this.errors.activeStatus = 'Active status is required for influencers.';
      }

      // Password confirmation validation
      if (this.form.password !== this.form.retypePassword) {
        this.errors.retypePassword = 'Passwords do not match.';
      }
      
      // Email validation for username
      const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailPattern.test(this.form.username)) {
        this.errors.username = 'Please enter a valid email address.';
      }

      // Password validation
      const passwordPattern = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*])[A-Za-z\d!@#$%^&*]{8,}$/;
      if (!passwordPattern.test(this.form.password)) {
        this.errors.password = 'Password must be at least 8 characters long and include at least one uppercase letter, one lowercase letter, one digit, and one special character.';
      }

      if (Object.keys(this.errors).length === 0) {
        // Submit form if no validation errors
        this.registerUser();
      }
    },
    async registerUser() {
      try {
        const response = await axios.post('http://127.0.0.1:5000/register', {
          username: this.form.username,
          password: this.form.password,
          name: this.form.name,
          role: this.form.role,
          niche: this.form.niche,
          reach: this.form.role === 'influencer' ? this.form.reach : undefined,
          active_status: this.form.role === 'influencer' ? this.form.activeStatus : undefined
        });

        const { user, access_token, refresh_token } = response.data;
        
        alert('Registration successful!');

        // Store tokens in localStorage
        localStorage.setItem('user', JSON.stringify(user));
        localStorage.setItem('access_token', access_token);
        localStorage.setItem('refresh_token', refresh_token);
        
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
          this.errors.username = error.response.data.error || 'An error occurred during registration.';
        } else {
          this.errors.username = 'An unexpected error occurred.';
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
