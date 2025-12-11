<template>
  <div class="modal-overlay">
    <div class="container">
      <div class="card">
        <span class="close-button" @click="$emit('close')">&times;</span>
        <h2 v-if="isEditMode">Edit Ad Request</h2>
        <h2 v-else>Send Ad Request</h2>
        <form @submit.prevent="handleSubmit">
        <div class="scrollable">
          <p><strong>Influencer Name:</strong> {{ user.name }}</p>
          <p><strong>Influencer Username:</strong> {{ user.username }}</p>
          <p><strong>Influencer Niche:</strong> {{ user.niche }}</p>
          <p><strong>Influencer Reach:</strong> {{ user.reach }}</p>
          <p><strong>Influencer Active Status:</strong> {{ user.active_status }}</p>

          
            <label for="campaign">Select Campaign</label>
            <select v-model="selectedCampaign" required>
              <option disabled value="">Please select a campaign</option>
              <option v-for="campaign in campaigns" :key="campaign.id" :value="campaign.id">
                {{ campaign.name }}
              </option>
            </select>
            <span v-if="errors.selectedCampaign" class="error-message">{{ errors.selectedCampaign }}</span>

            <label for="message">Message</label>
            <textarea
              v-model="message"
              id="message"
              placeholder="Enter your message"
              required
            ></textarea>
            <span v-if="errors.message" class="error-message">{{ errors.message }}</span>
        </div>

            <button type="submit" class="button" :disabled="isSubmitting">
              {{ isEditMode ? 'Update Request' : 'Send Request' }}
            </button>
        </form>
        
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/utils/auth';

export default {
  name: "AdRequestFormSponsor",
  props: {
    user: Object,      // Influencer details
    campaigns: Array,  // List of campaigns
    request: {         // Optional prop to pass the existing request in case of editing
      type: Object,
      default: null,
    }
  },
  data() {
    return {
      selectedCampaign: this.request ? this.request.campaign_id : '', // If edit, pre-populate campaign
      message: this.request ? this.request.messages : '',              // Pre-populate message if edit
      errors: {},
      isSubmitting: false
    };
  },
  computed: {
    isEditMode() {
      return !!this.request;  // Determine if it's edit mode by checking if a request is passed
    }
  },
  methods: {
    validateForm() {
      this.errors = {};

      if (!this.selectedCampaign) {
        this.errors.selectedCampaign = 'Please select a campaign.';
      }

      if (!this.message) {
        this.errors.message = 'Message is required.';
      } else if (this.message.length < 10) {
        this.errors.message = 'Message must be at least 10 characters long.';
      } else if (this.message.length > 500) {
        this.errors.message = 'Message cannot exceed 500 characters.';
      }

      return Object.keys(this.errors).length === 0;
    },
    async handleSubmit() {
      if (!this.validateForm()) return; // Prevent submission if validation fails

      this.isSubmitting = true;

      const adRequestData = {
        influencer_id: this.user.id,
        campaign_id: this.selectedCampaign,
        messages: this.message,
      };

      try {
        if (this.isEditMode) {
          // Edit request API call
          await api.put(`/update_request/${this.request.id}`, adRequestData);
          alert('Ad Request Updated');
        } else {
          // Create new request API call
          await api.post('/request_influencer', adRequestData);
          alert('Ad Request Sent');
        }

        this.$emit('adRequestSent');
        this.$emit('close'); // Close the form after submission
      } catch (error) {
        console.error('Error sending/updating ad request:', error);
      } finally {
        this.isSubmitting = false;
      }
    }
  }
};
</script>

<style scoped>
@import '@/assets/overlay.css';

.error-message {
  color: red;
  font-size: 0.9em;
}
</style>
