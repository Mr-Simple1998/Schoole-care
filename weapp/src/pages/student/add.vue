<template>
	<view class="page">
		<!-- 顶部说明 -->
		<view class="card intro-card">
			<view class="intro-title">📝 新增学生</view>
			<view class="intro-desc">填写学生基础信息并选择报名学科，保存后自动生成学号。</view>
		</view>

		<view class="card">
			<view class="card-title"><text class="bar"></text>基本信息</view>
			<view class="field">
				<text class="label">姓名<text class="req">*</text></text>
				<input class="input" v-model="form.name" placeholder="请输入学生姓名" />
				<view class="hint">必填项，用于学生档案与考勤记录</view>
			</view>
			<view class="field">
				<text class="label">性别</text>
				<picker :range="['男','女']" @change="e => form.gender=['男','女'][e.detail.value]">
					<view class="input picker-box">{{ form.gender || '请选择' }}<text class="arrow">›</text></view>
				</picker>
			</view>
			<view class="field">
				<text class="label">学校</text>
				<input class="input" v-model="form.school" placeholder="就读学校" />
			</view>
			<view class="field" v-if="campuses.length && !store.isTeacher">
				<text class="label">所属校区</text>
				<picker :range="campusLabels" @change="e => form.campus_id = campusIds[e.detail.value]">
					<view class="input picker-box">{{ campusName || '请选择（可选）' }}<text class="arrow">›</text></view>
				</picker>
			</view>
			<view class="field">
				<text class="label">年级</text>
				<picker :range="grades" @change="e => form.grade=grades[e.detail.value]">
					<view class="input picker-box">{{ form.grade || '请选择' }}<text class="arrow">›</text></view>
				</picker>
			</view>
			<view class="field">
				<text class="label">监护人</text>
				<input class="input" v-model="form.guardian_name" placeholder="监护人姓名" />
			</view>
			<view class="field">
				<text class="label">联系电话</text>
				<input class="input" v-model="form.guardian_phone" placeholder="监护人电话" />
				<view class="hint">用于联系监护人，请填写正确号码</view>
			</view>
			<view class="field">
				<text class="label">入学日期</text>
				<picker mode="date" @change="e => form.enrollment_date=e.detail.value">
					<view class="input picker-box">{{ form.enrollment_date || '请选择' }}<text class="arrow">›</text></view>
				</picker>
			</view>
		</view>

		<view class="card">
			<view class="card-title"><text class="bar"></text>学科与课时</view>
			<view class="hint section-hint">勾选学科后，可设置按课时核销或按到期时间，支持多选</view>
			<view v-for="sub in subjects" :key="sub.id" class="subject-line" :class="{ selected: isSelected(sub.id) }">
				<view class="flex">
					<checkbox-group @change="e => toggleSubject(sub.id, e.detail.value)">
						<checkbox :value="String(sub.id)" :checked="isSelected(sub.id)" />
					</checkbox-group>
					<text class="flex-1 sub-name">{{ sub.name }} <text class="text-muted cat">{{ sub.category }}</text></text>
				</view>
				<view v-if="isSelected(sub.id)" class="session-config">
					<radio-group class="flex" @change="e => setMode(sub.id, e.detail.value)">
						<label class="radio-item"><radio value="sessions" :checked="getCfg(sub.id).mode==='sessions'" />按课时核销</label>
						<label class="radio-item"><radio value="duration" :checked="getCfg(sub.id).mode==='duration'" />按到期时间</label>
					</radio-group>
					<view v-if="getCfg(sub.id).mode==='sessions'" class="flex session-input-row">
						<input class="input small" type="number" v-model="getCfg(sub.id).total_sessions" placeholder="总课时数" />
						<text class="unit-text">次</text>
					</view>
					<view v-else class="flex session-input-row">
						<input class="input small" type="number" v-model="getCfg(sub.id).duration_value" placeholder="时长" />
						<picker :range="units" @change="e => getCfg(sub.id).duration_unit=units[e.detail.value]">
							<view class="unit">{{ getCfg(sub.id).duration_unit }}</view>
						</picker>
					</view>
				</view>
			</view>
			<view v-if="!subjects.length" class="text-muted empty">暂无学科可选</view>
		</view>

		<button class="btn-primary submit-btn" @click="submit" :loading="loading">保存学生</button>
	</view>
</template>

<script>
import { get, post } from '../../utils/request';
import { useUserStore } from '../../stores/user';

const GRADES = ['小学一年级','小学二年级','小学三年级','小学四年级','小学五年级','小学六年级','初中一年级','初中二年级','初中三年级','高中一年级','高中二年级','高中三年级'];
const UNITS = ['天','月','年'];

export default {
	data() {
		return {
			store: useUserStore(),
			grades: GRADES,
			units: UNITS,
			subjects: [],
			campuses: [],
			selected: {}, // subject_id -> cfg
			form: {
				name: '', gender: '', school: '', grade: '',
				guardian_name: '', guardian_phone: '', enrollment_date: '',
				campus_id: null
			},
			loading: false
		};
	},
	computed: {
		campusLabels() {
			return this.campuses.map(c => c.name);
		},
		campusIds() {
			return this.campuses.map(c => c.id);
		},
		campusName() {
			const c = this.campuses.find(x => x.id === this.form.campus_id);
			return c ? c.name : '';
		}
	},
	onLoad() {
		this.loadSubjects();
		this.loadCampuses();
	},
	methods: {
		async loadCampuses() {
			try {
				this.campuses = await get('/campuses/options');
			} catch (e) {}
		},
		async loadSubjects() {
			try {
				this.subjects = await get('/subjects');
			} catch (e) {}
		},
		isSelected(id) { return !!this.selected[id]; },
		getCfg(id) {
			if (!this.selected[id]) {
				this.selected[id] = { mode: 'sessions', total_sessions: '', duration_value: '', duration_unit: '天' };
			}
			return this.selected[id];
		},
		toggleSubject(id, e) {
			if (e.length) {
				this.getCfg(id);
			} else {
				delete this.selected[id];
			}
		},
		setMode(id, mode) { this.getCfg(id).mode = mode; },
		async submit() {
			if (!this.form.name) {
				uni.showToast({ title: '请填写姓名', icon: 'none' });
				return;
			}
			const subjectIds = Object.keys(this.selected).map(Number);
			const subjectSessions = subjectIds.map(sid => {
				const c = this.selected[sid];
				if (c.mode === 'sessions') {
					return { subject_id: sid, total_sessions: Number(c.total_sessions) || null };
				}
				return { subject_id: sid, total_sessions: null, duration_value: Number(c.duration_value) || null, duration_unit: c.duration_unit };
			});
			this.loading = true;
			try {
				await post('/students', Object.assign({}, this.form, {
					subject_ids: subjectIds,
					subject_sessions: subjectSessions
				}));
				uni.showToast({ title: '保存成功', icon: 'success' });
				setTimeout(() => uni.navigateBack(), 500);
			} catch (e) {
			} finally {
				this.loading = false;
			}
		}
	}
};
</script>

<style scoped>
.page { padding-bottom: 40rpx; }
.intro-card { background: linear-gradient(135deg, #10b981, #059669); border-radius: 16rpx; }
.intro-title { color: #fff; font-size: 32rpx; font-weight: 700; }
.intro-desc { color: rgba(255,255,255,0.9); font-size: 24rpx; margin-top: 8rpx; line-height: 1.5; }
.field { margin-bottom: 24rpx; }
.label { display: block; font-size: 26rpx; color: #303133; font-weight: 500; margin-bottom: 10rpx; }
.req { color: #ef4444; margin-left: 4rpx; font-weight: 600; }
.hint { font-size: 22rpx; color: #c0c4cc; margin-top: 8rpx; line-height: 1.4; }
.section-hint { margin-bottom: 8rpx; }
.input {
	background: #f5f7fa;
	border-radius: 12rpx;
	padding: 18rpx 24rpx;
	font-size: 28rpx;
}
.input.small { flex: 1; margin-right: 16rpx; }
.picker-box { display: flex; align-items: center; justify-content: space-between; }
.picker-box .arrow { color: #c0c4cc; font-size: 32rpx; line-height: 1; }
.subject-line {
	padding: 18rpx 0;
	border-bottom: 1rpx solid #f0f0f0;
}
.subject-line.selected { background: #f0fdf4; border-radius: 12rpx; padding: 18rpx 16rpx; }
.subject-line:last-child { border-bottom: none; }
.sub-name { font-size: 28rpx; color: #303133; }
.cat { font-size: 22rpx; }
.session-config { margin: 12rpx 0 0 60rpx; }
.radio-item { margin-right: 30rpx; font-size: 26rpx; }
.session-input-row { margin-top: 12rpx; }
.unit-text { color: #909399; font-size: 24rpx; margin-right: 16rpx; }
.unit {
	background: #f0fdf4;
	color: #10b981;
	border-radius: 8rpx;
	padding: 12rpx 24rpx;
	font-size: 26rpx;
}
.empty { text-align: center; padding: 30rpx 0; }
.submit-btn { margin: 30rpx 20rpx; }
</style>
