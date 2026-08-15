<script>
export default {
	onLaunch: function () {
		console.log('小程序启动');
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
}
.text-muted { color: #909399; }
.text-primary { color: #10b981; }
.text-danger { color: #f56c6c; }
.text-warn { color: #e6a23c; }
.flex { display: flex; align-items: center; }
.flex-1 { flex: 1; }
.btn-primary { background: #10b981; color: #fff; border-radius: 12rpx; }
</style>