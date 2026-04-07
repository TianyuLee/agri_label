import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Annotate from '../views/Annotate.vue'

const routes = [
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/annotate',
    name: 'Annotate',
    component: Annotate
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.path === '/annotate' && !token) {
    next('/login')
  } else {
    next()
  }
})

export default router
