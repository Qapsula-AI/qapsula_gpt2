<script setup>
import { onMounted } from 'vue'
import { useAuth } from '@/composables/useAuth'

const { user, logout, fetchUser } = useAuth()

onMounted(async () => {
  // Загружаем данные пользователя при монтировании
  if (!user.value) {
    await fetchUser()
  }
})

async function handleLogout() {
  if (confirm('Вы уверены, что хотите выйти?')) {
    await logout()
  }
}
</script>

<template>
  <div class="dashboard">
    <header class="dashboard__header">
      <div class="container">
        <div class="header-content">
          <h1>Qapsula</h1>
          <div class="user-info">
            <span v-if="user" class="username">{{ user.username }}</span>
            <button @click="handleLogout" class="btn-logout">
              Выйти
            </button>
          </div>
        </div>
      </div>
    </header>

    <main class="dashboard__main">
      <div class="container">
        <div class="welcome-card">
          <h2>Добро пожаловать в Qapsula!</h2>
          <p v-if="user">
            Вы вошли как <strong>{{ user.full_name || user.username }}</strong>
          </p>
          <p v-if="user && user.is_superuser" class="admin-badge">
            Роль: Администратор
          </p>
        </div>

        <div class="info-card">
          <h3>RAG система</h3>
          <p>
            Qapsula - это система для работы с документами на основе RAG (Retrieval-Augmented Generation).
          </p>
          <div class="features">
            <div class="feature-item">
              <h4>Загрузка документов</h4>
              <p>Поддержка различных форматов документов</p>
            </div>
            <div class="feature-item">
              <h4>Поиск по документам</h4>
              <p>Быстрый семантический поиск</p>
            </div>
            <div class="feature-item">
              <h4>Чат с документами</h4>
              <p>Задавайте вопросы по содержимому</p>
            </div>
            <div class="feature-item">
              <h4>Мультитенантность</h4>
              <p>Поддержка нескольких клиентов</p>
            </div>
          </div>
        </div>

        <div v-if="user" class="user-details-card">
          <h3>Информация о пользователе</h3>
          <dl class="user-details">
            <dt>ID:</dt>
            <dd>{{ user.id }}</dd>

            <dt>Email:</dt>
            <dd>{{ user.email }}</dd>

            <dt>Статус:</dt>
            <dd>
              <span :class="['status-badge', user.is_active ? 'status-active' : 'status-inactive']">
                {{ user.is_active ? 'Активен' : 'Неактивен' }}
              </span>
            </dd>

            <dt>Дата создания:</dt>
            <dd>{{ user.created_at ? new Date(user.created_at).toLocaleString('ru-RU') : '-' }}</dd>

            <dt>Последний вход:</dt>
            <dd>{{ user.last_login_at ? new Date(user.last_login_at).toLocaleString('ru-RU') : '-' }}</dd>
          </dl>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.dashboard {
  min-height: 100vh;
  background-color: #f5f5f5;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

.dashboard__header {
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  padding: 16px 0;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dashboard__header h1 {
  font-size: 24px;
  font-weight: 600;
  color: #1a1a1a;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.username {
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

.btn-logout {
  padding: 8px 16px;
  background: #ff4d4f;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-logout:hover {
  background: #ff7875;
}

.dashboard__main {
  padding: 32px 0;
}

.welcome-card,
.info-card,
.user-details-card {
  background: white;
  border-radius: 8px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.welcome-card h2 {
  font-size: 24px;
  margin-bottom: 12px;
  color: #1a1a1a;
}

.welcome-card p {
  font-size: 16px;
  color: #666;
  margin-bottom: 8px;
}

.admin-badge {
  display: inline-block;
  background: #1677ff;
  color: white;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
}

.info-card h3,
.user-details-card h3 {
  font-size: 20px;
  margin-bottom: 16px;
  color: #1a1a1a;
}

.info-card > p {
  font-size: 16px;
  color: #666;
  margin-bottom: 24px;
}

.features {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
}

.feature-item {
  padding: 16px;
  background: #f9f9f9;
  border-radius: 6px;
  border-left: 3px solid #1677ff;
}

.feature-item h4 {
  font-size: 16px;
  margin-bottom: 8px;
  color: #1a1a1a;
}

.feature-item p {
  font-size: 14px;
  color: #666;
  margin: 0;
}

.user-details {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 12px 24px;
  max-width: 600px;
}

.user-details dt {
  font-weight: 600;
  color: #1a1a1a;
}

.user-details dd {
  color: #666;
  margin: 0;
}

.status-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.status-active {
  background: #f6ffed;
  color: #52c41a;
  border: 1px solid #b7eb8f;
}

.status-inactive {
  background: #fff1f0;
  color: #ff4d4f;
  border: 1px solid #ffccc7;
}
</style>