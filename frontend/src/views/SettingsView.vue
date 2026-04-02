<template>
  <div>
    <PageHeader
      title="Settings"
      eyebrow="Configuration"
      description="Manage personal preferences and platform-wide controls for LDAP, password reset, and SNMP."
    >
      <button class="btn-secondary" :disabled="isLoading" @click="copyDiagnostics">{{ isLoading ? 'Loading...' : 'Copy diagnostics' }}</button>
      <button class="btn-secondary" :disabled="isLoading" @click="exportDiagnostics">Export JSON</button>
      <button class="btn-primary" :disabled="isLoading" @click="load">{{ isLoading ? 'Refreshing...' : 'Refresh' }}</button>
    </PageHeader>

    <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <CardStat label="Application" :value="settings.runtime?.app_name || settings.app_name || 'n/a'" tone="identity" helper="Runtime application identifier." />
      <CardStat label="Environment" :value="settings.runtime?.environment || settings.environment || 'n/a'" tone="runtime" helper="Treat production as change-controlled." />
      <CardStat label="Risk level" :value="(settings.risk_level || 'unknown').toUpperCase()" :tone="riskTone" helper="Computed from runtime warnings and health checks." />
      <CardStat label="Warnings" :value="warningCount" tone="failed" :helper="warningCount ? 'Address high-severity warnings first.' : 'No warnings reported.'" />
    </div>

    <div class="mt-6 space-y-3">
      <BannerNotice
        v-if="settings.risk_level === 'high'"
        title="High Risk"
        tone="error"
        text="Configuration risks detected. Review warnings and avoid production job runs until remediated."
      />
      <BannerNotice
        v-else-if="settings.risk_level === 'medium'"
        title="Medium Risk"
        tone="warn"
        text="Non-blocking risks detected. Review warnings before high-impact automation."
      />
      <BannerNotice
        v-else
        title="Low Risk"
        tone="info"
        text="No critical posture warnings detected from current runtime checks."
      />
    </div>

    <div class="mt-6 grid gap-6 xl:grid-cols-2">
      <section class="rounded-2xl border border-console-edge bg-console-panel/70 p-5">
        <div class="flex items-start justify-between gap-4">
          <div>
            <p class="text-xs uppercase tracking-[0.2em] text-console-muted">User Preferences</p>
            <h3 class="mt-2 text-lg font-semibold text-slate-900">Personal defaults</h3>
          </div>
          <button class="btn-primary" :disabled="isSavingUser" @click="saveUserPreferences">{{ isSavingUser ? 'Saving...' : 'Save preferences' }}</button>
        </div>

        <div class="mt-4 grid gap-4 sm:grid-cols-2">
          <label>
            <span class="field-label">Timezone</span>
            <input v-model.trim="userForm.timezone" type="text" placeholder="UTC" :disabled="isSavingUser" />
          </label>
          <label>
            <span class="field-label">Date format</span>
            <select v-model="userForm.date_format" :disabled="isSavingUser">
              <option value="YYYY-MM-DD">YYYY-MM-DD</option>
              <option value="DD/MM/YYYY">DD/MM/YYYY</option>
              <option value="MM/DD/YYYY">MM/DD/YYYY</option>
            </select>
          </label>
          <label>
            <span class="field-label">Time format</span>
            <select v-model="userForm.time_format" :disabled="isSavingUser">
              <option value="24h">24-hour</option>
              <option value="12h">12-hour</option>
            </select>
          </label>
          <label>
            <span class="field-label">Auto-refresh (seconds)</span>
            <input v-model.number="userForm.auto_refresh_seconds" type="number" min="5" max="3600" :disabled="isSavingUser" />
          </label>
          <label class="setting-row sm:col-span-2" :class="{ 'is-disabled': isSavingUser }">
            <div class="setting-copy">
              <p class="setting-title">Relative time labels</p>
              <p class="setting-help">Show timestamps as relative values in list views.</p>
            </div>
            <span class="switch">
              <input v-model="userForm.show_relative_time" type="checkbox" :disabled="isSavingUser" />
              <span class="switch-track"></span>
            </span>
          </label>
        </div>
      </section>

      <section class="rounded-2xl border border-console-edge bg-console-panel/70 p-5">
        <div class="flex items-start justify-between gap-4">
          <div>
            <p class="text-xs uppercase tracking-[0.2em] text-console-muted">System-wide Settings</p>
            <h3 class="mt-2 text-lg font-semibold text-slate-900">LDAP, password reset, SNMP</h3>
          </div>
          <button class="btn-primary" :disabled="isSavingSystem" @click="saveSystemWide">{{ isSavingSystem ? 'Saving...' : 'Save system settings' }}</button>
        </div>

        <div class="mt-4 space-y-5">
          <div class="rounded-xl border border-console-edge/80 p-4">
            <p class="text-sm font-semibold text-slate-900">LDAP configuration</p>
            <div class="mt-3 grid gap-3 sm:grid-cols-2">
              <label class="setting-row sm:col-span-2" :class="{ 'is-disabled': isSavingSystem }">
                <div class="setting-copy">
                  <p class="setting-title">LDAP enabled</p>
                  <p class="setting-help">Use directory authentication for sign-in.</p>
                </div>
                <span class="switch">
                  <input v-model="systemForm.ldap.enabled" type="checkbox" :disabled="isSavingSystem" />
                  <span class="switch-track"></span>
                </span>
              </label>
              <label>
                <span class="field-label">LDAP server URI</span>
                <input v-model.trim="systemForm.ldap.server_uri" type="text" placeholder="ldap://ldap.example.internal" :disabled="isSavingSystem" />
              </label>
              <label>
                <span class="field-label">Bind DN</span>
                <input v-model.trim="systemForm.ldap.bind_dn" type="text" placeholder="cn=svc,dc=example,dc=internal" :disabled="isSavingSystem" />
              </label>
              <label>
                <span class="field-label">Search base</span>
                <input v-model.trim="systemForm.ldap.search_base" type="text" placeholder="dc=example,dc=internal" :disabled="isSavingSystem" />
              </label>
              <label>
                <span class="field-label">Username attribute</span>
                <input v-model.trim="systemForm.ldap.username_attribute" type="text" placeholder="sAMAccountName" :disabled="isSavingSystem" />
              </label>
              <label class="sm:col-span-2">
                <span class="field-label">Search filter</span>
                <input v-model.trim="systemForm.ldap.search_filter" type="text" placeholder="(sAMAccountName={username})" :disabled="isSavingSystem" />
              </label>
              <label>
                <span class="field-label">User DN template</span>
                <input v-model.trim="systemForm.ldap.user_dn_template" type="text" placeholder="uid={username},ou=people,dc=example,dc=internal" :disabled="isSavingSystem" />
              </label>
              <div class="space-y-2 rounded-xl border border-console-edge px-3 py-2">
                <label class="setting-row" :class="{ 'is-disabled': isSavingSystem }">
                  <div class="setting-copy">
                    <p class="setting-title">Use SSL</p>
                    <p class="setting-help">Encrypt LDAP transport with TLS/SSL.</p>
                  </div>
                  <span class="switch">
                    <input v-model="systemForm.ldap.use_ssl" type="checkbox" :disabled="isSavingSystem" />
                    <span class="switch-track"></span>
                  </span>
                </label>
                <label class="setting-row" :class="{ 'is-disabled': isSavingSystem }">
                  <div class="setting-copy">
                    <p class="setting-title">Allow local fallback auth</p>
                    <p class="setting-help">Permit local accounts when LDAP is unavailable.</p>
                  </div>
                  <span class="switch">
                    <input v-model="systemForm.ldap.allow_local_auth" type="checkbox" :disabled="isSavingSystem" />
                    <span class="switch-track"></span>
                  </span>
                </label>
              </div>
            </div>
          </div>

          <div class="rounded-xl border border-console-edge/80 p-4">
            <div class="flex items-start justify-between gap-4">
              <div>
                <p class="text-sm font-semibold text-slate-900">Password reset</p>
                <p class="mt-1 text-xs text-console-muted">Reset password for current local account.</p>
              </div>
              <button class="btn-secondary" :disabled="isSavingPassword" @click="savePasswordReset">{{ isSavingPassword ? 'Updating...' : 'Update password' }}</button>
            </div>
            <div class="mt-3 grid gap-3 sm:grid-cols-2">
              <label class="sm:col-span-2">
                <span class="field-label">Current password</span>
                <input v-model="passwordForm.current_password" type="password" autocomplete="current-password" :disabled="isSavingPassword" />
              </label>
              <label>
                <span class="field-label">New password</span>
                <input v-model="passwordForm.new_password" type="password" autocomplete="new-password" :disabled="isSavingPassword" />
              </label>
              <label>
                <span class="field-label">Confirm new password</span>
                <input v-model="passwordForm.confirm_password" type="password" autocomplete="new-password" :disabled="isSavingPassword" />
              </label>
            </div>
          </div>

          <div class="rounded-xl border border-console-edge/80 p-4">
            <p class="text-sm font-semibold text-slate-900">SNMP settings</p>
            <div class="mt-3 grid gap-3 sm:grid-cols-2">
              <label class="setting-row sm:col-span-2" :class="{ 'is-disabled': isSavingSystem }">
                <div class="setting-copy">
                  <p class="setting-title">SNMP enabled</p>
                  <p class="setting-help">Enable SNMP defaults for inventory integrations.</p>
                </div>
                <span class="switch">
                  <input v-model="systemForm.snmp.enabled" type="checkbox" :disabled="isSavingSystem" />
                  <span class="switch-track"></span>
                </span>
              </label>
              <label>
                <span class="field-label">Version</span>
                <select v-model="systemForm.snmp.version" :disabled="isSavingSystem">
                  <option value="v1">v1</option>
                  <option value="v2c">v2c</option>
                  <option value="v3">v3</option>
                </select>
              </label>
              <label>
                <span class="field-label">Default port</span>
                <input v-model.number="systemForm.snmp.default_port" type="number" min="1" max="65535" :disabled="isSavingSystem" />
              </label>
              <label>
                <span class="field-label">Timeout (seconds)</span>
                <input v-model.number="systemForm.snmp.timeout_seconds" type="number" min="1" max="30" :disabled="isSavingSystem" />
              </label>
              <label>
                <span class="field-label">Retries</span>
                <input v-model.number="systemForm.snmp.retries" type="number" min="0" max="10" :disabled="isSavingSystem" />
              </label>
              <label class="sm:col-span-2">
                <span class="field-label">Trap target</span>
                <input v-model.trim="systemForm.snmp.trap_target" type="text" placeholder="snmp-traps.example.internal" :disabled="isSavingSystem" />
              </label>
            </div>
          </div>
        </div>
      </section>
    </div>

    <div class="mt-6 grid gap-6 xl:grid-cols-2">
      <section class="rounded-2xl border border-console-edge bg-console-panel/70 p-5">
        <p class="text-xs uppercase tracking-[0.2em] text-console-muted">Runtime integrations</p>
        <div class="mt-4 space-y-2 text-sm">
          <p><strong>Database:</strong> {{ settings.integrations?.database_driver || 'n/a' }} @ {{ settings.integrations?.database_host || 'n/a' }}</p>
          <p><strong>Redis:</strong> {{ settings.integrations?.redis_host || 'n/a' }} (db {{ settings.integrations?.redis_db ?? 'n/a' }})</p>
          <p><strong>Runner data dir:</strong> {{ settings.execution?.runner_data_dir || 'n/a' }}</p>
          <p><strong>Artifact retention:</strong> {{ settings.execution?.artifact_retention_days ?? 'n/a' }} days</p>
        </div>
      </section>

      <section class="rounded-2xl border border-console-edge bg-console-panel/70 p-5">
        <p class="text-xs uppercase tracking-[0.2em] text-console-muted">Dependency health</p>
        <div class="mt-4 grid gap-3 sm:grid-cols-2">
          <HealthChip label="Database" :ok="settings.health?.db_ready" :detail="settings.health?.db_detail" />
          <HealthChip label="Redis" :ok="settings.health?.redis_ready" :detail="settings.health?.redis_detail" />
          <HealthChip label="Runner path" :ok="settings.health?.runner_path_writable" :detail="settings.health?.runner_detail" />
          <HealthChip label="Celery worker" :ok="settings.health?.celery_worker_online" :detail="settings.health?.celery_detail" />
        </div>
      </section>
    </div>

    <section class="mt-6 rounded-3xl border border-console-edge bg-console-panel/80 p-5 shadow-xl shadow-slate-300/25">
      <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <p class="text-xs uppercase tracking-[0.22em] text-console-glow">Runtime posture</p>
          <h3 class="mt-2 text-xl font-semibold text-slate-900">Warnings and recommendations</h3>
        </div>
        <p class="text-sm text-console-muted">Generated at: {{ generatedAtLabel }}</p>
      </div>
      <div class="mt-4 space-y-3">
        <div v-if="!warningCount" class="rounded-2xl border border-emerald-500/30 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
          No warnings returned by runtime posture checks.
        </div>
        <div
          v-for="warning in settings.warnings || []"
          :key="warning.code"
          class="rounded-2xl border px-4 py-3 text-sm"
          :class="warning.severity === 'high' ? 'border-rose-500/40 bg-rose-50 text-rose-700' : 'border-amber-500/40 bg-amber-50 text-amber-700'"
        >
          <p class="font-semibold uppercase tracking-[0.14em]">{{ warning.code }}</p>
          <p class="mt-1">{{ warning.message }}</p>
          <p class="mt-2 text-console-ink">Recommendation: {{ warning.recommendation }}</p>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, watchEffect } from 'vue'

import api from '../api/client'
import BannerNotice from '../components/common/BannerNotice.vue'
import CardStat from '../components/common/CardStat.vue'
import PageHeader from '../components/common/PageHeader.vue'
import { useAppStore } from '../stores/app'
import { formatDateTime } from '../utils/format'

const HealthChip = {
  props: {
    label: { type: String, required: true },
    ok: { type: Boolean, required: false, default: false },
    detail: { type: String, required: false, default: '' },
  },
  template: `
    <div class="rounded-xl border px-3 py-3 text-sm" :class="ok ? 'border-emerald-500/30 bg-emerald-50 text-emerald-700' : 'border-rose-500/30 bg-rose-50 text-rose-700'">
      <p class="font-semibold">{{ label }}: {{ ok ? 'OK' : 'Issue' }}</p>
      <p class="mt-1 text-xs">{{ detail || (ok ? 'Healthy' : 'No detail') }}</p>
    </div>
  `,
}

const app = useAppStore()
const settings = reactive<any>({})
const isSavingUser = computed(() => settings.__savingUser === true)
const isSavingSystem = computed(() => settings.__savingSystem === true)
const isSavingPassword = computed(() => settings.__savingPassword === true)
const isLoading = computed(() => settings.__loading === true)
const warningCount = computed(() => (settings.warnings || []).length)
const riskTone = computed(() => {
  if (settings.risk_level === 'high') return 'failed'
  if (settings.risk_level === 'medium') return 'runtime'
  return 'success'
})
const generatedAtLabel = computed(() => (settings.generated_at ? formatDateTime(settings.generated_at) : 'n/a'))
const diagnosticsJson = computed(() => JSON.stringify(settings, null, 2))

const userForm = reactive({
  timezone: 'UTC',
  date_format: 'YYYY-MM-DD',
  time_format: '24h',
  auto_refresh_seconds: 30,
  show_relative_time: true,
})

const systemForm = reactive({
  ldap: {
    enabled: true,
    server_uri: 'ldap://ldap.example.internal',
    use_ssl: false,
    bind_dn: '',
    search_base: '',
    search_filter: '(sAMAccountName={username})',
    username_attribute: 'sAMAccountName',
    user_dn_template: '',
    allow_local_auth: true,
  },
  snmp: {
    enabled: false,
    version: 'v2c',
    default_port: 161,
    timeout_seconds: 3,
    retries: 2,
    trap_target: '',
  },
})
const passwordForm = reactive({
  current_password: '',
  new_password: '',
  confirm_password: '',
})

watchEffect(() => {
  if (settings.__loading == null) settings.__loading = false
  if (settings.__savingUser == null) settings.__savingUser = false
  if (settings.__savingSystem == null) settings.__savingSystem = false
  if (settings.__savingPassword == null) settings.__savingPassword = false
})

function hydrateForms() {
  const user = settings.user_preferences || {}
  userForm.timezone = user.timezone || 'UTC'
  userForm.date_format = user.date_format || 'YYYY-MM-DD'
  userForm.time_format = user.time_format || '24h'
  userForm.auto_refresh_seconds = Number(user.auto_refresh_seconds || 30)
  userForm.show_relative_time = user.show_relative_time !== false

  const ldap = settings.system_wide?.ldap || {}
  systemForm.ldap.enabled = ldap.enabled !== false
  systemForm.ldap.server_uri = ldap.server_uri || 'ldap://ldap.example.internal'
  systemForm.ldap.use_ssl = !!ldap.use_ssl
  systemForm.ldap.bind_dn = ldap.bind_dn || ''
  systemForm.ldap.search_base = ldap.search_base || ''
  systemForm.ldap.search_filter = ldap.search_filter || '(sAMAccountName={username})'
  systemForm.ldap.username_attribute = ldap.username_attribute || 'sAMAccountName'
  systemForm.ldap.user_dn_template = ldap.user_dn_template || ''
  systemForm.ldap.allow_local_auth = ldap.allow_local_auth !== false

  const snmp = settings.system_wide?.snmp || {}
  systemForm.snmp.enabled = !!snmp.enabled
  systemForm.snmp.version = snmp.version || 'v2c'
  systemForm.snmp.default_port = Number(snmp.default_port || 161)
  systemForm.snmp.timeout_seconds = Number(snmp.timeout_seconds || 3)
  systemForm.snmp.retries = Number(snmp.retries || 2)
  systemForm.snmp.trap_target = snmp.trap_target || ''
}

async function load() {
  settings.__loading = true
  try {
    const response = await api.get('/system/settings')
    Object.assign(settings, response.data.data)
    hydrateForms()
  } catch {
    app.pushToast('System settings could not be loaded', 'error')
  } finally {
    settings.__loading = false
  }
}

async function saveUserPreferences() {
  settings.__savingUser = true
  try {
    const payload = {
      timezone: userForm.timezone.trim(),
      date_format: userForm.date_format,
      time_format: userForm.time_format,
      auto_refresh_seconds: Number(userForm.auto_refresh_seconds),
      show_relative_time: !!userForm.show_relative_time,
    }
    const response = await api.put('/system/settings/user-preferences', payload)
    settings.user_preferences = response.data.data
    app.pushToast('User preferences saved', 'success')
  } catch (error: any) {
    app.pushToast(error?.response?.data?.message || 'Unable to save user preferences', 'error')
  } finally {
    settings.__savingUser = false
  }
}

async function saveSystemWide() {
  settings.__savingSystem = true
  try {
    const payload = {
      ldap: {
        enabled: !!systemForm.ldap.enabled,
        server_uri: systemForm.ldap.server_uri.trim(),
        use_ssl: !!systemForm.ldap.use_ssl,
        bind_dn: systemForm.ldap.bind_dn.trim() || null,
        search_base: systemForm.ldap.search_base.trim() || null,
        search_filter: systemForm.ldap.search_filter.trim(),
        username_attribute: systemForm.ldap.username_attribute.trim(),
        user_dn_template: systemForm.ldap.user_dn_template.trim() || null,
        allow_local_auth: !!systemForm.ldap.allow_local_auth,
      },
      snmp: {
        enabled: !!systemForm.snmp.enabled,
        version: systemForm.snmp.version,
        default_port: Number(systemForm.snmp.default_port),
        timeout_seconds: Number(systemForm.snmp.timeout_seconds),
        retries: Number(systemForm.snmp.retries),
        trap_target: systemForm.snmp.trap_target.trim() || null,
      },
    }
    const response = await api.put('/system/settings/system-wide', payload)
    settings.system_wide = response.data.data
    settings.ldap_enabled = response.data.data?.ldap?.enabled
    settings.allow_local_auth = response.data.data?.ldap?.allow_local_auth
    app.pushToast('System-wide settings saved', 'success')
  } catch (error: any) {
    app.pushToast(error?.response?.data?.message || 'Unable to save system-wide settings', 'error')
  } finally {
    settings.__savingSystem = false
  }
}

async function savePasswordReset() {
  if (!passwordForm.current_password || !passwordForm.new_password || !passwordForm.confirm_password) {
    app.pushToast('Enter current password, new password, and confirmation', 'error')
    return
  }
  if (passwordForm.new_password !== passwordForm.confirm_password) {
    app.pushToast('New password and confirmation do not match', 'error')
    return
  }
  if (passwordForm.new_password.length < 8) {
    app.pushToast('New password must be at least 8 characters', 'error')
    return
  }

  settings.__savingPassword = true
  try {
    await api.post('/auth/change-password', {
      current_password: passwordForm.current_password,
      new_password: passwordForm.new_password,
    })
    passwordForm.current_password = ''
    passwordForm.new_password = ''
    passwordForm.confirm_password = ''
    app.pushToast('Password updated', 'success')
  } catch (error: any) {
    app.pushToast(error?.response?.data?.message || 'Unable to update password', 'error')
  } finally {
    settings.__savingPassword = false
  }
}

async function copyDiagnostics() {
  try {
    await navigator.clipboard.writeText(diagnosticsJson.value)
    app.pushToast('Diagnostics copied', 'success')
  } catch {
    app.pushToast('Unable to copy diagnostics', 'error')
  }
}

function exportDiagnostics() {
  const blob = new Blob([diagnosticsJson.value], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `settings-diagnostics-${new Date().toISOString().replace(/[:.]/g, '-')}.json`
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

onMounted(load)
</script>

<style scoped>
.setting-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.9rem;
  border: 1px solid rgb(203 213 225 / 0.95);
  border-radius: 0.75rem;
  background: rgb(255 255 255 / 0.9);
  padding: 0.65rem 0.85rem;
}

.setting-copy {
  min-width: 0;
}

.setting-title {
  margin: 0;
  font-size: 0.88rem;
  font-weight: 600;
  line-height: 1.2rem;
  color: rgb(15 23 42);
}

.setting-help {
  margin: 0.1rem 0 0;
  font-size: 0.76rem;
  line-height: 1.1rem;
  color: rgb(100 116 139);
}

.switch {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.25rem;
  min-width: 2.25rem;
}

.switch input {
  position: absolute;
  opacity: 0;
  width: 1px;
  height: 1px;
}

.switch-track {
  width: 2.25rem;
  height: 1.3rem;
  border-radius: 999px;
  border: 1px solid rgb(148 163 184);
  background: rgb(226 232 240);
  transition: all 120ms ease;
  position: relative;
}

.switch-track::after {
  content: '';
  position: absolute;
  left: 0.1rem;
  top: 0.1rem;
  width: 1rem;
  height: 1rem;
  border-radius: 999px;
  background: rgb(255 255 255);
  box-shadow: 0 1px 3px rgb(15 23 42 / 0.25);
  transition: transform 120ms ease;
}

.switch input:checked + .switch-track {
  background: rgb(14 165 233 / 0.32);
  border-color: rgb(14 116 144 / 0.75);
}

.switch input:checked + .switch-track::after {
  transform: translateX(0.9rem);
}

.setting-row.is-disabled {
  opacity: 0.65;
  cursor: not-allowed;
}
</style>
