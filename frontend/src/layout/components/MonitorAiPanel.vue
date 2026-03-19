<template>
  <div class="ai-card">
    <div class="ai-card-head">
      <div>
        <div class="ai-eyebrow">智能诊断</div>
        <h2 class="ai-title">{{ insight.title }}</h2>
      </div>
      <div class="ai-meta">
        <a-tag :color="toneMap[insight.level].color">
          {{ toneMap[insight.level].text }}
        </a-tag>
        <span class="ai-confidence">置信度 {{ Math.round(insight.confidence * 100) }}%</span>
      </div>
    </div>

    <p class="ai-summary">{{ insight.summary }}</p>

    <div class="ai-grid">
      <div class="ai-section">
        <div class="ai-section-title">关键观察</div>
        <ul class="ai-list">
          <li v-for="reason in insight.reasons" :key="reason">{{ reason }}</li>
        </ul>
      </div>

      <div class="ai-section">
        <div class="ai-section-title">建议动作</div>
        <ul class="ai-list">
          <li v-for="action in insight.actions" :key="action">{{ action }}</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { MonitorInsight } from "@/layout/composables/useTaskMonitorViewModel";

defineProps<{
  insight: MonitorInsight;
}>();

const toneMap = {
  success: { text: "稳定", color: "green" },
  warning: { text: "观察", color: "orange" },
  danger: { text: "风险", color: "red" },
};
</script>

<style scoped>
.ai-card {
  padding: 24px;
  border-radius: 22px;
  border: 1px solid rgba(148, 163, 184, 0.14);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(248, 250, 252, 0.94) 100%);
  box-shadow: 0 18px 36px rgba(15, 23, 42, 0.08);
}

.ai-card-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.ai-eyebrow {
  margin-bottom: 4px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #64748b;
}

.ai-title {
  margin: 0;
  font-size: 24px;
  line-height: 1.15;
  font-weight: 800;
  color: #0f172a;
}

.ai-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
}

.ai-confidence {
  font-size: 12px;
  color: #64748b;
}

.ai-summary {
  margin: 18px 0 22px;
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(241, 245, 249, 0.76);
  font-size: 14px;
  color: #334155;
  line-height: 1.75;
}

.ai-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
}

.ai-section {
  padding: 16px;
  border-radius: 18px;
  border: 1px solid rgba(148, 163, 184, 0.12);
  background: rgba(255, 255, 255, 0.88);
}

.ai-section-title {
  margin-bottom: 12px;
  font-size: 14px;
  font-weight: 700;
  color: #0f172a;
}

.ai-list {
  margin: 0;
  padding: 0;
  list-style: none;
}

.ai-list li {
  position: relative;
  padding-left: 18px;
  margin-bottom: 10px;
  font-size: 13px;
  line-height: 1.65;
  color: #475569;
}

.ai-list li::before {
  content: "";
  position: absolute;
  left: 0;
  top: 8px;
  width: 7px;
  height: 7px;
  border-radius: 999px;
  background: linear-gradient(180deg, #2563eb 0%, #0ea5e9 100%);
}

@media (max-width: 768px) {
  .ai-grid {
    grid-template-columns: 1fr;
  }

  .ai-card-head {
    flex-direction: column;
    align-items: flex-start;
  }

  .ai-meta {
    align-items: flex-start;
  }

  .ai-title {
    font-size: 20px;
  }
}
</style>
