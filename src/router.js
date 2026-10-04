import { createRouter, createWebHistory } from 'vue-router'

import HomeView from './views/client/HomeView.vue'
import LoginView from './views/auth/LoginView.vue'
import RegisterView from './views/auth/RegisterView.vue'
import HistoryView from './views/client/HistoryView.vue'
import InfoView from './views/client/InfoView.vue'
import NotFoundView from './views/NotFoundView.vue'
import { hasRole, isAuthenticated } from './services/authSession.js'

const routes = [
  { path: '/', component: HomeView, meta: { requiresAuth: true } },
  { path: '/history', component: HistoryView, meta: { requiresAuth: true } },
  { path: '/info', component: InfoView, meta: { requiresAuth: true } },
  { path: '/login', component: LoginView, meta: { guestOnly: true } },
  { path: '/register', component: RegisterView, meta: { guestOnly: true } },

  // --- ADMIN ROUTES (lazy-loaded) ---
  {
    path: '/admin',
    component: () => import('./views/admin/DashboardView.vue'),
    meta: { requiresAuth: true, roles: ['ADMIN'] }
  },
  {
    path: '/admin/cabinets',
    component: () => import('./views/admin/CabinetsView.vue'),
    meta: { requiresAuth: true, roles: ['ADMIN'] }
  },
  {
    path: '/admin/accounts',
    component: () => import('./views/admin/AccountsView.vue'),
    meta: { requiresAuth: true, roles: ['ADMIN'] }
  },
  {
    path: '/admin/buildings',
    component: () => import('./views/admin/BuildingsView.vue'),
    meta: { requiresAuth: true, roles: ['ADMIN'] }
  },
  {
    path: '/admin/history',
    component: () => import('./views/admin/HistoryView.vue'),
    meta: { requiresAuth: true, roles: ['ADMIN'] }
  },
  {
    path: '/admin/statistics',
    component: () => import('./views/admin/StatisticsView.vue'),
    meta: { requiresAuth: true, roles: ['ADMIN'] }
  },
  { path: '/:pathMatch(.*)*', component: NotFoundView }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// --- ROUTE GUARD ---
router.beforeEach((to) => {
  const authenticated = isAuthenticated()

  if (to.meta.guestOnly && authenticated) {
    return hasRole('ADMIN') ? '/admin' : '/'
  }

  if (to.meta.requiresAuth && !authenticated) {
    return {
      path: '/login',
      query: { redirect: to.fullPath }
    }
  }

  const allowedRoles = Array.isArray(to.meta.roles) ? to.meta.roles : []
  if (allowedRoles.length > 0 && !allowedRoles.some(hasRole)) {
    return '/'
  }

  return true
})

export default router
