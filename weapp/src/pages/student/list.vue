<template>
	<view class="page">
		<view class="search-bar">
			<input class="search-input" v-model="keyword" placeholder="搜索姓名/学号" @input="filterList" />
			<button class="btn-primary add-btn" @click="goAdd">新增</button>
		</view>

		<view v-if="filtered.length" class="student-list">
			<view v-for="s in filtered" :key="s.id" class="card student-item">
				<view class="flex" @click="goDetail(s.id)">
					<view class="avatar">{{ s.name[0] }}</view>
					<view class="flex-1">
						<view class="s-name">{{ s.name }}
							<text class="s-no">{{ s.student_no }}</text>
							<text v-if="s.status !== '在读'" class="s-status">{{ s.status }}</text>
						</view>
						<view class="text-muted s-meta">
							{{ s.school || '' }} {{ s.grade || '' }} · 入学 {{ s.enrollment_date || '-' }}
						</view>
						<view class="s-subjects" v-if="s.subjects && s.subjects.length">
							<text v-for="sub in s.subjects" :key="sub.id" class="sub-tag">{{ sub.name }}</text>
						</view>
					</view>
				</view>
				<button class="btn-primary attend-btn" @click="openAttend(s)">打卡</button>
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
				<view class="dialog-btns">
					<button class="btn-cancel" @click="showAttend=false">取消</button>
					<button class="btn-primary" @click="doAttend">确认打卡</button>
				</view>
			</view>
		</view>
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
			attendSubjectId: null
		};
	},
	onShow() {
		this.loadStudents();
	},
	computed: {
		attendNames() {
			return this.attendSubjects.map(s => this.attendLabel(s));
		},
		attendSubjectName() {
			const s = this.attendSubjects.find(x => x.id === this.attendSubjectId);
			return s ? this.attendLabel(s) : '请选择学科';
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
		goDetail(id) {
			uni.navigateTo({ url: '/pages/student/detail?id=' + id });
		},
		attendLabel(s) {
			return s.remaining !== null ? `${s.name}（剩${s.remaining}次）` : s.name;
		},
		openAttend(s) {
			this.attendStudent = s;
			this.attendSubjects = s.subject_sessions && s.subject_sessions.length ? s.subject_sessions : (s.subjects || []);
			this.attendSubjectId = this.attendSubjects.length ? this.attendSubjects[0].id : null;
			this.showAttend = true;
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
					date: new Date().toISOString().slice(0, 10),
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
}
.add-btn { margin: 0; font-size: 26rpx; }
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
}
.s-name { font-size: 32rpx; font-weight: 600; }
.s-no { font-size: 22rpx; color: #909399; margin-left: 10rpx; }
.s-status { font-size: 22rpx; color: #f56c6c; margin-left: 10rpx; }
.s-meta { font-size: 24rpx; margin-top: 6rpx; }
.s-subjects { margin-top: 10rpx; }
.sub-tag {
	display: inline-block;
	font-size: 22rpx;
	color: #10b981;
	background: #f0fdf4;
	border-radius: 8rpx;
	padding: 4rpx 14rpx;
	margin-right: 8rpx;
}
.empty { text-align: center; padding: 80rpx 0; }
.attend-btn {
	margin: 16rpx 24rpx 24rpx;
	font-size: 26rpx;
	height: 60rpx;
	line-height: 60rpx;
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
</style>