<template>
	<view class="page">
		<view class="card profile">
			<view class="avatar">{{ (store.userName || '?')[0] }}</view>
			<view class="flex-1" style="margin-left:20rpx">
				<view class="p-name">{{ store.userName }}</view>
				<view class="p-sub">
					<text :class="'tag ' + roleTagClass">{{ roleText }}</text>
					<text class="text-muted p-username">{{ store.user && store.user.username }}</text>
				</view>
			</view>
		</view>

		<view class="card">
			<!-- 平台超级管理员：与 PC 端一致，仅机构开户管理 -->
			<view class="menu-item" @click="goPlatform" v-if="store.isPlatform">
				<view class="mi-left"><text class="mi-emoji">🏢</text><text>机构开户管理</text></view>
				<text class="arrow">›</text>
			</view>
			<template v-else>
				<view class="menu-item" @click="goIncome" v-if="store.isPrincipal || store.isSubPrincipal">
					<view class="mi-left"><text class="mi-emoji">💰</text><text>收费管理</text></view>
					<text class="arrow">›</text>
				</view>
				<view class="menu-item" @click="goTeachers" v-if="store.isPrincipal || store.isSubPrincipal">
					<view class="mi-left"><text class="mi-emoji">👩‍🏫</text><text>教师管理</text></view>
					<text class="arrow">›</text>
				</view>
				<view class="menu-item" @click="goSubjects" v-if="store.isPrincipal">
					<view class="mi-left"><text class="mi-emoji">📚</text><text>学科管理</text></view>
					<text class="arrow">›</text>
				</view>
				<view class="menu-item" @click="goCampus" v-if="store.isPrincipal || store.isSubPrincipal">
					<view class="mi-left"><text class="mi-emoji">🏫</text><text>校区管理</text></view>
					<text class="arrow">›</text>
				</view>
				<view class="menu-item" @click="goPoints">
					<view class="mi-left"><text class="mi-emoji">🏆</text><text>积分管理</text></view>
					<text class="arrow">›</text>
				</view>
			</template>
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
			if (r === 'principal') return '总校长';
			if (r === 'sub_principal' || r === 'campus_head') return '校长管理号';
			if (r === 'teacher') return '教师';
			if (r === 'platform') return '平台管理员';
			return '';
		},
		// 纯展示：角色标签配色
		roleTagClass() {
			const r = this.store.user && this.store.user.role;
			if (r === 'platform') return 'tag-danger';
			if (r === 'principal') return 'tag-warn';
			if (r === 'sub_principal' || r === 'campus_head') return 'tag-success';
			return 'tag-primary';
		}
	},
	methods: {
		goIncome() { uni.navigateTo({ url: '/pages/income/income' }); },
		goTeachers() { uni.navigateTo({ url: '/pages/teachers/teachers' }); },
		goSubjects() { uni.navigateTo({ url: '/pages/subjects/subjects' }); },
		goPoints() { uni.navigateTo({ url: '/pages/points/points' }); },
		goCampus() { uni.navigateTo({ url: '/pages/campus/campus' }); },
		goPlatform() { uni.navigateTo({ url: '/pages/platform/platform' }); },
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
.profile {
	display: flex;
	align-items: center;
	background: linear-gradient(135deg, #ffffff, #ecfdf5);
}
.avatar {
	width: 100rpx; height: 100rpx; border-radius: 50%;
	background: linear-gradient(135deg, #10b981, #059669); color: #fff;
	text-align: center; line-height: 100rpx; font-size: 44rpx;
}
.p-name { font-size: 34rpx; font-weight: 600; }
.p-sub { display: flex; align-items: center; gap: 12rpx; margin-top: 10rpx; }
.p-username { font-size: 24rpx; }
.menu-item {
	display: flex; justify-content: space-between; align-items: center;
	padding: 28rpx 4rpx; border-bottom: 1rpx solid #f5f5f5; font-size: 30rpx;
}
.menu-item:last-child { border-bottom: none; }
.mi-left { display: flex; align-items: center; gap: 16rpx; }
.mi-emoji { font-size: 32rpx; }
.arrow { color: #c0c4cc; font-size: 36rpx; }
.logout-btn {
	margin: 40rpx 20rpx; background: #fff; color: #f56c6c;
	border: 1rpx solid #f56c6c; border-radius: 12rpx;
}
</style>