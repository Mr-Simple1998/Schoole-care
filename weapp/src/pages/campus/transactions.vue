<template>
	<view class="page">
		<!-- 筛选 -->
		<view class="filter-bar">
			<picker :range="campusLabels" @change="e => onCampusChange(e.detail.value)">
				<view class="filter-item">{{ campusName }}<text class="arrow">▾</text></view>
			</picker>
			<picker :range="kindLabels" @change="e => onKindChange(e.detail.value)">
				<view class="filter-item">{{ kindName }}<text class="arrow">▾</text></view>
			</picker>
			<text class="filter-count">共 {{ txns.length }} 条</text>
		</view>

		<!-- 列表 -->
		<view v-for="t in pagedTxns" :key="t.id" class="card txn-row">
			<view class="txn-head">
				<view class="txn-left">
					<text class="tag" :class="t.kind === 'income' ? 'tag-success' : 'tag-danger'">
						{{ t.kind === 'income' ? '收入' : '支出' }}
					</text>
					<text class="txn-cat">{{ t.category }}</text>
					<text class="txn-campus">{{ t.campus_name }}</text>
				</view>
				<text class="txn-amount" :class="t.kind === 'income' ? 'income' : 'expense'">
					{{ t.kind === 'income' ? '+' : '-' }}¥{{ fmt(t.amount) }}
				</text>
			</view>
			<view class="txn-meta">
				<text>{{ t.record_date }}</text>
				<text v-if="t.remark" class="txn-remark">{{ t.remark }}</text>
				<text v-else class="text-muted">无备注</text>
				<text v-if="t.created_by_name">登记人：{{ t.created_by_name }}</text>
			</view>
			<view class="txn-actions">
				<text class="link danger" @click="delTxn(t)">删除</text>
			</view>
		</view>

		<view v-if="!txns.length && !loading" class="empty">暂无收支记录</view>

		<!-- 加载更多 -->
		<view v-if="pagedTxns.length && txns.length > pagedTxns.length" class="load-more" @click="loadMore">
			<text>已加载 {{ pagedTxns.length }} / {{ txns.length }} 条，点击加载更多</text>
		</view>
		<view v-else-if="pagedTxns.length" class="load-more all-loaded">
			<text>已全部加载（共 {{ txns.length }} 条）</text>
		</view>
	</view>
</template>

<script>
import { get, del } from '../../utils/request';

export default {
	data() {
		return {
			txns: [],
			campuses: [],
			campusId: null,
			kind: null,
			loading: false,
			// 前端分页：一次只渲染 20 条，滚动到底加载更多
			pageSize: 20,
			visibleCount: 20,
			kindLabels: ['全部类型', '收入', '支出'],
			kindValues: [null, 'income', 'expense']
		};
	},
	computed: {
		campusLabels() {
			return ['全部校区'].concat(this.campuses.map(c => c.name));
		},
		campusValues() {
			return [null].concat(this.campuses.map(c => c.id));
		},
		campusName() {
			const idx = this.campusValues.indexOf(this.campusId);
			return this.campusLabels[idx] || '全部校区';
		},
		kindName() {
			const idx = this.kindValues.indexOf(this.kind);
			return this.kindLabels[idx] || '全部类型';
		},
		pagedTxns() {
			return this.txns.slice(0, this.visibleCount);
		}
	},
	onLoad(options) {
		if (options && options.campus_id !== undefined && options.campus_id !== '') {
			this.campusId = Number(options.campus_id);
		}
		this.load();
	},
	onPullDownRefresh() {
		this.load(true).then(() => uni.stopPullDownRefresh());
	},
	onReachBottom() {
		this.loadMore();
	},
	methods: {
		fmt(n) {
			return Number(n || 0).toLocaleString('zh-CN', { maximumFractionDigits: 2 });
		},
		async load(refresh = false) {
			if (!refresh) this.loading = true;
			try {
				const params = {};
				if (this.campusId) params.campus_id = this.campusId;
				if (this.kind) params.kind = this.kind;
				this.txns = await get('/campuses/transactions', params);
				this.visibleCount = this.pageSize;
			} catch (e) {
			} finally {
				this.loading = false;
			}
			try {
				// 用概况接口取校区下拉：负责人只见自己校区
				const ov = await get('/campuses');
				this.campuses = (ov.items || []).map(c => ({ id: c.id, name: c.name }));
			} catch (e) {}
		},
		loadMore() {
			if (this.visibleCount < this.txns.length) {
				this.visibleCount += this.pageSize;
			}
		},
		onCampusChange(idx) {
			this.campusId = this.campusValues[idx];
			this.load();
		},
		onKindChange(idx) {
			this.kind = this.kindValues[idx];
			this.load();
		},
		delTxn(t) {
			uni.showModal({
				title: '提示',
				content: `确定删除这笔${t.kind === 'income' ? '收入' : '支出'}（¥${this.fmt(t.amount)}）吗？`,
				success: async (res) => {
					if (!res.confirm) return;
					try {
						await del(`/campuses/transactions/${t.id}`);
						uni.showToast({ title: '已删除', icon: 'success' });
						this.load();
					} catch (e) {}
				}
			});
		}
	}
};
</script>

<style scoped>
.page { padding: 20rpx 20rpx 60rpx; }
.filter-bar {
	display: flex;
	align-items: center;
	gap: 16rpx;
	margin-bottom: 20rpx;
}
.filter-item {
	background: #fff;
	border-radius: 12rpx;
	padding: 14rpx 22rpx;
	font-size: 26rpx;
	color: #303133;
}
.filter-item .arrow { color: #c0c4cc; margin-left: 8rpx; font-size: 22rpx; }
.filter-count { margin-left: auto; font-size: 24rpx; color: #909399; }
.txn-row { margin-bottom: 18rpx; }
.txn-head {
	display: flex;
	justify-content: space-between;
	align-items: center;
	gap: 12rpx;
}
.txn-left { display: flex; align-items: center; gap: 12rpx; min-width: 0; }
.txn-cat { font-size: 28rpx; font-weight: 600; color: #303133; }
.txn-campus { font-size: 22rpx; color: #909399; }
.txn-amount { font-size: 32rpx; font-weight: 700; }
.txn-amount.income { color: #10b981; }
.txn-amount.expense { color: #ef4444; }
.txn-meta {
	display: flex;
	flex-wrap: wrap;
	gap: 16rpx;
	font-size: 22rpx;
	color: #909399;
	margin-top: 10rpx;
}
.txn-remark { color: #6b7280; }
.txn-actions {
	border-top: 1rpx dashed #e5e7eb;
	margin-top: 14rpx;
	padding-top: 12rpx;
	text-align: right;
}
.link { font-size: 26rpx; }
.link.danger { color: #ef4444; }
.empty { text-align: center; color: #c0c4cc; padding: 60rpx 0; font-size: 26rpx; }
.load-more {
	text-align: center;
	padding: 24rpx 0;
	font-size: 24rpx;
	color: #10b981;
}
.load-more.all-loaded { color: #c0c4cc; }
</style>
