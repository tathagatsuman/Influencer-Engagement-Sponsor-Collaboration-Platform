<template>
  <div class="card cardWidth">
    <h3>{{ title }}</h3>
    <!-- Search Bar (only for admin and sponsor roles) -->
    <div v-if="user.role === 'admin' || user.role === 'sponsor'" class="search-bar">
        <input 
          v-model="searchQuery" 
          type="text" 
          :placeholder="user.role === 'admin' ? 'Search by name, username, role, niche, or reach' : 'Search by name, username, niche, or reach'" 
          class="search-input" 
        />
    </div>
    <div class="scrollable">
      <ul class="Users">
        <li v-for="filteredUser in filteredUsers" :key="filteredUser.id">
          <div>
            <h4>{{ filteredUser.name }}</h4>
            <p>UserName: {{ filteredUser.username }}</p>
            <p>Role: {{ filteredUser.role }}</p>
            <p>Niche: {{ filteredUser.niche }}</p>
            <p v-if="user.role === 'admin'">Role: {{ filteredUser.role }}</p>
            <p v-if="filteredUser.role === 'influencer'">Reach: {{ filteredUser.reach }}</p>
            <p v-if="filteredUser.role === 'influencer'">Active-Status: {{ filteredUser.active_status }}</p> 
            
            <!-- Admin actions -->
            <button v-if="user.role === 'admin' && filteredUser.role !== 'admin' && !filteredUser.is_flagged" @click="flagUser(filteredUser.id)" class="button">Flag</button>
            <button v-if="user.role === 'admin' && filteredUser.role !== 'admin' && filteredUser.is_flagged" @click="unflagUser(filteredUser.id)" class="button">UnFlag</button>
            <button v-if="user.role === 'admin' && filteredUser.role !== 'admin'" @click="deleteUser(filteredUser.id)" class="button">Delete</button> 
            
            <!-- Sponsor action -->
            <button v-if="user.role === 'sponsor' && filteredUser.role === 'influencer'" @click="openAdRequestForm(filteredUser)" class="button">Send an AdRequest</button>
          </div>
        </li>
      </ul>
    </div>

    <!-- AdRequestForm Overlay -->
    <AdRequestFormSponsor 
      v-if="showAdRequestForm" 
      @close="showAdRequestForm = false" 
      @adRequestSent="handleAdRequestSent"
      :user="selectedUser" 
      :campaigns="campaigns" 
    />
  </div>
</template>

<script>
import api from '@/utils/auth';
import AdRequestFormSponsor from "@/components/icons/AdRequestFormSponsor.vue"; // Ensure this path is correct

export default {
  name: "UserList",
  props: ["users", "campaigns", "title"], // Added sponsorCampaigns as a prop
  data() {
    return {
      user: JSON.parse(localStorage.getItem('user')),
      showAdRequestForm: false, // Control the visibility of the AdRequest form
      selectedUser: null, // Store the selected user object to send ad request
      searchQuery: "", // Added searchQuery in data
    };
  },
  computed: {
    filteredUsers() {
      if (!this.searchQuery.trim()) {
        return this.users;
      }
      const query = this.searchQuery.trim().toLowerCase();
      let reachFilter = parseInt(query, 10);
      if (!isNaN(reachFilter)) {
        return this.users.filter((user) => 
          user.role === 'influencer' && user.reach >= reachFilter
        );
      }
      return this.users.filter((user) => 
        (user.name && user.name.toLowerCase().includes(query)) || 
        (user.username && user.username.toLowerCase().includes(query)) ||
        (user.role && user.role.toLowerCase().includes(query)) || 
        (user.niche && user.niche.toLowerCase().includes(query))
      );
    },
  },
  methods: {
    async flagUser(userId) {
      try {
        await api.put(`/admin/flag_user/user/${userId}`, {});
        alert('User flagged successfully');
        this.$emit('refreshDashboard');
      } catch (error) {
        console.error('Error flagging user:', error);
      }
    },

    // Unflag user by Admin
    async unflagUser(userId) {
      try {
        await api.put(`/admin/unflag_user/user/${userId}`, {});
        alert('User unflagged successfully');
        this.$emit('refreshDashboard');
      } catch (error) {
        console.error('Error unflagging user:', error);
      }
    },

    // Delete user by Admin
    async deleteUser(userId) {
      try {
        await api.delete(`/delete_user/${userId}`);
        alert('User deleted successfully');
        this.$emit('refreshDashboard');
      } catch (error) {
        console.error('Error deleting user:', error);
      }
    },

    handleAdRequestSent() {
      this.$emit('refreshDashboard'); // Emit event to refresh the dashboard
    },

    openAdRequestForm(user) {
      this.selectedUser = user;
      this.showAdRequestForm = true;
    },
  },
  components: {
    AdRequestFormSponsor, // Register the new form component
  },
};
</script>

<style scoped>
@import '@/assets/card.css';
</style>
