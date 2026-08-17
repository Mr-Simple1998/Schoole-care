<template>
	<view class="page">
		<!-- 积分排行榜 -->
		<view class="card">
			<view class="card-title"><text class="bar"></text>积分排行榜</view>
			<view v-for="s in leaderboard" :key="s.id" class="rank-row">
				<view class="rank-badge" :class="rankBadgeClass(s.rank)">{{ s.rank }}</view>
				<text class="rank-name">{{ s.name }}</text>
				<text class="rank-score">{{ s.points }} 分</text>
			</view>
			<view v-if="!leaderboard.length" class="empty">暂无数据</view>
		</view>

		<!-- 学生积分（加/扣积分，逻辑不变） -->
		<view class="card">
			<view class="card-title"><text class="bar"></text>加/扣积分</view>
			<view class="field">
				<text class="label">选择学生</text>
				<picker :range="students.map(s=>s.name)" @change="e => changeForm.student_id=students[e.detail.value].id">
					<view class="input">{{ changeStudentName }}</view>
				</picker>
				<text v-if="selectedStudentPoints !== null" class="points-hint">当前积分：<text class="text-warn">{{ selectedStudentPoints }}</text> 分</text>
			</view>
			<view class="field">
				<text class="label">积分变动（正数加，负数扣）</text>
				<input class="input" type="number" v-model="changeForm.change" placeholder="如 5 或 -3" />
			</view>
			<view class="field"><text class="label">原因</text><input class="input" v-model="changeForm.reason" placeholder="如表现优秀" /></view>
			<button class="btn-primary points-submit" @click="doChange">提交</button>
		</view>

		<!-- 积分记录 -->
		<view class="card">
			<view class="card-title"><text class="bar"></text>积分记录</view>
			<view v-for="r in pagedRecords" :key="r.id" class="info-row">
				<view class="ir-left">
					<view class="ir-title">{{ r.student_name }} · {{ r.reason || '无原因' }}</view>
					<view class="ir-sub">{{ r.category }} · {{ (r.created_at || '').slice(0,10) }}</view>
				</view>
				<view class="ir-right">
					<text :class="r.change >= 0 ? 'amount income' : 'amount'">{{ r.change >= 0 ? '+' : '' }}{{ r.change }}</text>
				</view>
			</view>
			<view v-if="!records.length" class="empty">暂无积分记录</view>
			<view v-if="pagedRecords.length && records.length > pagedRecords.length" class="load-more" @click="loadMoreRecords">
				<text>已加载 {{ pagedRecords.length }} / {{ records.length }} 条，点击加载更多</text>
			</view>
			<view v-else-if="pagedRecords.length" class="load-more all-loaded">
				<text>已全部加载（共 {{ records.length }} 条）</text>
			</view>
		</view>
	</view>
</template>

<script>
import { get, post } from '../../utils/request';

export default {
	data() {
		return {
			leaderboard: [],
			records: [],
			students: [],
			// 积分记录前端分页
			pageSize: 20,
			visibleCount: 20,
			changeForm: { student_id: null, change: '', reason: '' }
		};
	},
	computed: {
		changeStudentName() {
			const s = this.students.find(x => x.id === this.changeForm.student_id);
			return s ? s.name : '请选择学生';
		},
		pagedRecords() {
			return this.records.slice(0, this.visibleCount);
		},
		/* ===== 纯展示：选中学生的当前积分（数据来自排行榜，未选中/不在榜返回 null） ===== */
		selectedStudentPoints() {
			if (!this.changeForm.student_id) return null;
			const s = this.leaderboard.find(x => x.id === this.changeForm.student_id);
			return s ? s.points : null;
		}
	},
	onLoad() { this.loadAll(); },
	onReachBottom() {
		this.loadMoreRecords();
	},
	methods: {
		async loadAll() {
			try {
				this.leaderboard = await get('/points/leaderboard');
				this.records = await get('/points/records');
				this.students = await get('/students');
				this.visibleCount = this.pageSize;
			} catch (e) {}
		},
		loadMoreRecords() {
			if (this.visibleCount < this.records.length) {
				this.visibleCount += this.pageSize;
			}
		},
		async doChange() {
			if (!this.changeForm.student_id || this.changeForm.change === '') {
				uni.showToast({ title: '请选择学生并填写积分', icon: 'none' });
				return;
			}
			await post('/points/change', Object.assign({}, this.changeForm, { change: Number(this.changeForm.change) }));
			uni.showToast({ title: '已提交', icon: 'success' });
			this.changeForm = { student_id: null, change: '', reason: '' };
			this.loadAll();
		},
		/* ===== 纯展示 helper ===== */
		rankBadgeClass(rank) {
			if (rank === 1) return 'top1';
			if (rank === 2) return 'top2';
			if (rank === 3) return 'top3';
			return '';
		}
	}
};
</script>

<style scoped>
.page { padding-bottom: 40rpx; }
.points-submit { width: 100%; }
.points-hint { display: block; font-size: 24rpx; color: #909399; margin-top: 10rpx; }
.field { margin-bottom: 20rpx; }
.label { display: block; font-size: 24rpx; color: #606266; margin-bottom: 8rpx; }
.input { background: #f5f7fa; border-radius: 10rpx; padding: 16rpx 20rpx; font-size: 28rpx; }
.load-more {
	text-align: center;
	padding: 20rpx 0 8rpx;
	font-size: 24rpx;
	color: #10b981;
}
.load-more.all-loaded { color: #c0c4cc; }
</style>
