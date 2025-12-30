<script setup>
import { ref } from 'vue'
import { useAuth } from '@/composables/useAuth'

const { login } = useAuth()

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function handleLogin() {
  if (!username.value || !password.value) {
    error.value = 'Заполните все поля'
    return
  }

  error.value = ''
  loading.value = true

  try {
    await login(username.value, password.value)
  } catch (err) {
    error.value = err.message || 'Неверные учетные данные'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-form">
    <div class="login-form__header">
      <h2>Qapsula</h2>
      <p>Вход в систему</p>
    </div>

    <form @submit.prevent="handleLogin" class="login-form__form">
      <div class="form-group">
        <label for="username">Имя пользователя</label>
        <input
          id="username"
          v-model="username"
          type="text"
          placeholder="admin"
          required
          :disabled="loading"
        >
      </div>

      <div class="form-group">
        <label for="password">Пароль</label>
        <input
          id="password"
          v-model="password"
          type="password"
          placeholder="••••••••"
          required
          :disabled="loading"
        >
      </div>

      <button type="submit" class="btn-primary" :disabled="loading">
        {{ loading ? 'Вход...' : 'Войти' }}
      </button>

      <p v-if="error" class="error-message">{{ error }}</p>
    </form>
  </div>
</template>

<style scoped>
.login-form {
  width: 100%;
  max-width: 400px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 32px;
}

.login-form__header {
  text-align: center;
  margin-bottom: 32px;
}

.login-form__header h2 {
  font-size: 28px;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 8px;
}

.login-form__header p {
  font-size: 14px;
  color: #666;
}

.login-form__form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.form-group input {
  padding: 12px 16px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  transition: border-color 0.2s;
}

.form-group input:focus {
  outline: none;
  border-color: #4096ff;
}

.form-group input:disabled {
  background-color: #f5f5f5;
  cursor: not-allowed;
}

.btn-primary {
  padding: 12px 24px;
  background: #1677ff;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-primary:hover:not(:disabled) {
  background: #4096ff;
}

.btn-primary:disabled {
  background: #91caff;
  cursor: not-allowed;
}

.error-message {
  color: #ff4d4f;
  font-size: 14px;
  text-align: center;
  margin: 0;
}
</style>