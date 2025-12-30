import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

// Глобальное состояние авторизации
const token = ref(localStorage.getItem('access_token'))
const user = ref(null)

export function useAuth() {
  const router = useRouter()

  // Computed свойство для проверки авторизации
  const isAuthenticated = computed(() => !!token.value)

  /**
   * Авторизация пользователя
   * @param {string} username - Имя пользователя
   * @param {string} password - Пароль
   * @returns {Promise<void>}
   * @throws {Error} Если авторизация не удалась
   */
  async function login(username, password) {
    try {
      // Формируем данные для OAuth2PasswordRequestForm
      const formData = new FormData()
      formData.append('username', username)
      formData.append('password', password)

      const response = await fetch('/api/login', {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Ошибка авторизации')
      }

      const data = await response.json()

      // Сохраняем токен
      token.value = data.access_token
      localStorage.setItem('access_token', data.access_token)

      // Загружаем данные пользователя
      await fetchUser()

      // Переход на главную страницу
      router.push('/')
    } catch (error) {
      console.error('Ошибка авторизации:', error)
      throw error
    }
  }

  /**
   * Выход из системы
   */
  async function logout() {
    try {
      // Опциональный запрос на сервер (для логирования)
      if (token.value) {
        await fetch('/api/logout', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token.value}`
          }
        })
      }
    } catch (error) {
      console.error('Ошибка при выходе:', error)
    } finally {
      // Всегда очищаем локальное состояние
      token.value = null
      user.value = null
      localStorage.removeItem('access_token')
      router.push('/login')
    }
  }

  /**
   * Загрузить данные текущего пользователя
   * @returns {Promise<void>}
   */
  async function fetchUser() {
    if (!token.value) {
      return
    }

    try {
      const response = await fetch('/api/users/me', {
        headers: {
          'Authorization': `Bearer ${token.value}`
        }
      })

      if (!response.ok) {
        // Токен невалиден - выходим
        if (response.status === 401) {
          await logout()
          return
        }
        throw new Error('Не удалось загрузить данные пользователя')
      }

      user.value = await response.json()
    } catch (error) {
      console.error('Ошибка загрузки пользователя:', error)
      throw error
    }
  }

  /**
   * Выполнить API запрос с авторизацией
   * @param {string} url - URL запроса
   * @param {Object} options - Опции fetch
   * @returns {Promise<Response>}
   */
  async function apiRequest(url, options = {}) {
    const headers = {
      ...options.headers,
      'Authorization': `Bearer ${token.value}`
    }

    const response = await fetch(url, {
      ...options,
      headers
    })

    // Если 401 - токен истек, выходим
    if (response.status === 401) {
      await logout()
      throw new Error('Сессия истекла')
    }

    return response
  }

  return {
    token,
    user,
    isAuthenticated,
    login,
    logout,
    fetchUser,
    apiRequest
  }
}