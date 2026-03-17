<template>
  <div class="smart-home">
    <section class="hero-panel">
      <div class="hero-main">
        <div class="eyebrow">Smart Dashboard</div>
        <h1 class="hero-title">欢迎回来，{{ userInfo.name }}。今天先看 AI 告诉你的重点，再决定下一步压测动作。</h1>
        <p class="hero-description">
          当前平台正在从“配置与展示”升级成“生成方案、解释异常、指导复测”的智能压测工作台。
          首页优先呈现风险任务、推荐动作和 AI 快捷入口，让你先看到结论，再进入具体任务处理。
        </p>

        <div class="hero-actions">
          <a-button type="primary" size="large" @click="quickCreateTask">让 AI 创建任务</a-button>
          <a-button size="large" @click="goToTaskPage">查看运行中任务</a-button>
        </div>

        <div class="hero-meta">
          <div class="hero-meta-item">
            <span class="meta-label">今天日期</span>
            <strong>{{ currentDate }}</strong>
          </div>
          <div class="hero-meta-item">
            <span class="meta-label">AI 已分析</span>
            <strong>8 个任务</strong>
          </div>
          <div class="hero-meta-item">
            <span class="meta-label">高优先风险</span>
            <strong>2 项</strong>
          </div>
        </div>
      </div>

      <div class="hero-side">
        <div class="signal-card">
          <div class="signal-title">今日智能摘要</div>
          <div class="signal-main">登录链路和支付链路是今天最需要优先关注的容量风险点。</div>
          <div class="signal-list">
            <div class="signal-item">
              <span>最危险任务</span>
              <strong>登录链路峰值压测</strong>
            </div>
            <div class="signal-item">
              <span>推荐下一步</span>
              <strong>做 300 - 450 - 600 并发阶梯压测</strong>
            </div>
            <div class="signal-item">
              <span>热点接口</span>
              <strong>/api/user/login</strong>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="ai-grid">
      <div class="content-card span-7">
        <div class="section-head">
          <div>
            <div class="section-title">AI 推荐动作</div>
            <div class="section-subtitle">基于最近任务、监控趋势和历史报告自动生成</div>
          </div>
        </div>

        <div class="recommend-list">
          <div class="recommend-item" v-for="item in recommendations" :key="item">
            {{ item }}
          </div>
        </div>
      </div>

      <div class="content-card span-5">
        <div class="section-head">
          <div>
            <div class="section-title">AI 快速入口</div>
            <div class="section-subtitle">把 AI 放进任务创建、场景编排和结果复盘主路径</div>
          </div>
        </div>

        <div class="action-grid">
          <div class="action-card" v-for="item in quickActions" :key="item.title" :data-accent="item.accent">
            <div class="action-title">{{ item.title }}</div>
            <div class="action-description">{{ item.description }}</div>
            <a-button type="link" class="action-link" @click="item.onClick">{{ item.cta }}</a-button>
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

    <section class="overview-grid">
      <div class="content-card span-8">
        <div class="section-head">
          <div>
            <div class="section-title">运行中任务风险面板</div>
            <div class="section-subtitle">先看 AI 风险结论，再进入监控页和报告页处理</div>
          </div>
          <a-button type="link" @click="goToTaskPage">查看全部任务</a-button>
        </div>

        <div class="task-list">
          <div class="task-row" v-for="item in runningTasks" :key="item.name">
            <div class="task-main">
              <div class="task-name">{{ item.name }}</div>
              <div class="task-summary">{{ item.summary }}</div>
            </div>
            <div class="task-side">
              <a-tag :color="item.statusColor">{{ item.status }}</a-tag>
              <a-button type="link" @click="item.onClick">{{ item.action }}</a-button>
            </div>
          </div>
        </div>
      </div>

      <div class="content-card span-4">
        <div class="section-head">
          <div>
            <div class="section-title">平台概览</div>
            <div class="section-subtitle">保留传统首页的关键业务统计</div>
          </div>
        </div>

        <div class="platform-stats">
          <div class="platform-item">
            <span>在线压测节点</span>
            <strong>{{ stats.onlineNodes }}</strong>
          </div>
          <div class="platform-item">
            <span>今日任务数</span>
            <strong>{{ stats.todayTasks }}</strong>
          </div>
          <div class="platform-item">
            <span>成功率</span>
            <strong>{{ stats.successRate }}%</strong>
          </div>
          <div class="platform-item">
            <span>项目总数</span>
            <strong>{{ statistics.projects }}</strong>
          </div>
          <div class="platform-item">
            <span>测试用例</span>
            <strong>{{ statistics.testcases }}</strong>
          </div>
          <div class="platform-item">
            <span>压测场景</span>
            <strong>{{ statistics.scenarios }}</strong>
          </div>
          <div class="platform-item">
            <span>执行任务</span>
            <strong>{{ statistics.tasks }}</strong>
          </div>
        </div>
      </div>
    </section>

    <section class="content-grid">
      <div class="content-card span-7">
        <div class="section-head">
          <div>
            <div class="section-title">最近任务</div>
            <div class="section-subtitle">保留原首页任务列表，作为操作入口层</div>
          </div>
          <a-button type="link" @click="goToTaskPage">查看全部</a-button>
        </div>

        <a-table
          :columns="taskColumns"
          :data-source="recentTasks"
          :pagination="false"
          row-key="id"
          size="small"
          class="task-table"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'name'">
              <div class="task-name-cell">
                <div class="task-name">{{ record.name }}</div>
                <div class="task-id">{{ record.id }}</div>
              </div>
            </template>

            <template v-if="column.key === 'status'">
              <a-tag :color="taskStatusMap[record.status].color">
                {{ taskStatusMap[record.status].text }}
              </a-tag>
            </template>

            <template v-if="column.key === 'progress'">
              <div class="progress-wrap">
                <a-progress
                  :percent="record.progress"
                  :status="record.status === 'failed' ? 'exception' : 'normal'"
                  size="small"
                />
              </div>
            </template>

            <template v-if="column.key === 'actions'">
              <a-space size="small">
                <a-button type="link" size="small" @click="viewTaskDetail(record.id)">详情</a-button>
                <a-button v-if="record.status === 'running'" type="link" size="small" @click="stopTask(record.id)">停止</a-button>
                <a-button v-if="record.status !== 'running'" type="link" size="small" @click="viewReport(record.id)">报告</a-button>
              </a-space>
            </template>
          </template>
        </a-table>
      </div>

      <div class="content-card span-5">
        <div class="section-head">
          <div>
            <div class="section-title">活跃场景与系统通知</div>
            <div class="section-subtitle">保留原首页的场景入口和通知聚合</div>
          </div>
        </div>

        <div class="scenario-list">
          <div class="scenario-card" v-for="scenario in activeScenarios.slice(0, 3)" :key="scenario.id">
            <div class="scenario-head">
              <div class="scenario-name">{{ scenario.name }}</div>
              <a-tag :color="scenario.status === 'active' ? 'green' : 'orange'">
                {{ scenario.status === 'active' ? '启用中' : '草稿' }}
              </a-tag>
            </div>
            <div class="scenario-description">{{ scenario.description }}</div>
            <div class="scenario-meta">{{ scenario.project }} · {{ scenario.testcaseCount }} 个用例</div>
          </div>
        </div>

        <div class="notification-panel">
          <div class="mini-title">系统通知</div>
          <div class="notification-item" v-for="item in notifications" :key="item.id">
            <div class="notification-top">
              <span>{{ item.title }}</span>
              <a-tag :color="item.type === 'warning' ? 'orange' : 'blue'">
                {{ item.type === 'warning' ? '警告' : '信息' }}
              </a-tag>
            </div>
            <div class="notification-content">{{ item.content }}</div>
            <div class="notification-time">{{ item.time }}</div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue';
import { message, Modal } from 'ant-design-vue';
import { useRouter } from 'vue-router';

const router = useRouter();

const userInfo = reactive({
  name: '张管理员',
});

const currentDate = computed(() => {
  const now = new Date();
  return `${now.getFullYear()}年${now.getMonth() + 1}月${now.getDate()}日`;
});

const stats = reactive({
  onlineNodes: 3,
  todayTasks: 12,
  successRate: 98.5
});

const statistics = reactive({
  projects: 42,
  testcases: 156,
  scenarios: 28,
  tasks: 312
});

const recommendations = [
  '优先给“登录链路峰值压测”增加自动止损策略，避免失败率继续放大。',
  '下一个建议任务：做 300 到 450 到 600 并发阶梯压测，用于定位容量拐点。',
  '建议把“支付核心链路回归压测”拆成下单、回调、查询三个独立场景，提高根因定位效率。'
];

const reportCards = [
  { title: '昨日压测结论', value: '12', unit: '份智能报告', detail: '其中 4 份识别出明确瓶颈接口' },
  { title: '待处理风险', value: '3', unit: '项告警', detail: '1 项高风险，2 项关注' },
  { title: '建议复测任务', value: '5', unit: '个场景', detail: '基于历史结果自动推荐' },
  { title: 'SLA 达成率', value: '91%', unit: '最近 7 天', detail: '主要风险来自登录与支付链路' }
];

const recentTasks = ref([
  {
    id: 'TASK-20240120-001',
    name: 'Baidu首页压测',
    project: '搜索引擎',
    status: 'running',
    progress: 65,
    userCount: 100
  },
  {
    id: 'TASK-20240120-002',
    name: '双十一大促压测',
    project: '电商平台',
    status: 'completed',
    progress: 100,
    userCount: 500
  },
  {
    id: 'TASK-20240120-003',
    name: '用户登录性能测试',
    project: '用户中心',
    status: 'failed',
    progress: 30,
    userCount: 200
  },
  {
    id: 'TASK-20240119-001',
    name: 'API网关压力测试',
    project: 'API网关',
    status: 'completed',
    progress: 100,
    userCount: 1000
  }
]);

const activeScenarios = ref([
  {
    id: 'SCENARIO-001',
    name: '首页访问场景',
    project: '电商平台',
    description: '模拟用户访问电商首页的完整流程',
    status: 'active',
    testcaseCount: 4
  },
  {
    id: 'SCENARIO-002',
    name: '下单流程场景',
    project: '电商平台',
    description: '完整的购物下单流程，从商品选择到支付完成',
    status: 'active',
    testcaseCount: 5
  },
  {
    id: 'SCENARIO-003',
    name: '用户登录注册场景',
    project: '用户中心',
    description: '用户登录、注册、找回密码等核心功能测试',
    status: 'active',
    testcaseCount: 3
  }
]);

const notifications = ref([
  { id: 1, title: '系统维护通知', content: '系统将于本周六凌晨2:00-4:00进行维护升级', type: 'info', time: '2小时前' },
  { id: 2, title: '压测节点异常', content: '节点 node-003 响应异常，已自动切换到备用节点', type: 'warning', time: '5小时前' },
  { id: 3, title: '新功能发布', content: '分布式压测功能已上线，支持更大规模并发测试', type: 'info', time: '1天前' }
]);

const taskStatusMap: Record<string, { text: string; color: string }> = {
  running: { text: '运行中', color: 'blue' },
  completed: { text: '已完成', color: 'green' },
  failed: { text: '失败', color: 'red' },
  pending: { text: '待执行', color: 'orange' }
};

const taskColumns = [
  { title: '任务名称', dataIndex: 'name', key: 'name', width: 220 },
  { title: '项目', dataIndex: 'project', key: 'project', width: 120 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 100 },
  { title: '进度', key: 'progress', width: 160 },
  { title: '并发用户', dataIndex: 'userCount', key: 'userCount', width: 100 },
  { title: '操作', key: 'actions', width: 150 }
];

const goToTaskPage = () => {
  router.push('/task');
};

const quickCreateTask = () => {
  message.info('后续这里将接入 AI 创建任务流程');
};

const quickCreateScenario = () => {
  router.push('/scenario');
};

const quickCreateTestCase = () => {
  router.push('/csse');
};

const viewTaskDetail = (taskId: string) => {
  router.push(`/monitor/${taskId}`);
};

const stopTask = (taskId: string) => {
  Modal.confirm({
    title: '确认停止',
    content: '确定要停止此压测任务吗？',
    onOk() {
      message.success(`任务 ${taskId} 已停止`);
    }
  });
};

const viewReport = (taskId: string) => {
  message.info(`后续这里将接入 AI 报告：${taskId}`);
};

const runningTasks = [
  {
    name: '登录链路峰值压测',
    status: '高风险',
    statusColor: 'red',
    summary: 'P95 在最近 3 分钟持续走高，失败率从 0.8% 上升到 3.4%。',
    action: '查看实时分析',
    onClick: () => router.push('/monitor/10001')
  },
  {
    name: '搜索服务容量验证',
    status: '稳定',
    statusColor: 'green',
    summary: '吞吐稳定在 1.8k RPS，尾延迟保持在目标阈值之内。',
    action: '打开任务页',
    onClick: () => router.push('/task')
  },
  {
    name: '支付核心链路回归压测',
    status: '关注',
    statusColor: 'orange',
    summary: 'TPS 达到目标，但下游查询接口偶发抖动，需要继续观测。',
    action: '查看场景',
    onClick: () => router.push('/scenario')
  }
];

const quickActions = [
  {
    title: 'AI 创建压测任务',
    description: '通过自然语言生成任务参数、SLA 和负载模型。',
    accent: 'ocean',
    cta: '开始创建',
    onClick: quickCreateTask
  },
  {
    title: 'AI 生成场景编排',
    description: '根据业务目标自动组合用例、权重和用户路径。',
    accent: 'amber',
    cta: '生成场景',
    onClick: quickCreateScenario
  },
  {
    title: 'AI 输出测试报告',
    description: '自动总结压测结论、瓶颈接口和优化建议。',
    accent: 'rose',
    cta: '查看报告',
    onClick: () => viewReport('TASK-20240120-002')
  },
  {
    title: 'AI 辅助新建用例',
    description: '根据业务描述生成请求配置、断言与场景前置条件。',
    accent: 'mint',
    cta: '新建用例',
    onClick: quickCreateTestCase
  }
];
</script>

<style scoped>
.smart-home {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.hero-panel,
.content-card,
.stats-card,
.signal-card {
  border-radius: 24px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.06);
}

.hero-panel {
  display: grid;
  grid-template-columns: minmax(0, 1.45fr) minmax(320px, 0.9fr);
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

.hero-meta {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 20px;
}

.hero-meta-item {
  min-width: 140px;
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.72);
}

.meta-label {
  display: block;
  margin-bottom: 6px;
  font-size: 12px;
  color: #64748b;
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

.signal-item span,
.stats-title,
.section-subtitle,
.stats-detail,
.task-summary,
.action-description,
.scenario-description,
.scenario-meta,
.notification-content,
.notification-time {
  color: #64748b;
}

.ai-grid,
.overview-grid,
.content-grid {
  display: grid;
  grid-template-columns: repeat(12, minmax(0, 1fr));
  gap: 16px;
}

.span-7 { grid-column: span 7; }
.span-5 { grid-column: span 5; }
.span-8 { grid-column: span 8; }
.span-4 { grid-column: span 4; }

.content-card {
  padding: 22px;
}

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

.recommend-list,
.task-list,
.scenario-list,
.notification-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 18px;
}

.recommend-item,
.task-row,
.scenario-card,
.notification-item,
.platform-item {
  padding: 14px 16px;
  border-radius: 16px;
  background: #f8fafc;
}

.recommend-item {
  line-height: 1.7;
  color: #334155;
}

.action-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  margin-top: 18px;
}

.action-card {
  padding: 18px;
  border-radius: 20px;
  background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
  border: 1px solid rgba(15, 23, 42, 0.06);
}

.action-card[data-accent="ocean"] { background: linear-gradient(180deg, #eff6ff 0%, #ffffff 100%); }
.action-card[data-accent="amber"] { background: linear-gradient(180deg, #fffbeb 0%, #ffffff 100%); }
.action-card[data-accent="rose"] { background: linear-gradient(180deg, #fff1f2 0%, #ffffff 100%); }
.action-card[data-accent="mint"] { background: linear-gradient(180deg, #ecfdf5 0%, #ffffff 100%); }

.action-title,
.task-name,
.scenario-name,
.mini-title {
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

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.stats-card {
  padding: 20px;
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

.task-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
}

.task-side {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 10px;
  flex-shrink: 0;
}

.platform-stats {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 18px;
}

.platform-item span {
  display: block;
  margin-bottom: 8px;
  font-size: 12px;
  color: #64748b;
}

.platform-item strong {
  font-size: 22px;
  color: #0f172a;
}

.progress-wrap {
  min-width: 120px;
}

.task-name-cell .task-id {
  margin-top: 4px;
  font-size: 12px;
  color: #94a3b8;
}

.scenario-head,
.notification-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.scenario-description,
.notification-content {
  margin-top: 10px;
  line-height: 1.7;
}

.scenario-meta,
.notification-time {
  margin-top: 8px;
  font-size: 12px;
}

.task-table {
  margin-top: 18px;
}

@media (max-width: 1200px) {
  .hero-panel,
  .stats-grid,
  .action-grid,
  .platform-stats {
    grid-template-columns: 1fr;
  }

  .ai-grid,
  .overview-grid,
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
  .hero-meta,
  .task-row,
  .section-head,
  .scenario-head,
  .notification-top {
    flex-direction: column;
    align-items: flex-start;
  }

  .task-side {
    align-items: flex-start;
  }
}
</style>
