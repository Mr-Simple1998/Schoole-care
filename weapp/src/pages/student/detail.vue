<template>
	<view class="page" v-if="student">
		<!-- 学生信息 -->
		<view class="card">
			<view class="flex">
				<view class="avatar">{{ student.name[0] }}</view>
				<view class="flex-1">
					<view class="s-name">{{ student.name }}<text class="s-no">{{ student.student_no }}</text>
						<text :class="student.status === '在读' ? 'tag tag-success' : 'tag tag-grey'" class="status-tag">{{ student.status }}</text>
					</view>
					<view class="text-muted s-meta">
						{{ student.school || '' }} {{ student.grade || '' }} · 入学 {{ student.enrollment_date || '-' }}
					</view>
					<view class="s-meta">
						<text class="text-info">负责教师：{{ student.teacher_name || '暂存校区负责人' }}</text>
						<text v-if="canAssign" class="change-teacher" @click="openTeacherPick">更换 ›</text>
					</view>
				</view>
			</view>
		</view>

		<!-- 统计卡片 -->
		<view class="stat-grid">
			<view class="stat-card is-orange">
				<view class="stat-top">
					<text class="stat-label">积分</text>
					<text class="stat-emoji">⭐</text>
				</view>
				<text class="stat-num">{{ student.points || 0 }}</text>
				<text class="stat-sub">积分余额</text>
			</view>
			<view class="stat-card is-purple">
				<view class="stat-top">
					<text class="stat-label">总课时</text>
					<text class="stat-emoji">📚</text>
				</view>
				<text class="stat-num">{{ sessionTotals.total }}</text>
				<text class="stat-sub">全部科目</text>
			</view>
			<view class="stat-card is-blue">
				<view class="stat-top">
					<text class="stat-label">已核销</text>
					<text class="stat-emoji">✅</text>
				</view>
				<text class="stat-num">{{ sessionTotals.used }}</text>
				<text class="stat-sub">已使用课时</text>
			</view>
			<view class="stat-card is-green">
				<view class="stat-top">
					<text class="stat-label">剩余课时</text>
					<text class="stat-emoji">⏳</text>
				</view>
				<text class="stat-num">{{ sessionTotals.remain }}</text>
				<text class="stat-sub">待核销</text>
			</view>
		</view>

		<!-- 到期提醒横幅 -->
		<view class="banner" :class="expireBanner.type" v-if="expireBanner">
			<view>
				<view class="banner-title">{{ expireBanner.title }}</view>
				<view class="banner-desc">{{ expireBanner.desc }}</view>
			</view>
		</view>

		<!-- 课时核销概览 -->
		<view class="card" v-if="student.subject_sessions && student.subject_sessions.length">
			<view class="card-title"><text class="bar"></text>课时核销情况</view>
			<view v-for="ss in student.subject_sessions" :key="ss.subject_id" class="session-item">
				<view class="session-head">
					<text class="session-name">{{ ss.subject_name }}</text>
					<text v-if="ss.total_sessions !== null" class="session-count">已核 {{ ss.used_sessions }} / {{ ss.total_sessions }}<text class="text-muted">（剩 {{ ss.remaining }}）</text></text>
					<text v-else class="tag tag-info">按到期时间</text>
				</view>
				<view v-if="ss.total_sessions !== null" class="session-progress">
					<view class="progress" :class="progressClass(ss)">
						<view class="progress-inner" :style="{ width: progressWidth(ss) + '%' }"></view>
					</view>
					<text class="progress-text">{{ progressWidth(ss) }}%</text>
				</view>
				<view v-if="ss.total_sessions === null" class="text-muted expire-line">
					<view v-if="ss.expire_date" class="expire-row">
						<text>到期：{{ ss.expire_date }}</text>
						<text :class="'tag ' + expireTagClass(ss.expire_date)">{{ expireTagText(ss.expire_date) }}</text>
					</view>
					<view v-else>时长：{{ ss.duration_value }}{{ ss.duration_unit }}（首次打卡后开始计时）</view>
				</view>
			</view>
		</view>

		<!-- 功能入口 -->
		<view class="card">
			<view class="card-title"><text class="bar"></text>功能</view>
			<view class="quick-grid">
				<!-- 学生分开管理：各角色只能给自己负责的学生打卡 -->
				<template v-if="student.teacher_id === store.user.id">
					<view class="quick-item" :class="{ 'is-done': student.attended_today }" @click="openAttend(false)"><text>{{ student.attended_today ? '已打卡' : '考勤打卡' }}</text></view>
					<view class="quick-item is-makeup" @click="openAttend(true)"><text>补卡</text></view>
				</template>
				<view class="quick-item" @click="openScore"><text>成绩</text></view>
				<view class="quick-item" @click="openHomework"><text>作业</text></view>
				<view class="quick-item" @click="togglePerf"><text>课堂表现</text></view>
			</view>
		</view>

		<!-- 打卡弹窗 -->
		<view class="mask" v-if="showAttend" @click="showAttend=false">
			<view class="dialog" @click.stop>
				<view class="dialog-title">{{ attendTitle }}</view>
				<view class="field">
					<text class="label">选择学科</text>
					<picker :range="subjectNames" @change="e => attendSubjectId = attendSubjects[e.detail.value].id">
						<view class="input">{{ attendSubjectName }}</view>
					</picker>
				</view>
				<view class="field">
					<text class="label">打卡日期</text>
					<picker mode="date" :value="attendDate" @change="e => attendDate=e.detail.value">
						<view class="input">{{ attendDate }}</view>
					</picker>
				</view>
				<view class="dialog-btns">
					<button class="btn-cancel" @click="showAttend=false">取消</button>
					<button class="btn-primary" @click="doAttend">确认打卡</button>
				</view>
			</view>
		</view>

		<!-- 成绩弹窗 -->
		<view class="mask" v-if="showScore" @click="showScore=false">
			<view class="dialog" @click.stop>
				<view class="dialog-title">记录成绩</view>
				<view class="field"><input class="input" v-model="scoreForm.subject" placeholder="科目" /></view>
				<view class="field"><input class="input" type="number" v-model="scoreForm.score" placeholder="得分" /></view>
				<view class="field"><input class="input" v-model="scoreForm.exam_type" placeholder="考试类型（如月考）" /></view>
				<view class="dialog-btns">
					<button class="btn-cancel" @click="showScore=false">取消</button>
					<button class="btn-primary" @click="doScore">保存</button>
				</view>
			</view>
		</view>

		<!-- 作业弹窗 -->
		<view class="mask" v-if="showHw" @click="showHw=false">
			<view class="dialog" @click.stop>
				<view class="dialog-title">布置作业</view>
				<view class="field"><input class="input" v-model="hwForm.subject" placeholder="科目" /></view>
				<view class="field"><textarea class="input" v-model="hwForm.content" placeholder="作业内容" /></view>
				<view class="dialog-btns">
					<button class="btn-cancel" @click="showHw=false">取消</button>
					<button class="btn-primary" @click="doHomework">保存</button>
				</view>
			</view>
		</view>

		<!-- 课堂表现弹窗 -->
		<view class="mask" v-if="showPerf" @click="showPerf=false">
			<view class="dialog" @click.stop>
				<view class="dialog-title">记录课堂表现</view>
				<view class="field">
					<picker :range="perfTypes" @change="e => perfForm.performance_type=perfTypes[e.detail.value]">
						<view class="input">{{ perfForm.performance_type }}</view>
					</picker>
				</view>
				<view class="field">
					<text class="label">评分：{{ perfForm.rating }} / 5</text>
					<slider :value="perfForm.rating" min="1" max="5" :step="1" @change="e => perfForm.rating=e.detail.value" />
				</view>
				<view class="field"><textarea class="input" v-model="perfForm.comment" placeholder="评语" /></view>
				<view class="dialog-btns">
					<button class="btn-cancel" @click="showPerf=false">取消</button>
					<button class="btn-primary" @click="doPerf">保存</button>
				</view>
			</view>
		</view>

		<!-- 更换负责教师弹窗（校长/校区负责人：分配或暂存） -->
		<view class="mask" v-if="showTeacherPick" @click="showTeacherPick=false">
			<view class="dialog" @click.stop>
				<view class="dialog-title">更换负责教师</view>
				<view class="field">
					<text class="label">学生：{{ student && student.name }}（{{ student && student.student_no }}）</text>
				</view>
				<view class="field">
					<text class="label">负责教师</text>
					<picker :range="teacherLabels" @change="e => selectedTeacherId = teacherIds[e.detail.value]">
						<view class="input">{{ selectedTeacherName }}</view>
					</picker>
					<text class="pick-tip">选择“暂存至校区负责人”可清空负责教师，学生数据全部保留。</text>
				</view>
				<view class="dialog-btns">
					<button class="btn-cancel" @click="showTeacherPick=false">取消</button>
					<button class="btn-primary" @click="doChangeTeacher">保存</button>
				</view>
			</view>
		</view>

		<!-- 记录列表 -->
		<view class="card" v-if="scores.length">
			<view class="card-title"><text class="bar"></text>近期成绩</view>
			<view v-for="sc in scores.slice(0,5)" :key="sc.id" class="record-item">
				<view class="flex-1">
					<view class="record-title">{{ sc.subject }} <text class="text-muted record-type">{{ sc.exam_type }}</text></view>
					<view class="text-muted record-sub" v-if="sc.exam_date">{{ sc.exam_date }}</view>
				</view>
				<text class="score-num">{{ sc.score }}<text class="score-full"> / {{ sc.full_score }}</text></text>
			</view>
		</view>
		<view class="card" v-if="hwList.length">
			<view class="card-title"><text class="bar"></text>近期作业</view>
			<view v-for="h in hwList.slice(0,5)" :key="h.id" class="record-item">
				<view class="flex-1">
					<view class="record-title">{{ h.subject }}</view>
					<view class="text-muted record-sub">{{ h.assign_date || '-' }}</view>
				</view>
				<text :class="'tag ' + hwStatusClass(h.complete_status)">{{ h.complete_status }}</text>
			</view>
		</view>
	</view>
	<view v-else class="page loading-page">
		<view class="loading-box">
			<view class="loading-spin"></view>
			<text class="loading-text">加载中...</text>
		</view>
	</view>
</template>

<script>
import { get, post, put } from '../../utils/request';
import { useUserStore } from '../../stores/user';

const PERF_TYPES = ['纪律','专注','积极','作业','礼仪'];

export default {
	data() {
		return {
			id: null,
			store: useUserStore(),
			student: null,
			scores: [],
			hwList: [],
			teachers: [],
			loading: false,
			showTeacherPick: false,
			selectedTeacherId: null,
			showAttend: false, attendTitle: '考勤打卡', attendSubjects: [], attendSubjectId: null, attendDate: '',
			showScore: false, scoreForm: { subject: '', score: '', exam_type: '平时考' },
			showHw: false, hwForm: { subject: '', content: '' },
			showPerf: false, perfTypes: PERF_TYPES, perfForm: { performance_type: '纪律', rating: 3, comment: '' }
		};
	},
	computed: {
		canAssign() {
			return this.store.isPrincipal || this.store.isSubPrincipal;
		},
		teacherLabels() {
			return ['暂存至校区负责人'].concat(this.teachers.map(t => `${t.name}（${t.username}）${this.teacherRoleTag(t)}`));
		},
		teacherIds() {
			return [null].concat(this.teachers.map(t => t.id));
		},
		selectedTeacherName() {
			if (this.selectedTeacherId === null || this.selectedTeacherId === undefined) return '暂存至校区负责人';
			const t = this.teachers.find(x => x.id === this.selectedTeacherId);
			return t ? `${t.name}（${t.username}）${this.teacherRoleTag(t)}` : '暂存至校区负责人';
		},
		subjectNames() {
			return this.attendSubjects.map(s => s.name);
		},
		attendSubjectName() {
			const s = this.attendSubjects.find(x => x.id === this.attendSubjectId);
			return s ? s.name : '请选择学科';
		},
		/* 纯展示：课时汇总（仅由现有 subject_sessions 数据派生） */
		sessionTotals() {
			const list = (this.student && this.student.subject_sessions) || [];
			let total = 0, used = 0, remain = 0;
			list.forEach(ss => {
				if (typeof ss.total_sessions === 'number') total += ss.total_sessions;
				if (typeof ss.used_sessions === 'number') used += ss.used_sessions;
				if (typeof ss.remaining === 'number') remain += ss.remaining;
			});
			return { total, used, remain };
		},
		/* 纯展示：到期提醒横幅（仅对按到期时间计时的科目判断） */
		expireBanner() {
			const list = (this.student && this.student.subject_sessions) || [];
			let expired = null, soon = null;
			list.forEach(ss => {
				if (!ss.expire_date || ss.total_sessions !== null) return;
				const days = this.daysLeft(ss.expire_date);
				if (days < 0 && (!expired || days < expired.days)) expired = { name: ss.subject_name, days };
				if (days >= 0 && days <= 5 && (!soon || days < soon.days)) soon = { name: ss.subject_name, days };
			});
			if (expired) {
				return { type: 'is-danger', title: expired.name + ' 课时已到期', desc: '已到期 ' + (-expired.days) + ' 天，请及时安排续费' };
			}
			if (soon) {
				return { type: 'is-warn', title: soon.name + ' 课时即将到期', desc: '还剩 ' + soon.days + ' 天到期，请关注续费' };
			}
			return null;
		}
	},
	onLoad(options) {
		this.id = options.id;
		this.attendDate = new Date().toISOString().slice(0, 10);
		this.loadAll();
	},
	methods: {
		async loadAll() {
			this.loading = true;
			try {
				// 并行拉取：学生档案 / 成绩 / 作业 同时请求，缩短首屏等待
				const [student, scores, hw] = await Promise.all([
					get('/students/' + this.id),
					get('/learning/scores', { student_id: this.id }),
					get('/learning/homework', { student_id: this.id })
				]);
				this.student = student;
				// 打卡学科：优先用课时会话（subject_sessions：subject_id/subject_name/remaining），否则退回学科列表（subjects：id/name）
				const sessions = (this.student.subject_sessions && this.student.subject_sessions.length)
					? this.student.subject_sessions
					: (this.student.subjects || []);
				this.attendSubjects = sessions.map(x => ({
					id: x.subject_id != null ? x.subject_id : x.id,
					name: x.subject_name || x.name || '',
					remaining: x.remaining
				}));
				if (this.attendSubjects.length) this.attendSubjectId = this.attendSubjects[0].id;
				this.scores = scores || [];
				this.hwList = hw || [];
				if (this.canAssign) {
					try {
						this.teachers = await get('/auth/teachers');
					} catch (e) {
						this.teachers = [];
					}
				}
			} catch (e) {
				this.student = null;
			} finally {
				this.loading = false;
			}
		},
		openTeacherPick() {
			this.selectedTeacherId = (this.student && this.student.teacher_id) || null;
			this.showTeacherPick = true;
		},
		teacherRoleTag(t) {
			if (t.role === 'principal') return '· 校长';
			if (t.role === 'sub_principal' || t.role === 'campus_head') return '· 校区负责人';
			return '';
		},
		async doChangeTeacher() {
			try {
				await put('/students/' + this.id, { teacher_id: this.selectedTeacherId });
				uni.showToast({ title: '已保存', icon: 'success' });
				this.showTeacherPick = false;
				this.loadAll();
			} catch (e) {}
		},
		expireClass(d) {
			const days = this.daysLeft(d);
			if (days < 0) return 'text-danger';
			if (days <= 5) return 'text-warn';
			return 'text-primary';
		},
		expireText(d) {
			const days = this.daysLeft(d);
			if (days < 0) return `（已到期 ${-days} 天）`;
			if (days <= 5) return `（剩 ${days} 天）`;
			return '';
		},
		daysLeft(d) {
			const today = new Date(); today.setHours(0,0,0,0);
			const exp = new Date(d); exp.setHours(0,0,0,0);
			return Math.round((exp - today) / 86400000);
		},
		/* 纯展示：课时进度条 */
		progressWidth(ss) {
			const t = ss.total_sessions, u = ss.used_sessions || 0;
			if (!t) return 0;
			return Math.min(100, Math.round(u / t * 100));
		},
		progressClass(ss) {
			const t = ss.total_sessions, u = ss.used_sessions || 0;
			if (!t) return '';
			const remainRatio = (t - u) / t;
			if (remainRatio <= 0.2) return 'is-danger';
			if (remainRatio <= 0.5) return 'is-warn';
			return '';
		},
		/* 纯展示：到期标签 */
		expireTagClass(d) {
			const days = this.daysLeft(d);
			if (days < 0) return 'tag-danger';
			if (days <= 5) return 'tag-warn';
			return 'tag-success';
		},
		expireTagText(d) {
			const days = this.daysLeft(d);
			if (days < 0) return '已到期 ' + (-days) + ' 天';
			if (days === 0) return '今天到期';
			return '剩 ' + days + ' 天';
		},
		/* 纯展示：作业完成状态标签 */
		hwStatusClass(st) {
			if (st === '已完成') return 'tag-success';
			if (st === '未完成') return 'tag-warn';
			return 'tag-grey';
		},
		openAttend(isMakeup = false) {
			this.attendDate = new Date().toISOString().slice(0, 10);
			this.attendTitle = isMakeup ? '补卡' : '考勤打卡';
			this.showAttend = true;
		},
		async doAttend() {
			try {
				const res = await post('/learning/attendance', {
					student_id: Number(this.id),
					subject_id: this.attendSubjectId,
					date: this.attendDate,
					status: '正常'
				});
				uni.showToast({ title: '打卡成功', icon: 'success' });
				this.showAttend = false;
				this.loadAll();
			} catch (e) {}
		},
		openScore() { this.showScore = true; },
		async doScore() {
			await post('/learning/scores', Object.assign({}, this.scoreForm, {
				student_id: Number(this.id), score: Number(this.scoreForm.score), full_score: 100
			}));
			this.showScore = false;
			this.scoreForm = { subject: '', score: '', exam_type: '平时考' };
			this.loadAll();
		},
		openHomework() { this.showHw = true; },
		async doHomework() {
			await post('/learning/homework', Object.assign({}, this.hwForm, { student_id: Number(this.id) }));
			this.showHw = false;
			this.hwForm = { subject: '', content: '' };
			this.loadAll();
		},
		togglePerf() { this.showPerf = true; },
		async doPerf() {
			await post('/learning/performances', Object.assign({}, this.perfForm, { student_id: Number(this.id) }));
			this.showPerf = false;
			this.perfForm = { performance_type: '纪律', rating: 3, comment: '' };
			uni.showToast({ title: '已记录', icon: 'success' });
		}
	}
};
</script>

<style scoped>
.page { padding-bottom: 40rpx; }
.loading-page { padding-top: 120rpx; }
.loading-box {
	display: flex;
	flex-direction: column;
	align-items: center;
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
.avatar {
	width: 90rpx; height: 90rpx; border-radius: 50%;
	background: #10b981; color: #fff; text-align: center; line-height: 90rpx; font-size: 40rpx; margin-right: 20rpx;
	flex-shrink: 0;
}
.s-name { font-size: 34rpx; font-weight: 600; display: flex; align-items: center; flex-wrap: wrap; }
.s-no { font-size: 22rpx; color: #909399; margin-left: 10rpx; font-weight: 400; }
.status-tag { margin-left: 12rpx; }
.s-meta { font-size: 24rpx; margin-top: 6rpx; }
.change-teacher { color: #10b981; margin-left: 16rpx; }
.pick-tip { font-size: 22rpx; color: #909399; margin-top: 8rpx; line-height: 1.5; }
.session-item { padding: 14rpx 0; border-bottom: 1rpx solid #f0f0f0; }
.session-item:last-child { border-bottom: none; }
.session-head { display: flex; align-items: center; justify-content: space-between; gap: 16rpx; }
.session-name { font-size: 28rpx; font-weight: 500; color: #303133; }
.session-count { font-size: 24rpx; color: #10b981; font-variant-numeric: tabular-nums; }
.session-progress { display: flex; align-items: center; margin-top: 12rpx; }
.expire-line { font-size: 24rpx; margin-top: 12rpx; }
.expire-row { display: flex; align-items: center; justify-content: space-between; gap: 12rpx; }
.quick-grid { display: flex; flex-wrap: wrap; }
.quick-item {
	width: calc(50% - 12rpx);
	background: #f0fdf4; color: #10b981; text-align: center;
	padding: 26rpx 0; border-radius: 12rpx; margin-right: 12rpx; margin-bottom: 12rpx; font-size: 26rpx;
}
.quick-item:nth-child(2n) { margin-right: 0; }
.quick-item.is-done { background: #f3f4f6; color: #9ca3af; }
.quick-item.is-makeup { background: #fff7e6; color: #e6a23c; }
.record-item {
	display: flex; align-items: center; padding: 16rpx 0; border-bottom: 1rpx solid #f5f5f5; font-size: 26rpx;
}
.record-item:last-child { border-bottom: none; }
.record-title { font-size: 27rpx; color: #303133; }
.record-type { font-size: 22rpx; margin-left: 8rpx; }
.record-sub { font-size: 22rpx; margin-top: 4rpx; }
.score-num { font-size: 32rpx; font-weight: 700; color: #10b981; font-variant-numeric: tabular-nums; }
.score-full { font-size: 22rpx; font-weight: 400; color: #c0c4cc; }
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
</style>
