<template>
  <div v-if="isVisible" class="modal-overlay" @click.self="closeModal">
    <div class="container">
      <div class="card">
        <span class="close-button" @click="$emit('close')">&times;</span>
        <h2>Profile</h2>
        <form @submit.prevent="validateAndUpdateProfile">
          <div class="scrollable">
            
            <label for="name">Name</label>
            <input type="text" id="name" v-model="profile.name" :disabled="isDisabled" @input="clearError('name')" required/>
            <span v-if="errors.name" class="error">{{ errors.name }}</span>

            <label for="username">Username</label>
            <input type="text" id="username" v-model="profile.username" disabled />

            <label for="niche">Niche</label>
            <select id="niche" v-model="profile.niche" :disabled="isDisabled" @change="clearError('niche')" required>
              <option value="" disabled>Niche/Category</option>
              <option v-for="niche in niches" :key="niche" :value="niche">{{ niche }}</option>
            </select>
            <span v-if="errors.niche" class="error">{{ errors.niche }}</span>

            <div v-if="profile.role === 'influencer'">
              <label for="active_status">Active Status</label>
              <select id="active_status" v-model="profile.active_status" @change="clearError('active_status')" required>
                <option value="" disabled>Active-Status</option>
                <option v-for="activeStatus in activeStatuses" :key="activeStatus" :value="activeStatus">{{ activeStatus }}</option>
              </select>
              <span v-if="errors.active_status" class="error">{{ errors.active_status }}</span>

              <label for="reach">Reach</label>
              <input type="number" id="reach" v-model="profile.reach" @input="clearError('reach')" min="1" required/>
              <span v-if="errors.reach" class="error">{{ errors.reach }}</span>
            </div>
          </div>

          <button type="submit" class="button" :disabled="isDisabled || hasErrors">Update Profile</button>
        </form>
        
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/utils/auth';

export default {
  data() {
    return {
      profile: JSON.parse(localStorage.getItem('user')),
      niches: [
        'automobiles', 'beverages', 'education', 'fashion', 'food',
        'real estates', 'sports', 'technology'
      ],
      activeStatuses: ['active', 'inactive'],
      errors: {
        name: '',
        niche: '',
        active_status: '',
        reach: ''
      }
    };
  },
  props: {
    isVisible: {
      type: Boolean,
      default: false
    }
  },
  computed: {
    isDisabled() {
      return this.profile.role === 'admin';
    },
    hasErrors() {
      return Object.values(this.errors).some(error => error);
    }
  },
  methods: {
    closeModal() {
      this.$emit('close');
    },
    validateAndUpdateProfile() {
      if (!this.profile.name) {
        this.errors.name = 'Name is required.';
      }
      if (!this.profile.niche) {
        this.errors.niche = 'Please select a niche.';
      }
      if (this.profile.role === 'influencer') {
        if (!this.profile.active_status) {
          this.errors.active_status = 'Please select an active status.';
        }
        if (!this.profile.reach || this.profile.reach < 1) {
          this.errors.reach = 'Reach should be a positive number.';
        }
      }
      if (!this.hasErrors) {
        this.updateProfile();
      }
    },
    async updateProfile() {
      try {
        const updateData = {
          name: this.profile.name,
          niche: this.profile.niche
        };
        if (this.profile.role === 'influencer') {
          updateData.active_status = this.profile.active_status;
          updateData.reach = this.profile.reach;
        }
        const response = await api.put('/profile', updateData);
        // Update local storage after successful update
        localStorage.setItem('user', JSON.stringify(this.profile));
        // Handle success
        console.log('Profile updated successfully:', response.data);
        this.$emit('close'); // Close the modal after successful update
      } catch (error) {
        console.error('Error updating profile:', error);
      }
    },
    clearError(field) {
      this.errors[field] = '';
    }
  }
};
</script>

<style scoped>
@import '@/assets/overlay.css';
.error {
  color: red;
  font-size: 0.8em;
  margin-top: 4px;
}
</style>
