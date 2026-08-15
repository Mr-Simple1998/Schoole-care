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
		uni.login({
			provider: 'weixin',
			success: (res) => {
				if (res && res.code) {
					resolve(res.code);
				} else {
					resolve(getLocalSim());
				}
			},
			fail: () => resolve(getLocalSim())
		});
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