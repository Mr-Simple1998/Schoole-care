/**
 * Element Plus 按需注入（on-demand injection）
 *
 * 说明：
 * - 不再 `app.use(ElementPlus)` 全量注册，只注册本项目模板里实际用到的组件；
 * - CSS 同步改为按组件引入（base + 用到的 el-xxx.css），替代全量 dist/index.css；
 * - ElMessage / ElMessageBox 仍由各页面按需 import（函数式调用），这里仅补其样式；
 * - 语言包（zh-cn）通过 App.vue 的 <el-config-provider> 注入，见 frontend/src/App.vue。
 *
 * 若后续新增 el-* 组件：请同步在 components 数组和下方样式清单中补上对应
 * `el-xxx.css`（theme-chalk 下存在同名文件，0 字节的文件表示样式在父组件 css 内）。
 */
import {
  ElAlert,
  ElAside,
  ElAvatar,
  ElBadge,
  ElButton,
  ElCard,
  ElCheckbox,
  ElCol,
  ElConfigProvider,
  ElContainer,
  ElDatePicker,
  ElDescriptions,
  ElDescriptionsItem,
  ElDialog,
  ElDivider,
  ElDrawer,
  ElDropdown,
  ElDropdownItem,
  ElDropdownMenu,
  ElEmpty,
  ElForm,
  ElFormItem,
  ElHeader,
  ElIcon,
  ElInput,
  ElInputNumber,
  ElLoading,
  ElMain,
  ElMenu,
  ElMenuItem,
  ElOption,
  ElOptionGroup,
  ElPagination,
  ElProgress,
  ElRadio,
  ElRadioButton,
  ElRadioGroup,
  ElRate,
  ElRow,
  ElSelect,
  ElSwitch,
  ElTable,
  ElTableColumn,
  ElTabPane,
  ElTabs,
  ElTag,
  ElTimePicker,
  ElUpload,
} from 'element-plus'

/* ---------- 按组件引入样式 ---------- */
// 基础：CSS 变量 + 过渡动画 + .el-icon（含 reset 字体基线）
import 'element-plus/theme-chalk/base.css'
import 'element-plus/theme-chalk/el-reset.css'
// 弹层/指令依赖（dialog/message-box/loading/下拉等共用）
import 'element-plus/theme-chalk/el-overlay.css'
import 'element-plus/theme-chalk/el-popper.css'
import 'element-plus/theme-chalk/el-scrollbar.css'
import 'element-plus/theme-chalk/el-spinner.css'
// 消息类（函数式调用，需手动补样式）
import 'element-plus/theme-chalk/el-message.css'
import 'element-plus/theme-chalk/el-message-box.css'
// 组件样式
import 'element-plus/theme-chalk/el-alert.css'
import 'element-plus/theme-chalk/el-aside.css'
import 'element-plus/theme-chalk/el-avatar.css'
import 'element-plus/theme-chalk/el-badge.css'
import 'element-plus/theme-chalk/el-button.css'
import 'element-plus/theme-chalk/el-card.css'
import 'element-plus/theme-chalk/el-checkbox.css'
import 'element-plus/theme-chalk/el-col.css'
import 'element-plus/theme-chalk/el-container.css'
import 'element-plus/theme-chalk/el-date-picker-panel.css'
import 'element-plus/theme-chalk/el-descriptions.css'
import 'element-plus/theme-chalk/el-descriptions-item.css'
import 'element-plus/theme-chalk/el-dialog.css'
import 'element-plus/theme-chalk/el-divider.css'
import 'element-plus/theme-chalk/el-drawer.css'
import 'element-plus/theme-chalk/el-dropdown.css'
import 'element-plus/theme-chalk/el-empty.css'
import 'element-plus/theme-chalk/el-form.css'
import 'element-plus/theme-chalk/el-form-item.css'
import 'element-plus/theme-chalk/el-header.css'
import 'element-plus/theme-chalk/el-input.css'
import 'element-plus/theme-chalk/el-input-number.css'
import 'element-plus/theme-chalk/el-loading.css'
import 'element-plus/theme-chalk/el-main.css'
import 'element-plus/theme-chalk/el-menu.css'
import 'element-plus/theme-chalk/el-option.css'
import 'element-plus/theme-chalk/el-option-group.css'
import 'element-plus/theme-chalk/el-pagination.css'
import 'element-plus/theme-chalk/el-progress.css'
import 'element-plus/theme-chalk/el-radio.css'
import 'element-plus/theme-chalk/el-radio-button.css'
import 'element-plus/theme-chalk/el-radio-group.css'
import 'element-plus/theme-chalk/el-rate.css'
import 'element-plus/theme-chalk/el-row.css'
import 'element-plus/theme-chalk/el-select.css'
import 'element-plus/theme-chalk/el-switch.css'
import 'element-plus/theme-chalk/el-table.css'
import 'element-plus/theme-chalk/el-table-column.css'
import 'element-plus/theme-chalk/el-tabs.css'
import 'element-plus/theme-chalk/el-tag.css'
import 'element-plus/theme-chalk/el-time-picker.css'
import 'element-plus/theme-chalk/el-upload.css'

/** 实际使用到的组件列表（app.use 逐个注册，tree-shaking 生效） */
const components = [
  ElAlert,
  ElAside,
  ElAvatar,
  ElBadge,
  ElButton,
  ElCard,
  ElCheckbox,
  ElCol,
  ElConfigProvider,
  ElContainer,
  ElDatePicker,
  ElDescriptions,
  ElDescriptionsItem,
  ElDialog,
  ElDivider,
  ElDrawer,
  ElDropdown,
  ElDropdownItem,
  ElDropdownMenu,
  ElEmpty,
  ElForm,
  ElFormItem,
  ElHeader,
  ElIcon,
  ElInput,
  ElInputNumber,
  ElLoading,
  ElMain,
  ElMenu,
  ElMenuItem,
  ElOption,
  ElOptionGroup,
  ElPagination,
  ElProgress,
  ElRadio,
  ElRadioButton,
  ElRadioGroup,
  ElRate,
  ElRow,
  ElSelect,
  ElSwitch,
  ElTable,
  ElTableColumn,
  ElTabPane,
  ElTabs,
  ElTag,
  ElTimePicker,
  ElUpload,
]

export function setupElementPlus(app) {
  components.forEach((component) => app.use(component))
}
