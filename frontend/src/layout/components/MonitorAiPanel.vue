<template>
  <div class="ai-card">
    <div class="ai-card-head">
      <div>
        <div class="ai-eyebrow">AI 实时分析</div>
        <h2 class="ai-title">{{ aiInsight.title }}</h2>
      </div>
      <div class="ai-meta">
        <a-tag :color="aiInsightToneMap[aiInsight.level].color">
          {{ aiInsightToneMap[aiInsight.level].text }}
        </a-tag>
        <span class="ai-confidence">置信度 {{ Math.round(aiInsight.confidence * 100) }}%</span>
      </div>
    </div>

    <p class="ai-summary">{{ aiInsight.summary }}</p>

    <div class="ai-grid">
      <div class="ai-section">
        <div class="ai-section-title">判断依据</div>
        <ul class="ai-list">
          <li v-for="reason in aiInsight.reasons" :key="reason">{{ reason }}</li>
        </ul>
      </div>

      <div class="ai-section">
        <div class="ai-section-title">建议动作</div>
        <ul class="ai-list">
          <li v-for="action in aiInsight.actions" :key="action">{{ action }}</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { MetricHistoryPoint, Metrics, Stats } from "@/layout/type.ts";

type MonitorRiskLevel = "success" | "warning" | "danger";

interface AiInsight {
  title: string;
  summary: string;
  level: MonitorRiskLevel;
  reasons: string[];
  actions: string[];
  confidence: number;
}

const props = defineProps<{
  dataSource: Stats[];
  metrics: Metrics;
  history: MetricHistoryPoint[];
}>();

const aiInsightToneMap: Record<MonitorRiskLevel, { text: string; color: string }> = {
  success: { text: '稳定', color: 'green' },
  warning: { text: '关注', color: 'orange' },
  danger: { text: '风险', color: 'red' }
};

const aiInsight = computed<AiInsight>(() => {
  const runtimeSeconds = props.metrics.runtime_seconds;
  const stats = props.dataSource;
  const failRatio = props.metrics.fail_ratio;
  const totalRps = props.metrics.total_rps;
  const hotspot = [...stats]
      .sort((a, b) => (b.current_fail_per_sec + b.avg_response_time / 1000) - (a.current_fail_per_sec + a.avg_response_time / 1000))[0];
  const p95 = hotspot?.["response_time_percentile_0.95"] ?? 0;

  if (!stats.length) {
    return {
      title: '等待监控数据',
      summary: '当前还没有收到压测指标，AI 将在数据进入后给出实时判断。',
      level: 'warning',
      reasons: ['指标流为空，暂时无法判断系统瓶颈。'],
      actions: ['确认任务已启动，并检查任务配置和目标服务是否可达。'],
      confidence: 0.42
    };
  }

  if (failRatio >= 0.05 || p95 >= 800) {
    return {
      title: '接口延迟与失败率正在放大',
      summary: `${hotspot?.name || '核心接口'} 已成为热点风险点，P95 ${p95}ms，失败率 ${(failRatio * 100).toFixed(1)}%。`,
      level: 'danger',
      reasons: [
        `总失败率已达到 ${(failRatio * 100).toFixed(1)}%，超过常见压测告警阈值。`,
        `${hotspot?.name || '热点接口'} 当前失败 ${hotspot?.current_fail_per_sec?.toFixed(2) || '0.00'}/s。`,
        `并发用户 ${props.metrics.user_count} 下，整体吞吐 ${totalRps} RPS 出现波动。`
      ],
      actions: [
        '优先检查热点接口对应的数据库连接池、缓存命中率和下游超时。',
        '下一轮建议降低爬升速率，做 70% 到 100% 目标并发的阶梯压测。',
        '如果这是验收场景，可先基于 P95 和失败率设置自动止损。'
      ],
      confidence: 0.91
    };
  }

  if (failRatio >= 0.02 || p95 >= 500 || runtimeSeconds < 180) {
    return {
      title: '系统整体可用，但进入观测区间',
      summary: `当前吞吐 ${totalRps} RPS，热点接口 ${hotspot?.name || '未知'} 的 P95 为 ${p95}ms。`,
      level: 'warning',
      reasons: [
        `任务已运行 ${props.metrics.runtime}，仍处于负载爬升后的敏感窗口。`,
        `热点接口平均响应 ${hotspot?.avg_response_time}ms，建议持续观察尾延迟。`,
        `失败率 ${(failRatio * 100).toFixed(1)}%，尚未失控但已有抬头迹象。`
      ],
      actions: [
        '继续观测 3 到 5 分钟，确认指标是否稳定收敛。',
        '补充慢接口明细和错误码分布，便于区分容量问题与业务异常。',
        '下一步可以联动日志或 APM，做接口级根因定位。'
      ],
      confidence: 0.78
    };
  }

  return {
    title: '压测状态稳定，当前无明显风险',
    summary: `并发 ${props.metrics.user_count} 下系统保持稳定，当前总吞吐 ${totalRps} RPS。`,
    level: 'success',
    reasons: [
      `总失败率维持在 ${(failRatio * 100).toFixed(1)}%。`,
      `热点接口 ${hotspot?.name || '未知'} 的 P95 为 ${p95}ms，仍在可控范围内。`,
      `任务已运行 ${props.metrics.runtime}，指标曲线没有明显失真。`
    ],
    actions: [
      '可以逐步继续加压，验证系统容量上限。',
      '建议在任务结束后自动输出一份 AI 复盘报告。',
      '如果这是基线压测，可将当前结果沉淀为容量基准。'
    ],
    confidence: 0.86
  };
});
</script>

<style scoped>
.ai-card {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.ai-card-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.ai-eyebrow {
  font-size: 12px;
  color: #666;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 4px;
}

.ai-title {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.ai-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
}

.ai-confidence {
  font-size: 12px;
  color: #6b7280;
}

.ai-summary {
  font-size: 14px;
  color: #4b5563;
  line-height: 1.6;
  margin-bottom: 20px;
}

.ai-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.ai-section-title {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 12px;
}

.ai-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.ai-list li {
  font-size: 13px;
  color: #4b5563;
  line-height: 1.5;
  margin-bottom: 8px;
  padding-left: 16px;
  position: relative;
}

.ai-list li:before {
  content: "•";
  color: #3b82f6;
  font-weight: bold;
  position: absolute;
  left: 0;
}

@media (max-width: 768px) {
  .ai-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .ai-card-head {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .ai-meta {
    align-items: flex-start;
  }
}
</style>