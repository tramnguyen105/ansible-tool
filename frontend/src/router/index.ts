import { createRouter, createWebHistory } from 'vue-router'

import ConsoleLayout from '../layouts/ConsoleLayout.vue'
import { useAuthStore } from '../stores/auth'
import AuditLogsView from '../views/audit/AuditLogsView.vue'
import LoginView from '../views/auth/LoginView.vue'
import ConverterView from '../views/converter/ConverterView.vue'
import CredentialsView from '../views/credentials/CredentialsView.vue'
import DashboardView from '../views/dashboard/DashboardView.vue'
import InventoryView from '../views/inventory/InventoryView.vue'
import JobDetailView from '../views/jobs/JobDetailView.vue'
import JobsView from '../views/jobs/JobsView.vue'
import PlaybooksView from '../views/playbooks/PlaybooksView.vue'
import SchedulesView from '../views/schedules/SchedulesView.vue'
import SettingsView from '../views/SettingsView.vue'
import TemplatesView from '../views/templates/TemplatesView.vue'

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
        { path: 'audit', component: AuditLogsView },
        { path: 'settings', component: SettingsView },
      ],
    },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  await auth.ensureSession()
  if (!to.meta.public && !auth.isAuthenticated) {
    return '/login'
  }
  if (to.path === '/login' && auth.isAuthenticated) {
    return '/'
  }
  return true
})

export default router
