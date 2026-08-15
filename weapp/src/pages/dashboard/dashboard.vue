<template>
	<view class="page">
		<!-- 欢迎头 -->
		<view class="welcome">
			<view class="welcome-name">{{ store.userName }}，你好</view>
			<view class="welcome-role">{{ roleText }}</view>
		</view>

		<!-- 到期提醒横幅 -->
		<view v-if="overview.fee_expire_reminders && overview.fee_expire_reminders.length" class="banner" :class="hasExpired ? 'is-danger' : 'is-warn'">
			<view>
				<view class="banner-title">{{ hasExpired ? '⚠️ 有费用 / 课时已到期' : '⏰ 费用 / 课时即将到期' }}</view>
				<view class="banner-desc">{{ overview.fee_expire_reminders.length }} 条待处理，请及时联系家长续费</view>
			</view>
		</view>

		<!-- 统计卡片 -->
		<view class="stat-grid">
			<view class="stat-card is-blue" @click="goStudents">
				<view class="stat-top">
					<text class="stat-label">学生总数</text>
					<text class="stat-emoji">👥</text>
				</view>
				<text class="stat-num">{{ overview.total_students || 0 }}</text>
			</view>
			<view class="stat-card is-green" v-if="store.isPrincipal || store.isSubPrincipal">
				<view class="stat-top">
					<text class="stat-label">本月收入</text>
					<text class="stat-emoji">💰</text>
				</view>
				<text class="stat-num">¥{{ overview.month_income || 0 }}</text>
			</view>
			<view class="stat-card is-orange">
				<view class="stat-top">
					<text class="stat-label">今日考勤</text>
					<text class="stat-emoji">📋</text>
				</view>
				<text class="stat-num">{{ overview.today_attendance || 0 }}</text>
			</view>
			<view class="stat-card is-red" v-if="store.isPrincipal || store.isSubPrincipal">
				<view class="stat-top">
					<text class="stat-label">总欠费</text>
					<text class="stat-emoji">⚠️</text>
				</view>
				<text class="stat-num">¥{{ overview.total_unpaid || 0 }}</text>
			</view>
		</view>

		<!-- 到期提醒 -->
		<view class="card">
			<view class="card-title"><text class="bar"></text>费用 / 课时到期提醒</view>
			<view v-if="overview.fee_expire_reminders && overview.fee_expire_reminders.length">
				<view v-for="(r, i) in overview.fee_expire_reminders" :key="i" class="info-row">
					<view class="ir-left">
						<view class="ir-title">{{ r.student_name }}</view>
						<view class="ir-sub">{{ r.fee_type }} · {{ r.expire_date }} · {{ r.teacher_name || '未分配' }}</view>
					</view>
					<view class="ir-right">
						<text :class="r.days_left < 0 ? 'tag tag-danger' : 'tag tag-warn'">
							{{ r.days_left < 0 ? '已到期 ' + (-r.days_left) + '天' : '剩 ' + r.days_left + ' 天' }}
						</text>
					</view>
				</view>
			</view>
			<view v-else class="empty">暂无到期提醒</view>
		</view>

		<!-- 快捷入口 -->
		<view class="card">
			<view class="card-title"><text class="bar"></text>快捷操作</view>
			<view class="quick-grid">
				<view class="quick-item" @click="goStudents"><text class="qi-emoji">👥</text><text>学生管理</text></view>
				<view class="quick-item" @click="goIncome" v-if="store.isPrincipal || store.isSubPrincipal"><text class="qi-emoji">💰</text><text>收费管理</text></view>
				<view class="quick-item" @click="goSubjects" v-if="store.isPrincipal"><text class="qi-emoji">📚</text><text>学科管理</text></view>
				<view class="quick-item" @click="goTeachers" v-if="store.isPrincipal || store.isSubPrincipal"><text class="qi-emoji">👩‍🏫</text><text>教师管理</text></view>
				<view class="quick-item" @click="goPoints"><text class="qi-emoji">🏆</text><text>积分管理</text></view>
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
			if (r === 'principal') return '总校长';
			if (r === 'sub_principal' || r === 'campus_head') return '校长管理号';
			if (r === 'teacher') return '教师';
			if (r === 'platform') return '平台管理员';
			return '';
		},
		// 纯展示：是否存在已到期的提醒（决定横幅颜色）
		hasExpired() {
			return (this.overview.fee_expire_reminders || []).some((r) => r.days_left < 0);
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
	background: linear-gradient(135deg, #10b981, #059669);
	color: #fff;
	padding: 48rpx 40rpx;
}
.welcome-name { font-size: 40rpx; font-weight: 700; }
.welcome-role { font-size: 26rpx; opacity: 0.85; margin-top: 8rpx; }
.quick-grid { display: flex; flex-wrap: wrap; }
.quick-item {
	width: calc(33.33% - 16rpx);
	background: #f0fdf4;
	color: #10b981;
	text-align: center;
	padding: 24rpx 0;
	border-radius: 12rpx;
	margin-right: 16rpx;
	margin-bottom: 16rpx;
	font-size: 26rpx;
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 8rpx;
}
.quick-item:nth-child(3n) { margin-right: 0; }
.qi-emoji { font-size: 36rpx; }
</style>
