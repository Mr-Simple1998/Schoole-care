import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
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
app.use(ElementPlus, { locale: zhCn })

app.mount('#app')
