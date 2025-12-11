<template>
  <div class="modal-overlay">
    <div class="container">
      <div class="card">
        <span class="close-button" @click="$emit('close')">&times;</span>
        <h2>{{ request ? 'Edit Ad Request' : 'Send Ad Request' }}</h2>
        <form @submit.prevent="submitRequest">
        <div class="scrollable">
          <p><strong>Campaign Name:</strong> {{ campaign.name }}</p>
          <p><strong>Description:</strong> {{ campaign.description }}</p>
          <p><strong>Start-Date:</strong> {{ campaign.start_date }}</p>
          <p><strong>End-Date:</strong> {{ campaign.end_date }}</p>
          <p><strong>Budget:</strong> {{ campaign.budget }}</p>
          <p><strong>Niche:</strong> {{ campaign.niche }}</p>
          <p><strong>Visibility:</strong> {{ campaign.visibility }}</p>
          <p><strong>Goals:</strong> {{ campaign.goals }}</p>
          
          
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
              {{ request ? 'Update Request' : 'Send Request' }}
            </button>
        
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/utils/auth';

export default {
  name: 'AdRequestFormInfluencer',
  props: ['campaign', 'request'],
  data() {
    return {
      user: JSON.parse(localStorage.getItem('user')),
      message: this.request ? this.request.messages : '', // Prepopulate if editing
      errors: {},
      isSubmitting: false
    };
  },
  methods: {
    validateMessage() {
      this.errors = {};
      if (!this.message) {
        this.errors.message = 'Message is required.';
      } else if (this.message.length < 10) {
        this.errors.message = 'Message must be at least 10 characters long.';
      } else if (this.message.length > 500) {
        this.errors.message = 'Message cannot exceed 500 characters.';
      }
      return Object.keys(this.errors).length === 0;
    },
    async submitRequest() {
      if (!this.validateMessage()) {
        return; // Prevent submission if validation fails
      }
      
      this.isSubmitting = true; // Disable the button during submission

      try {
        const adRequestData = {
          messages: this.message,
        };

        if (this.request) {
          // Editing an existing request
          await api.put(`/update_request/${this.request.request_id}`, adRequestData);
          alert('Ad Request updated successfully!');
        } else {
          // Creating a new request
          const response = await api.post(
            `/send_request/${this.campaign.id}/${this.campaign.sponsor_id}`,
            adRequestData
          );
          console.log('Ad Request Sent:', response.data);
          alert('Ad Request sent successfully!');
        }

        this.$emit('adRequestSent');
        this.$emit('close');
      } catch (error) {
        console.error('Error sending/updating ad request:', error);
        if (error.response && error.response.status === 409) {
          alert('Request already exists.');
        } else {
          alert('Failed to process request. Please try again later.');
        }
      } finally {
        this.isSubmitting = false; // Re-enable the button after processing
      }
    },
  },
};
</script>

<style scoped>
@import '@/assets/overlay.css';
.error-message {
  color: red;
  font-size: 0.9em;
}
</style>
