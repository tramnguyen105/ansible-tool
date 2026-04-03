import { createRouter, createWebHistory } from 'vue-router'

import ConsoleLayout from '../layouts/ConsoleLayout.vue'
import { useAuthStore } from '../stores/auth'

const LoginView = () => import('../views/auth/LoginView.vue')
const DashboardView = () => import('../views/dashboard/DashboardView.vue')
const InventoryView = () => import('../views/inventory/InventoryView.vue')
const CredentialsView = () => import('../views/credentials/CredentialsView.vue')
const TemplatesView = () => import('../views/templates/TemplatesView.vue')
const PlaybooksView = () => import('../views/playbooks/PlaybooksView.vue')
const ConverterView = () => import('../views/converter/ConverterView.vue')
const JobsView = () => import('../views/jobs/JobsView.vue')
const JobDetailView = () => import('../views/jobs/JobDetailView.vue')
const SchedulesView = () => import('../views/schedules/SchedulesView.vue')
const AuditLogsView = () => import('../views/audit/AuditLogsView.vue')
const UsersView = () => import('../views/users/UsersView.vue')
const SettingsView = () => import('../views/SettingsView.vue')

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: LoginView, meta: { public: true } },
    {
      path: '/',
      component: ConsoleLayout,
      children: [
        { path: '', component: DashboardView },
        { path: 'inventory', component: InventoryView },
        { path: 'credentials', component: CredentialsView },
        { path: 'templates', component: TemplatesView },
        { path: 'playbooks', component: PlaybooksView },
        { path: 'converter', component: ConverterView },
        { path: 'jobs', component: JobsView },
        { path: 'jobs/:id', component: JobDetailView },
        { path: 'schedules', component: SchedulesView },
        { path: 'audit', component: AuditLogsView, meta: { admin: true } },
        { path: 'users', component: UsersView, meta: { admin: true } },
        { path: 'settings', component: SettingsView, meta: { admin: true } },
      ],
    },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  await auth.ensureSession(!to.meta.public)
  if (!to.meta.public && !auth.isAuthenticated) {
    return '/login'
  }
  if (to.path === '/login' && auth.isAuthenticated) {
    return '/'
  }
  if (to.meta.admin && !auth.isAdmin) {
    return '/'
  }
  return true
})

export default router
