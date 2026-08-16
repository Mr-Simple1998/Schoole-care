// 获取微信登录凭证（wx.login 的 code）
// 真实接入：uni.login 返回微信临时 code，后端用它通过 code2session 换取 openid
// 兼容回退：若 uni.login 失败（如未配置 AppID），生成本地模拟标识，便于本地联调
const SIM_KEY = 'wx_dev_openid';

function genId() {
	let s = '';
	for (let i = 0; i < 32; i++) s += Math.floor(Math.random() * 16).toString(16);
	return 'dev_' + s;
}

export function getWxCode() {
	return new Promise((resolve) => {
		let settled = false;
		const fallback = () => {
			if (settled) return;
			settled = true;
			clearTimeout(timer);
			resolve(getLocalSim());
		};
		// 开发者工具（真实 AppID 但无权限/未登录）下 uni.login 可能既不 success 也不 fail，
		// 加超时兜底，避免登录卡住无反应
		const timer = setTimeout(fallback, 2000);
		try {
			uni.login({
				provider: 'weixin',
				success: (res) => {
					if (settled) return;
					settled = true;
					clearTimeout(timer);
					resolve(res && res.code ? res.code : getLocalSim());
				},
				fail: () => fallback()
			});
		} catch (e) {
			fallback();
		}
	});
}

// 本地模拟标识（仅当 uni.login 失败时使用）
function getLocalSim() {
	let id = uni.getStorageSync(SIM_KEY);
	if (!id) {
		id = genId();
		uni.setStorageSync(SIM_KEY, id);
	}
	return id;
}