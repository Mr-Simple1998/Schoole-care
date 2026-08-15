<template>
	<view class="page">
		<view class="card profile">
			<view class="avatar">{{ (store.userName || '?')[0] }}</view>
			<view class="flex-1" style="margin-left:20rpx">
				<view class="p-name">{{ store.userName }}</view>
				<view class="text-muted p-role">{{ roleText }} · {{ store.user && store.user.username }}</view>
			</view>
		</view>

		<view class="card">
			<view class="menu-item" @click="goIncome" v-if="store.isPrincipal">
				<text>收费管理</text><text class="arrow">›</text>
			</view>
			<view class="menu-item" @click="goTeachers" v-if="store.isPrincipal">
				<text>教师管理</text><text class="arrow">›</text>
			</view>
			<view class="menu-item" @click="goSubjects" v-if="store.isPrincipal">
				<text>学科管理</text><text class="arrow">›</text>
			</view>
			<view class="menu-item" @click="goPoints">
				<text>积分管理</text><text class="arrow">›</text>
			</view>
		</view>

		<button class="logout-btn" @click="doLogout">退出登录</button>
	</view>
</template>

<script>
import { useUserStore } from '../../stores/user';

export default {
	data() {
		return { store: useUserStore() };
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
	methods: {
		goIncome() { uni.navigateTo({ url: '/pages/income/income' }); },
		goTeachers() { uni.navigateTo({ url: '/pages/teachers/teachers' }); },
		goSubjects() { uni.navigateTo({ url: '/pages/subjects/subjects' }); },
		goPoints() { uni.navigateTo({ url: '/pages/points/points' }); },
		doLogout() {
			uni.showModal({
				title: '提示',
				content: '确定退出登录吗？',
				success: (res) => { if (res.confirm) this.store.logout(); }
			});
		}
	}
};
</script>

<style scoped>
.page { padding-bottom: 40rpx; }
.profile { display: flex; align-items: center; }
.avatar {
	width: 100rpx; height: 100rpx; border-radius: 50%;
	background: #10b981; color: #fff; text-align: center; line-height: 100rpx; font-size: 44rpx;
}
.p-name { font-size: 34rpx; font-weight: 600; }
.p-role { font-size: 24rpx; margin-top: 6rpx; }
.menu-item {
	display: flex; justify-content: space-between; align-items: center;
	padding: 28rpx 4rpx; border-bottom: 1rpx solid #f5f5f5; font-size: 30rpx;
}
.menu-item:last-child { border-bottom: none; }
.arrow { color: #c0c4cc; font-size: 36rpx; }
.logout-btn {
	margin: 40rpx 20rpx; background: #fff; color: #f56c6c;
	border: 1rpx solid #f56c6c; border-radius: 12rpx;
}
</style>