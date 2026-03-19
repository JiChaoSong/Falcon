<template>
  <section class="structure-panel">
    <div class="panel-head">
      <div>
        <div class="panel-eyebrow">任务结构</div>
        <h2 class="panel-title">场景与用例编排</h2>
      </div>
      <div class="panel-count">
        <span class="count-pill">{{ scenarios.length }} 个场景</span>
        <span class="count-pill count-pill-strong">{{ totalCases }} 个用例</span>
      </div>
    </div>

    <div v-if="scenarios.length" class="scenario-list">
      <article v-for="scenario in scenarios" :key="scenario.scenario_id" class="scenario-card">
        <button type="button" class="scenario-head" @click="toggleScenario(scenario.scenario_id)">
          <div class="scenario-main">
            <div>
              <div class="scenario-order">场景 {{ scenario.order }}</div>
              <h3 class="scenario-title">{{ scenario.scenario }}</h3>
            </div>
            <div class="scenario-stats">
              <span class="stat-chip">权重 {{ scenario.weight }}</span>
              <span class="stat-chip">目标用户 {{ scenario.target_users ?? '-' }}</span>
              <span class="stat-chip stat-chip-strong">{{ scenario.cases?.length || 0 }} 个用例</span>
            </div>
          </div>
          <span class="toggle-indicator">{{ expandedScenarioIds.includes(scenario.scenario_id) ? '收起' : '展开' }}</span>
        </button>

        <div v-if="expandedScenarioIds.includes(scenario.scenario_id)" class="case-list">
          <div v-if="scenario.cases?.length" class="case-summary">
            <span>共 {{ scenario.cases.length }} 个用例</span>
            <span>按配置顺序展示</span>
          </div>

          <div v-if="scenario.cases?.length" class="case-items">
            <div v-for="item in scenario.cases" :key="item.id" class="case-row">
              <div class="case-main">
                <span class="case-method">{{ item.method || 'HTTP' }}</span>
                <div class="case-text">
                  <span class="case-name">{{ item.name }}</span>
                  <span class="case-url" :title="item.url">{{ item.url }}</span>
                </div>
              </div>
              <div class="case-meta">
                <span>顺序 {{ item.order }}</span>
                <span>权重 {{ item.weight }}</span>
                <span>{{ item.status || 'unknown' }}</span>
              </div>
            </div>
          </div>

          <div v-else class="empty-inline">当前场景下还没有绑定用例。</div>
        </div>
      </article>
    </div>

    <div v-else class="empty-state">当前任务还没有配置场景信息。</div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { TaskScenarioInfo } from '@/types/task'

const props = defineProps<{
  scenarios: TaskScenarioInfo[]
}>()

const expandedScenarioIds = ref<number[]>([])

watch(
  () => props.scenarios,
  (value) => {
    expandedScenarioIds.value = value.slice(0, 2).map((item) => item.scenario_id)
  },
  { immediate: true }
)

const totalCases = computed(() => props.scenarios.reduce((sum, item) => sum + (item.cases?.length || 0), 0))

const toggleScenario = (scenarioId: number) => {
  expandedScenarioIds.value = expandedScenarioIds.value.includes(scenarioId)
    ? expandedScenarioIds.value.filter((item) => item !== scenarioId)
    : [...expandedScenarioIds.value, scenarioId]
}
</script>

<style scoped>
.structure-panel {
  padding: 22px;
  border-radius: 28px;
  border: 1px solid rgba(148, 163, 184, 0.14);
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 16px 32px rgba(15, 23, 42, 0.06);
}

.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 18px;
}

.panel-eyebrow {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #64748b;
}

.panel-title {
  margin: 8px 0 0;
  font-size: 22px;
  color: #0f172a;
}

.panel-count {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.count-pill {
  display: inline-flex;
  align-items: center;
  height: 30px;
  padding: 0 12px;
  border-radius: 999px;
  background: rgba(241, 245, 249, 0.92);
  color: #475569;
  font-size: 12px;
  font-weight: 700;
}

.count-pill-strong {
  background: #dbeafe;
  color: #1d4ed8;
}

.scenario-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.scenario-card {
  border-radius: 22px;
  border: 1px solid rgba(148, 163, 184, 0.12);
  background:
    radial-gradient(circle at top right, rgba(239, 246, 255, 0.78), transparent 30%),
    #ffffff;
  overflow: hidden;
}

.scenario-head {
  width: 100%;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 18px;
  background: transparent;
  border: 0;
  text-align: left;
  cursor: pointer;
}

.scenario-main {
  flex: 1;
  min-width: 0;
}

.scenario-order {
  color: #64748b;
  font-size: 12px;
}

.scenario-title {
  margin: 4px 0 0;
  font-size: 18px;
  color: #0f172a;
}

.scenario-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.stat-chip {
  display: inline-flex;
  align-items: center;
  height: 28px;
  padding: 0 12px;
  border-radius: 999px;
  background: #eff6ff;
  color: #1d4ed8;
  font-size: 12px;
  font-weight: 700;
}

.stat-chip-strong {
  background: #dbeafe;
}

.toggle-indicator {
  color: #64748b;
  font-size: 12px;
  font-weight: 700;
}

.case-list {
  padding: 0 18px 18px;
}

.case-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 12px;
  margin-bottom: 12px;
  border-radius: 14px;
  background: rgba(248, 250, 252, 0.96);
  color: #64748b;
  font-size: 12px;
}

.case-items {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.case-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(248, 250, 252, 0.96);
  border: 1px solid rgba(148, 163, 184, 0.1);
}

.case-main {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  min-width: 0;
  flex: 1;
}

.case-method {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 56px;
  height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  background: #dbeafe;
  color: #1d4ed8;
  font-size: 12px;
  font-weight: 700;
}

.case-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
  flex: 1;
}

.case-name {
  color: #0f172a;
  font-weight: 700;
}

.case-url {
  color: #64748b;
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.case-meta {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
  color: #64748b;
  font-size: 12px;
}

.empty-state,
.empty-inline {
  padding: 18px;
  border-radius: 18px;
  background: rgba(248, 250, 252, 0.92);
  color: #64748b;
  font-size: 13px;
}
</style>
