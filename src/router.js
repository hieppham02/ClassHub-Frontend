import { createRouter, createWebHistory } from 'vue-router'

import Index from './components/index.vue'
import Login from './components/login.vue'
import Register from './components/register.vue'
import History from './components/history.vue'
import Info from './components/info.vue'
import NotFound from './components/NotFound.vue'
import { hasRole, isAuthenticated } from './services/authSession.js'

const routes = [
  { path: '/', component: Index, meta: { requiresAuth: true } },
  { path: '/history', component: History, meta: { requiresAuth: true } },
  { path: '/info', component: Info, meta: { requiresAuth: true } },
  { path: '/login', component: Login, meta: { guestOnly: true } },
  { path: '/register', component: Register, meta: { guestOnly: true } },

  // --- ADMIN ROUTES (lazy-loaded) ---
  {
    path: '/admin',
    component: () => import('./components/admin/dashboard.vue'),
    meta: { requiresAuth: true, roles: ['ADMIN'] }
  },
  {
    path: '/admin/cabinets',
    component: () => import('./components/admin/cabinets.vue'),
    meta: { requiresAuth: true, roles: ['ADMIN'] }
  },
  {
    path: '/admin/accounts',
    component: () => import('./components/admin/accounts.vue'),
    meta: { requiresAuth: true, roles: ['ADMIN'] }
  },
  {
    path: '/admin/buildings',
    component: () => import('./components/admin/buildings.vue'),
    meta: { requiresAuth: true, roles: ['ADMIN'] }
  },
  {
    path: '/admin/history',
    component: () => import('./components/admin/history-admin.vue'),
    meta: { requiresAuth: true, roles: ['ADMIN'] }
  },
  {
    path: '/admin/statistics',
    component: () => import('./components/admin/statistics.vue'),
    meta: { requiresAuth: true, roles: ['ADMIN'] }
  },
  { path: '/:pathMatch(.*)*', component: NotFound }
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
