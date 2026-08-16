<template>
	<view class="page">
		<button class="btn-primary add-btn" @click="showAdd=true">新增教师</button>

		<!-- 概览小卡（纯展示） -->
		<view class="stat-grid" v-if="teachers && teachers.length">
			<view class="stat-card is-green">
				<view class="stat-top">
					<text class="stat-label">教师总数</text>
					<text class="stat-emoji">👩‍🏫</text>
				</view>
				<text class="stat-num">{{ teacherStats.total }}</text>
				<text class="stat-sub">教师账号统计</text>
				<view class="stat-accent"></view>
			</view>
			<view class="stat-card is-green">
				<view class="stat-top">
					<text class="stat-label">正常启用</text>
					<text class="stat-emoji">✅</text>
				</view>
				<text class="stat-num">{{ teacherStats.active }}</text>
				<text class="stat-sub">可正常登录使用</text>
				<view class="stat-accent"></view>
			</view>
			<view class="stat-card is-red">
				<view class="stat-top">
					<text class="stat-label">已停用</text>
					<text class="stat-emoji">⛔</text>
				</view>
				<text class="stat-num">{{ teacherStats.inactive }}</text>
				<text class="stat-sub">暂不可登录</text>
				<view class="stat-accent"></view>
			</view>
			<view class="stat-card is-blue">
				<view class="stat-top">
					<text class="stat-label">已分配学科</text>
					<text class="stat-emoji">📚</text>
				</view>
				<text class="stat-num">{{ teacherStats.withSubject }}</text>
				<text class="stat-sub">有归属学科</text>
				<view class="stat-accent"></view>
			</view>
		</view>

		<view class="card">
			<view class="card-title"><view class="bar"></view>教师列表</view>
			<view v-for="t in teachers" :key="t.id" class="info-row">
				<view class="ir-left">
					<view class="ir-title">
						<text>{{ t.name }}</text>
						<text class="tag" :class="roleTagClass(t.role)">{{ roleText(t) }}</text>
					</view>
					<view class="ir-sub">
						<text>@{{ t.username }}</text>
						<text v-if="subjectText(t)" class="sub-divider">·</text>
						<text v-if="subjectText(t)" class="sub-subjects">{{ subjectText(t) }}</text>
						<text v-if="t.work_start_time" class="sub-divider">·</text>
						<text v-if="t.work_start_time" class="sub-schedule">上下班 {{ t.work_start_time }}-{{ t.work_end_time || '未设' }}</text>
					</view>
				</view>
				<view class="ir-right">
					<text class="tag" :class="t.resigned ? 'tag-danger' : (t.is_active ? 'tag-success' : 'tag-danger')">
						<text class="dot" :class="t.resigned ? 'dot-red' : (t.is_active ? 'dot-green' : 'dot-red')"></text>{{ t.resigned ? '已离职' : (t.is_active ? '启用' : '停用') }}
					</text>
					<text v-if="t.role === 'teacher'" class="schedule" @click="openSchedule(t)">上下班</text>
					<text class="edit" @click="openEdit(t)">编辑</text>
					<text class="del" @click="doDelete(t)">删除</text>
				</view>
			</view>
			<view v-if="!teachers.length" class="text-muted empty">暂无教师</view>
		</view>

		<view class="mask" v-if="showAdd" @click="showAdd=false">
			<view class="dialog" @click.stop>
				<view class="dialog-title">新增教师</view>
				<view class="field"><text class="label">姓名</text><input class="input" v-model="form.name" /></view>
				<view class="field"><text class="label">用户名</text><input class="input" v-model="form.username" /></view>
				<view class="field"><text class="label">密码</text><input class="input" password v-model="form.password" /></view>
				<view class="dialog-btns">
					<button class="btn-cancel" @click="showAdd=false">取消</button>
					<button class="btn-primary" @click="doAdd">保存</button>
				</view>
			</view>
		</view>

		<!-- 编辑教师（改名） -->
		<view class="mask" v-if="showEdit" @click="showEdit=false">
			<view class="dialog" @click.stop>
				<view class="dialog-title">编辑教师</view>
				<view class="field"><text class="label">账号：{{ editTarget && editTarget.username }}</text></view>
				<view class="field"><text class="label">姓名</text><input class="input" v-model="editForm.name" placeholder="修改后名下数据保持不变" /></view>
				<view class="tip">修改姓名不会影响该账号名下的学生、考勤、收费等数据。</view>
				<view class="dialog-btns">
					<button class="btn-cancel" @click="showEdit=false">取消</button>
					<button class="btn-primary" @click="doEdit">保存</button>
				</view>
			</view>
		</view>

		<!-- 设置教师上下班打卡时间 -->
		<view class="mask" v-if="showSchedule" @click="showSchedule=false">
			<view class="dialog" @click.stop>
				<view class="dialog-title">设置上下班时间</view>
				<view class="field"><text class="label">教师：{{ scheduleTarget && scheduleTarget.name }}</text></view>
				<view class="field">
					<text class="label">上班时间</text>
					<picker mode="time" :value="scheduleForm.work_start_time" @change="e => scheduleForm.work_start_time = e.detail.value">
						<view class="input picker-box">{{ scheduleForm.work_start_time || '请选择' }}<text class="arrow">›</text></view>
					</picker>
				</view>
				<view class="field">
					<text class="label">下班时间</text>
					<picker mode="time" :value="scheduleForm.work_end_time" @change="e => scheduleForm.work_end_time = e.detail.value">
						<view class="input picker-box">{{ scheduleForm.work_end_time || '请选择' }}<text class="arrow">›</text></view>
					</picker>
				</view>
				<view class="tip">设置后，教师可在工作台进行上下班打卡；上班晚于设定时间会在月度考勤汇总中标记为「迟到」。</view>
				<view class="dialog-btns">
					<button class="btn-cancel" @click="showSchedule=false">取消</button>
					<button class="btn-primary" @click="doSaveSchedule">保存</button>
				</view>
			</view>
		</view>
	</view>
</template>

<script>
import { get, post, del, put } from '../../utils/request';

export default {
	data() {
		return {
			teachers: [],
			showAdd: false,
			form: { name: '', username: '', password: '' },
			showEdit: false,
			editTarget: null,
			editForm: { name: '' },
			showSchedule: false,
			scheduleTarget: null,
			scheduleForm: { work_start_time: '', work_end_time: '' }
		};
	},
	computed: {
		// 纯展示：角色文案与配色（校区负责人显示所属校区）
		roleText() {
			return (t) => {
				const r = typeof t === 'string' ? t : (t && t.role);
				if (r === 'principal') return '校长';
				if (r === 'sub_principal' || r === 'campus_head') {
					const campusName = typeof t === 'object' && t && t.campus_name ? t.campus_name : '';
					return campusName ? `${campusName}·校区负责人` : '校区负责人';
				}
				return '教师';
			};
		},
		roleTagClass() {
			return (r) => {
				if (r === 'principal') return 'tag-info';
				if (r === 'sub_principal' || r === 'campus_head') return 'tag-warn';
				return 'tag-primary';
			};
		},
		// 纯展示：概览统计
		teacherStats() {
			const list = this.teachers || [];
			const total = list.length;
			const active = list.filter(t => t.is_active).length;
			const withSubject = list.filter(t => (t.subjects || []).length > 0).length;
			return {
				total: total,
				active: active,
				inactive: total - active,
				withSubject: withSubject
			};
		}
	},
	onLoad() { this.loadTeachers(); },
	methods: {
		// 纯展示：所属学科文案
		subjectText(t) {
			const subs = (t.subjects || []).map(s => s.name).filter(Boolean);
			return subs.length ? subs.join('、') : '';
		},
		async loadTeachers() {
			try { this.teachers = await get('/auth/teachers'); } catch (e) {}
		},
		async doAdd() {
			if (!this.form.name || !this.form.username || !this.form.password) {
				uni.showToast({ title: '请填写完整', icon: 'none' });
				return;
			}
			await post('/auth/register', Object.assign({}, this.form, { role: 'teacher' }));
			uni.showToast({ title: '已添加', icon: 'success' });
			this.showAdd = false;
			this.form = { name: '', username: '', password: '' };
			this.loadTeachers();
		},
		doDelete(t) {
			uni.showModal({
				title: '提示',
				content: '确定删除教师 ' + t.name + ' 吗？',
				success: async (res) => {
					if (res.confirm) {
						try {
							await del('/auth/teachers/' + t.id);
							uni.showToast({ title: '已删除', icon: 'success' });
							this.loadTeachers();
						} catch (e) {}
					}
				}
			});
		},
		openEdit(t) {
			this.editTarget = t;
			this.editForm = { name: t.name || '' };
			this.showEdit = true;
		},
		async doEdit() {
			if (!this.editForm.name.trim()) {
				uni.showToast({ title: '请输入姓名', icon: 'none' });
				return;
			}
			try {
				await put('/auth/users/' + this.editTarget.id, { name: this.editForm.name.trim() });
				uni.showToast({ title: '已保存', icon: 'success' });
				this.showEdit = false;
				this.loadTeachers();
			} catch (e) {}
		},
		openSchedule(t) {
			this.scheduleTarget = t;
			this.scheduleForm = {
				work_start_time: t.work_start_time || '',
				work_end_time: t.work_end_time || ''
			};
			this.showSchedule = true;
		},
		async doSaveSchedule() {
			try {
				await put('/auth/users/' + this.scheduleTarget.id + '/work-time', {
					work_start_time: this.scheduleForm.work_start_time || null,
					work_end_time: this.scheduleForm.work_end_time || null
				});
				uni.showToast({ title: '已保存', icon: 'success' });
				this.showSchedule = false;
				this.loadTeachers();
			} catch (e) {}
		}
	}
};
</script>

<style scoped>
.page { padding-bottom: 40rpx; }
.add-btn { margin: 20rpx; }
.ir-title { display: flex; align-items: center; gap: 12rpx; }
.ir-title .tag { padding: 2rpx 12rpx; font-size: 20rpx; }
.sub-divider { color: #c0c4cc; }
.sub-subjects { color: #10b981; }
.del { color: #f56c6c; margin-left: 8rpx; font-size: 26rpx; }
.schedule { color: #3b82f6; margin-left: 8rpx; font-size: 26rpx; }
.edit { color: #10b981; margin-left: 8rpx; font-size: 26rpx; }
.sub-schedule { color: #3b82f6; }
.picker-box { display: flex; align-items: center; justify-content: space-between; }
.arrow { color: #c0c4cc; font-size: 32rpx; }
.tip { font-size: 22rpx; color: #909399; margin-bottom: 16rpx; line-height: 1.5; }
.empty { text-align: center; padding: 30rpx 0; }
.mask { position: fixed; left:0; top:0; right:0; bottom:0; background: rgba(0,0,0,0.45); z-index:99; display:flex; align-items:center; justify-content:center; }
.dialog { width: 80%; background:#fff; border-radius:16rpx; padding:36rpx 32rpx; }
.dialog-title { font-size:32rpx; font-weight:600; margin-bottom:24rpx; }
.dialog-btns { display:flex; margin-top:20rpx; }
.dialog-btns button { flex:1; margin:0 8rpx; font-size:28rpx; }
.btn-cancel { background:#f5f7fa; color:#606266; border-radius:12rpx; }
.field { margin-bottom:20rpx; }
.label { display:block; font-size:24rpx; color:#606266; margin-bottom:8rpx; }
.input { background:#f5f7fa; border-radius:10rpx; padding:16rpx 20rpx; font-size:28rpx; }
</style>
