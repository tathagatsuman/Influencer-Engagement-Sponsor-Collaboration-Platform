<template>
    <div class="body">
    <NavBar />
    <div class="container">
      <h2>Welcome! {{ userName }}</h2>
      <div class="fram">
        <AdRequestInfluencer :requests="sent_requests"  @refreshRequests="fetchData" title="Sent Requests to Sponsors" />
        <AdRequestInfluencer :requests="recieved_requests" @refreshRequests="fetchData" title="Recieved Requests from Sponsors" />
      </div>
      <CampaignList :campaigns="campaigns" @refreshDashboard="fetchData" title="Available Campaigns" />
      </div>
    </div>
    
  </template>
  
  <script>
  import api from '@/utils/auth';
  import NavBar from '@/components/icons/NavBar.vue';
  import CampaignList from '@/components/icons/CampaignList.vue';
  import AdRequestInfluencer from '@/components/icons/AdRequestInfluencer.vue';


  export default {
    name: "influencerDashboard",
    components: { NavBar, CampaignList, AdRequestInfluencer },
    data() {
      return {
        campaigns: [], // Replace with user data
        sent_requests: [], // Replace with received request data
        recieved_requests: [], // Replace with available campaign data
      };
    },
    methods: {
      async fetchData() {
      try {
        // Make an API call to get dashboard data
        const response = await api.get('/dashboard');
        
        // Update the component's data properties based on the response
        if(response && response.data){
          this.campaigns = response.data.campaigns || [];
          this.sent_requests = response.data.sent_requests || [];
          this.recieved_requests = response.data.recieved_requests || [];
          
        } else {
          throw new Error("Unexpected response structure");
        }
        
      } catch (error) {
        console.error("Error fetching dashboard data:", error);
        alert("Failed to load dashboard data. Please try again later.");
      }
    }
    },
  created() {
    // Call the fetchData method when the component is created
    this.fetchData();
  }
  };
  </script>
  
  <style scoped>
  @import '@/assets/dashboardBody.css';
  @import '@/assets/card.css';
  </style>
  