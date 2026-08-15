<template>
	<view class="page" v-if="student">
		<!-- 学生信息 -->
		<view class="card">
			<view class="flex">
				<view class="avatar">{{ student.name[0] }}</view>
				<view class="flex-1">
					<view class="s-name">{{ student.name }} <text class="s-no">{{ student.student_no }}</text></view>
					<view class="text-muted s-meta">
						{{ student.school || '' }} {{ student.grade || '' }} · 入学 {{ student.enrollment_date || '-' }}
					</view>
					<view class="s-meta"><text class="text-warn">积分 {{ student.points }}</text> · {{ student.status }}</view>
				</view>
			</view>
		</view>

		<!-- 课时核销概览 -->
		<view class="card" v-if="student.subject_sessions && student.subject_sessions.length">
			<view class="card-title">课时核销情况</view>
			<view v-for="ss in student.subject_sessions" :key="ss.subject_id" class="session-item">
				<view class="flex">
					<text class="flex-1">{{ ss.subject_name }}</text>
					<text v-if="ss.total_sessions !== null" :class="ss.remaining > 0 ? 'text-primary' : 'text-danger'">
						已核 {{ ss.used_sessions }} / {{ ss.total_sessions }}（剩 {{ ss.remaining }}）
					</text>
					<text v-else class="text-muted">按到期时间</text>
				</view>
				<view v-if="ss.total_sessions === null" class="text-muted expire-line">
					<text v-if="ss.expire_date">
						到期：{{ ss.expire_date }}
						<text :class="expireClass(ss.expire_date)">{{ expireText(ss.expire_date) }}</text>
					</text>
					<text v-else>时长：{{ ss.duration_value }}{{ ss.duration_unit }}（首次打卡后开始计时）</text>
				</view>
			</view>
		</view>

		<!-- 功能入口 -->
		<view class="card">
			<view class="card-title">功能</view>
			<view class="quick-grid">
				<view class="quick-item" @click="openAttend"><text>考勤打卡</text></view>
				<view class="quick-item" @click="openScore"><text>成绩</text></view>
				<view class="quick-item" @click="openHomework"><text>作业</text></view>
				<view class="quick-item" @click="togglePerf"><text>课堂表现</text></view>
			</view>
		</view>

		<!-- 打卡弹窗 -->
		<view class="mask" v-if="showAttend" @click="showAttend=false">
			<view class="dialog" @click.stop>
				<view class="dialog-title">考勤打卡</view>
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

		<!-- 记录列表 -->
		<view class="card" v-if="scores.length">
			<view class="card-title">近期成绩</view>
			<view v-for="sc in scores.slice(0,5)" :key="sc.id" class="record-item">
				<text class="flex-1">{{ sc.subject }} · {{ sc.exam_type }}</text>
				<text class="text-primary">{{ sc.score }} / {{ sc.full_score }}</text>
			</view>
		</view>
		<view class="card" v-if="hwList.length">
			<view class="card-title">近期作业</view>
			<view v-for="h in hwList.slice(0,5)" :key="h.id" class="record-item">
				<text class="flex-1">{{ h.subject }} · {{ h.complete_status }}</text>
				<text class="text-muted">{{ h.assign_date }}</text>
			</view>
		</view>
	</view>
</template>

<script>
import { get, post } from '../../utils/request';

const PERF_TYPES = ['纪律','专注','积极','作业','礼仪'];

export default {
	data() {
		return {
			id: null,
			student: null,
			scores: [],
			hwList: [],
			showAttend: false, attendSubjects: [], attendSubjectId: null, attendDate: '',
			showScore: false, scoreForm: { subject: '', score: '', exam_type: '平时考' },
			showHw: false, hwForm: { subject: '', content: '' },
			showPerf: false, perfTypes: PERF_TYPES, perfForm: { performance_type: '纪律', rating: 3, comment: '' }
		};
	},
	computed: {
		subjectNames() {
			return this.attendSubjects.map(s => s.name);
		},
		attendSubjectName() {
			const s = this.attendSubjects.find(x => x.id === this.attendSubjectId);
			return s ? s.name : '请选择学科';
		}
	},
	onLoad(options) {
		this.id = options.id;
		this.attendDate = new Date().toISOString().slice(0, 10);
		this.loadAll();
	},
	methods: {
		async loadAll() {
			try {
				this.student = await get('/students/' + this.id);
				this.attendSubjects = this.student.subjects || [];
				if (this.attendSubjects.length) this.attendSubjectId = this.attendSubjects[0].id;
				this.scores = await get('/learning/scores', { student_id: this.id });
				this.hwList = await get('/learning/homework', { student_id: this.id });
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
		openAttend() { this.showAttend = true; },
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
.avatar {
	width: 90rpx; height: 90rpx; border-radius: 50%;
	background: #10b981; color: #fff; text-align: center; line-height: 90rpx; font-size: 40rpx; margin-right: 20rpx;
}
.s-name { font-size: 34rpx; font-weight: 600; }
.s-no { font-size: 22rpx; color: #909399; margin-left: 10rpx; }
.s-meta { font-size: 24rpx; margin-top: 6rpx; }
.session-item { padding: 14rpx 0; border-bottom: 1rpx solid #f0f0f0; }
.session-item:last-child { border-bottom: none; }
.expire-line { font-size: 24rpx; margin-top: 6rpx; }
.quick-grid { display: flex; flex-wrap: wrap; }
.quick-item {
	width: calc(50% - 12rpx);
	background: #f0fdf4; color: #10b981; text-align: center;
	padding: 26rpx 0; border-radius: 12rpx; margin-right: 12rpx; margin-bottom: 12rpx; font-size: 26rpx;
}
.quick-item:nth-child(2n) { margin-right: 0; }
.record-item {
	display: flex; padding: 12rpx 0; border-bottom: 1rpx solid #f5f5f5; font-size: 26rpx;
}
.record-item:last-child { border-bottom: none; }
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