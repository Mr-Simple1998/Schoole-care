<template>
	<view class="page">
		<!-- 非校长引导兜底（入口仅校长可见，防御直达） -->
		<view v-if="!store.isPrincipal" class="card tip-card">
			<view class="tip-title">🔒 仅校长可查看已删除学生</view>
			<view class="tip-desc">请使用校长账号登录后查看；教师 / 校区负责人账号无此权限。</view>
		</view>

		<template v-else>
			<!-- 顶部说明 + 清空全部 -->
			<view v-if="students.length" class="card head-card">
				<view class="head-main">
					<view class="head-title">🗑️ 已删除学生档案（{{ students.length }}）</view>
					<view class="head-desc">以下学生已移出在读名单；可「彻底删除」抹除其全部数据（收费/考勤/成绩/积分等），不可恢复。</view>
				</view>
				<button class="btn-danger clear-btn" @click="purgeAll">清空全部</button>
			</view>

			<!-- 已删除学生列表 -->
			<view v-if="students.length" class="student-list">
				<view v-for="s in students" :key="s.id" class="card student-item">
					<view class="flex">
						<view class="avatar">{{ (s.name || '?')[0] }}</view>
						<view class="flex-1 info-row ir-body">
							<view class="ir-left">
								<view class="ir-title">{{ s.name }}<text class="s-no">{{ s.student_no }}</text></view>
								<view class="ir-sub">
									<text v-if="s.school">{{ s.school }}</text>
									<text v-if="s.grade">{{ s.grade }}</text>
									<text v-if="s.guardian_phone">{{ s.guardian_phone }}</text>
									<text v-else class="text-muted">未留电话</text>
								</view>
							</view>
							<view class="ir-right">
								<text class="tag tag-danger">已删除</text>
								<button class="purge-btn" @click="purgeOne(s)">彻底删除</button>
							</view>
						</view>
					</view>
					<view v-if="s.notes" class="s-subjects">
						<text class="sub-label">备注</text>
						<text class="sub-tag">{{ s.notes }}</text>
					</view>
				</view>
			</view>
			<view v-else-if="!loading" class="text-muted empty">暂无已删除学生记录</view>
			<view v-else class="loading-box">
				<view class="loading-spin"></view>
				<text class="loading-text">加载中...</text>
			</view>
		</template>
	</view>
</template>

<script>
import { useUserStore } from '../../stores/user';
import { get, del } from '../../utils/request';

export default {
	data() {
		return {
			store: useUserStore(),
			students: [],
			loading: false
		};
	},
	onShow() {
		if (this.store.isPrincipal) this.loadList();
	},
	onPullDownRefresh() {
		this.loadList(true).then(() => uni.stopPullDownRefresh());
	},
	methods: {
		async loadList(refresh = false) {
			if (!refresh) this.loading = true;
			try {
				this.students = await get('/students/deleted');
			} catch (e) {
			} finally {
				this.loading = false;
			}
		},
		// 彻底删除单名学生（不可恢复）
		purgeOne(s) {
			uni.showModal({
				title: '彻底删除确认',
				content: `确定彻底删除「${s.name}」吗？将永久删除其全部数据（收费记录、考勤、成绩、作业、积分等），无法恢复！`,
				confirmText: '彻底删除',
				confirmColor: '#dc2626',
				success: async (res) => {
					if (!res.confirm) return;
					try {
						const r = await del(`/students/deleted/${s.id}`);
						uni.showToast({ title: (r && r.detail) || '已彻底删除', icon: 'success' });
						this.loadList();
					} catch (e) {
						uni.showToast({ title: (e && (e.detail || e.message)) || '删除失败，请重试', icon: 'none' });
					}
				}
			});
		},
		// 一键清空全部已删除学生（不可恢复）
		purgeAll() {
			uni.showModal({
				title: '清空确认',
				content: `确定清空全部 ${this.students.length} 名已删除学生吗？将永久删除其全部数据，无法恢复！`,
				confirmText: '全部清空',
				confirmColor: '#dc2626',
				success: async (res) => {
					if (!res.confirm) return;
					try {
						const r = await del('/students/deleted');
						uni.showToast({ title: (r && r.detail) || '已清空', icon: 'success' });
						this.students = []; // 立即清空显示，不再展示任何已删除学生
						this.loadList(); // 双保险：重新拉取确认后端已清空
					} catch (e) {
						uni.showToast({ title: (e && (e.detail || e.message)) || '清空失败，请重试', icon: 'none' });
					}
				}
			});
		}
	}
};
</script>

<style scoped>
.page { padding-bottom: 40rpx; }
.tip-card { padding-top: 20rpx; }
.tip-title { font-size: 32rpx; font-weight: 700; color: #303133; margin-bottom: 12rpx; }
.tip-desc { font-size: 26rpx; color: #6b7280; line-height: 1.6; }
.head-card {
	display: flex;
	align-items: center;
	gap: 20rpx;
	margin: 20rpx;
	background: #fef2f2;
	border: 1rpx solid #fecaca;
}
.head-main { flex: 1; min-width: 0; }
.head-title { font-size: 30rpx; font-weight: 700; color: #dc2626; margin-bottom: 8rpx; }
.head-desc { font-size: 24rpx; color: #6b7280; line-height: 1.5; }
.btn-danger {
	flex-shrink: 0;
	background: #dc2626;
	color: #fff;
	border-radius: 12rpx;
	font-size: 26rpx;
	padding: 0 28rpx;
	height: 64rpx;
	line-height: 64rpx;
}
.clear-btn { margin: 0; }
.student-item { margin: 16rpx 20rpx; }
.avatar {
	width: 80rpx;
	height: 80rpx;
	border-radius: 50%;
	background: #10b981;
	color: #fff;
	text-align: center;
	line-height: 80rpx;
	font-size: 36rpx;
	margin-right: 20rpx;
	flex-shrink: 0;
}
.ir-body { padding: 4rpx 0; border-bottom: none; }
.s-no { font-size: 22rpx; color: #909399; margin-left: 10rpx; font-weight: 400; }
.ir-right {
	display: flex;
	align-items: center;
	gap: 12rpx;
}
.purge-btn {
	margin: 0;
	padding: 0 20rpx;
	height: 52rpx;
	line-height: 52rpx;
	font-size: 22rpx;
	background: #fef2f2;
	color: #dc2626;
	border: 1rpx solid #fca5a5;
	border-radius: 10rpx;
}
.s-subjects { margin-top: 16rpx; display: flex; align-items: center; flex-wrap: wrap; }
.sub-label { font-size: 22rpx; color: #909399; margin-right: 10rpx; }
.sub-tag {
	display: inline-block;
	font-size: 22rpx;
	color: #6b7280;
	background: #f5f7fa;
	border-radius: 8rpx;
	padding: 4rpx 14rpx;
	margin-right: 8rpx;
	margin-bottom: 6rpx;
}
.empty { text-align: center; padding: 80rpx 0; }
.loading-box {
	display: flex;
	flex-direction: column;
	align-items: center;
	padding: 80rpx 0;
	gap: 16rpx;
}
.loading-spin {
	width: 40rpx;
	height: 40rpx;
	border: 4rpx solid #e5e7eb;
	border-top-color: #10b981;
	border-radius: 50%;
	animation: spin 0.8s linear infinite;
}
@keyframes spin {
	to { transform: rotate(360deg); }
}
.loading-text { font-size: 24rpx; color: #909399; }
</style>
