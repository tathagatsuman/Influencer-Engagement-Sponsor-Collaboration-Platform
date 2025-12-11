<template>
  <nav>
    <!-- Hamburger Icon for Mobile -->
    <div class="hamburger" @click="toggleMenu">
      <span :class="{ 'hamburger-open': isMenuOpen }"></span>
      <span :class="{ 'hamburger-open': isMenuOpen }"></span>
      <span :class="{ 'hamburger-open': isMenuOpen }"></span>
    </div>

    <!-- Navigation Links -->
    <div :class="['nav-links', { 'show-menu': isMenuOpen }]">
      <div class="nav-left">
        <span @click="openModal" class="nav-link">Profile</span>
        <ProfileForm :isVisible="isProfileVisible" @close="isProfileVisible = false" />
        <router-link v-if="user.role === 'admin'" :to="{ name: 'adminDashboard', params: { name: user.name } }" class="nav-link" @click="closeMenu">Dashboard</router-link>
        <router-link v-if="user.role === 'influencer'" :to="{ name: 'influencerDashboard', params: { name: user.name } }" class="nav-link" @click="closeMenu">Dashboard</router-link>
        <router-link v-if="user.role === 'sponsor'" :to="{ name: 'sponsorDashboard', params: { name: user.name } }" class="nav-link" @click="closeMenu">Dashboard</router-link>
        <span v-if="user.role === 'sponsor'" @click="exportCSV" class="nav-link">Export as CSV</span>
      </div>
      <div class="nav-right">
        <span @click="logoutHandler" class="nav-link">Log Out</span>
      </div>
    </div>
  </nav>
</template>

<script>
import ProfileForm from "@/components/icons/ProfileForm.vue";
import { logout } from "@/utils/logout";
import api from "@/utils/auth";

export default {
  name: "NavBar",
  components: { ProfileForm },
  data() {
    return {
      user: JSON.parse(localStorage.getItem("user")),
      isProfileVisible: false, // Controls visibility of the Profile modal
      isMenuOpen: false, // Controls visibility of the hamburger menu
    };
  },
  methods: {
    openModal() {
      this.isProfileVisible = true; // Show the modal
    },
    closeModal() {
      this.isProfileVisible = false; // Hide the modal
    },
    async logoutHandler() {
      try {
        await logout(); // Call the logout function
      } catch (error) {
        console.error("Error during logout:", error);
      }
    },
    async exportCSV() {
      try {
        const response = await api.get("/sponsor/export_csv_report");
        alert(response.data.message); // Notify the user of success
      } catch (error) {
        console.error("Error exporting CSV:", error);
        alert(
          "Failed to export CSV: " + (error.response.data.error || error.message)
        );
      }
    },
    toggleMenu() {
      this.isMenuOpen = !this.isMenuOpen; // Toggle hamburger menu visibility
    },
    closeMenu() {
      this.isMenuOpen = false; // Close the hamburger menu when an option is clicked
    },
  },
};
</script>

<style scoped>
@import "@/assets/navBar.css";
</style>
