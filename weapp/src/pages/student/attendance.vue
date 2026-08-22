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
					<view v-for="s in pageStudents" :key="s.student_id" class="cal-row">
						<view class="cal-name">{{ s.student_name }}</view>
						<view v-for="d in monthDays" :key="d.dayStr" class="cal-cell" :class="{ disabled: d.dayStr > todayStr() }" @click="onDayClick(s, d)">
							<view class="dots"><view v-for="record in dayRecords(s, d.dayStr)" :key="record.id" class="dot subject-dot" :class="'is-' + statusClass(record.status)" :style="{ borderColor: subjectColor(record.subject_id) }" @click.stop="cycleRecord(record)"></view></view>
						</view>
					</view>
				</view>
			</scroll-view>
			<!-- 学生分页：网格行很多，分页只渲染当前页，避免整月表格卡顿 -->
			<view v-if="totalPages > 1" class="cal-pager">
				<text class="page-btn" :class="{ disabled: attPage <= 1 }" @click="attPrev">‹ 上一页</text>
				<text class="page-info">{{ attPage }} / {{ totalPages }}（共 {{ students.length }} 人）</text>
				<text class="page-btn" :class="{ disabled: attPage >= totalPages }" @click="attNext">下一页 ›</text>
			</view>
		</view>
		<view v-else-if="loading" class="card empty">加载中...</view>
		<view v-else class="card empty">该月暂无学生考勤数据</view>
	</view>
</template>

<script>
import { useUserStore } from '../../stores/user';
import { get, post } from '../../utils/request';

export default {
	data() {
		const d = new Date();
		return {
			store: useUserStore(),
			month: `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`,
			students: [],
			loading: false,
			// 学生分页：一次只渲染一页行（每页 20 人），大幅减少 DOM 节点
			attPage: 1,
			attPageSize: 20
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
		},
		// 当前页学生（切片）
		pageStudents() {
			const start = (this.attPage - 1) * this.attPageSize;
			return this.students.slice(start, start + this.attPageSize);
		},
		totalPages() {
			return Math.max(1, Math.ceil(this.students.length / this.attPageSize));
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
		attPrev() {
			if (this.attPage > 1) this.attPage--;
		},
		attNext() {
			if (this.attPage < this.totalPages) this.attPage++;
		},
		// 考勤状态 → 图标 class
		statusClass(status) {
			const map = { '正常': 'normal', '迟到': 'late', '缺勤': 'absent', '请假': 'leave', '早退': 'early' };
			return map[status] || 'empty';
		},
		dayRecords(student, day) { return (student.recordsByDate && student.recordsByDate[day]) || []; },
		subjectColor(id) { return `hsl(${((id || 0) * 47) % 360} 58% 42%)`; },
		async onDayClick(student, day) {
			if (day.dayStr > this.todayStr()) return;
			const detail = await get('/students/' + student.student_id);
			const subjects = detail.subject_sessions || [];
			if (!subjects.length) return uni.showToast({ title: '该学生未设置学科', icon: 'none' });
			uni.showActionSheet({ itemList: subjects.map(s => `${s.subject_name}（剩${s.remaining ?? '-'}次）`), success: async res => {
				const subject = subjects[res.tapIndex];
				try { await post('/learning/attendance', { student_id: student.student_id, subject_id: subject.subject_id, date: day.dayStr, status: '正常' }); this.load(); } catch (e) {}
			}});
		},
		async cycleRecord(record) {
			const states = ['正常', '迟到', '请假', '缺勤', '早退'];
			const index = states.indexOf(record.status);
			try {
				if (index === states.length - 1) await post(`/learning/attendance/${record.id}/cancel`);
				else await post(`/learning/attendance/${record.id}/status`, { status: states[index + 1] });
				this.load();
			} catch (e) {}
		},
		todayStr() {
			const d = new Date();
			return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
		},
		cancelAttendance(id) {
			uni.showModal({ title: '确认退卡', content: '退卡后将回退一次课时，可重新打卡。', success: async res => {
				if (!res.confirm) return;
				try { await post(`/learning/attendance/${id}/cancel`); uni.showToast({ title: '已退卡', icon: 'success' }); this.load(); } catch (e) {}
			}});
		},
		async load() {
			this.loading = true;
			try {
				const data = await get('/dashboard/attendance-summary', { month: this.month });
				// 预建「日期 → 状态」索引：一次遍历，之后渲染每格都是 O(1) 查找，
				// 避免原来每格 records.find() 线性扫描造成的大列表卡顿
				this.students = (data.students || []).map(s => {
					const recordsByDate = {};
					(s.records || []).forEach(r => { if (r.date) (recordsByDate[r.date] ||= []).push(r); });
					return { student_id: s.student_id, student_name: s.student_name, recordsByDate };
				});
				this.attPage = 1;
			} catch (e) {
				this.students = [];
			} finally {
				this.loading = false;
			}
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
.dots { display: flex; justify-content: center; gap: 2rpx; min-height: 18rpx; }
.subject-dot { border: 3rpx solid transparent; }
.cal-cell.disabled { opacity: .35; }
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
.cal-pager {
	display: flex;
	align-items: center;
	justify-content: center;
	gap: 20rpx;
	padding: 16rpx 0 8rpx;
}
.cal-pager .page-btn {
	font-size: 24rpx;
	color: #10b981;
	padding: 8rpx 22rpx;
	background: #f0fdf4;
	border-radius: 10rpx;
}
.cal-pager .page-btn.disabled { color: #c0c4cc; background: #f5f7fa; }
.cal-pager .page-info { font-size: 24rpx; color: #6b7280; }
</style>
