<script>
import { useUserStore } from './stores/user';

export default {
	onLaunch: function () {
		// 恢复本地登录态；无 token 时尝试静默登录（已绑定微信的账号自动进入）
		const store = useUserStore();
		store.init();
		if (store.token) {
			// 后台刷新一次用户信息（角色/校区可能已变化）
			store.fetchMe().catch(() => {});
		} else {
			store.silentLogin();
		}
	},
	onShow: function () { },
	onHide: function () { },
}
</script>

<style>
/* 全局公共样式 */
page {
	background-color: #f5f7fa;
	font-size: 28rpx;
	color: #303133;
}
/* 扁平通用卡片 */
.card {
	background: #fff;
	border-radius: 16rpx;
	padding: 24rpx;
	margin: 20rpx;
	box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.04);
}
.card-title {
	font-size: 30rpx;
	font-weight: 600;
	margin-bottom: 16rpx;
	display: flex;
	align-items: center;
	gap: 10rpx;
}
.card-title .bar {
	width: 8rpx;
	height: 28rpx;
	border-radius: 4rpx;
	background: #10b981;
	display: inline-block;
}
.text-muted { color: #909399; }
.text-primary { color: #10b981; }
.text-danger { color: #f56c6c; }
.text-warn { color: #e6a23c; }
.text-info { color: #3b82f6; }
.flex { display: flex; align-items: center; }
.flex-1 { flex: 1; }
.btn-primary { background: #10b981; color: #fff; border-radius: 12rpx; }

/* ============ 数据直观化工具类（仅展示层） ============ */

/* 统计卡片：可配不同强调色 */
.stat-card {
	background: #fff;
	border-radius: 16rpx;
	padding: 24rpx;
	box-sizing: border-box;
	position: relative;
	overflow: hidden;
	border: 1rpx solid #f0f0f0;
}
.stat-card .stat-top {
	display: flex;
	align-items: center;
	justify-content: space-between;
	margin-bottom: 12rpx;
}
.stat-card .stat-label { font-size: 24rpx; color: #909399; }
.stat-card .stat-emoji { font-size: 34rpx; }
.stat-card .stat-num {
	display: block;
	font-size: 44rpx;
	font-weight: 700;
	line-height: 1.2;
	color: #10b981;
	font-variant-numeric: tabular-nums;
}
.stat-card .stat-sub { display: block; font-size: 22rpx; color: #c0c4cc; margin-top: 6rpx; }
.stat-card.is-blue .stat-num { color: #3b82f6; }
.stat-card.is-green .stat-num { color: #10b981; }
.stat-card.is-orange .stat-num { color: #f59e0b; }
.stat-card.is-red .stat-num { color: #ef4444; }
.stat-card.is-purple .stat-num { color: #8b5cf6; }
.stat-card .stat-accent {
	position: absolute;
	left: 0;
	top: 0;
	bottom: 0;
	width: 8rpx;
}
.stat-card.is-blue .stat-accent { background: #3b82f6; }
.stat-card.is-green .stat-accent { background: #10b981; }
.stat-card.is-orange .stat-accent { background: #f59e0b; }
.stat-card.is-red .stat-accent { background: #ef4444; }
.stat-card.is-purple .stat-accent { background: #8b5cf6; }

/* 双列统计网格 */
.stat-grid {
	display: flex;
	flex-wrap: wrap;
	margin: 20rpx;
}
.stat-grid .stat-card {
	width: calc(50% - 20rpx);
	margin-right: 20rpx;
	margin-bottom: 20rpx;
}
.stat-grid .stat-card:nth-child(2n) { margin-right: 0; }

/* 标签 */
.tag {
	display: inline-flex;
	align-items: center;
	padding: 4rpx 14rpx;
	border-radius: 8rpx;
	font-size: 22rpx;
	line-height: 1.6;
	flex-shrink: 0;
}
.tag-success { background: #ecfdf5; color: #059669; }
.tag-danger { background: #fef2f2; color: #dc2626; }
.tag-warn { background: #fffbeb; color: #d97706; }
.tag-info { background: #eff6ff; color: #2563eb; }
.tag-primary { background: #d1fae5; color: #059669; }
.tag-grey { background: #f3f4f6; color: #6b7280; }
.tag-plain { background: #fff; color: #909399; border: 1rpx solid #e5e7eb; }

/* 状态圆点 */
.dot {
	width: 12rpx;
	height: 12rpx;
	border-radius: 50%;
	display: inline-block;
	margin-right: 8rpx;
}
.dot-green { background: #10b981; }
.dot-red { background: #ef4444; }
.dot-orange { background: #f59e0b; }
.dot-blue { background: #3b82f6; }
.dot-grey { background: #c0c4cc; }

/* 迷你进度条 */
.progress {
	height: 14rpx;
	background: #f0f0f0;
	border-radius: 7rpx;
	overflow: hidden;
	flex: 1;
}
.progress .progress-inner {
	height: 100%;
	border-radius: 7rpx;
	background: #10b981;
	transition: width 0.5s ease;
}
.progress.is-warn .progress-inner { background: #f59e0b; }
.progress.is-danger .progress-inner { background: #ef4444; }
.progress.is-info .progress-inner { background: #3b82f6; }
.progress-text { font-size: 22rpx; color: #909399; margin-left: 12rpx; }

/* 提醒横幅 */
.banner {
	display: flex;
	align-items: flex-start;
	gap: 12rpx;
	padding: 20rpx 24rpx;
	border-radius: 16rpx;
	margin: 20rpx;
	font-size: 26rpx;
}
.banner .banner-title { font-weight: 600; }
.banner .banner-desc { font-size: 24rpx; margin-top: 4rpx; opacity: 0.9; }
.banner.is-warn { background: #fffbeb; color: #b45309; border: 1rpx solid #fde68a; }
.banner.is-danger { background: #fef2f2; color: #b91c1c; border: 1rpx solid #fecaca; }
.banner.is-info { background: #eff6ff; color: #1d4ed8; border: 1rpx solid #bfdbfe; }
.banner.is-success { background: #ecfdf5; color: #047857; border: 1rpx solid #a7f3d0; }

/* 键值行 */
.kv-row {
	display: flex;
	padding: 18rpx 0;
	border-bottom: 1rpx dashed #f0f0f0;
	font-size: 26rpx;
}
.kv-row:last-child { border-bottom: none; }
.kv-row .kv-label { width: 170rpx; flex-shrink: 0; color: #909399; }
.kv-row .kv-value { flex: 1; color: #303133; word-break: break-all; }

/* 信息行（列表项） */
.info-row {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 16rpx;
	padding: 22rpx 0;
	border-bottom: 1rpx solid #f5f5f5;
}
.info-row:last-child { border-bottom: none; }
.info-row .ir-left { min-width: 0; flex: 1; }
.info-row .ir-title { font-size: 28rpx; font-weight: 500; color: #303133; }
.info-row .ir-sub { font-size: 24rpx; color: #909399; margin-top: 6rpx; display: flex; align-items: center; gap: 10rpx; flex-wrap: wrap; }
.info-row .ir-right { flex-shrink: 0; display: flex; align-items: center; gap: 10rpx; }

/* 排行榜行 */
.rank-row {
	display: flex;
	align-items: center;
	gap: 16rpx;
	padding: 20rpx 0;
	border-bottom: 1rpx solid #f5f5f5;
}
.rank-row:last-child { border-bottom: none; }
.rank-badge {
	width: 44rpx;
	height: 44rpx;
	border-radius: 12rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 24rpx;
	font-weight: 700;
	flex-shrink: 0;
	background: #f3f4f6;
	color: #6b7280;
}
.rank-badge.top1 { background: linear-gradient(135deg, #fbbf24, #f59e0b); color: #fff; }
.rank-badge.top2 { background: linear-gradient(135deg, #e5e7eb, #9ca3af); color: #fff; }
.rank-badge.top3 { background: linear-gradient(135deg, #f59e0b, #d97706); color: #fff; }
.rank-name { flex: 1; font-size: 26rpx; color: #303133; }
.rank-score { font-size: 28rpx; font-weight: 700; color: #f59e0b; font-variant-numeric: tabular-nums; }

/* 金额 */
.amount { color: #ef4444; font-weight: 600; font-variant-numeric: tabular-nums; }
.amount.income { color: #10b981; }

/* 空状态 */
.empty {
	text-align: center;
	color: #c0c4cc;
	font-size: 24rpx;
	padding: 40rpx 0;
}

/* 区块小标题 */
.section-title {
	display: flex;
	align-items: center;
	gap: 10rpx;
	font-size: 28rpx;
	font-weight: 600;
	color: #303133;
	margin: 24rpx 20rpx 8rpx;
}
.section-title .bar {
	width: 8rpx;
	height: 28rpx;
	border-radius: 4rpx;
	background: #10b981;
	display: inline-block;
}

/* 分隔线 */
.divider { height: 1rpx; background: #f0f0f0; margin: 16rpx 0; }
</style>