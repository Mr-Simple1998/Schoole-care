<template>
	<view class="page">
		<!-- 年月选择 -->
		<view class="toolbar">
			<picker mode="date" fields="month" :value="month" @change="onMonthChange">
				<view class="picker-box">
					<text class="picker-val">{{ month }}</text>
					<text class="arrow">›</text>
				</view>
			</picker>
			<text class="hint">每行一名学生 · 每列一天</text>
		</view>

		<!-- 图例 -->
		<view class="legend">
			<text class="leg"><text class="dot is-normal"></text>正常</text>
			<text class="leg"><text class="dot is-late"></text>迟到</text>
			<text class="leg"><text class="dot is-absent"></text>缺勤</text>
			<text class="leg"><text class="dot is-leave"></text>请假</text>
			<text class="leg"><text class="dot is-early"></text>早退</text>
			<text class="leg"><text class="dot is-empty"></text>未记录</text>
		</view>

		<!-- 全体学生考勤日历 -->
		<view v-if="students.length" class="card cal-card">
			<scroll-view scroll-x class="cal-scroll">
				<view class="cal">
					<view class="cal-row cal-head">
						<view class="cal-name">学生</view>
						<view v-for="d in monthDays" :key="d.dayStr" class="cal-day" :class="{ 'is-today': d.isToday }">{{ d.day }}</view>
					</view>
					<view v-for="s in students" :key="s.student_id" class="cal-row">
						<view class="cal-name">{{ s.student_name }}</view>
						<view v-for="d in monthDays" :key="d.dayStr" class="cal-cell">
							<view class="dot" :class="'is-' + statusClass(cellStatus(s, d.dayStr))"></view>
						</view>
					</view>
				</view>
			</scroll-view>
		</view>
		<view v-else class="card empty">该月暂无学生考勤数据</view>
	</view>
</template>

<script>
import { useUserStore } from '../../stores/user';
import { get } from '../../utils/request';

export default {
	data() {
		const d = new Date();
		return {
			store: useUserStore(),
			month: `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`,
			students: []
		};
	},
	computed: {
		// 当月各天（用于日历列）
		monthDays() {
			const [y, m] = this.month.split('-').map(Number);
			const days = new Date(y, m, 0).getDate();
			const t = new Date();
			const today = `${t.getFullYear()}-${String(t.getMonth() + 1).padStart(2, '0')}-${String(t.getDate()).padStart(2, '0')}`;
			return Array.from({ length: days }, (_, i) => {
				const day = i + 1;
				const dayStr = `${this.month}-${String(day).padStart(2, '0')}`;
				return { day, dayStr, isToday: dayStr === today };
			});
		}
	},
	onLoad() {
		this.load();
	},
	methods: {
		onMonthChange(e) {
			this.month = e.detail.value;
			this.load();
		},
		cellStatus(s, dayStr) {
			const rec = (s.records || []).find(r => r.date === dayStr);
			return rec ? rec.status : '';
		},
		// 考勤状态 → 图标 class
		statusClass(status) {
			const map = { '正常': 'normal', '迟到': 'late', '缺勤': 'absent', '请假': 'leave', '早退': 'early' };
			return map[status] || 'empty';
		},
		async load() {
			try {
				const data = await get('/dashboard/attendance-summary', { month: this.month });
				this.students = data.students || [];
			} catch (e) {}
		}
	}
};
</script>

<style scoped>
.page { padding-bottom: 40rpx; }
.toolbar {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 20rpx 24rpx 8rpx;
}
.picker-box {
	display: flex;
	align-items: center;
	gap: 8rpx;
	background: #fff;
	border-radius: 12rpx;
	padding: 12rpx 20rpx;
	box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.04);
}
.picker-val { font-size: 28rpx; color: #303133; font-weight: 600; }
.arrow { color: #c0c4cc; font-size: 30rpx; }
.hint { font-size: 22rpx; color: #909399; }
.legend {
	display: flex;
	flex-wrap: wrap;
	gap: 16rpx;
	padding: 8rpx 24rpx 12rpx;
}
.leg { display: flex; align-items: center; gap: 6rpx; font-size: 22rpx; color: #6b7280; }
.leg .dot { display: inline-block; width: 16rpx; height: 16rpx; }

.cal-card { padding: 8rpx 0 16rpx; }
.cal-scroll { width: 100%; }
.cal { display: flex; flex-direction: column; }
.cal-row { display: flex; align-items: center; }
.cal-name {
	width: 150rpx;
	flex-shrink: 0;
	font-size: 26rpx;
	color: #303133;
	padding: 14rpx 10rpx;
	box-sizing: border-box;
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
}
.cal-day, .cal-cell {
	width: 42rpx;
	flex-shrink: 0;
	text-align: center;
	box-sizing: border-box;
}
.cal-head { border-bottom: 1rpx solid #f0f0f0; }
.cal-head .cal-day { font-size: 22rpx; color: #909399; padding: 10rpx 0; }
.cal-day.is-today { color: #059669; font-weight: 700; }
.cal-row:not(.cal-head) { border-bottom: 1rpx solid #f7f7f7; }
.cal-cell { padding: 12rpx 0; }
.dot { width: 18rpx; height: 18rpx; border-radius: 50%; margin: 0 auto; }
.dot.is-normal { background: #10b981; }
.dot.is-late { background: #f59e0b; }
.dot.is-absent { background: #ef4444; }
.dot.is-leave { background: #3b82f6; }
.dot.is-early { background: #8b5cf6; }
.dot.is-empty { background: #e5e7eb; }
.empty { text-align: center; color: #c0c4cc; font-size: 26rpx; padding: 60rpx 0; }
</style>
