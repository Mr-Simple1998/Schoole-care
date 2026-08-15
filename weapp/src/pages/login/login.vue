<template>
	<view class="login-page">
		<view class="logo-title">机构后台管理</view>
		<view class="logo-sub">微信授权 · 账号绑定登录</view>

		<view class="card login-card">
			<view class="field">
				<text class="label">用户名</text>
				<input class="input" v-model="username" placeholder="请输入用户名" />
			</view>
			<view class="field">
				<text class="label">密码</text>
				<input class="input" v-model="password" password placeholder="请输入密码" />
			</view>
			<button class="btn-primary login-btn" @click="doBind" :loading="loading">登录并绑定微信</button>
			<view class="tip">首次需输入校长/教师账号密码完成微信绑定，之后自动登录</view>
		</view>
	</view>
</template>

<script>
import { useUserStore } from '../../stores/user';

export default {
	data() {
		return {
			username: '',
			password: '',
			loading: false
		};
	},
	onLoad() {
		// 尝试静默登录（本地 openid 已绑定时直接进入）
		const store = useUserStore();
		if (store.token) {
			uni.switchTab({ url: '/pages/dashboard/dashboard' });
		}
	},
	methods: {
		async doBind() {
			if (!this.username || !this.password) {
				uni.showToast({ title: '请输入用户名和密码', icon: 'none' });
				return;
			}
			this.loading = true;
			try {
				const store = useUserStore();
				await store.bindLogin(this.username, this.password);
				uni.showToast({ title: '登录成功', icon: 'success' });
				setTimeout(() => uni.switchTab({ url: '/pages/dashboard/dashboard' }), 500);
			} catch (e) {
				// 错误已由 request 统一提示
			} finally {
				this.loading = false;
			}
		}
	}
};
</script>

<style scoped>
.login-page {
	min-height: 100vh;
	background: linear-gradient(160deg, #10b981 0%, #0ea5e9 100%);
	padding: 120rpx 40rpx;
}
.logo-title {
	color: #fff;
	font-size: 56rpx;
	font-weight: 700;
	text-align: center;
}
.logo-sub {
	color: rgba(255, 255, 255, 0.85);
	font-size: 28rpx;
	text-align: center;
	margin: 16rpx 0 60rpx;
}
.login-card {
	padding: 40rpx 32rpx;
}
.field {
	margin-bottom: 28rpx;
}
.label {
	display: block;
	font-size: 26rpx;
	color: #606266;
	margin-bottom: 10rpx;
}
.input {
	background: #f5f7fa;
	border-radius: 12rpx;
	padding: 20rpx 24rpx;
	font-size: 30rpx;
}
.login-btn {
	margin-top: 20rpx;
	width: 100%;
}
.tip {
	margin-top: 24rpx;
	font-size: 24rpx;
	color: #909399;
	text-align: center;
}
</style>