<template>
    <div class="card cardWidth">
      <h3>{{ title }}</h3>
      <div class="scrollable">
        <ul class="Req">
              <li v-for="request in requests" :key="request.request_id">
                <div>
                  <h4>Campaign Name: {{ request.name }}</h4>
                  <p>Description: {{ request.description }}</p>
                  <p>Sponsor Name: {{ request.sponsor_name }}</p>
                  <p>Sponsor UserName: {{ request.sponsor_username }}</p>
                  <p>Niche: {{ request.niche }}</p>
                  <p>Start-Date: {{ request.start_date }}</p>
                  <p>End-Date: {{ request.end_date }}</p>
                  <p>Budget: {{ request.budget }}</p>
                  <p>Goals: {{ request.goals }}</p>
                  <p v-if="request.request_type === 'sponsor'">Message(Payment-Offered): {{ request.messages }}</p>
                  <p v-if="request.request_type === 'influencer'">Message(Payment-Demanded): {{ request.messages }}</p>
                  <p>{{ request.status }}</p>
                  <button v-if="request.status === 'Pending' && request.request_type === 'sponsor'" @click="manageRequest(request.request_id, 'accept')" class="button">Accept</button>
                  <button v-if="request.status === 'Pending' && request.request_type === 'sponsor'" @click="manageRequest(request.request_id, 'reject')" class="button">Reject</button>                
                  <button v-if="request.request_type === 'influencer' && request.status === 'Pending'" @click="editRequest(request)" class="button">Edit</button>
                  <button v-if="request.request_type === 'influencer'" @click="deleteRequest(request.request_id)" class="button">Delete</button>                 
                </div>
              </li>
            </ul>
      </div>
      <AdRequestFormInfluencer v-if="showEditForm" @close="closeForm" @adRequestSent="refreshRequests" :campaign="campaign" :request="selectedRequest" />
    </div>
</template>

<script>
import api from '@/utils/auth';
import AdRequestFormInfluencer from '@/components/icons/AdRequestFormInfluencer.vue';

export default {
    name: "AdRequestInfluencer",
    props: ["requests", "title"],
    data() {
    return {
      campaign: null,
      selectedRequest: null, // The selected request for editing
      showEditForm: false, // Controls the visibility of the edit form
    };
    },
    methods: {

    editRequest(request) {
      this.campaign = {
        name: request.name,
        description: request.description,
        start_date: request.start_date,
        end_date: request.end_date,
        budget: request.budget,
        niche: request.niche,
        visibility: request.visibility,
        goals: request.goals,
      },
      this.selectedRequest = request;
      this.showEditForm = true;
    },

    closeForm() {
      this.selectedRequest = null;
      this.showEditForm = false;
    },
    
        // API call to delete a request
    async deleteRequest(requestId) {
      try {
        await api.delete(`/delete_request/${requestId}`);
        alert("Request deleted successfully!");
        this.$emit('refreshRequests');  // Emit event to parent to refresh the list
      } catch (error) {
        console.error("Error deleting request:", error);
        alert("Failed to delete the request.");
      }
    },

    // API call to manage (accept/reject) a request
    async manageRequest(requestId, action) {
      try {
        await api.put(`/manage_request/${requestId}/${action}`);
        alert(`Request ${action}ed successfully!`);
        this.$emit('refreshRequests');  // Emit event to parent to refresh the list
      } catch (error) {
        console.error(`Error ${action}ing request:`, error);
        alert(`Failed to ${action} the request.`);
      }
    },
    refreshRequests() {
      this.$emit('refreshRequests');  // Refresh the request list
    }
    },
  components: {
    AdRequestFormInfluencer
  }
}
</script>

<style scoped>
@import '@/assets/card.css';
</style>
