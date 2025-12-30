import { createRouter, createWebHistory } from 'vue-router'
import Login from './views/Login.vue'
import Dashboard from './views/Dashboard.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresGuest: true }  // Только для неавторизованных
  },
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard,
    meta: { requiresAuth: true }  // Требует авторизации
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard для защиты маршрутов
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('access_token')

  if (to.meta.requiresAuth && !token) {
    // Пытаемся зайти на защищенный маршрут без токена - редирект на login
    next('/login')
  } else if (to.meta.requiresGuest && token) {
    // Пытаемся зайти на login имея токен - редирект на главную
    next('/')
  } else {
    // Все ок, пропускаем
    next()
  }
})

export default router