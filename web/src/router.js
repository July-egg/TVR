import Vue from 'vue'
import Router from 'vue-router'

Vue.use(Router)

// 引入各个页面对应的组件
const login = () => import('./views/login')
const homepage = () => import('./views/homepage')

const routes = [
  {
    // 默认跳转页面为首页
    path: '',
    redirect:'/login'
  },
  {
    path:'/login',
    component: login
  },
  {
    path:'/home',
    component: homepage
  },
]

const router = new Router({
  // mode: 'history',
  mode:process.env.IS_ELECTRON? 'hash':'history',
  base: process.env.BASE_URL,
  routes
})

export default router
