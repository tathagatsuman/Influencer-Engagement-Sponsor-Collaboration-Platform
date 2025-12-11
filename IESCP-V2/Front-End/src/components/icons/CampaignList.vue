<template>
  <div :class="cardClass">
    <h3>{{ title }}</h3>

    <!-- Search bar for Admins and Influencers -->
    <div v-if="user.role === 'admin' || user.role === 'influencer'" class="search-bar">
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Search by name, niche, budget or (start-date or end-date  in YYYY-MM-DD)"
        class="search-input"
      />
    </div>

    <!-- Button to create a new campaign for sponsors -->
    <button v-if="user.role === 'sponsor' && user.isApproved" @click="showCreateCampaignForm" class="button btn">Create New Campaign</button>

    <div class="scrollable">
      <ul class="Camp">
        <li v-for="campaign in filteredCampaigns" :key="campaign.id">
          <div>
            <h4>{{ campaign.name }}</h4>
            <p>Description: {{ campaign.description }}</p>
            <p v-if="user.role !== 'sponsor'">Sponsor Name: {{ campaign.sponsor_name }}</p>
            <p v-if="user.role !== 'sponsor'">Sponsor UserName: {{ campaign.sponsor_username }}</p>
            <p>Start Date: {{ campaign.start_date }}</p>
            <p>End Date: {{ campaign.end_date }}</p>
            <p>Budget: {{ campaign.budget }}</p>
            <p>Visibility: {{ campaign.visibility }}</p>
            <p>Goals: {{ campaign.goals }}</p>

            <!-- Admin actions -->
            <button v-if="user.role === 'admin' && !campaign.is_flagged" @click="flagCampaign(campaign.id)" class="button">Flag</button>
            <button v-if="user.role === 'admin' && campaign.is_flagged" @click="unflagCampaign(campaign.id)" class="button">UnFlag</button>
            <button v-if="user.role === 'admin'" @click="deleteCampaign(campaign.id)" class="button">Delete</button>

            <!-- Sponsor actions -->
            <button v-if="user.role === 'sponsor'" @click="showEditCampaignForm(campaign)" class="button campaign-btn">Edit Campaign</button>
            <button v-if="user.role === 'sponsor'" @click="deleteCampaign(campaign.id)" class="button">Delete</button>

            <!-- Influencer actions -->
            <button v-if="user.role === 'influencer'" @click="openAdRequestForm(campaign)" class="button campaign-btn">Send an AdRequest</button>
          </div>
        </li>
      </ul>
    </div>

    <!-- CampaignForm Overlay for creating/editing campaigns -->
    <CampaignForm
      v-if="showForm"
      :existingCampaign="selectedCampaign"
      @close="closeForm"
      @campaignUpdated="refreshCampaignList"
      :isSponsor="user.role === 'sponsor'"
    />

    <!-- AdRequestForm Overlay for influencers to send ad requests -->
    <!-- CampaignList.vue -->
<AdRequestFormInfluencer v-if="showAdRequestForm" @close="closeAdRequestForm" @adRequestSent="onAdRequestSent" :campaign="selectedCampaign" :request="null" />

  </div>
</template>

<script>
import api from '@/utils/auth';
import CampaignForm from '@/components/icons/CampaignForm.vue';
import AdRequestFormInfluencer from '@/components/icons/AdRequestFormInfluencer.vue';

export default {
  name: "CampaignList",
  props: ["campaigns", "title"],
  data() {
    return {
      user: JSON.parse(localStorage.getItem('user')),
      showForm: false, // Controls the visibility of the CampaignForm
      showAdRequestForm: false, // Controls the visibility of the AdRequestForm
      selectedCampaign: null, // Selected campaign for editing or ad request
      searchQuery: "", // Binding for search input
    };
  },
  computed: {
    filteredCampaigns() {
      if (!this.searchQuery.trim()) {
        return this.campaigns;
      }

      const query = this.searchQuery.trim().toLowerCase();
      let budgetFilter = parseFloat(this.searchQuery);
      if (!isNaN(budgetFilter)) {
        return this.campaigns.filter((campaign) => campaign.budget >= budgetFilter);
      }

      const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
      if (dateRegex.test(query)) {
        return this.campaigns.filter((campaign) => {
          const startDate = new Date(campaign.start_date).getTime();
          const endDate = new Date(campaign.end_date).getTime();
          const searchDate = new Date(query).getTime();

          // Check if search date is within the campaign's start and end dates
          return searchDate >= startDate && searchDate <= endDate;
        });
      }

      return this.campaigns.filter((campaign) =>
        campaign.name.toLowerCase().includes(query) ||
        campaign.niche.toLowerCase().includes(query) ||
        campaign.start_date.toLowerCase().includes(query) ||
        campaign.end_date.toLowerCase().includes(query)
      );
    },
    cardClass() {
      return this.user.role === 'influencer' ? 'card' : 'card cardWidth';
    }
  },
  methods: {
  async flagCampaign(campaignId) {
    try {
      await api.put(`/admin/flag_campaign/campaign/${campaignId}`, {});
      alert('Campaign flagged successfully');
      this.$emit('refreshDashboard');
    } catch (error) {
      console.error('Error flagging campaign:', error);
    }
  },
  async unflagCampaign(campaignId) {
    try {
      await api.put(`/admin/unflag_campaign/campaign/${campaignId}`, {});
      alert('Campaign unflagged successfully');
      this.$emit('refreshDashboard');
    } catch (error) {
      console.error('Error unflagging campaign:', error);
    }
  },
  async deleteCampaign(campaignId) {
    try {
      await api.delete(`/delete_campaign/${campaignId}`);
      alert('Campaign deleted successfully');
      this.$emit('refreshDashboard');
    } catch (error) {
      console.error('Error deleting campaign:', error);
    }
  },
    showCreateCampaignForm() {
      this.selectedCampaign = null; // Clear selected campaign for new creation
      this.showForm = true;
    },
    showEditCampaignForm(campaign) {
      this.selectedCampaign = campaign; // Set selected campaign for editing
      this.showForm = true;
    },
    closeForm() {
      this.showForm = false;
      this.selectedCampaign = null; // Reset selected campaign when form is closed
    },
    refreshCampaignList() {
    this.$emit('refreshDashboard'); // Emit refreshDashboard to parent
    this.closeForm(); // Close the form after updating or creating a campaign
    },
    openAdRequestForm(campaign) {
      this.selectedCampaign = campaign;
      this.showAdRequestForm = true; // Open ad request form for the selected campaign
    },
    closeAdRequestForm() {
      this.showAdRequestForm = false;
      this.selectedCampaign = null; // Reset selected campaign when ad request form is closed
    },
    onAdRequestSent() {
      this.$emit('refreshDashboard'); // Emit event to parent to refresh the dashboard
      this.closeAdRequestForm();
    }
  },
  components: {
    CampaignForm,
    AdRequestFormInfluencer, // Register the AdRequestForm component
  },
};
</script>

<style scoped>
@import '@/assets/card.css';
</style>
