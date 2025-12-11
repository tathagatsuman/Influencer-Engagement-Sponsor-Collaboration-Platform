<template>
  <div class="modal-overlay">
    <div class="container">
      <div class="card">
        <span class="close-button" @click="$emit('close')">&times;</span>
        <h2>{{ isEditing ? 'Edit Campaign' : 'Create Campaign' }}</h2>
        <form @submit.prevent="isEditing ? editCampaign() : createCampaign()">
          <div class="scrollable">
            <label for="name">Campaign Name</label>
            <input type="text" id="name" v-model="form.name" required />
            <span v-if="errors.name" class="error-message">{{ errors.name }}</span>

            <label for="description">Description</label>
            <textarea id="description" v-model="form.description" required></textarea>
            <span v-if="errors.description" class="error-message">{{ errors.description }}</span>

            <label for="start_date">Start Date</label>
            <input type="date" id="start_date" v-model="form.start_date" required />
            <span v-if="errors.start_date" class="error-message">{{ errors.start_date }}</span>

            <label for="end_date">End Date</label>
            <input type="date" id="end_date" v-model="form.end_date" required />
            <span v-if="errors.end_date" class="error-message">{{ errors.end_date }}</span>

            <label for="budget">Budget</label>
            <input type="number" id="budget" v-model="form.budget" required />
            <span v-if="errors.budget" class="error-message">{{ errors.budget }}</span>

            <label for="niche">Niche</label>
            <select id="niche" v-model="form.niche" required>
              <option disabled value="">Niche/Category</option>
              <option value="automobiles">Automobiles</option>
              <option value="beverages">Beverages</option>
              <option value="education">Education</option>
              <option value="fashion">Fashion</option>
              <option value="food">Food</option>
              <option value="real estates">Real Estates</option>
              <option value="sports">Sports</option>
              <option value="technology">Technology</option>
            </select>
            <span v-if="errors.niche" class="error-message">{{ errors.niche }}</span>

            <label for="visibility">Visibility</label>
            <select id="visibility" v-model="form.visibility" required>
              <option disabled value="">Visibility</option>
              <option value="public">Public</option>
              <option value="private">Private</option>
            </select>
            <span v-if="errors.visibility" class="error-message">{{ errors.visibility }}</span>

            <label for="goals">Goals</label>
            <textarea id="goals" v-model="form.goals" required></textarea>
            <span v-if="errors.goals" class="error-message">{{ errors.goals }}</span>
          </div>
          <button type="submit" class="button">{{ isEditing ? 'Update Campaign' : 'Create Campaign' }}</button>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/utils/auth';

export default {
  name: "CampaignForm",
  props: {
    existingCampaign: {
      type: Object,
      default: null,
    },
    isSponsor: {
      type: Boolean,
      required: true,
    },
  },
  data() {
    return {
      isEditing: false,
      form: {
        name: '',
        description: '',
        start_date: '',
        end_date: '',
        budget: '',
        niche: '',
        visibility: '',
        goals: ''
      },
      errors: {}
    };
  },
  created() {
    if (this.existingCampaign) {
      this.isEditing = true;
      this.form = { ...this.existingCampaign };
    }
  },
  methods: {
    validateForm() {
      this.errors = {};

      if (!this.form.name) {
        this.errors.name = 'Campaign name is required.';
      } else if (this.form.name.length < 3) {
        this.errors.name = 'Campaign name must be at least 3 characters.';
      }

      if (!this.form.description) {
        this.errors.description = 'Description is required.';
      } else if (this.form.description.length < 10) {
        this.errors.description = 'Description must be at least 10 characters.';
      }

      if (!this.form.start_date) {
        this.errors.start_date = 'Start date is required.';
      }

      if (!this.form.end_date) {
        this.errors.end_date = 'End date is required.';
      } else if (this.form.end_date < this.form.start_date) {
        this.errors.end_date = 'End date cannot be earlier than start date.';
      }

      if (!this.form.budget) {
        this.errors.budget = 'Budget is required.';
      } else if (this.form.budget <= 0) {
        this.errors.budget = 'Budget must be a positive number.';
      }

      if (!this.form.niche) {
        this.errors.niche = 'Please select a niche.';
      }

      if (!this.form.visibility) {
        this.errors.visibility = 'Please select visibility.';
      }

      if (!this.form.goals) {
        this.errors.goals = 'Goals are required.';
      } else if (this.form.goals.length < 10) {
        this.errors.goals = 'Goals must be at least 10 characters.';
      }

      return Object.keys(this.errors).length === 0;
    },
    async createCampaign() {
      if (!this.validateForm()) return;

      try {
        await api.post('/create_campaign', this.form);
        alert('Campaign created successfully');
        this.$emit('campaignUpdated');
        this.$emit('close');
      } catch (error) {
        console.error('Error creating campaign:', error);
      }
    },
    async editCampaign() {
      if (!this.validateForm()) return;

      try {
        await api.put(`/edit_campaign/${this.form.id}`, this.form);
        alert('Campaign updated successfully');
        this.$emit('campaignUpdated');
        this.$emit('close');
      } catch (error) {
        console.error('Error updating campaign:', error);
      }
    }
  }
};
</script>

<style scoped>
@import '@/assets/overlay.css';

.error-message {
  color: red;
  font-size: 0.9em;
}
</style>
