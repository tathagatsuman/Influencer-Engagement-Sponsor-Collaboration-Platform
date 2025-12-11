<template>
  <div class="card cardWidth">
    <h3>{{ title }}</h3>
    <div class="scrollable">
      <ul class="Req">
        <li v-for="request in requests" :key="request.id">
          <div>
            <h4>Campaign Name: {{ request.campaign_name }}</h4>
            <p>Influencer Name: {{ request.influencer_name }}</p>
            <p>Influencer UserName: {{ request.influencer_username }}</p>
            <p>Influencer Niche: {{ request.niche }}</p>
            <p>Influencer Reach: {{ request.reach }}</p>
            <p>Influencer Active-Status: {{ request.active_status }}</p>
            <p v-if="request.request_type === 'influencer'">Message(Payment-Demanded): {{ request.messages }}</p>
            <p v-if="request.request_type === 'sponsor'">Message(Payment-Offered): {{ request.messages }}</p>
            <p>{{ request.status }}</p>
            <button v-if="request.status === 'Pending' && request.request_type === 'influencer'" @click="manageRequest(request.id, 'accept')" class="button">Accept</button>
            <button v-if="request.status === 'Pending' && request.request_type === 'influencer'" @click="manageRequest(request.id, 'reject')" class="button">Reject</button>
            <button v-if="request.request_type === 'sponsor' && request.status === 'Pending'"  @click="openEditForm(request)" class="button">Edit</button>
            <button v-if="request.request_type === 'sponsor'" @click="deleteRequest(request.id)" class="button">Delete</button>
          </div>
        </li>
      </ul>
    </div>

    <!-- Only show form if there's a valid selectedRequest -->
    <AdRequestFormSponsor
      v-if="showEditForm && selectedRequest"
      @close="showEditForm = false"
      @adRequestSent="refreshRequests"
      :user="getUserData(selectedRequest)"
      :campaigns="campaigns"
      :request="selectedRequest"
    />
  </div>
</template>

<script>
import api from '@/utils/auth';
import AdRequestFormSponsor from '@/components/icons/AdRequestFormSponsor.vue';

export default {
  name: "AdRequestSponsor",
  props: ["requests", "title", "campaigns"],
  data() {
    return {
      showEditForm: false,  // Control edit form visibility
      selectedRequest: null,  // Store the selected request for editing
      
    };
  },
  methods: {
    openEditForm(request) {
      this.selectedRequest = request;  // Set the request to be edited
      this.showEditForm = true;
    },
    getUserData(request) {
      // Create user object based on the request fields
      return {
        name: request.influencer_name,
        username: request.influencer_username,
        niche: request.niche,
        reach: request.reach,
        active_status: request.active_status
      };
    },
    async manageRequest(requestId, action) {
      try {
        await api.put(`/manage_request/${requestId}/${action}`);
        alert(`Request ${action}ed successfully`);
        this.$emit('refreshRequests'); // Emit event to refresh request list after action
      } catch (error) {
        console.error(`Error ${action}ing request:`, error);
        alert(`Failed to ${action} the request`);
      }
    },

    async deleteRequest(requestId) {
      try {
        await api.delete(`/delete_request/${requestId}`);
        alert('Request deleted successfully');
        this.$emit('refreshRequests'); // Emit event to refresh request list after deletion
      } catch (error) {
        console.error('Error deleting request:', error);
        alert('Failed to delete the request');
      }
    },
    refreshRequests() {
      this.$emit('refreshRequests');  // Refresh the request list
    }
  },
  components: {
    AdRequestFormSponsor
  }
};
</script>

<style scoped>
@import '@/assets/card.css';
</style>
