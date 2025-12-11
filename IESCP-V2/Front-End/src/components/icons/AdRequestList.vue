<template>
    <div class="card">
      <h3>{{ title }}</h3>
      <div class="scrollable">
        <ul class="Req">
          <li v-for="request in requests" :key="request.id">
            <div>
              <p>
                Campaign Name: {{ request.campaign_name }} -
                Sender Name: {{ request.sender_name }} -
                Sender UserName: {{ request.sender_username }} -
                Receiver Name: {{ request.receiver_name }} -
                Receiver UserName: {{ request.receiver_username }} -
                Type: {{ request.request_type }} -
                Status: {{ request.status }}
              </p>
              <button @click="deleteRequest(request.id)" class="button">Delete</button>
            </div>
          </li>
        </ul>
      </div>
    </div>
  </template>
  
  <script>
  import api from '@/utils/auth';

  export default {
    name: "AdRequestList",
    props: ["requests", "title"],
    methods: {
      async deleteRequest(requestId) {
        try {
          await api.delete(`/delete_request/${requestId}`);
          alert('Ad request deleted successfully');
          this.$emit('refreshDashboard'); // Emit event to refresh dashboard
        } catch (error) {
        console.error('Error deleting ad request:', error);
        }
      }
    },
  };
</script>
  
<style scoped>
@import '@/assets/card.css';
</style>
  