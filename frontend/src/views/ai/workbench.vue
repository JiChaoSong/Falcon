<script setup lang="ts">
const quickActions = [
  {
    title: 'AI 创建压测任务',
    description: '通过自然语言生成任务参数、SLA 和负载模型。',
    accent: 'ocean',
    cta: '开始创建'
  },
  {
    title: 'AI 生成场景编排',
    description: '根据业务目标自动组合用例、权重和用户路径。',
    accent: 'amber',
    cta: '生成场景'
  },
  {
    title: 'AI 输出测试报告',
    description: '自动总结压测结论、瓶颈接口和优化建议。',
    accent: 'rose',
    cta: '查看报告'
  }
];

const runningTasks = [
  {
    name: '登录链路峰值压测',
    status: '高风险',
    statusColor: 'red',
    summary: 'P95 在最近 3 分钟持续走高，失败率从 0.8% 上升到 3.4%。',
    action: '查看实时分析'
  },
  {
    name: '搜索服务容量验证',
    status: '稳定',
    statusColor: 'green',
    summary: '吞吐稳定在 1.8k RPS，尾延迟保持在目标阈值之内。',
    action: '打开监控页'
  },
  {
    name: '支付核心链路回归压测',
    status: '关注',
    statusColor: 'orange',
    summary: 'TPS 达到目标，但下游查询接口偶发抖动，需要继续观测。',
    action: '查看复测建议'
  }
];

const recommendations = [
  '优先给“登录链路峰值压测”增加自动止损策略，避免失败率继续放大。',
  '下一个建议任务：做 300 -> 450 -> 600 并发阶梯压测，用于定位容量拐点。',
  '建议把“支付核心链路回归压测”拆成下单、回调、查询三个独立场景，提高根因定位效率。'
];

const reportCards = [
  {
    title: '昨日压测结论',
    value: '12',
    unit: '份智能报告',
    detail: '其中 4 份识别出明确瓶颈接口'
  },
  {
    title: '待处理风险',
    value: '3',
    unit: '项告警',
    detail: '1 项高风险，2 项关注'
  },
  {
    title: '建议复测任务',
    value: '5',
    unit: '个场景',
    detail: '基于历史结果自动推荐'
  },
  {
    title: 'SLA 达成率',
    value: '91%',
    unit: '最近 7 天',
    detail: 'AI 识别主要风险来自登录与支付链路'
  }
];
</script>

<template>
  <div class="ai-workbench">
    <section class="hero-panel">
      <div class="hero-copy">
        <div class="eyebrow">AI Load Assistant</div>
        <h1 class="hero-title">把压测平台升级成会生成方案、会解释异常、会给建议的智能工作台</h1>
        <p class="hero-description">
          从任务创建、实时分析到压测复盘，AI 工作台会基于当前项目、场景、任务和监控数据，
          帮你更快找到风险、更快形成下一轮压测策略。
        </p>
        <div class="hero-actions">
          <a-button type="primary" size="large">让 AI 创建任务</a-button>
          <a-button size="large">查看实时分析</a-button>
        </div>
      </div>

      <div class="hero-side">
        <div class="signal-card">
          <div class="signal-title">今日智能摘要</div>
          <div class="signal-main">AI 已分析 8 个任务，识别出 2 个热点瓶颈链路</div>
          <div class="signal-list">
            <div class="signal-item">
              <span>最危险任务</span>
              <strong>登录链路峰值压测</strong>
            </div>
            <div class="signal-item">
              <span>推荐下一步</span>
              <strong>阶梯压测验证容量拐点</strong>
            </div>
            <div class="signal-item">
              <span>重点接口</span>
              <strong>/api/user/login</strong>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="stats-grid">
      <div class="stats-card" v-for="item in reportCards" :key="item.title">
        <div class="stats-title">{{ item.title }}</div>
        <div class="stats-value-row">
          <span class="stats-value">{{ item.value }}</span>
          <span class="stats-unit">{{ item.unit }}</span>
        </div>
        <div class="stats-detail">{{ item.detail }}</div>
      </div>
    </section>

    <section class="content-grid">
      <div class="content-card span-7">
        <div class="section-head">
          <div>
            <div class="section-title">快速入口</div>
            <div class="section-subtitle">把 AI 放到任务创建、场景编排和报告生成的主路径里</div>
          </div>
        </div>

        <div class="action-grid">
          <div class="action-card" v-for="item in quickActions" :key="item.title" :data-accent="item.accent">
            <div class="action-title">{{ item.title }}</div>
            <div class="action-description">{{ item.description }}</div>
            <a-button type="link" class="action-link">{{ item.cta }}</a-button>
          </div>
        </div>
      </div>

      <div class="content-card span-5">
        <div class="section-head">
          <div>
            <div class="section-title">AI 推荐动作</div>
            <div class="section-subtitle">基于最近任务、监控与报告自动生成</div>
          </div>
        </div>

        <div class="recommend-list">
          <div class="recommend-item" v-for="item in recommendations" :key="item">
            {{ item }}
          </div>
        </div>
      </div>

      <div class="content-card span-8">
        <div class="section-head">
          <div>
            <div class="section-title">运行中任务风险面板</div>
            <div class="section-subtitle">未来可直接联动你的监控页和 AI 实时分析卡片</div>
          </div>
          <a-button type="link">查看全部任务</a-button>
        </div>

        <div class="task-list">
          <div class="task-row" v-for="item in runningTasks" :key="item.name">
            <div class="task-main">
              <div class="task-name">{{ item.name }}</div>
              <div class="task-summary">{{ item.summary }}</div>
            </div>
            <div class="task-side">
              <a-tag :color="item.statusColor">{{ item.status }}</a-tag>
              <a-button type="link">{{ item.action }}</a-button>
            </div>
          </div>
        </div>
      </div>

      <div class="content-card span-4">
        <div class="section-head">
          <div>
            <div class="section-title">接入规划</div>
            <div class="section-subtitle">建议分阶段落地 AI 助手能力</div>
          </div>
        </div>

        <div class="roadmap">
          <div class="roadmap-item is-done">
            <span class="roadmap-step">01</span>
            <div>
              <div class="roadmap-title">AI 工作台</div>
              <div class="roadmap-desc">统一入口与智能摘要</div>
            </div>
          </div>
          <div class="roadmap-item">
            <span class="roadmap-step">02</span>
            <div>
              <div class="roadmap-title">AI 创建</div>
              <div class="roadmap-desc">自然语言生成任务与场景</div>
            </div>
          </div>
          <div class="roadmap-item">
            <span class="roadmap-step">03</span>
            <div>
              <div class="roadmap-title">AI 实时分析</div>
              <div class="roadmap-desc">联动监控数据解释异常</div>
            </div>
          </div>
          <div class="roadmap-item">
            <span class="roadmap-step">04</span>
            <div>
              <div class="roadmap-title">AI 报告</div>
              <div class="roadmap-desc">自动生成复盘与优化建议</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.ai-workbench {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.hero-panel,
.stats-card,
.content-card,
.signal-card {
  border-radius: 24px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.06);
}

.hero-panel {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) minmax(320px, 0.9fr);
  gap: 20px;
  padding: 28px;
  background:
      radial-gradient(circle at top right, rgba(59, 130, 246, 0.18), transparent 30%),
      radial-gradient(circle at bottom left, rgba(16, 185, 129, 0.12), transparent 24%),
      linear-gradient(180deg, #f8fbff 0%, #ffffff 100%);
}

.eyebrow {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #2563eb;
}

.hero-title {
  margin: 12px 0;
  max-width: 780px;
  font-size: 34px;
  line-height: 1.2;
  color: #0f172a;
}

.hero-description {
  max-width: 760px;
  margin: 0;
  font-size: 15px;
  line-height: 1.8;
  color: #475569;
}

.hero-actions {
  display: flex;
  gap: 12px;
  margin-top: 22px;
}

.signal-card {
  height: 100%;
  padding: 22px;
  background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
  color: #e2e8f0;
}

.signal-title {
  font-size: 13px;
  color: #93c5fd;
}

.signal-main {
  margin-top: 12px;
  font-size: 22px;
  line-height: 1.4;
  font-weight: 700;
}

.signal-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 20px;
}

.signal-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(148, 163, 184, 0.12);
}

.signal-item span {
  font-size: 12px;
  color: #94a3b8;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.stats-card {
  padding: 20px;
}

.stats-title,
.section-subtitle,
.stats-detail,
.task-summary,
.roadmap-desc,
.action-description {
  color: #64748b;
}

.stats-title {
  font-size: 13px;
}

.stats-value-row {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-top: 12px;
}

.stats-value {
  font-size: 30px;
  font-weight: 700;
  color: #0f172a;
}

.stats-unit {
  font-size: 13px;
  color: #475569;
}

.stats-detail {
  margin-top: 10px;
  font-size: 13px;
  line-height: 1.6;
}

.content-grid {
  display: grid;
  grid-template-columns: repeat(12, minmax(0, 1fr));
  gap: 16px;
}

.content-card {
  padding: 22px;
}

.span-7 { grid-column: span 7; }
.span-5 { grid-column: span 5; }
.span-8 { grid-column: span 8; }
.span-4 { grid-column: span 4; }

.section-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.section-title {
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
}

.section-subtitle {
  margin-top: 4px;
  font-size: 13px;
}

.action-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  margin-top: 18px;
}

.action-card {
  padding: 18px;
  border-radius: 20px;
  background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
  border: 1px solid rgba(15, 23, 42, 0.06);
}

.action-card[data-accent="ocean"] {
  background: linear-gradient(180deg, #eff6ff 0%, #ffffff 100%);
}

.action-card[data-accent="amber"] {
  background: linear-gradient(180deg, #fffbeb 0%, #ffffff 100%);
}

.action-card[data-accent="rose"] {
  background: linear-gradient(180deg, #fff1f2 0%, #ffffff 100%);
}

.action-title,
.task-name,
.roadmap-title {
  font-size: 16px;
  font-weight: 700;
  color: #0f172a;
}

.action-description {
  margin-top: 10px;
  min-height: 66px;
  line-height: 1.7;
}

.action-link {
  padding-left: 0;
  margin-top: 6px;
}

.recommend-list,
.task-list,
.roadmap {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 18px;
}

.recommend-item,
.task-row,
.roadmap-item {
  padding: 14px 16px;
  border-radius: 16px;
  background: #f8fafc;
}

.recommend-item {
  line-height: 1.7;
  color: #334155;
}

.task-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
}

.task-summary {
  margin-top: 8px;
  line-height: 1.7;
}

.task-side {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 10px;
  flex-shrink: 0;
}

.roadmap-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.roadmap-item.is-done {
  background: linear-gradient(180deg, #ecfdf5 0%, #f8fafc 100%);
}

.roadmap-step {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  border-radius: 999px;
  background: #dbeafe;
  color: #1d4ed8;
  font-size: 13px;
  font-weight: 700;
  flex-shrink: 0;
}

@media (max-width: 1200px) {
  .hero-panel,
  .stats-grid,
  .action-grid {
    grid-template-columns: 1fr;
  }

  .content-grid {
    grid-template-columns: 1fr;
  }

  .span-7,
  .span-5,
  .span-8,
  .span-4 {
    grid-column: auto;
  }
}

@media (max-width: 768px) {
  .hero-panel,
  .content-card,
  .stats-card {
    padding: 18px;
  }

  .hero-title {
    font-size: 28px;
  }

  .hero-actions,
  .task-row,
  .section-head {
    flex-direction: column;
    align-items: flex-start;
  }

  .task-side {
    align-items: flex-start;
  }
}
</style>
