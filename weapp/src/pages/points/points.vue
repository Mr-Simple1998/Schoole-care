<template>
	<view class="page">
		<view class="card">
			<view class="card-title">积分排行榜</view>
			<view v-for="s in leaderboard" :key="s.id" class="rank-item">
				<text class="rank-no">{{ s.rank }}</text>
				<text class="flex-1">{{ s.name }}</text>
				<text class="text-warn">{{ s.points }} 分</text>
			</view>
			<view v-if="!leaderboard.length" class="text-muted empty">暂无数据</view>
		</view>

		<view class="card">
			<view class="card-title">加/扣积分</view>
			<view class="field">
				<text class="label">选择学生</text>
				<picker :range="students.map(s=>s.name)" @change="e => changeForm.student_id=students[e.detail.value].id">
					<view class="input">{{ changeStudentName }}</view>
				</picker>
			</view>
			<view class="field">
				<text class="label">积分变动（正数加，负数扣）</text>
				<input class="input" type="number" v-model="changeForm.change" placeholder="如 5 或 -3" />
			</view>
			<view class="field"><text class="label">原因</text><input class="input" v-model="changeForm.reason" placeholder="如表现优秀" /></view>
			<button class="btn-primary" @click="doChange">提交</button>
		</view>

		<view class="card">
			<view class="card-title">积分记录</view>
			<view v-for="r in records" :key="r.id" class="rec-item">
				<view class="flex">
					<text class="flex-1">{{ r.student_name }} · {{ r.reason || '无原因' }}</text>
					<text :class="r.change >= 0 ? 'text-primary' : 'text-danger'">{{ r.change >= 0 ? '+' : '' }}{{ r.change }}</text>
				</view>
				<view class="text-muted" style="font-size:24rpx">{{ r.category }} · {{ (r.created_at || '').slice(0,10) }}</view>
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
			changeForm: { student_id: null, change: '', reason: '' }
		};
	},
	computed: {
		changeStudentName() {
			const s = this.students.find(x => x.id === this.changeForm.student_id);
			return s ? s.name : '请选择学生';
		}
	},
	onLoad() { this.loadAll(); },
	methods: {
		async loadAll() {
			try {
				this.leaderboard = await get('/points/leaderboard');
				this.records = await get('/points/records');
				this.students = await get('/students');
			} catch (e) {}
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
		}
	}
};
</script>

<style scoped>
.rank-item { display: flex; align-items: center; padding: 14rpx 0; border-bottom: 1rpx solid #f5f5f5; }
.rank-item:last-child { border-bottom: none; }
.rank-no { width: 56rpx; height: 56rpx; line-height: 56rpx; text-align: center; border-radius: 50%; background: #f0fdf4; color: #10b981; margin-right: 16rpx; }
.rec-item { padding: 14rpx 0; border-bottom: 1rpx solid #f5f5f5; }
.rec-item:last-child { border-bottom: none; }
.field { margin-bottom: 20rpx; }
.label { display: block; font-size: 24rpx; color: #606266; margin-bottom: 8rpx; }
.input { background: #f5f7fa; border-radius: 10rpx; padding: 16rpx 20rpx; font-size: 28rpx; }
.empty { text-align: center; padding: 30rpx 0; }
</style>