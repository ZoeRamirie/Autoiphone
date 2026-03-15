import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from './views/Dashboard.vue'
import Customers from './views/Customers.vue'

const routes = [
    {
        path: '/',
        name: 'Dashboard',
        component: Dashboard
    },
    {
        path: '/customers',
        name: 'Customers',
        component: Customers
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

export default router
