import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { setupElementPlus } from './plugins/element-plus'
import {
  ArrowDown,
  Avatar,
  Calendar,
  CircleCheck,
  Collection,
  Expand,
  Fold,
  Grid,
  InfoFilled,
  Money,
  Odometer,
  OfficeBuilding,
  Reading,
  Star,
  SwitchButton,
  Trophy,
  User,
  UserFilled,
  Warning,
} from '@element-plus/icons-vue'

import './style.css'
import App from './App.vue'
import router from './router'

const app = createApp(App)

const icons = {
  ArrowDown, Avatar, Calendar, CircleCheck, Collection, Expand, Fold, Grid,
  InfoFilled, Money, Odometer, OfficeBuilding, Reading, Star, SwitchButton,
  Trophy, User, UserFilled, Warning,
}
for (const [name, component] of Object.entries(icons)) app.component(name, component)

app.use(createPinia())
app.use(router)
setupElementPlus(app)

app.mount('#app')
