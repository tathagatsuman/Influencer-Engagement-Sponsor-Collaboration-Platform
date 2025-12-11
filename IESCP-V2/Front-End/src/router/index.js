import { createRouter, createWebHistory } from 'vue-router'
import HomePage from '@/components/HomePage.vue';
import LoginPage from '@/components/LoginPage.vue';
import RegisterPage from '@/components/RegisterPage.vue';
import AdminDashboardPage from '@/components/AdminDashboardPage.vue';
import SponsorDashboardPage from '@/components/SponsorDashboardPage.vue';
import InfluencerDashboardPage from '@/components/InfluencerDashboardPage.vue';
import NotFound from '@/components/NotFound.vue';

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL || '/'),
  routes: [
    { path: '/', component: HomePage, name: 'home' },
    { path: '/login', component: LoginPage, name: 'login' },
    { path: '/register', component: RegisterPage, name: 'register' },
    { path: '/admin/dashboard/:name', component: AdminDashboardPage, name:'adminDashboard', meta: { requiresAuth: true, role: 'admin' }, },
    { path: '/sponsor/:name', component: SponsorDashboardPage, name: 'sponsorDashboard', meta: { requiresAuth: true, role: 'sponsor' } },
    { path: '/influencer/:name', component: InfluencerDashboardPage, name: 'influencerDashboard', meta: { requiresAuth: true, role: 'influencer' } },
    { path: '/:pathMatch(.*)*', component: NotFound, name: 'NotFound' }
  ]
});

router.beforeEach((to, from, next) => {
  const user = JSON.parse(localStorage.getItem('user')) || {};
  const isLoggedIn = !!localStorage.getItem('access_token');
  const userRole = user.role;

  if (to.matched.some(record => record.meta.requiresAuth)) {
    if (!isLoggedIn) {
      return next({ name: 'Login' });
    }

    if (to.meta.role && to.meta.role !== userRole) {
      return next({ name: `${userRole}Dashboard`, params: { name: user.name } });
    }
  }

  next();
});

export default router
