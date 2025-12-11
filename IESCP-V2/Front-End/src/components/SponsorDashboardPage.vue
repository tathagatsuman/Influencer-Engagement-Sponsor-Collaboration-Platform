<template>
    <div class="body">
        <NavBar />
        <div class="container">
            <h2>Welcome! {{ user.name }}</h2>
            <div class="fram">
              <CampaignList :campaigns="campaigns" @refreshDashboard="fetchData" title="Your Campaigns:" />
              <UserList :users="users" :campaigns="campaigns" @refreshDashboard="fetchData" title="Active Influencers:" />
            </div>
            <div class="fram">
              <AdRequestSponsor :requests="sent_requests" :campaigns="campaigns" @refreshRequests="fetchData" title="Sent Requests to Influencers" />
              <AdRequestSponsor :requests="recieved_requests" @refreshRequests="fetchData" title="Recieved Requests from Influencers" />              
            </div>
        </div>    
    </div>
</template>
  
<script>
    import api from '@/utils/auth';
    import NavBar from "@/components/icons/NavBar.vue";
    import CampaignList from "@/components/icons/CampaignList.vue";
    import UserList from "@/components/icons/UserList.vue";
    import AdRequestSponsor from "@/components/icons/AdRequestSponsor.vue";

export default {
    name: "sponsorDashboard",
    components: { NavBar, CampaignList, UserList, AdRequestSponsor},
    data() {
      return {
        user: JSON.parse(localStorage.getItem('user')),
        campaigns: [], // Replace with campaign data
        users: [], // Replace with influencer data
        sent_requests: [], // Replace with sent request data
        recieved_requests: [],
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
          this.users = response.data.influencers || [];
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
  },
  };
</script>
  
<style scoped>
@import '@/assets/dashboardBody.css';
@import '@/assets/card.css';
</style>