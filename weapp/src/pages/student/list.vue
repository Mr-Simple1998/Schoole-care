<template>
	<view class="page">
		<!-- 平台超级管理员：无机构数据，引导进入机构开户管理（与 PC 端一致） -->
		<view v-if="store.isPlatform" class="platform-tip">
			<view class="card">
				<view class="tip-title">🏢 平台账号无机构学生数据</view>
				<view class="tip-desc">机构开户、续费与流水请在「机构开户管理」中操作；学生数据请使用校长 / 校区负责人 / 教师账号登录查看。</view>
				<button class="btn-primary tip-btn" @click="goPlatform">进入机构开户管理</button>
			</view>
		</view>

		<template v-else>
			<!-- 顶部统计 -->
			<view class="stat-grid" v-if="students.length">
			<view class="stat-card is-blue">
				<view class="stat-top">
					<text class="stat-label">学生总数</text>
					<text class="stat-emoji">👥</text>
				</view>
				<text class="stat-num">{{ listStats.total }}</text>
				<text class="stat-sub">全部学生</text>
			</view>
			<view class="stat-card is-green">
				<view class="stat-top">
					<text class="stat-label">在读人数</text>
					<text class="stat-emoji">🎓</text>
				</view>
				<text class="stat-num">{{ listStats.active }}</text>
				<text class="stat-sub">正常在读</text>
			</view>
			<view class="stat-card is-orange">
				<view class="stat-top">
					<text class="stat-label">剩余课时</text>
					<text class="stat-emoji">⏳</text>
				</view>
				<text class="stat-num">{{ listStats.remain }}</text>
				<text class="stat-sub">待核销</text>
			</view>
			<view class="stat-card is-purple">
				<view class="stat-top">
					<text class="stat-label">已核课时</text>
					<text class="stat-emoji">✅</text>
				</view>
				<text class="stat-num">{{ listStats.used }}</text>
				<text class="stat-sub">累计核销</text>
			</view>
		</view>

		<view class="search-bar">
			<input class="search-input" v-model="keyword" placeholder="搜索姓名/学号" @input="filterList" />
			<button v-if="store.isTeacher" class="btn-ghost att-btn" @click="goAttendance">考勤</button>
			<button class="btn-primary add-btn" @click="goAdd">新增</button>
		</view>

		<view v-if="filtered.length" class="student-list">
			<view v-for="s in filtered" :key="s.id" class="card student-item">
				<view class="flex" @click="goDetail(s.id)">
					<view class="avatar">{{ s.name[0] }}</view>
					<view class="flex-1 info-row ir-body">
						<view class="ir-left">
							<view class="ir-title">{{ s.name }}<text class="s-no">{{ s.student_no }}</text></view>
							<view class="ir-sub">
								<text>{{ s.school || '未填写' }}</text>
								<text v-if="s.grade">{{ s.grade }}</text>
								<text v-if="s.teacher_name">教师：{{ s.teacher_name }}</text>
								<text v-else class="stash">暂存校区负责人</text>
							</view>
						</view>
						<view class="ir-right">
							<text :class="s.status === '在读' ? 'tag tag-success' : 'tag tag-grey'">{{ s.status || '未知' }}</text>
						</view>
					</view>
				</view>
				<view class="s-subjects" v-if="s.subjects && s.subjects.length">
					<text class="sub-label">科目</text>
					<text v-for="sub in s.subjects" :key="sub.id" class="sub-tag">{{ sub.name }}</text>
				</view>
				<!-- 学生分开管理：各角色只能给自己负责的学生打卡（校长/校区负责人/教师均可拥有自己的学生） -->
				<button v-if="s.teacher_id === store.user.id" class="btn-primary attend-btn" @click="openAttend(s)">打卡</button>
			</view>
		</view>
		<view v-else class="text-muted empty">暂无学生</view>

		<!-- 打卡弹窗 -->
		<view class="mask" v-if="showAttend" @click="showAttend=false">
			<view class="dialog" @click.stop>
				<view class="dialog-title">考勤打卡</view>
				<view class="field">
					<text class="label">学生：{{ attendStudent && attendStudent.name }}</text>
				</view>
				<view class="field">
					<text class="label">选择学科</text>
					<picker :range="attendNames" @change="e => attendSubjectId = attendSubjects[e.detail.value].id">
						<view class="input">{{ attendSubjectName }}</view>
					</picker>
				</view>
				<view class="field">
					<text class="label">打卡日期（可补卡）</text>
					<picker mode="date" :value="attendDate" @change="e => attendDate=e.detail.value">
						<view class="input picker-box">{{ attendDate }}<text class="arrow">›</text></view>
					</picker>
				</view>
				<view class="dialog-btns">
					<button class="btn-cancel" @click="showAttend=false">取消</button>
					<button class="btn-primary" @click="doAttend">确认打卡</button>
				</view>
			</view>
		</view>
		</template>
	</view>
</template>

<script>
import { useUserStore } from '../../stores/user';
import { get, post } from '../../utils/request';

export default {
	data() {
		return {
			store: useUserStore(),
			students: [],
			filtered: [],
			keyword: '',
			showAttend: false,
			attendStudent: null,
			attendSubjects: [],
			attendSubjectId: null,
			attendDate: ''
		};
	},
	onShow() {
		if (!this.store.isPlatform) {
			this.loadStudents();
		}
	},
	computed: {
		attendNames() {
			return this.attendSubjects.map(s => this.attendLabel(s));
		},
		attendSubjectName() {
			const s = this.attendSubjects.find(x => x.id === this.attendSubjectId);
			return s ? this.attendLabel(s) : '请选择学科';
		},
		/* 纯展示：顶部统计卡数据（仅由现有 students 数据派生） */
		listStats() {
			let total = this.students.length;
			let active = 0, used = 0, remain = 0;
			this.students.forEach(s => {
				if (s.status === '在读') active++;
				(s.subject_sessions || []).forEach(ss => {
					if (typeof ss.used_sessions === 'number') used += ss.used_sessions;
					if (typeof ss.remaining === 'number') remain += ss.remaining;
				});
			});
			return { total, active, used, remain };
		}
	},
	onPullDownRefresh() {
		this.loadStudents().then(() => uni.stopPullDownRefresh());
	},
	methods: {
		async loadStudents() {
			try {
				this.students = await get('/students');
				this.filterList();
			} catch (e) {}
		},
		filterList() {
			const k = this.keyword.trim();
			this.filtered = this.students.filter(s =>
				!k || s.name.includes(k) || s.student_no.includes(k)
			);
		},
		goAdd() {
			uni.navigateTo({ url: '/pages/student/add' });
		},
		goAttendance() {
			uni.navigateTo({ url: '/pages/student/attendance' });
		},
		goPlatform() {
			uni.navigateTo({ url: '/pages/platform/platform' });
		},
		goDetail(id) {
			uni.navigateTo({ url: '/pages/student/detail?id=' + id });
		},
		attendLabel(s) {
			const hasRemain = s.remaining !== null && s.remaining !== undefined;
			return hasRemain ? `${s.name}（剩${s.remaining}次）` : s.name;
		},
		openAttend(s) {
			this.attendStudent = s;
			// 打卡学科：优先用课时会话（subject_sessions：subject_id/subject_name/remaining），否则退回学科列表（subjects：id/name）
			const sessions = (s.subject_sessions && s.subject_sessions.length) ? s.subject_sessions : (s.subjects || []);
			this.attendSubjects = sessions.map(x => ({
				id: x.subject_id != null ? x.subject_id : x.id,
				name: x.subject_name || x.name || '',
				remaining: x.remaining
			}));
			this.attendSubjectId = this.attendSubjects.length ? this.attendSubjects[0].id : null;
			this.attendDate = this.todayStr();
			this.showAttend = true;
		},
		todayStr() {
			const d = new Date();
			const m = String(d.getMonth() + 1).padStart(2, '0');
			const dd = String(d.getDate()).padStart(2, '0');
			return `${d.getFullYear()}-${m}-${dd}`;
		},
		async doAttend() {
			if (!this.attendSubjectId) {
				uni.showToast({ title: '请选择学科', icon: 'none' });
				return;
			}
			try {
				await post('/learning/attendance', {
					student_id: Number(this.attendStudent.id),
					subject_id: this.attendSubjectId,
					date: this.attendDate || this.todayStr(),
					status: '正常'
				});
				uni.showToast({ title: '打卡成功', icon: 'success' });
				this.showAttend = false;
				this.loadStudents();
			} catch (e) {}
		}
	}
};
</script>

<style scoped>
.page { padding-bottom: 40rpx; }
.stat-grid { margin-top: 20rpx; }
.search-bar {
	display: flex;
	padding: 20rpx;
	align-items: center;
}
.search-input {
	flex: 1;
	background: #fff;
	border-radius: 12rpx;
	padding: 16rpx 24rpx;
	margin-right: 16rpx;
	font-size: 26rpx;
}
.add-btn { margin: 0; font-size: 26rpx; }
.btn-ghost {
	background: #fff;
	color: #10b981;
	border: 1rpx solid #10b981;
	border-radius: 12rpx;
	font-size: 26rpx;
}
.att-btn { margin: 0 12rpx 0 0; }
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
/* info-row 内嵌于卡片时的对齐修正 */
.ir-body {
	padding: 4rpx 0;
	border-bottom: none;
}
.s-no { font-size: 22rpx; color: #909399; margin-left: 10rpx; font-weight: 400; }
.stash { color: #e6a23c; }
.s-subjects { margin-top: 16rpx; display: flex; align-items: center; flex-wrap: wrap; }
.sub-label { font-size: 22rpx; color: #909399; margin-right: 10rpx; }
.sub-tag {
	display: inline-block;
	font-size: 22rpx;
	color: #10b981;
	background: #f0fdf4;
	border-radius: 8rpx;
	padding: 4rpx 14rpx;
	margin-right: 8rpx;
	margin-bottom: 6rpx;
}
.empty { text-align: center; padding: 80rpx 0; }
.platform-tip { padding-top: 20rpx; }
.tip-title { font-size: 32rpx; font-weight: 700; color: #303133; margin-bottom: 12rpx; }
.tip-desc {
	font-size: 26rpx;
	color: #6b7280;
	line-height: 1.6;
	margin-bottom: 24rpx;
}
.tip-btn { font-size: 28rpx; }
.attend-btn {
	margin: 20rpx 0 0;
	font-size: 26rpx;
	height: 60rpx;
	line-height: 60rpx;
	width: 100%;
}
.mask {
	position: fixed; left: 0; top: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.45); z-index: 99;
	display: flex; align-items: center; justify-content: center;
}
.dialog { width: 80%; background: #fff; border-radius: 16rpx; padding: 36rpx 32rpx; }
.dialog-title { font-size: 32rpx; font-weight: 600; margin-bottom: 24rpx; }
.dialog-btns { display: flex; margin-top: 20rpx; }
.dialog-btns button { flex: 1; margin: 0 8rpx; font-size: 28rpx; }
.btn-cancel { background: #f5f7fa; color: #606266; border-radius: 12rpx; }
.field { margin-bottom: 20rpx; }
.label { display: block; font-size: 24rpx; color: #606266; margin-bottom: 8rpx; }
.input { background: #f5f7fa; border-radius: 10rpx; padding: 16rpx 20rpx; font-size: 28rpx; }
.picker-box { display: flex; align-items: center; justify-content: space-between; }
.picker-box .arrow { color: #c0c4cc; font-size: 32rpx; line-height: 1; }
</style>
