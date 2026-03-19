<template>
  <aside class="task-panel">
    <div class="panel-section hero-section">
      <div class="section-eyebrow">任务摘要</div>
      <h3 class="section-title">{{ taskInfo?.name || "未命名任务" }}</h3>
      <p class="section-desc">
        {{ taskInfo?.description || "这里展示当前任务的基础配置、运行环境、场景编排和用例清单，方便在监控过程中快速回看任务上下文。" }}
      </p>

      <div class="summary-chips">
        <span class="summary-chip summary-chip-state">{{ statusName }}</span>
        <span class="summary-chip">{{ taskInfo?.execution_strategy || "默认策略" }}</span>
        <span class="summary-chip">{{ taskInfo?.users ?? 0 }} 用户</span>
        <span class="summary-chip">{{ taskInfo?.spawn_rate ?? 0 }}/s 加压</span>
      </div>
    </div>

    <div class="panel-section">
      <div class="section-head">
        <div class="section-title-sm">任务配置</div>
        <span class="section-count">压测参数</span>
      </div>

      <div class="metric-grid">
        <div class="metric-card metric-card-primary">
          <span class="metric-label">并发用户</span>
          <span class="metric-value">{{ taskInfo?.users ?? 0 }}</span>
          <span class="metric-foot">目标压测规模</span>
        </div>
        <div class="metric-card">
          <span class="metric-label">加压速度</span>
          <span class="metric-value">{{ taskInfo?.spawn_rate ?? 0 }}/s</span>
          <span class="metric-foot">用户增长速率</span>
        </div>
        <div class="metric-card">
          <span class="metric-label">任务时长</span>
          <span class="metric-value">{{ taskInfo?.duration ?? 0 }}s</span>
          <span class="metric-foot">计划运行时长</span>
        </div>
        <div class="metric-card">
          <span class="metric-label">当前状态</span>
          <span class="metric-value">{{ statusName }}</span>
          <span class="metric-foot">任务运行阶段</span>
        </div>
      </div>
    </div>

    <div class="panel-section">
      <div class="section-head">
        <div class="section-title-sm">运行环境</div>
        <span class="section-count">任务上下文</span>
      </div>

      <div class="panel-grid">
        <div class="info-item">
          <span class="info-label">所属项目</span>
          <span class="info-value">{{ taskInfo?.project || "-" }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">目标主机</span>
          <span class="info-value">{{ taskInfo?.host || "-" }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">执行策略</span>
          <span class="info-value">{{ taskInfo?.execution_strategy || "-" }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">任务负责人</span>
          <span class="info-value">{{ taskInfo?.owner || taskInfo?.created_by_name || "-" }}</span>
        </div>
      </div>
    </div>

    <div class="panel-section">
      <div class="section-head">
        <div class="section-title-sm">运行摘要</div>
        <span class="section-count">实时概况</span>
      </div>

      <div class="panel-grid">
        <div class="info-item">
          <span class="info-label">运行时长</span>
          <span class="info-value">{{ metrics?.runtime || "--" }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">在线用户</span>
          <span class="info-value">{{ metrics?.user_count ?? 0 }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">当前吞吐</span>
          <span class="info-value">{{ formatNumber(metrics?.total_rps ?? 0) }} RPS</span>
        </div>
        <div class="info-item">
          <span class="info-label">失败率</span>
          <span class="info-value">{{ formatPercent(metrics?.fail_ratio ?? 0) }}</span>
        </div>
      </div>
    </div>

    <div class="panel-section">
      <div class="section-head">
        <div class="section-title-sm">场景编排</div>
        <span class="section-count">{{ scenarios.length }} 个场景</span>
      </div>

      <div v-if="scenarios.length" class="scenario-list">
        <div v-for="item in scenarios" :key="item.scenario_id" class="scenario-card">
          <div class="scenario-main">
            <span class="scenario-order">#{{ item.order }}</span>
            <div class="scenario-text">
              <span class="scenario-name">{{ item.scenario }}</span>
              <span class="scenario-count">{{ item.cases?.length || 0 }} 个用例</span>
            </div>
          </div>
          <div class="scenario-meta">
            <span>权重 {{ item.weight }}</span>
            <span>目标用户 {{ item.target_users ?? "-" }}</span>
          </div>
        </div>
      </div>
      <div v-else class="empty-note">当前任务还没有绑定场景，或者场景数据暂未返回。</div>
    </div>

    <div class="panel-section">
      <div class="section-head">
        <div class="section-title-sm">用例信息</div>
        <span class="section-count">{{ totalCases }} 个用例</span>
      </div>

      <div v-if="scenariosWithCases.length" class="case-groups">
        <div v-for="scenario in scenariosWithCases" :key="scenario.scenario_id" class="case-group">
          <div class="case-group-head">
            <span class="case-group-name">{{ scenario.scenario }}</span>
            <span class="case-group-count">{{ scenario.cases.length }} 个</span>
          </div>

          <div class="case-list">
            <div v-for="item in scenario.cases" :key="item.id" class="case-row">
              <div class="case-main">
                <span class="case-method">{{ item.method || "HTTP" }}</span>
                <div class="case-text">
                  <span class="case-name">{{ item.name }}</span>
                  <span class="case-url">{{ item.url }}</span>
                </div>
              </div>
              <div class="case-meta">
                <span>顺序 {{ item.order }}</span>
                <span>权重 {{ item.weight }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div v-else class="empty-note">当前任务详情里还没有可展示的用例清单。</div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed } from "vue";

import { STATE_NAMES } from "@/layout/type.ts";
import { formatNumber, formatPercent } from "@/utils/tools";
import type { Metrics } from "@/layout/type.ts";
import type { TaskInfo } from "@/types/task";

const props = defineProps<{
  taskInfo: TaskInfo | null;
  metrics: Metrics | null;
}>();

const scenarios = computed(() => props.taskInfo?.scenarios || []);
const scenariosWithCases = computed(() => scenarios.value.filter((item) => (item.cases || []).length > 0));
const totalCases = computed(() => scenarios.value.reduce((sum, item) => sum + (item.cases?.length || 0), 0));
const statusName = computed(() => STATE_NAMES[props.metrics?.state || "missing"] || "运行异常");
</script>

<style scoped>
.task-panel {
  position: sticky;
  top: 84px;
  width: 320px;
  height: fit-content;
  max-height: calc(100vh - 156px);
  overflow: auto;
  padding: 18px;
  border-radius: 24px;
  border: 1px solid rgba(148, 163, 184, 0.16);
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.08);
}

.panel-section + .panel-section {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid rgba(148, 163, 184, 0.12);
}

.hero-section {
  padding: 18px;
  border-radius: 20px;
  border: 1px solid rgba(59, 130, 246, 0.12);
  background:
    radial-gradient(circle at top right, rgba(191, 219, 254, 0.55), transparent 34%),
    linear-gradient(180deg, #eff6ff 0%, #ffffff 100%);
}

.section-eyebrow {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #64748b;
}

.section-title {
  margin: 8px 0 6px;
  font-size: 21px;
  line-height: 1.2;
  color: #0f172a;
}

.section-desc {
  margin: 0;
  color: #64748b;
  font-size: 13px;
  line-height: 1.6;
}

.summary-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
}

.summary-chip {
  display: inline-flex;
  align-items: center;
  height: 28px;
  padding: 0 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(148, 163, 184, 0.12);
  color: #0f172a;
  font-size: 12px;
  font-weight: 700;
}

.summary-chip-state {
  color: #1d4ed8;
  background: rgba(219, 234, 254, 0.92);
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.section-title-sm {
  font-size: 15px;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: 0.01em;
}

.section-count {
  color: #64748b;
  font-size: 12px;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.metric-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 14px;
  border-radius: 18px;
  background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
  border: 1px solid rgba(148, 163, 184, 0.12);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.9);
}

.metric-card-primary {
  border-color: rgba(59, 130, 246, 0.16);
  background: linear-gradient(180deg, #eff6ff 0%, #ffffff 100%);
}

.metric-label,
.metric-foot,
.info-label,
.section-count {
  color: #64748b;
}

.metric-label {
  font-size: 12px;
}

.metric-value {
  color: #0f172a;
  font-size: 19px;
  line-height: 1.2;
  font-weight: 800;
}

.metric-foot {
  font-size: 11px;
}

.panel-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 10px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 14px;
  background: #f8fafc;
  border: 1px solid rgba(148, 163, 184, 0.08);
}

.info-label {
  font-size: 12px;
}

.info-value {
  max-width: 160px;
  text-align: right;
  color: #0f172a;
  font-size: 13px;
  font-weight: 700;
  word-break: break-word;
}

.scenario-list,
.case-groups,
.case-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.scenario-card,
.case-group {
  padding: 12px 14px;
  border-radius: 16px;
  border: 1px solid rgba(59, 130, 246, 0.12);
  background: linear-gradient(180deg, #eff6ff 0%, #f8fbff 100%);
}

.scenario-main,
.case-main,
.case-group-head {
  display: flex;
  align-items: center;
  gap: 10px;
}

.case-group-head {
  justify-content: space-between;
  margin-bottom: 10px;
}

.scenario-order {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 999px;
  background: #2563eb;
  color: #fff;
  font-size: 12px;
  font-weight: 800;
}

.scenario-text,
.case-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.scenario-name,
.case-group-name,
.case-name {
  color: #0f172a;
  font-size: 14px;
  font-weight: 700;
}

.scenario-count,
.case-group-count,
.case-url,
.scenario-meta,
.case-meta {
  color: #64748b;
  font-size: 12px;
}

.scenario-meta,
.case-meta {
  display: flex;
  gap: 12px;
  margin-top: 8px;
}

.case-row {
  padding: 10px 12px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(148, 163, 184, 0.08);
}

.case-method {
  flex-shrink: 0;
  padding: 3px 8px;
  border-radius: 999px;
  background: #2563eb;
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
}

.case-url {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.empty-note {
  padding: 14px;
  border-radius: 14px;
  background: #f8fafc;
  border: 1px dashed rgba(148, 163, 184, 0.24);
  color: #64748b;
  font-size: 13px;
  line-height: 1.6;
}
</style>
