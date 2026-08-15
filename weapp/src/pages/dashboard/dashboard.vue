<template>
	<view class="page">
		<!-- 欢迎头 -->
		<view class="welcome">
			<view class="welcome-name">{{ store.userName }}，你好</view>
			<view class="welcome-role">{{ roleText }}</view>
		</view>

		<!-- 统计卡片 -->
		<view class="stat-grid">
			<view class="stat-card" @click="goStudents">
				<text class="stat-num">{{ overview.total_students }}</text>
				<text class="stat-label">学生总数</text>
			</view>
			<view class="stat-card" v-if="!store.isTeacher">
				<text class="stat-num">{{ overview.month_income }}</text>
				<text class="stat-label">本月收入</text>
			</view>
			<view class="stat-card">
				<text class="stat-num">{{ overview.today_attendance }}</text>
				<text class="stat-label">今日考勤</text>
			</view>
			<view class="stat-card" v-if="store.isPrincipal">
				<text class="stat-num">{{ overview.total_unpaid }}</text>
				<text class="stat-label">总欠费</text>
			</view>
		</view>

		<!-- 到期提醒 -->
		<view class="card">
			<view class="card-title">费用 / 课时到期提醒</view>
			<view v-if="overview.fee_expire_reminders && overview.fee_expire_reminders.length">
				<view v-for="(r, i) in overview.fee_expire_reminders" :key="i" class="remind-item">
					<view class="flex">
						<text class="flex-1">{{ r.student_name }}</text>
						<text :class="r.days_left < 0 ? 'text-danger' : 'text-warn'">
							{{ r.days_left < 0 ? '已到期 ' + (-r.days_left) + '天' : '剩 ' + r.days_left + ' 天' }}
						</text>
					</view>
					<view class="text-muted remind-sub">{{ r.fee_type }} · {{ r.expire_date }} · {{ r.teacher_name || '未分配' }}</view>
				</view>
			</view>
			<view v-else class="text-muted empty">暂无到期提醒</view>
		</view>

		<!-- 快捷入口 -->
		<view class="card">
			<view class="card-title">快捷操作</view>
			<view class="quick-grid">
				<view class="quick-item" @click="goStudents"><text>学生管理</text></view>
				<view class="quick-item" @click="goIncome" v-if="store.isPrincipal"><text>收费管理</text></view>
				<view class="quick-item" @click="goSubjects" v-if="store.isPrincipal"><text>学科管理</text></view>
				<view class="quick-item" @click="goTeachers" v-if="store.isPrincipal"><text>教师管理</text></view>
				<view class="quick-item" @click="goPoints"><text>积分管理</text></view>
			</view>
		</view>
	</view>
</template>

<script>
import { useUserStore } from '../../stores/user';
import { get } from '../../utils/request';

export default {
	data() {
		return {
			store: useUserStore(),
			overview: {}
		};
	},
	computed: {
		roleText() {
			const r = this.store.user && this.store.user.role;
			if (r === 'principal') return '校长';
			if (r === 'teacher') return '教师';
			if (r === 'platform') return '平台管理员';
			return '';
		}
	},
	onShow() {
		this.loadOverview();
	},
	methods: {
		async loadOverview() {
			try {
				this.overview = await get('/dashboard/overview');
			} catch (e) {}
		},
		goStudents() { uni.switchTab({ url: '/pages/student/list' }); },
		goIncome() { uni.navigateTo({ url: '/pages/income/income' }); },
		goSubjects() { uni.navigateTo({ url: '/pages/subjects/subjects' }); },
		goTeachers() { uni.navigateTo({ url: '/pages/teachers/teachers' }); },
		goPoints() { uni.navigateTo({ url: '/pages/points/points' }); }
	}
};
</script>

<style scoped>
.page { padding-bottom: 40rpx; }
.welcome {
	background: #10b981;
	color: #fff;
	padding: 48rpx 40rpx;
}
.welcome-name { font-size: 40rpx; font-weight: 700; }
.welcome-role { font-size: 26rpx; opacity: 0.85; margin-top: 8rpx; }
.stat-grid {
	display: flex;
	flex-wrap: wrap;
	margin: 20rpx;
}
.stat-card {
	width: calc(50% - 20rpx);
	background: #fff;
	border-radius: 16rpx;
	padding: 28rpx;
	margin-right: 20rpx;
	margin-bottom: 20rpx;
	box-sizing: border-box;
}
.stat-card:nth-child(2n) { margin-right: 0; }
.stat-num { display: block; font-size: 44rpx; font-weight: 700; color: #10b981; }
.stat-label { display: block; font-size: 24rpx; color: #909399; margin-top: 8rpx; }
.remind-item {
	padding: 16rpx 0;
	border-bottom: 1rpx solid #f0f0f0;
}
.remind-item:last-child { border-bottom: none; }
.remind-sub { font-size: 24rpx; margin-top: 6rpx; }
.empty { padding: 20rpx 0; text-align: center; }
.quick-grid { display: flex; flex-wrap: wrap; }
.quick-item {
	width: calc(33.33% - 16rpx);
	background: #f0fdf4;
	color: #10b981;
	text-align: center;
	padding: 28rpx 0;
	border-radius: 12rpx;
	margin-right: 16rpx;
	margin-bottom: 16rpx;
	font-size: 26rpx;
}
.quick-item:nth-child(3n) { margin-right: 0; }
</style>