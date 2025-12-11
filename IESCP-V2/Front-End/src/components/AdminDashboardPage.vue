<template>
    <div class="body">
    
      <NavBar />
      <div class="container">
        <h2>Admin Dashboard</h2>
        <div class="card">
          <h3>Approve-Sponsor:</h3>
          <div class="search-bar">
            <input v-model="searchQuery" type="text" :placeholder="'Search by name, username, niche'" class="search-input" />
          </div>
          <div class="scrollable">
            <ul class="Users">
              <li v-for="filteredUser in filteredUsers" :key="filteredUser.id">
              <div>
                <h4>{{ filteredUser.name }}</h4>
                <p>UserName: {{ filteredUser.username }}</p>
                <p>Role: {{ filteredUser.role }}</p>
                <p>Niche: {{ filteredUser.niche }}</p>

                <button v-if="!filteredUser.isApproved" @click="approveUser(filteredUser.id)" class="button">Approve</button>
                <button v-if="!filteredUser.isApproved" @click="deleteUser(filteredUser.id)" class="button">Reject</button> 
              </div>
              </li>
            </ul>
          </div>
        </div>
        <div class="fram">
          <UserList :users="unflaggedUsers" :campaigns="[]" @refreshDashboard="fetchData" title="All Users (Not Flagged Inappropriate):" />
          <UserList :users="flaggedUsers" :campaigns="[]" @refreshDashboard="fetchData" title="All Users (Flagged Inappropriate):" />
        </div>
        <div class="fram">
          <CampaignList :campaigns="unflaggedCampaigns" @refreshDashboard="fetchData" title="All Campaigns (Not Flagged Inappropriate):" />
          <CampaignList :campaigns="flaggedCampaigns" @refreshDashboard="fetchData" title="All Campaigns (Flagged Inappropriate):" />
        </div>
        <AdRequestList :requests="requests" @refreshDashboard="fetchData" title="Ad Requests:"/>
      </div>
    </div>
    
</template>
  
<script>
  import api from '@/utils/auth'
  import NavBar from "@/components/icons/NavBar.vue";
  import UserList from "@/components/icons/UserList.vue";
  import CampaignList from "@/components/icons/CampaignList.vue";
  import AdRequestList from "@/components/icons/AdRequestList.vue";
  
  export default {
    name: "adminDashboard",
    components: { NavBar, UserList, CampaignList, AdRequestList },
    data() {
      return {
        users: [], // Fetch or pass this data
        campaigns: [], // Fetch or pass this data
        requests: [], // Fetch or pass this data
        searchQuery: ''
      };
    },
    computed: {
    filteredUsers() {
      const filteredUsers = this.users.filter((user) => user.role === 'sponsor' && !user.isApproved );

      if (!this.searchQuery.trim()) {
        return filteredUsers
      }
      const query = this.searchQuery.trim().toLowerCase();
      return filteredUsers.filter((user) => 
        (user.name && user.name.toLowerCase().includes(query)) || 
        (user.username && user.username.toLowerCase().includes(query)) ||
        (user.role && user.role.toLowerCase().includes(query)) || 
        (user.niche && user.niche.toLowerCase().includes(query))
      );
    },
      unflaggedUsers() {
        return this.users.filter(user => !user.is_flagged && user.role !== 'admin');
      },
      flaggedUsers() {
        return this.users.filter(user => user.is_flagged && user.role !== 'admin');
      },
      unflaggedCampaigns() {
        return this.campaigns.filter(campaign => !campaign.is_flagged);
      },
      flaggedCampaigns() {
        return this.campaigns.filter(campaign => campaign.is_flagged);
      },
    },
    methods: {
    async deleteUser(userId) {
      try {
        await api.delete(`/delete_user/${userId}`);
        alert('Sponsor rejected successfully');
        this.fetchData();
      } catch (error) {
        console.error('Error rejecting sponsor:', error);
      }
    },

    async approveUser(userId) {
      try {
        await api.put(`/admin/approve_sponsor/${userId}`);
        alert('Sponsor approved successfully');
        this.fetchData();
      } catch (error) {
        console.error('Error approving sponsor:', error);
      }
    },
    // Method to fetch data from the backend API
    async fetchData() {
      try {
        // Make an API call to get dashboard data
        const response = await api.get('/dashboard')
        
        // Update the component's data properties based on the response
        if (response && response.data) {
          this.users = response.data.users || [];
          this.campaigns = response.data.campaigns || [];
          this.requests = response.data.requests || [];
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
  