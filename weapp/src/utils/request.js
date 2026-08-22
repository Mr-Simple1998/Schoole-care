// 请求封装：统一 baseUrl、token 注入、错误处理
// 生产环境默认微信云托管域名（见 DEPLOY_CLOUD.md）；
// 本地联调可运行时调用 setApiBase('http://127.0.0.1:8000/api') 覆盖，或临时改回本地地址
// 注意：不要在此文件使用 import.meta（mp-weixin 构建会转译出 require("url") 导致小程序启动崩溃）
let BASE_URL = 'https://express-4ml2-297660-5-1312930292.sh.run.tcloudbase.com/api';
const CLOUD_ENV_ID = '297660-5';
const CLOUD_SERVICE = 'express-4ml2';
const CLOUD_API_PREFIX = '/api';

export function setApiBase(url) {
	if (url) BASE_URL = url;
}

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

function cleanParams(params) {
	if (!params || typeof params !== 'object') return params;
	return Object.fromEntries(
		Object.entries(params).filter(([, value]) => value !== undefined && value !== null && value !== '')
	);
}

// 错误 toast 去重：并发请求失败时只提示一次，避免连续弹窗刷屏
let lastToast = { title: '', time: 0 };
function showErrToast(title) {
	const now = Date.now();
	if (lastToast.title === title && now - lastToast.time < 2000) return;
	lastToast = { title, time: now };
	uni.showToast({ title, icon: 'none', duration: 2500 });
}

// 从后端错误响应里提取可读的中文提示：
// - detail 为字符串（业务错误）→ 直接显示
// - detail 为数组（FastAPI 422 校验错误，元素是 {loc,msg}）→ 取第一条 msg，避免显示 [object Object]
// - message 字符串 → 显示
function extractDetail(data) {
	if (!data) return '请求失败';
	const d = data.detail;
	if (typeof d === 'string') return d;
	if (Array.isArray(d) && d.length) {
		const first = d[0] || {};
		const loc = Array.isArray(first.loc) && first.loc.length ? first.loc.join('.') : '';
		const msg = first.msg || '';
		if (loc && msg) return `参数 ${loc}：${msg}`;
		if (msg) return msg;
		if (loc) return `参数错误：${loc}`;
		return '请求参数有误';
	}
	if (typeof data.message === 'string') return data.message;
	return '请求失败';
}

export function request(options) {
	return new Promise((resolve, reject) => {
		const header = Object.assign({}, options.header || {});
		const token = getToken();
		if (token) header['Authorization'] = 'Bearer ' + token;
		const method = options.method || 'GET';
		const data = method.toUpperCase() === 'GET' ? cleanParams(options.data || {}) : (options.data || {});
		// 需要操作型请求可带 loading：true，自动弹加载框并避免重复点击
		if (options.loading) {
			uni.showLoading({ title: options.loadingText || '处理中...', mask: true });
		}

		const success = (res) => {
			if (options.loading) uni.hideLoading();
			if (res.statusCode >= 200 && res.statusCode < 300) {
				resolve(res.data);
			} else if (res.statusCode === 401) {
				toLogin();
				reject(res.data || { detail: '未授权' });
			} else {
				const msg = extractDetail(res.data);
				if (!options.silent) showErrToast(msg);
				reject(res.data || {});
			}
		};
		const fail = (err) => {
			if (options.loading) uni.hideLoading();
			if (!options.silent) showErrToast('网络异常，请检查后端是否启动');
			reject(err);
		};

		if (typeof wx !== 'undefined' && wx.cloud && typeof wx.cloud.callContainer === 'function') {
			wx.cloud.callContainer({
				config: { env: CLOUD_ENV_ID },
				path: CLOUD_API_PREFIX + options.url,
				method,
				data,
				header: Object.assign({}, header, { 'X-WX-SERVICE': CLOUD_SERVICE }),
				success,
				fail
			});
			return;
		}

		uni.request({
			url: BASE_URL + options.url,
			method,
			data,
			header,
			timeout: options.timeout || 15000,
			success,
			fail
		});
	});
}

export const get = (url, data = {}) => request({ url, method: 'GET', data });
export const post = (url, data = {}) => request({ url, method: 'POST', data });
export const put = (url, data = {}) => request({ url, method: 'PUT', data });
export const del = (url, data = {}) => request({ url, method: 'DELETE', data });
