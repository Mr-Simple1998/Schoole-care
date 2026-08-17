<template>
	<view class="login-page">
		<!-- 品牌区（纯展示） -->
		<view class="brand">
			<view class="brand-logo">📚</view>
			<view class="logo-title">机构后台管理</view>
			<view class="logo-sub">微信授权 · 账号绑定登录</view>
		</view>

		<!-- 登录卡片 -->
		<view class="login-card">
			<view class="card-title"><view class="bar"></view>账号登录</view>
			<view class="field">
				<text class="label">用户名</text>
				<view class="input-wrap">
					<text class="input-icon">👤</text>
					<input class="input" v-model="username" placeholder="请输入用户名" />
				</view>
			</view>
			<view class="field">
				<text class="label">密码</text>
				<view class="input-wrap">
					<text class="input-icon">🔒</text>
					<input class="input" v-model="password" password placeholder="请输入密码" />
				</view>
			</view>
			<button class="btn-primary login-btn" @click="doBind" :loading="loading">登录并绑定微信</button>
			<view class="tip">首次需输入校长/校区负责人/教师账号密码完成微信绑定，之后自动登录</view>
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
			loading: false,
			silentDone: false
		};
	},
	onShow() {
		// 每次回到登录页都尝试：已有 token 直接进入；否则静默登录（本地 openid 已绑定时自动进入）
		const store = useUserStore();
		store.init();
		if (store.token) {
			this.afterLogin(store);
			return;
		}
		if (this.silentDone) return; // 本次会话已尝试过静默登录，避免重复请求
		this.silentDone = true;
		store.silentLogin().then((ok) => {
			if (ok && store.token) this.afterLogin(store);
		});
	},
	methods: {
		// 平台超级管理员直接进入机构开户管理（与 PC 端一致）；其他角色进入工作台
		afterLogin(store) {
			if (store.isPlatform) {
				uni.reLaunch({ url: '/pages/platform/platform' });
			} else {
				uni.switchTab({ url: '/pages/dashboard/dashboard' });
			}
		},
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
				setTimeout(() => this.afterLogin(store), 500);
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
	box-sizing: border-box;
	background: linear-gradient(160deg, #0f9d74 0%, #10b981 45%, #0ea5e9 100%);
	padding: 140rpx 44rpx 80rpx;
}

/* 品牌区 */
.brand {
	text-align: center;
	margin-bottom: 64rpx;
}
.brand-logo {
	width: 128rpx;
	height: 128rpx;
	line-height: 128rpx;
	border-radius: 36rpx;
	background: rgba(255, 255, 255, 0.18);
	border: 2rpx solid rgba(255, 255, 255, 0.35);
	backdrop-filter: blur(8rpx);
	text-align: center;
	font-size: 64rpx;
	margin: 0 auto 28rpx;
	box-shadow: 0 12rpx 32rpx rgba(0, 0, 0, 0.12);
}
.logo-title {
	color: #fff;
	font-size: 48rpx;
	font-weight: 700;
	letter-spacing: 2rpx;
	text-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.15);
}
.logo-sub {
	color: rgba(255, 255, 255, 0.88);
	font-size: 26rpx;
	margin-top: 14rpx;
	letter-spacing: 1rpx;
}

/* 登录卡片 */
.login-card {
	background: #fff;
	border-radius: 24rpx;
	padding: 44rpx 36rpx;
	box-shadow: 0 16rpx 48rpx rgba(0, 0, 0, 0.12);
}
.login-card .card-title {
	font-size: 32rpx;
	margin-bottom: 32rpx;
}
.field { margin-bottom: 28rpx; }
.label {
	display: block;
	font-size: 26rpx;
	color: #606266;
	margin-bottom: 12rpx;
}
.input-wrap {
	display: flex;
	align-items: center;
	background: #f5f7fa;
	border-radius: 14rpx;
	padding: 0 24rpx;
	border: 1rpx solid transparent;
	transition: border-color 0.2s;
}
.input-wrap:focus-within { border-color: #10b981; }
.input-icon {
	font-size: 28rpx;
	margin-right: 16rpx;
	flex-shrink: 0;
}
.input {
	flex: 1;
	background: transparent;
	padding: 20rpx 0;
	font-size: 30rpx;
}
.login-btn {
	margin-top: 36rpx;
	width: 100%;
	height: 92rpx;
	line-height: 92rpx;
	font-size: 30rpx;
	font-weight: 600;
	background: linear-gradient(90deg, #10b981, #059669);
	border-radius: 14rpx;
	box-shadow: 0 8rpx 20rpx rgba(16, 185, 129, 0.3);
	letter-spacing: 2rpx;
}
.login-btn::after { border: none; }
.tip {
	margin-top: 26rpx;
	font-size: 22rpx;
	color: #b0b3b8;
	text-align: center;
	line-height: 1.6;
}
</style>
