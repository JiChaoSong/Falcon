<template>
  <div class="login-container">
    <div class="container">
      <!-- 左侧品牌介绍区域 -->
      <div class="brand-section">
        <div class="brand-content">
          <div class="logo">
            <div class="logo-icon">
              <area-chart-outlined />
            </div>
            <div class="logo-text">PerfLocust</div>
          </div>

          <h1 class="brand-title">企业级性能压测平台</h1>
          <p class="brand-subtitle">一站式性能测试解决方案，为您的应用提供全面的压测管理、场景编排和结果分析</p>

          <div class="features">
            <div class="feature-item">
              <div class="feature-icon">
                <project-outlined />
              </div>
              <div class="feature-text">项目管理 - 压测项目创建、团队协作、资源配置</div>
            </div>

            <div class="feature-item">
              <div class="feature-icon">
                <unordered-list-outlined />
              </div>
              <div class="feature-text">用例管理 - 支持多种协议和复杂业务逻辑</div>
            </div>

            <div class="feature-item">
              <div class="feature-icon">
                <sliders-outlined />
              </div>
              <div class="feature-text">场景管理 - 用例编排、权重分配、场景模板</div>
            </div>

            <div class="feature-item">
              <div class="feature-icon">
                <play-circle-outlined />
              </div>
              <div class="feature-text">任务管理 - 压测任务创建、启停控制、状态查看</div>
            </div>


            <div class="feature-item">
              <div class="feature-icon">
                <line-chart-outlined />
              </div>
              <div class="feature-text">监控中心 - 压测实时统计、启停控制、指标查看</div>
            </div>
          </div>
        </div>

        <div class="platform-info">
          <p>当前版本: v2.5.0 </p>
        </div>
      </div>

      <!-- 右侧登录表单区域 -->
      <div class="login-section">
        <div class="login-header">
          <h2 class="login-title">欢迎回来</h2>
          <p class="login-subtitle">登录您的PerfLocust账户，开始管理压测任务</p>
        </div>

        <a-form
            :model="formState"
            name="login-form"
            autocomplete="off"
            @finish="onFinish"
            @finishFailed="onFinishFailed"
        >
          <a-form-item
              name="username"
              :rules="[{ required: true, message: '请输入用户名' }]"
          >
            <a-input
                v-model:value="formState.username"
                placeholder="请输入用户名"
                size="large"
            >
              <template #prefix>
                <user-outlined />
              </template>
            </a-input>
          </a-form-item>

          <a-form-item
              name="password"
              :rules="[{ required: true, message: '请输入密码' }]"
          >
            <a-input-password
                v-model:value="formState.password"
                placeholder="请输入密码"
                size="large"
            >
              <template #prefix>
                <lock-outlined />
              </template>
            </a-input-password>
          </a-form-item>

          <div class="form-options">
            <div class="remember-me">
              <a-checkbox v-model:checked="formState.remember">记住我</a-checkbox>
            </div>
            <a class="forgot-password" @click="handleForgotPassword">忘记密码？</a>
          </div>

          <a-form-item>
            <a-button
                type="primary"
                html-type="submit"
                size="large"
                :loading="loading"
                block
                class="login-btn"
            >
              登录
            </a-button>
          </a-form-item>

          <div class="divider" v-show="false">
            <span>或使用以下方式登录</span>
          </div>

          <div class="social-login" v-show="false">
            <a-button
                shape="circle"
                size="large"
                class="social-btn"
                @click="handleSocialLogin('github')"
            >
              <github-outlined />
            </a-button>
            <a-button
                shape="circle"
                size="large"
                class="social-btn"
                @click="handleSocialLogin('google')"
            >
              <google-circle-filled />
            </a-button>
            <a-button
                shape="circle"
                size="large"
                class="social-btn"
                @click="handleSocialLogin('microsoft')"
            >
              <windows-outlined />
            </a-button>
          </div>

          <div class="register-link" v-show="false">
            还没有账户？ <a @click="handleRegister">立即注册</a>
          </div>

          <div class="demo-credentials">
            <div class="demo-title">演示账户</div>
            <div class="demo-info">用户名: admin | 密码: perfdemo2024</div>
          </div>
        </a-form>
      </div>
    </div>
  </div>
</template>

<script  lang="ts">
import { defineComponent, reactive, ref } from 'vue'
import {
  AreaChartOutlined,
  UserOutlined,
  LockOutlined,
  ProjectOutlined,
  UnorderedListOutlined,
  SlidersOutlined,
  PlayCircleOutlined,
  LineChartOutlined,
  GithubOutlined,
  WindowsOutlined
} from '@ant-design/icons-vue'
import {
  Form as AForm,
  Input as AInput,
  InputPassword as AInputPassword,
  Button as AButton,
  Checkbox as ACheckbox,
  message
} from 'ant-design-vue'
import type { FormProps } from 'ant-design-vue'
import { useUserStore } from '@/store/modules/user'

// 自定义Google图标组件
const GoogleCircleFilled = {
  template: `
    <svg viewBox="64 64 896 896" focusable="false" data-icon="google-circle" width="1em" height="1em" fill="currentColor" aria-hidden="true">
      <path d="M512 64C264.6 64 64 264.6 64 512s200.6 448 448 448 448-200.6 448-448S759.4 64 512 64zm167 633.6C638.4 735 583 757 516.9 757c-95.7 0-178.5-54.9-218.8-134.9C281.5 589 272 551.6 272 512s9.5-77 26.1-110.1c40.3-80.1 123.1-135 218.8-135 66 0 121.4 24.3 163.9 63.8L610.6 401c-25.4-24.3-57.7-36.5-93.6-36.5-63.8 0-117.8 43.1-137.1 101-4.9 14.7-7.7 30.4-7.7 46.6s2.8 31.9 7.7 46.6c19.3 57.9 73.3 101 137.1 101 33 0 61-8.7 82.9-23.4 26-17.4 43.2-43.3 48.9-74H516.9v-94.8h230.7c2.9 16.1 4.4 32.8 4.4 50.1 0 74.7-26.7 137.4-73 180.1z"></path>
    </svg>
  `
}

interface FormState {
  username: string;
  password: string;
  remember: boolean;
}

export default defineComponent({
  name: 'LoginPage',
  components: {
    AreaChartOutlined,
    UserOutlined,
    LockOutlined,
    ProjectOutlined,
    UnorderedListOutlined,
    SlidersOutlined,
    PlayCircleOutlined,
    LineChartOutlined,
    GithubOutlined,
    WindowsOutlined,
    GoogleCircleFilled,
    AForm,
    AFormItem: AForm.Item,
    AInput,
    AInputPassword,
    AButton,
    ACheckbox
  },
  setup() {
    const loading = ref(false)
    const router = useRouter()

    const userStore = useUserStore()
    const formState = reactive<FormState>({
      username: 'admin',
      password: '123456',
      remember: false
    })

    const onFinish: FormProps['onFinish'] = async (values) => {
      loading.value = true

      try {
        await userStore.login({
          username: values.username as string,
          password: values.password as string,
        })
        message.success('登录成功')
        await router.push('/')
      } catch (error) {
        message.error('登录失败，请检查用户名和密码')
      } finally {
        loading.value = false
      }
    }

    const onFinishFailed: FormProps['onFinishFailed'] = (errorInfo) => {
      console.log('Failed:', errorInfo)
      message.error('用户名/密码不能为空')
    }

    const handleForgotPassword = () => {
      message.info('忘记密码功能正在开发中...')
    }

    const handleRegister = () => {
      message.info('注册功能正在开发中...')
    }

    const handleSocialLogin = (platform: string) => {
      message.info(`即将通过${platform}账号登录，该功能当前为演示状态`)
    }

    return {
      loading,
      formState,
      onFinish,
      onFinishFailed,
      handleForgotPassword,
      handleRegister,
      handleSocialLogin
    }
  }
})
</script>

<style scoped>
.login-container {
  background-color: #f5f7fa;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.container {
  display: flex;
  width: 100%;
  max-width: 1200px;
  box-shadow: 0 0 30px rgba(0, 0, 0, 0.05);
  border-radius: 8px;
  overflow: hidden;
  min-height: 70vh;
}

/* 左侧品牌介绍区域 */
.brand-section {
  flex: 1;
  background: linear-gradient(135deg, #1890ff 0%, #096dd9 100%);
  color: white;
  padding: 40px 40px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.brand-content {
  flex: 1;
}

.logo {
  display: flex;
  align-items: center;
  margin-bottom: 30px;
}

.logo-icon {
  font-size: 28px;
  margin-right: 12px;
  background: rgba(255, 255, 255, 0.2);
  width: 50px;
  height: 50px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-text {
  font-size: 28px;
  font-weight: 700;
  letter-spacing: 1px;
}

.brand-title {
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 20px;
  line-height: 1.3;
}

.brand-subtitle {
  font-size: 16px;
  opacity: 0.9;
  margin-bottom: 30px;
}

.features {
  margin-top: 40px;
}

.feature-item {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
}

.feature-icon {
  width: 36px;
  height: 36px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 15px;
}

.feature-text {
  font-size: 15px;
}

.platform-info {
  margin-top: 20px;
  font-size: 14px;
  opacity: 0.8;
  border-top: 1px solid rgba(255, 255, 255, 0.2);
  padding-top: 20px;
}

/* 右侧登录表单区域 */
.login-section {
  flex: 1;
  background-color: white;
  padding: 60px 50px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.login-header {
  margin-bottom: 40px;
}

.login-title {
  font-size: 28px;
  font-weight: 700;
  color: #1f2d3d;
  margin-bottom: 10px;
}

.login-subtitle {
  color: #6c757d;
  font-size: 15px;
}

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 25px;
  font-size: 14px;
}

.remember-me {
  display: flex;
  align-items: center;
}

.forgot-password {
  color: #1890ff;
  text-decoration: none;
  transition: color 0.3s;
  cursor: pointer;
}

.forgot-password:hover {
  color: #096dd9;
  text-decoration: underline;
}

.login-btn {
  height: 48px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 6px;
  background: linear-gradient(135deg, #1890ff 0%, #096dd9 100%);
  border: none;
  transition: all 0.3s;
  margin-bottom: 25px;
}

.login-btn:hover {
  background: linear-gradient(135deg, #096dd9 0%, #0050b3 100%);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.3);
}

.login-btn:active {
  transform: translateY(0);
}

.divider {
  text-align: center;
  position: relative;
  margin: 25px 0;
  color: #6c757d;
  font-size: 14px;
}

.divider::before {
  content: "";
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 1px;
  background-color: #dee2e6;
  z-index: 1;
}

.divider span {
  background-color: white;
  padding: 0 15px;
  position: relative;
  z-index: 2;
}

.social-login {
  display: flex;
  justify-content: center;
  gap: 15px;
  margin-bottom: 25px;
}

.social-btn {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f8f9fa;
  border: 1px solid #dee2e6;
  color: #495057;
  font-size: 18px;
  transition: all 0.3s;
}

.social-btn:hover {
  background-color: #e9ecef;
  transform: translateY(-3px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.05);
}

.register-link {
  text-align: center;
  font-size: 14px;
  color: #6c757d;
}

.register-link a {
  color: #1890ff;
  text-decoration: none;
  font-weight: 600;
  cursor: pointer;
}

.register-link a:hover {
  text-decoration: underline;
}

.demo-credentials {
  margin-top: 25px;
  padding: 15px;
  background-color: #f8f9fa;
  border-radius: 6px;
  border-left: 4px solid #1890ff;
  font-size: 13px;
}

.demo-title {
  font-weight: 600;
  margin-bottom: 5px;
  color: #1f2d3d;
}

.demo-info {
  color: #6c757d;
}

/* 响应式设计 */
@media (max-width: 992px) {
  .container {
    flex-direction: column;
    min-height: 100vh;
    border-radius: 0;
  }

  .brand-section {
    padding: 30px 25px;
  }

  .login-section {
    padding: 40px 30px;
  }
}

@media (max-width: 576px) {
  .brand-title {
    font-size: 24px;
  }

  .logo-text {
    font-size: 22px;
  }

  .login-title {
    font-size: 24px;
  }

  .form-options {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .login-container {
    padding: 0;
  }
}

/* 自定义Ant Design样式覆盖 */
:deep(.ant-input-affix-wrapper) {
  padding: 10px 15px;
  border-radius: 6px;
}

:deep(.ant-input-affix-wrapper-lg) {
  padding: 14px 15px 14px 45px;
}

:deep(.ant-input-prefix) {
  margin-right: 10px;
  color: #6c757d;
}

:deep(.ant-btn-circle) {
  min-width: 50px;
  width: 50px;
  height: 50px;
  padding: 0;
}
</style>
