<template>
  <div class="login-container">
    <div class="login-box">
      <h1 class="title">标注系统</h1>
      <div class="form-container">
        <div class="input-group">
          <input
            v-model="phone"
            type="text"
            placeholder="手机号"
            maxlength="11"
            @keyup.enter="handleSubmit"
          >
        </div>
        <div class="input-group">
          <input
            v-model="password"
            type="password"
            placeholder="密码"
            @keyup.enter="handleSubmit"
          >
        </div>
        <div v-if="error" class="error-message">{{ error }}</div>
        <button class="submit-btn" @click="handleSubmit" :disabled="loading">
          {{ loading ? '处理中...' : (isLogin ? '登录' : '注册') }}
        </button>
        <div class="switch-mode">
          <span @click="toggleMode">
            {{ isLogin ? '还没有账号？去注册' : '已有账号？去登录' }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const phone = ref('')
const password = ref('')
const isLogin = ref(true)
const error = ref('')
const loading = ref(false)

const toggleMode = () => {
  isLogin.value = !isLogin.value
  error.value = ''
}

const handleSubmit = async () => {
  if (!phone.value || !password.value) {
    error.value = '请填写手机号和密码'
    return
  }

  // root账号特殊处理，普通用户需要11位手机号
  if (phone.value !== 'root' && !/^\d{11}$/.test(phone.value)) {
    error.value = '手机号格式不正确'
    return
  }

  // root账号密码不做长度限制，普通用户密码至少6位
  if (phone.value !== 'root' && password.value.length < 6) {
    error.value = '密码长度至少6位'
    return
  }

  loading.value = true
  error.value = ''

  try {
    const url = isLogin.value ? '/api/login' : '/api/register'
    const res = await axios.post(url, {
      phone: phone.value,
      password: password.value
    })

    localStorage.setItem('token', res.data.token)
    localStorage.setItem('userId', res.data.user_id)
    if (res.data.phone) {
      localStorage.setItem('phone', res.data.phone)
    }
    if (res.data.is_root) {
      localStorage.setItem('isRoot', 'true')
    } else {
      localStorage.removeItem('isRoot')
    }

    router.push('/annotate')
  } catch (err) {
    error.value = err.response?.data?.detail || '请求失败，请重试'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-box {
  background: white;
  padding: 40px;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  width: 100%;
  max-width: 400px;
}

.title {
  text-align: center;
  color: #333;
  margin-bottom: 30px;
  font-size: 28px;
  font-weight: 600;
}

.form-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.input-group input {
  width: 100%;
  padding: 14px 16px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 16px;
  transition: border-color 0.3s;
}

.input-group input:focus {
  outline: none;
  border-color: #667eea;
}

.error-message {
  color: #e74c3c;
  font-size: 14px;
  text-align: center;
}

.submit-btn {
  width: 100%;
  padding: 14px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
}

.submit-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.switch-mode {
  text-align: center;
}

.switch-mode span {
  color: #667eea;
  cursor: pointer;
  font-size: 14px;
}

.switch-mode span:hover {
  text-decoration: underline;
}
</style>
