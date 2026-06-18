import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../components/LoginView.vue'
import RegisterView from '../components/RegisterView.vue'
import WelcomeScreen from '../components/WelcomeScreen.vue'
import SubjectSelect from '../components/SubjectSelect.vue'
import GradeSelect from '../components/GradeSelect.vue'
import HomeView from '../components/HomeView.vue'
import LearningView from '../components/LearningView.vue'
import { useUserStore } from "../stores/user.js";

const routes = [
  {
    path: '/',
    name: 'Welcome',
    component: WelcomeScreen,
  },
  {
    path: '/login',
    name: 'Login',
    component: LoginView,
  },
  {
    path: '/register',
    name: 'Register',
    component: RegisterView,
  },
  {
    path: '/select-subject',
    name: 'SubjectSelect',
    component: SubjectSelect,
  },
  {
    path: '/select-grade',
    name: 'GradeSelect',
    component: GradeSelect,
  },
  {
    path: '/home',
    name: 'Home',
    component: HomeView,
  },
  {
    path: '/learning',
    name: 'Learning',
    component: LearningView,
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 导航守卫：检查登录状态
router.beforeEach(async (to, from, next) => {
  // 白名单路由（不需要登录）
  const publicRoutes = ['/login', '/register']

  if (publicRoutes.includes(to.path)) {
    next()
    return
  }
  const userStore = useUserStore();
  if (userStore.checkAuth()) {
    // 已登录，继续
    next()
  } else {
    next('/login')
  }
})

export default router
