// 请求封装：统一 baseUrl、token 注入、错误处理
const BASE_URL = 'http://127.0.0.1:8000/api';

export function getToken() {
	return uni.getStorageSync('token') || '';
}

export function setAuth(token, user) {
	uni.setStorageSync('token', token);
	uni.setStorageSync('user', user);
}

export function clearAuth() {
	uni.removeStorageSync('token');
	uni.removeStorageSync('user');
}

function toLogin() {
	clearAuth();
	uni.reLaunch({ url: '/pages/login/login' });
}

export function request(options) {
	return new Promise((resolve, reject) => {
		const header = Object.assign({}, options.header || {});
		const token = getToken();
		if (token) header['Authorization'] = 'Bearer ' + token;

		uni.request({
			url: BASE_URL + options.url,
			method: options.method || 'GET',
			data: options.data || {},
			header,
			timeout: 15000,
			success(res) {
				if (res.statusCode >= 200 && res.statusCode < 300) {
					resolve(res.data);
				} else if (res.statusCode === 401) {
					toLogin();
					reject(res.data || { detail: '未授权' });
				} else {
					const msg = (res.data && (res.data.detail || res.data.message)) || '请求失败';
					uni.showToast({ title: String(msg), icon: 'none', duration: 2500 });
					reject(res.data || {});
				}
			},
			fail(err) {
				uni.showToast({ title: '网络异常，请检查后端是否启动', icon: 'none', duration: 2500 });
				reject(err);
			}
		});
	});
}

export const get = (url, data = {}) => request({ url, method: 'GET', data });
export const post = (url, data = {}) => request({ url, method: 'POST', data });
export const put = (url, data = {}) => request({ url, method: 'PUT', data });
export const del = (url, data = {}) => request({ url, method: 'DELETE', data });