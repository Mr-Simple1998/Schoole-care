import { defineStore } from 'pinia';
import { getToken, setAuth, clearAuth, get, post, request } from '../utils/request';
import { getWxCode, getWxDeviceId } from '../utils/openid';

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
					// silent: true 避免未绑定账号（后端 404 NOT_BOUND）时弹出提示
					const res = await request({ url: '/auth/wx-login', method: 'POST', data: { code, device_id: getWxDeviceId() }, silent: true });
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
				wx_openid: code,
				device_id: getWxDeviceId()
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
