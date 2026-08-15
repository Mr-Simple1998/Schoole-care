import { defineStore } from 'pinia';
import { getToken, setAuth, clearAuth, get, post } from '../utils/request';
import { getWxCode } from '../utils/openid';

export const useUserStore = defineStore('user', {
	state: () => ({
		token: '',
		user: null
	}),
	getters: {
		isLogin: (s) => !!s.token,
		isPrincipal: (s) => s.user && s.user.role === 'principal',
		isSubPrincipal: (s) => s.user && (s.user.role === 'sub_principal' || s.user.role === 'campus_head'),
		isTeacher: (s) => s.user && s.user.role === 'teacher',
		isCampusHead: (s) => s.user && s.user.role === 'campus_head',
		isPlatform: (s) => s.user && s.user.role === 'platform',
		userName: (s) => (s.user && s.user.name) || ''
	},
	actions: {
		init() {
			this.token = getToken();
			this.user = uni.getStorageSync('user') || null;
		},
		// 静默登录：用微信 code 尝试直接登录（后端 code2session 换 openid）
		async silentLogin() {
			if (!this.token) {
				try {
					const code = await getWxCode();
					const res = await post('/auth/wx-login', { code });
					this.setAuthData(res);
					return true;
				} catch (e) {
					return false;
				}
			}
			return true;
		},
		// 绑定登录：校验账号密码并绑定当前微信 openid
		async bindLogin(username, password) {
			const code = await getWxCode();
			const res = await post('/auth/wx-bind', {
				username,
				password,
				wx_openid: code
			});
			this.setAuthData(res);
			return res;
		},
		setAuthData(res) {
			this.token = res.access_token;
			this.user = res.user;
			setAuth(res.access_token, res.user);
		},
		async fetchMe() {
			const me = await get('/auth/me');
			this.user = me;
			uni.setStorageSync('user', me);
		},
		logout() {
			this.token = '';
			this.user = null;
			clearAuth();
			uni.reLaunch({ url: '/pages/login/login' });
		}
	}
});