import { createApp } from 'vue'
import './style.css'
import router from './router'
import App from './App.vue'
import { setUnauthorizedHandler } from '@/services/apiClient.js'

import { library } from '@fortawesome/fontawesome-svg-core'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { faArrowsRotate } from '@fortawesome/free-solid-svg-icons'

library.add(faArrowsRotate)

setUnauthorizedHandler(() => {
  sessionStorage.removeItem('classhub-token')
  sessionStorage.removeItem('classhub-user')
  if (window.location.pathname !== '/login') window.location.href = '/login'
})

const app = createApp(App)

app.component('font-awesome-icon', FontAwesomeIcon)
app.use(router)
app.mount('#app')
