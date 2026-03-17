<template>
  <div class="app-container">
    <!-- 页面标题和操作 -->
    <div class="page-header">
      <div class="page-title-section">
        <h1 class="page-title">用例管理</h1>
        <p class="page-subtitle">压测用例创建、编辑、调试，支持多种协议和复杂业务逻辑，为场景提供基础测试单元</p>
      </div>

      <Space>
        <!-- 视图切换 -->
<!--        <Button.Group>-->
<!--          <Button-->
<!--              :type="state.viewMode === 'card' ? 'primary' : 'default'"-->
<!--              @click="switchView('card')"-->
<!--          >-->
<!--            <template #icon><AppstoreOutlined /></template>-->
<!--            卡片视图-->
<!--          </Button>-->
<!--          <Button-->
<!--              :type="state.viewMode === 'table' ? 'primary' : 'default'"-->
<!--              @click="switchView('table')"-->
<!--          >-->
<!--            <template #icon><UnorderedListOutlined /></template>-->
<!--            表格视图-->
<!--          </Button>-->
<!--        </Button.Group>-->

        <!-- 新增用例按钮 -->
        <Button type="primary" @click="showAddModal">
          <template #icon><PlusOutlined /></template>
          新增用例
        </Button>
      </Space>
    </div>

<!--    &lt;!&ndash; 统计卡片 &ndash;&gt;-->
<!--    <Row :gutter="16" class="stats-row">-->
<!--      <Col :span="6">-->
<!--        <ACard>-->
<!--          <Statistic-->
<!--              title="用例总数"-->
<!--              :value="statistics.total"-->
<!--              :value-style="{ color: '#1890ff', fontSize: '24px' }"-->
<!--          >-->
<!--            <template #prefix><ProjectOutlined /></template>-->
<!--            <template #suffix>-->
<!--              <span style="font-size: 12px; color: #666">较上月 +12</span>-->
<!--            </template>-->
<!--          </Statistic>-->
<!--        </ACard>-->
<!--      </Col>-->
<!--      <Col :span="6">-->
<!--        <ACard>-->
<!--          <Statistic-->
<!--              title="启用用例"-->
<!--              :value="statistics.active"-->
<!--              :value-style="{ color: '#52c41a', fontSize: '24px' }"-->
<!--          >-->
<!--            <template #prefix><PlayCircleOutlined /></template>-->
<!--            <template #suffix>-->
<!--              <span style="font-size: 12px; color: #666">占比 {{ Math.round((statistics.active / statistics.total) * 100) }}%</span>-->
<!--            </template>-->
<!--          </Statistic>-->
<!--        </ACard>-->
<!--      </Col>-->
<!--      <Col :span="6">-->
<!--        <ACard>-->
<!--          <Statistic-->
<!--              title="HTTP用例"-->
<!--              :value="statistics.httpCount"-->
<!--              :value-style="{ color: '#faad14', fontSize: '24px' }"-->
<!--          >-->
<!--            <template #prefix><ApiOutlined /></template>-->
<!--            <template #suffix>-->
<!--              <span style="font-size: 12px; color: #666">占比 {{ Math.round((statistics.httpCount / statistics.total) * 100) }}%</span>-->
<!--            </template>-->
<!--          </Statistic>-->
<!--        </ACard>-->
<!--      </Col>-->
<!--      <Col :span="6">-->
<!--        <ACard>-->
<!--          <Statistic-->
<!--              title="跨项目用例"-->
<!--              :value="statistics.projects"-->
<!--              :value-style="{ color: '#13c2c2', fontSize: '24px' }"-->
<!--          >-->
<!--            <template #prefix><ScheduleOutlined /></template>-->
<!--            <template #suffix>-->
<!--              <span style="font-size: 12px; color: #666">{{ statistics.uniqueProjects }} 个项目</span>-->
<!--            </template>-->
<!--          </Statistic>-->
<!--        </ACard>-->
<!--      </Col>-->
<!--    </Row>-->

    <!-- 筛选区域 -->
    <ACard title="用例筛选" class="filter-card">
      <template #extra><FilterOutlined /></template>

      <Row :gutter="16">
        <Col :span="6">
          <Input
              v-model:value="state.searchFilters.name"
              placeholder="输入用例名称或描述"
              allow-clear
              @pressEnter="applyFilters"
          />
        </Col>
        <Col :span="6">
          <Select
              v-model:value="state.searchFilters.project"
              placeholder="所属项目"
              allow-clear
              style="width: 100%"
          >
            <Select.Option value="">全部项目</Select.Option>
            <Select.Option value="电商平台">电商平台</Select.Option>
            <Select.Option value="API网关">API网关</Select.Option>
            <Select.Option value="用户中心">用户中心</Select.Option>
            <Select.Option value="支付系统">支付系统</Select.Option>
            <Select.Option value="搜索引擎">搜索引擎</Select.Option>
          </Select>
        </Col>
        <Col :span="6">
          <Select
              v-model:value="state.searchFilters.type"
              placeholder="用例类型"
              allow-clear
              style="width: 100%"
          >
            <Select.Option value="">全部类型</Select.Option>
            <Select.Option value="http">HTTP/HTTPS</Select.Option>
            <Select.Option value="websocket">WebSocket</Select.Option>
            <Select.Option value="grpc">gRPC</Select.Option>
            <Select.Option value="custom">自定义脚本</Select.Option>
          </Select>
        </Col>
        <Col :span="6">
          <Select
              v-model:value="state.searchFilters.status"
              placeholder="用例状态"
              allow-clear
              style="width: 100%"
          >
            <Select.Option value="">全部状态</Select.Option>
            <Select.Option value="active">启用中</Select.Option>
            <Select.Option value="inactive">已停用</Select.Option>
            <Select.Option value="deprecated">已废弃</Select.Option>
          </Select>
        </Col>
      </Row>

      <Divider />

      <Row justify="space-between">
        <Col>
          <Button @click="resetFilters">
            <template #icon><RedoOutlined /></template>
            重置筛选条件
          </Button>
        </Col>
        <Col>
          <Button type="primary" @click="applyFilters">
            <template #icon><SearchOutlined /></template>
            查询用例
          </Button>
        </Col>
      </Row>
    </ACard>

    <!-- 批量操作栏 -->
    <ACard v-if="state.selectedTestCaseIds.length > 0" class="batch-actions-card">
      <div class="batch-content">
        <Checkbox v-model:checked="state.isAllSelected" @change="toggleSelectAll">
          全选
        </Checkbox>

        <div class="batch-buttons">
          <Button @click="batchEnableTestCases">
            <template #icon><CheckCircleOutlined /></template>
            启用
          </Button>
          <Button @click="batchDisableTestCases">
            <template #icon><StopOutlined /></template>
            停用
          </Button>
          <Button @click="batchExportTestCases">
            <template #icon><DownloadOutlined /></template>
            导出
          </Button>
          <Button danger @click="batchDeleteTestCases">
            <template #icon><DeleteOutlined /></template>
            删除
          </Button>
        </div>

        <div class="selected-count">
          已选择 <span>{{ state.selectedTestCaseIds.length }}</span> 个用例
        </div>
      </div>
    </ACard>

    <!-- 用例展示区域 -->
    <div v-if="state.viewMode === 'card'">
      <!-- 卡片视图 -->
      <Row :gutter="[16, 16]" v-if="paginatedTestCases.length > 0">
        <Col :span="8" v-for="testcase in paginatedTestCases" :key="testcase.id">
          <ACard class="testcase-card" hoverable>
            <template #title>
              <div class="testcase-card-header">
                <h3 class="testcase-name">{{ testcase.name }}</h3>
                <div class="testcase-id">{{ testcase.id }}</div>
              </div>
            </template>

            <template #extra>
              <Tag :color="statusMap[testcase.status].color">
                {{ statusMap[testcase.status].text }}
              </Tag>
            </template>

            <div class="testcase-meta">
              <div class="meta-item">
                <span class="meta-label">所属项目</span>
                <div class="meta-value">{{ testcase.project }}</div>
              </div>

              <div class="meta-item">
                <span class="meta-label">类型</span>
                <div class="meta-value">
                  <Tag :color="typeMap[testcase.type].color" size="small">
                    {{ typeMap[testcase.type].text }}
                  </Tag>
                </div>
              </div>

              <div class="meta-item">
                <span class="meta-label">请求方法</span>
                <div class="meta-value">
                  <Tag :color="methodMap[testcase.method]?.color || 'default'" size="small">
                    {{ testcase.method }}
                  </Tag>
                </div>
              </div>
            </div>

            <div class="testcase-description">
              {{ truncateText(testcase.description, 80) }}
            </div>

            <div class="testcase-url">
              <span class="url-label">URL:</span>
              <span class="url-value">{{ truncateText(testcase.url || '自定义脚本', 50) }}</span>
            </div>

            <div class="testcase-footer">
              <div class="create-time">
                <span class="time-label">创建时间:</span>
                <span class="time-value">{{ testcase.createdAt.split(' ')[0] }}</span>
              </div>
              <div class="update-time">
                <span class="time-label">最后更新:</span>
                <span class="time-value">{{ testcase.updatedAt.split(' ')[0] }}</span>
              </div>
            </div>

            <template #actions>
              <Tooltip title="预览">
                <Button type="link" @click="previewTestCase(testcase)">
                  <template #icon><EyeOutlined /></template>
                </Button>
              </Tooltip>
              <Tooltip title="编辑">
                <Button type="link" @click="showEditModal(testcase.id)">
                  <template #icon><EditOutlined /></template>
                </Button>
              </Tooltip>
              <Tooltip title="复制">
                <Button type="link" @click="copyTestCase(testcase)">
                  <template #icon><CopyOutlined /></template>
                </Button>
              </Tooltip>
              <Tooltip title="删除">
                <Button type="link" danger @click="deleteTestCase(testcase.id)">
                  <template #icon><DeleteOutlined /></template>
                </Button>
              </Tooltip>
            </template>
          </ACard>
        </Col>
      </Row>

      <!-- 卡片视图空状态 -->
      <div v-if="paginatedTestCases.length === 0" class="empty-state">
        <div class="empty-icon">
          <ApiOutlined />
        </div>
        <h3>暂无用例数据</h3>
        <p>当前没有找到符合筛选条件的用例，请尝试调整筛选条件或创建新的测试用例。</p>
        <Button type="primary" @click="showAddModal">
          <template #icon><PlusOutlined /></template>
          新增用例
        </Button>
      </div>
    </div>

    <!-- 表格视图 -->
    <div v-else>
      <ACard>
        <Table
            :columns="columns"
            :data-source="paginatedTestCases"
            :pagination="false"
            :row-key="record => record.id"
            :row-selection="rowSelection"
            :scroll="{ x: 1300 }"
        >
          <template #bodyCell="{ column, record }">
            <!-- 用例类型 -->
            <template v-if="column.key === 'type'">
              <Tag :color="typeMap[record.type].color">
                {{ typeMap[record.type].text }}
              </Tag>
            </template>

            <!-- 请求方法 -->
            <template v-if="column.key === 'method'">
              <Tag :color="methodMap[record.method]?.color || 'default'">
                {{ record.method }}
              </Tag>
            </template>

            <!-- 请求URL/描述 -->
            <template v-if="column.key === 'url'">
              <Tooltip :title="record.url || record.description" placement="topLeft">
                <span class="testcase-description">
                  {{ truncateText(record.url || record.description, 50) }}
                </span>
              </Tooltip>
            </template>

            <!-- 状态 -->
            <template v-if="column.key === 'status'">
              <Tag :color="statusMap[record.status].color">
                {{ statusMap[record.status].text }}
              </Tag>
            </template>

            <!-- 操作 -->
            <template v-if="column.key === 'actions'">
              <Space size="small">
                <Tooltip title="预览">
                  <Button type="link" size="small" @click="previewTestCase(record)">
                    <EyeOutlined />
                  </Button>
                </Tooltip>
                <Tooltip title="编辑">
                  <Button type="link" size="small" @click="showEditModal(record.id)">
                    <EditOutlined />
                  </Button>
                </Tooltip>
                <Tooltip title="复制">
                  <Button type="link" size="small" @click="copyTestCase(record)">
                    <CopyOutlined />
                  </Button>
                </Tooltip>
                <Tooltip title="删除">
                  <Button type="link" size="small" danger @click="deleteTestCase(record.id)">
                    <DeleteOutlined />
                  </Button>
                </Tooltip>
              </Space>
            </template>
          </template>

          <template #emptyText>
            <div class="empty-state">
              <div class="empty-icon">
                <ApiOutlined />
              </div>
              <h3>暂无用例数据</h3>
              <p>当前没有找到符合筛选条件的用例，请尝试调整筛选条件或创建新的测试用例。</p>
              <Button type="primary" @click="showAddModal">
                <template #icon><PlusOutlined /></template>
                新增用例
              </Button>
            </div>
          </template>
        </Table>
      </ACard>
    </div>

    <!-- 分页 -->
    <div class="pagination-container" v-if="state.filteredTestCases.length > 0">
      <Pagination
          v-model:current="state.currentPage"
          v-model:pageSize="state.pageSize"
          :total="state.filteredTestCases.length"
          show-quick-jumper
          show-size-changer
          :show-total="(total: number) => `共 ${total} 条`"
      />
    </div>

    <!-- 新增/编辑用例模态框 -->
    <Modal
        v-model:visible="state.modalVisible"
        :title="state.modalTitle"
        width="800px"
        :mask-closable="false"
        @ok="handleModalOk"
        @cancel="handleModalCancel"
    >
      <Tabs v-model:activeKey="state.activeTab" @change="handleTabChange">
        <TabPane key="basic" tab="基础信息">
          <Form layout="vertical">
            <Form.Item label="用例名称" required>
              <Input
                  v-model:value="state.formData.name"
                  placeholder="例如：用户登录接口"
              />
            </Form.Item>

            <Row :gutter="16">
              <Col :span="12">
                <Form.Item label="所属项目" required>
                  <Select v-model:value="state.formData.project" placeholder="请选择项目">
                    <Select.Option value="电商平台">电商平台</Select.Option>
                    <Select.Option value="API网关">API网关</Select.Option>
                    <Select.Option value="用户中心">用户中心</Select.Option>
                    <Select.Option value="支付系统">支付系统</Select.Option>
                    <Select.Option value="搜索引擎">搜索引擎</Select.Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col :span="12">
                <Form.Item label="用例状态">
                  <Select v-model:value="state.formData.status">
                    <Select.Option value="active">启用中</Select.Option>
                    <Select.Option value="inactive">已停用</Select.Option>
                    <Select.Option value="deprecated">已废弃</Select.Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>

            <Row :gutter="16">
              <Col :span="12">
                <Form.Item label="用例类型">
                  <Select v-model:value="state.formData.type" @change="handleTypeChange">
                    <Select.Option value="http">HTTP/HTTPS</Select.Option>
                    <Select.Option value="websocket">WebSocket</Select.Option>
                    <Select.Option value="grpc">gRPC</Select.Option>
                    <Select.Option value="custom">自定义脚本</Select.Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col :span="12" v-if="state.formData.type === 'http'">
                <Form.Item label="请求方法">
                  <Select v-model:value="state.formData.method">
                    <Select.Option value="GET">GET</Select.Option>
                    <Select.Option value="POST">POST</Select.Option>
                    <Select.Option value="PUT">PUT</Select.Option>
                    <Select.Option value="DELETE">DELETE</Select.Option>
                    <Select.Option value="PATCH">PATCH</Select.Option>
                    <Select.Option value="HEAD">HEAD</Select.Option>
                    <Select.Option value="OPTIONS">OPTIONS</Select.Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>

            <Form.Item label="用例描述">
              <Input.TextArea
                  v-model:value="state.formData.description"
                  placeholder="描述此用例的测试目的、业务场景和注意事项..."
                  :rows="3"
              />
            </Form.Item>
          </Form>
        </TabPane>

        <TabPane key="request" tab="请求配置" :disabled="state.formData.type === 'custom'">
          <Form layout="vertical" v-if="state.formData.type !== 'custom'">
            <Form.Item label="请求URL" :required="state.formData.type === 'http'">
              <Input
                  v-model:value="state.formData.url"
                  placeholder="例如：https://api.example.com/v1/login"
              />
            </Form.Item>

            <Form.Item label="请求参数">
              <Input.TextArea
                  v-model:value="state.formData.params"
                  placeholder='// JSON 格式
{
  "username": "test_user",
  "password": "password123"
}

// 或 Form 格式
username=test_user&password=password123'
                  :rows="5"
                  class="code-textarea"
              />
            </Form.Item>

            <Form.Item label="请求体 (Body)">
              <Input.TextArea
                  v-model:value="state.formData.body"
                  placeholder='// JSON 示例
{
  "username": "test_user",
  "password": "password123",
  "remember": true
}'
                  :rows="5"
                  class="code-textarea"
              />
            </Form.Item>
          </Form>
          <div v-else style="text-align: center; padding: 40px; color: #999;">
            <ApiOutlined style="font-size: 48px; margin-bottom: 16px;" />
            <p>自定义脚本类型无需配置请求信息</p>
          </div>
        </TabPane>

        <TabPane key="headers" tab="请求头" :disabled="state.formData.type === 'custom'">
          <Form layout="vertical" v-if="state.formData.type !== 'custom'">
            <Table
                :columns="headerColumns"
                :data-source="state.formData.headers"
                :pagination="false"
                size="small"
            >
              <template #bodyCell="{ column, index }">
                <template v-if="column.key === 'name'">
                  <Input
                      v-model:value="state.formData.headers[index].name"
                      placeholder="Header名称"
                      size="small"
                  />
                </template>
                <template v-if="column.key === 'value'">
                  <Input
                      v-model:value="state.formData.headers[index].value"
                      placeholder="Header值"
                      size="small"
                  />
                </template>
                <template v-if="column.key === 'action'">
                  <Button type="link" danger size="small" @click="removeHeader(index)">
                    <DeleteOutlined />
                  </Button>
                </template>
              </template>
            </Table>
            <Button type="dashed" @click="addHeader" style="width: 100%; margin-top: 16px;">
              <PlusOutlined />
              添加请求头
            </Button>
          </Form>
          <div v-else style="text-align: center; padding: 40px; color: #999;">
            <ApiOutlined style="font-size: 48px; margin-bottom: 16px;" />
            <p>自定义脚本类型无需配置请求头</p>
          </div>
        </TabPane>

        <TabPane key="advanced" tab="高级设置">
          <Form layout="vertical">
            <Form.Item label="断言脚本">
              <Input.TextArea
                  v-model:value="state.formData.assertion"
                  placeholder='// JavaScript 断言脚本
// response 为响应对象，包含 status、headers、body 等属性

// 示例：检查响应状态码
if (response.status !== 200) {
    throw new Error(`Expected status 200, got ${response.status}`);
}

// 示例：检查响应体包含特定字段
const data = JSON.parse(response.body);
if (!data.success) {
    throw new Error("Request failed: " + data.message);
}'
                  :rows="6"
                  class="code-textarea"
              />
            </Form.Item>

            <Row :gutter="16">
              <Col :span="12">
                <Form.Item label="期望状态码">
                  <Input
                      v-model:value="state.formData.expectedStatus"
                      placeholder="例如：200, 201"
                  />
                </Form.Item>
              </Col>
              <Col :span="12">
                <Form.Item label="期望响应时间 (ms)">
                  <Input
                      v-model:value="state.formData.expectedResponseTime"
                      type="number"
                      placeholder="例如：1000"
                  />
                </Form.Item>
              </Col>
            </Row>

            <Form.Item label="预置脚本 (Pre-request Script)">
              <Input.TextArea
                  v-model:value="state.formData.preRequestScript"
                  placeholder='// 请求前执行的脚本，用于生成动态参数
// 例如：生成时间戳、签名等

// 生成当前时间戳
const timestamp = Date.now();

// 生成随机字符串
function randomString(length) {
    const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
    let result = "";
    for (let i = 0; i < length; i++) {
        result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
}

// 设置动态参数
const nonce = randomString(8);'
                  :rows="5"
                  class="code-textarea"
              />
            </Form.Item>
          </Form>
        </TabPane>
      </Tabs>
    </Modal>

    <!-- 预览模态框 -->
    <Modal
        v-model:visible="state.previewVisible"
        title="用例详情预览"
        width="800px"
        :footer="null"
    >
      <Tabs v-model:activeKey="state.previewTab">
        <TabPane key="info" tab="基本信息">
          <Descriptions :column="2" bordered>
            <DescriptionsItem label="用例ID">{{ state.previewData.id }}</DescriptionsItem>
            <DescriptionsItem label="用例名称">{{ state.previewData.name }}</DescriptionsItem>
            <DescriptionsItem label="所属项目">{{ state.previewData.project }}</DescriptionsItem>
            <DescriptionsItem label="用例类型">
              <Tag :color="typeMap[state.previewData.type].color">
                {{ typeMap[state.previewData.type].text }}
              </Tag>
            </DescriptionsItem>
            <DescriptionsItem label="请求方法">
              <Tag :color="methodMap[state.previewData.method]?.color || 'default'">
                {{ state.previewData.method }}
              </Tag>
            </DescriptionsItem>
            <DescriptionsItem label="用例状态">
              <Tag :color="statusMap[state.previewData.status].color">
                {{ statusMap[state.previewData.status].text }}
              </Tag>
            </DescriptionsItem>
            <DescriptionsItem label="创建时间">{{ state.previewData.createdAt }}</DescriptionsItem>
            <DescriptionsItem label="最后更新">{{ state.previewData.updatedAt }}</DescriptionsItem>
            <DescriptionsItem label="用例描述" :span="2">
              {{ state.previewData.description }}
            </DescriptionsItem>
          </Descriptions>
        </TabPane>

        <TabPane key="request" tab="请求详情">
          <div style="margin-bottom: 16px">
            <div style="font-weight: 500; margin-bottom: 8px; color: rgba(0, 0, 0, 0.85);">
              请求URL
            </div>
            <pre class="preview-code">{{ state.previewData.url || '自定义脚本' }}</pre>
          </div>

          <div style="margin-bottom: 16px">
            <div style="font-weight: 500; margin-bottom: 8px; color: rgba(0, 0, 0, 0.85);">
              请求头
            </div>
            <pre class="preview-code" v-if="state.previewData.headers && state.previewData.headers.length > 0">
              {{ formatHeaders(state.previewData.headers) }}
            </pre>
            <div v-else style="color: #999; padding: 8px;">无</div>
          </div>

          <div>
            <div style="font-weight: 500; margin-bottom: 8px; color: rgba(0, 0, 0, 0.85);">
              请求体
            </div>
            <pre class="preview-code">{{ state.previewData.body || '无' }}</pre>
          </div>
        </TabPane>

        <TabPane key="script" tab="脚本代码">
          <div style="margin-bottom: 16px">
            <div style="font-weight: 500; margin-bottom: 8px; color: rgba(0, 0, 0, 0.85);">
              断言脚本
            </div>
            <pre class="preview-code">{{ state.previewData.assertion || '无' }}</pre>
          </div>

          <div>
            <div style="font-weight: 500; margin-bottom: 8px; color: rgba(0, 0, 0, 0.85);">
              预置脚本
            </div>
            <pre class="preview-code">{{ state.previewData.preRequestScript || '无' }}</pre>
          </div>
        </TabPane>
      </Tabs>
    </Modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, h } from 'vue'
import {
  Card as ACard,
  Row,
  Col,
  Button,
  Input,
  Select,
  Table,
  Tag,
  Statistic,
  Modal,
  Form,
  Checkbox,
  Pagination,
  Space,
  Divider,
  Descriptions,
  DescriptionsItem,
  Tooltip,
  Tabs,
  message
} from 'ant-design-vue'
import {
  PlusOutlined,
  SearchOutlined,
  RedoOutlined,
  EyeOutlined,
  EditOutlined,
  DeleteOutlined,
  CopyOutlined,
  AppstoreOutlined,
  UnorderedListOutlined,
  ProjectOutlined,
  PlayCircleOutlined,
  ApiOutlined,
  ScheduleOutlined,
  FilterOutlined,
  CheckCircleOutlined,
  StopOutlined,
  DownloadOutlined
} from '@ant-design/icons-vue'

const TabPane = Tabs.TabPane

// 模拟用例数据
const mockTestCases = [
  {
    id: "TC-001",
    name: "用户登录接口",
    project: "用户中心",
    type: "http",
    method: "POST",
    url: "https://api.example.com/v1/login",
    description: "用户登录接口测试，验证用户名密码认证流程，包含token生成和返回。",
    status: "active",
    headers: [
      { name: "Content-Type", value: "application/json" },
      { name: "User-Agent", value: "PerfLocust/1.0" }
    ],
    body: '{"username": "test_user", "password": "password123"}',
    assertion: 'if (response.status !== 200) { throw new Error("登录失败"); }',
    preRequestScript: 'const timestamp = Date.now();',
    expectedStatus: "200",
    expectedResponseTime: 1000,
    createdAt: "2024-01-20 10:30:00",
    updatedAt: "2024-01-20 14:15:00"
  },
  // ... 添加更多测试用例数据
]

// 响应式数据
const state = reactive({
  testcases: [...mockTestCases],
  filteredTestCases: [...mockTestCases],
  currentPage: 1,
  pageSize: 8,
  viewMode: 'table', // 'card' 或 'table'
  searchFilters: {
    name: '',
    project: '',
    type: '',
    status: ''
  },
  selectedTestCaseIds: [] as string[],
  isAllSelected: false,
  modalVisible: false,
  modalTitle: '创建新用例',
  isEditing: false,
  currentEditId: null as string | null,
  activeTab: 'basic',
  previewVisible: false,
  previewTab: 'info',
  formData: {
    id: '',
    name: '',
    project: '',
    type: 'http',
    status: 'active',
    description: '',
    method: 'POST',
    url: '',
    params: '',
    body: '',
    headers: [
      { name: 'User-Agent', value: 'PerfLocust/1.0' },
      { name: 'Content-Type', value: 'application/json' }
    ] as Array<{ name: string, value: string }>,
    assertion: '',
    expectedStatus: '',
    expectedResponseTime: null as number | null,
    preRequestScript: ''
  },
  previewData: {
    id: '',
    name: '',
    project: '',
    type: '',
    method: '',
    status: '',
    description: '',
    url: '',
    headers: [] as Array<{ name: string, value: string }>,
    body: '',
    assertion: '',
    preRequestScript: '',
    createdAt: '',
    updatedAt: ''
  }
})

// 计算属性
const statistics = computed(() => {
  const total = state.testcases.length
  const active = state.testcases.filter(t => t.status === 'active').length
  const httpCount = state.testcases.filter(t => t.type === 'http').length
  const projects = new Set(state.testcases.map(t => t.project)).size
  const uniqueProjects = projects

  return { total, active, httpCount, projects, uniqueProjects }
})

const paginatedTestCases = computed(() => {
  const start = (state.currentPage - 1) * state.pageSize
  const end = start + state.pageSize
  return state.filteredTestCases.slice(start, end)
})

const rowSelection = computed(() => ({
  selectedRowKeys: state.selectedTestCaseIds,
  onChange: (selectedRowKeys: string[]) => {
    state.selectedTestCaseIds = selectedRowKeys
    state.isAllSelected = selectedRowKeys.length === paginatedTestCases.value.length && paginatedTestCases.value.length > 0
  }
}))

// 映射表
const statusMap = {
  active: { text: '启用中', color: 'green' },
  inactive: { text: '已停用', color: 'gray' },
  deprecated: { text: '已废弃', color: 'orange' }
}

const typeMap = {
  http: { text: 'HTTP', color: 'blue' },
  websocket: { text: 'WebSocket', color: 'purple' },
  grpc: { text: 'gRPC', color: 'orange' },
  custom: { text: '自定义', color: 'cyan' }
}

const methodMap: Record<string, { color: string }> = {
  GET: { color: 'green' },
  POST: { color: 'blue' },
  PUT: { color: 'orange' },
  DELETE: { color: 'red' },
  PATCH: { color: 'purple' },
  HEAD: { color: 'cyan' },
  OPTIONS: { color: 'geekblue' }
}

// 表格列定义
const columns = [
  {
    title: '用例ID',
    dataIndex: 'id',
    key: 'id',
    width: 100
  },
  {
    title: '用例名称',
    dataIndex: 'name',
    key: 'name',
    width: 180,
    customRender: ({ text }: { text: string }) => {
      return h('div', { style: { fontWeight: 'bold' } }, text)
    }
  },
  {
    title: '所属项目',
    dataIndex: 'project',
    key: 'project',
    width: 120
  },
  {
    title: '类型',
    key: 'type',
    width: 100
  },
  {
    title: '方法',
    key: 'method',
    width: 80
  },
  {
    title: '请求URL/描述',
    key: 'url',
    width: 200
  },
  {
    title: '状态',
    key: 'status',
    width: 100
  },
  {
    title: '创建时间',
    dataIndex: 'createdAt',
    key: 'createdAt',
    width: 140,
    customRender: ({ text }: { text: string }) => text.split(' ')[0]
  },
  {
    title: '操作',
    key: 'actions',
    width: 180,
    fixed: 'right'
  }
]

// 请求头表格列
const headerColumns = [
  {
    title: 'Header 名称',
    key: 'name',
    width: '40%'
  },
  {
    title: 'Header 值',
    key: 'value',
    width: '50%'
  },
  {
    title: '操作',
    key: 'action',
    width: '10%'
  }
]

// 方法
const applyFilters = () => {
  const { name, project, type, status } = state.searchFilters

  state.filteredTestCases = state.testcases.filter(testcase => {
    // 名称/描述筛选
    if (name &&
        !testcase.name.toLowerCase().includes(name.toLowerCase()) &&
        !testcase.description.toLowerCase().includes(name.toLowerCase())) {
      return false
    }

    // 项目筛选
    if (project && testcase.project !== project) {
      return false
    }

    // 类型筛选
    if (type && testcase.type !== type) {
      return false
    }

    // 状态筛选
    if (status && testcase.status !== status) {
      return false
    }

    return true
  })

  state.currentPage = 1
  state.selectedTestCaseIds = []
  state.isAllSelected = false
}

const resetFilters = () => {
  state.searchFilters = {
    name: '',
    project: '',
    type: '',
    status: ''
  }
  state.filteredTestCases = [...state.testcases]
  state.currentPage = 1
  state.selectedTestCaseIds = []
  state.isAllSelected = false
}

const switchView = (mode: string) => {
  state.viewMode = mode
}

const showAddModal = () => {
  state.modalTitle = '创建新用例'
  state.isEditing = false
  state.currentEditId = null
  state.activeTab = 'basic'
  state.formData = {
    id: '',
    name: '',
    project: '',
    type: 'http',
    status: 'active',
    description: '',
    method: 'POST',
    url: '',
    params: '',
    body: '',
    headers: [
      { name: 'User-Agent', value: 'PerfLocust/1.0' },
      { name: 'Content-Type', value: 'application/json' }
    ],
    assertion: '',
    expectedStatus: '',
    expectedResponseTime: null,
    preRequestScript: ''
  }
  state.modalVisible = true
}

const showEditModal = (testcaseId: string) => {
  const testcase = state.testcases.find(t => t.id === testcaseId)
  if (!testcase) return

  state.modalTitle = '编辑用例'
  state.isEditing = true
  state.currentEditId = testcaseId
  state.activeTab = 'basic'
  state.formData = {
    id: testcase.id,
    name: testcase.name,
    project: testcase.project,
    type: testcase.type,
    status: testcase.status,
    description: testcase.description,
    method: testcase.method,
    url: testcase.url,
    params: testcase.params || '',
    body: testcase.body || '',
    headers: Array.isArray(testcase.headers) ? [...testcase.headers] : [],
    assertion: testcase.assertion || '',
    expectedStatus: testcase.expectedStatus || '',
    expectedResponseTime: testcase.expectedResponseTime || null,
    preRequestScript: testcase.preRequestScript || ''
  }
  state.modalVisible = true
}

const handleModalOk = () => {
  const { name, project, type, method, url } = state.formData

  // 验证
  if (!name.trim()) {
    message.error('请输入用例名称')
    return
  }

  if (!project) {
    message.error('请选择所属项目')
    return
  }

  if (type === 'http' && !url.trim()) {
    message.error('请输入请求URL')
    return
  }

  if (state.isEditing && state.currentEditId) {
    // 编辑用例
    const index = state.testcases.findIndex(t => t.id === state.currentEditId)
    if (index !== -1) {
      state.testcases[index] = {
        ...state.testcases[index],
        ...state.formData,
        headers: [...state.formData.headers],
        updatedAt: new Date().toLocaleString('zh-CN')
      }
      message.success(`用例 ${name} 已更新`)
    }
  } else {
    // 新增用例
    const newId = `TC-${String(state.testcases.length + 1).padStart(3, '0')}`
    const now = new Date().toLocaleString('zh-CN')

    const newTestCase = {
      ...state.formData,
      id: newId,
      headers: [...state.formData.headers],
      createdAt: now,
      updatedAt: now
    }

    state.testcases.unshift(newTestCase)
    message.success(`用例 ${name} 已创建`)
  }

  state.modalVisible = false
  resetFilters()
}

const handleModalCancel = () => {
  state.modalVisible = false
}

const handleTabChange = (key: string) => {
  state.activeTab = key
}

const handleTypeChange = (value: string) => {
  if (value !== 'http') {
    state.formData.method = ''
  } else {
    state.formData.method = 'POST'
  }
}

const addHeader = () => {
  state.formData.headers.push({ name: '', value: '' })
}

const removeHeader = (index: number) => {
  state.formData.headers.splice(index, 1)
}

const previewTestCase = (testcase: any) => {
  state.previewData = {
    id: testcase.id,
    name: testcase.name,
    project: testcase.project,
    type: testcase.type,
    method: testcase.method,
    status: testcase.status,
    description: testcase.description,
    url: testcase.url,
    headers: Array.isArray(testcase.headers) ? [...testcase.headers] : [],
    body: testcase.body || '',
    assertion: testcase.assertion || '',
    preRequestScript: testcase.preRequestScript || '',
    createdAt: testcase.createdAt,
    updatedAt: testcase.updatedAt
  }
  state.previewTab = 'info'
  state.previewVisible = true
}

const copyTestCase = (testcase: any) => {
  Modal.confirm({
    title: '确认复制',
    content: `确定要复制用例 "${testcase.name}" 吗？`,
    onOk() {
      const newId = `TC-${String(state.testcases.length + 1).padStart(3, '0')}`
      const now = new Date().toLocaleString('zh-CN')

      const copiedTestCase = {
        ...testcase,
        id: newId,
        name: `${testcase.name} (副本)`,
        headers: Array.isArray(testcase.headers) ? [...testcase.headers] : [],
        createdAt: now,
        updatedAt: now
      }

      state.testcases.unshift(copiedTestCase)
      resetFilters()
      message.success(`用例 "${testcase.name}" 已复制为 "${copiedTestCase.name}"`)
    }
  })
}

const deleteTestCase = (testcaseId: string) => {
  const testcase = state.testcases.find(t => t.id === testcaseId)
  if (!testcase) return

  Modal.confirm({
    title: '确认删除',
    content: `确定要删除用例 "${testcase.name}" 吗？此操作不可恢复。`,
    okType: 'danger',
    onOk() {
      const index = state.testcases.findIndex(t => t.id === testcaseId)
      if (index !== -1) {
        state.testcases.splice(index, 1)
        resetFilters()
        state.selectedTestCaseIds = state.selectedTestCaseIds.filter(id => id !== testcaseId)
        message.success(`用例 "${testcase.name}" 已删除`)
      }
    }
  })
}

const toggleSelectAll = (e: any) => {
  if (e.target.checked) {
    state.selectedTestCaseIds = paginatedTestCases.value.map(t => t.id)
  } else {
    state.selectedTestCaseIds = []
  }
  state.isAllSelected = e.target.checked
}

const batchEnableTestCases = () => {
  if (state.selectedTestCaseIds.length === 0) return

  Modal.confirm({
    title: '确认启用',
    content: `确定要启用选中的 ${state.selectedTestCaseIds.length} 个用例吗？`,
    onOk() {
      state.testcases.forEach(testcase => {
        if (state.selectedTestCaseIds.includes(testcase.id)) {
          testcase.status = 'active'
          testcase.updatedAt = new Date().toLocaleString('zh-CN')
        }
      })

      message.success(`已启用 ${state.selectedTestCaseIds.length} 个用例`)
      state.selectedTestCaseIds = []
      state.isAllSelected = false
      resetFilters()
    }
  })
}

const batchDisableTestCases = () => {
  if (state.selectedTestCaseIds.length === 0) return

  Modal.confirm({
    title: '确认停用',
    content: `确定要停用选中的 ${state.selectedTestCaseIds.length} 个用例吗？`,
    onOk() {
      state.testcases.forEach(testcase => {
        if (state.selectedTestCaseIds.includes(testcase.id)) {
          testcase.status = 'inactive'
          testcase.updatedAt = new Date().toLocaleString('zh-CN')
        }
      })

      message.success(`已停用 ${state.selectedTestCaseIds.length} 个用例`)
      state.selectedTestCaseIds = []
      state.isAllSelected = false
      resetFilters()
    }
  })
}

const batchExportTestCases = () => {
  if (state.selectedTestCaseIds.length === 0) return

  const exportData = state.testcases.filter(testcase =>
      state.selectedTestCaseIds.includes(testcase.id)
  )

  message.info(`已准备导出 ${state.selectedTestCaseIds.length} 个用例数据 - 在实际系统中会生成下载文件`)
  // 在实际系统中这里会生成JSON或CSV文件供下载
}

const batchDeleteTestCases = () => {
  if (state.selectedTestCaseIds.length === 0) return

  Modal.confirm({
    title: '确认删除',
    content: `确定要删除选中的 ${state.selectedTestCaseIds.length} 个用例吗？此操作不可恢复。`,
    okType: 'danger',
    onOk() {
      // 从后往前删除，避免索引问题
      for (let i = state.testcases.length - 1; i >= 0; i--) {
        if (state.selectedTestCaseIds.includes(state.testcases[i].id)) {
          state.testcases.splice(i, 1)
        }
      }

      message.success(`已删除 ${state.selectedTestCaseIds.length} 个用例`)
      state.selectedTestCaseIds = []
      state.isAllSelected = false
      resetFilters()
    }
  })
}

// 工具函数
const truncateText = (text: string, maxLength: number) => {
  if (!text) return ''
  return text.length > maxLength ? text.substring(0, maxLength) + '...' : text
}

const formatHeaders = (headers: Array<{ name: string, value: string }>) => {
  if (!headers || headers.length === 0) return '无'
  return headers.map(h => `${h.name}: ${h.value}`).join('\n')
}

onMounted(() => {
  // 初始化数据
  resetFilters()
})
</script>

<style scoped>
.app-container {
  padding: 10px;
  min-height: calc(100vh - 64px);
  box-sizing: border-box; /* 确保padding被包含在高度内 */
  overflow-y: auto; /* 只在需要时显示滚动条 */

}

.page-header {
  display: flex;
  justify-content: space-between;
  //align-items: flex-start;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 16px;
}

.page-title-section {
  flex: 1;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
  color: rgba(0, 0, 0, 0.85);
}

.page-subtitle {
  font-size: 14px;
  color: rgba(0, 0, 0, 0.45);
  margin: 8px 0 0 0;
}

.stats-row {
  margin-bottom: 20px;
}

.filter-card {
  margin-bottom: 20px;
}

.batch-actions-card {
  margin-bottom: 20px;
  background-color: #fafafa;
}

.batch-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.batch-buttons {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.selected-count {
  margin-left: auto;
  font-size: 14px;
  color: rgba(0, 0, 0, 0.45);
}

.selected-count span {
  color: #1890ff;
  font-weight: 600;
}

.testcase-card {
  height: 100%;
  margin-bottom: 20px;
}

.testcase-card-header {
  margin-bottom: 12px;
}

.testcase-name {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 4px 0;
  color: rgba(0, 0, 0, 0.85);
}

.testcase-id {
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
  margin-bottom: 8px;
}

.testcase-meta {
  background-color: #fafafa;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 12px;
}

.meta-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.meta-item:last-child {
  margin-bottom: 0;
}

.meta-label {
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
}

.meta-value {
  font-size: 14px;
  color: rgba(0, 0, 0, 0.85);
  font-weight: 500;
}

.testcase-description {
  font-size: 14px;
  color: rgba(0, 0, 0, 0.65);
  line-height: 1.5;
  margin-bottom: 12px;
}

.testcase-url {
  background-color: #fafafa;
  border-radius: 4px;
  padding: 8px 12px;
  margin-bottom: 12px;
  font-size: 13px;
}

.url-label {
  color: rgba(0, 0, 0, 0.45);
  margin-right: 8px;
}

.url-value {
  color: rgba(0, 0, 0, 0.85);
  font-family: 'Courier New', monospace;
  word-break: break-all;
}

.testcase-footer {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.create-time, .update-time {
  display: flex;
  flex-direction: column;
}

.time-label {
  margin-bottom: 2px;
}

.time-value {
  color: rgba(0, 0, 0, 0.65);
  font-weight: 500;
}

.empty-state {
  text-align: center;
  padding: 40px 0;
}

.empty-icon {
  font-size: 48px;
  color: rgba(0, 0, 0, 0.25);
  margin-bottom: 16px;
}

.empty-state h3 {
  font-size: 18px;
  color: rgba(0, 0, 0, 0.85);
  margin-bottom: 8px;
}

.empty-state p {
  color: rgba(0, 0, 0, 0.45);
  max-width: 400px;
  margin: 0 auto 16px;
}

.pagination-container {
  margin-top: 20px;
  text-align: right;
}

.code-textarea {
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
}

.preview-code {
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
  white-space: pre-wrap;
  background-color: #fafafa;
  color: rgba(0, 0, 0, 0.85);
  padding: 16px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 0;
  border: 1px solid #f0f0f0;
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
  }

  .stats-row .ant-col {
    margin-bottom: 16px;
  }

  .batch-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .selected-count {
    margin-left: 0;
    align-self: flex-end;
  }

  .testcase-card {
    margin-bottom: 16px;
  }
}
</style>