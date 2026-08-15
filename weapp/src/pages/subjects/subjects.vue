<template>
	<view class="page">
		<button class="btn-primary add-btn" v-if="store.isPrincipal" @click="showAdd=true">新增学科</button>

		<!-- 概览小卡（纯展示） -->
		<view class="stat-grid" v-if="subjects && subjects.length">
			<view class="stat-card is-green">
				<view class="stat-top">
					<text class="stat-label">学科总数</text>
					<text class="stat-emoji">📚</text>
				</view>
				<text class="stat-num">{{ subjectStats.total }}</text>
				<text class="stat-sub">含学科与非学科</text>
				<view class="stat-accent"></view>
			</view>
			<view class="stat-card is-green">
				<view class="stat-top">
					<text class="stat-label">文化学科</text>
					<text class="stat-emoji">📖</text>
				</view>
				<text class="stat-num">{{ subjectStats.academic }}</text>
				<text class="stat-sub">知识类课程</text>
				<view class="stat-accent"></view>
			</view>
			<view class="stat-card is-purple">
				<view class="stat-top">
					<text class="stat-label">非学科</text>
					<text class="stat-emoji">🎨</text>
				</view>
				<text class="stat-num">{{ subjectStats.hobby }}</text>
				<text class="stat-sub">艺术/体育类</text>
				<view class="stat-accent"></view>
			</view>
			<view class="stat-card is-blue">
				<view class="stat-top">
					<text class="stat-label">正常启用</text>
					<text class="stat-emoji">✅</text>
				</view>
				<text class="stat-num">{{ subjectStats.active }}</text>
				<text class="stat-sub">可分配给学生</text>
				<view class="stat-accent"></view>
			</view>
		</view>

		<!-- 学科卡片网格 -->
		<view class="sub-grid">
			<view v-for="s in subjects" :key="s.id" class="sub-card" :class="s.category === '学科' ? 'is-academic' : 'is-hobby'">
				<view class="sub-head">
					<view class="sub-name">
						<view class="sub-icon">{{ s.category === '学科' ? '📖' : '🎨' }}</view>
						<text class="sub-title">{{ s.name }}</text>
					</view>
					<text class="tag" :class="s.category === '学科' ? 'tag-primary' : 'tag-warn'">{{ s.category }}</text>
				</view>
				<view class="sub-foot">
					<view class="flex">
						<text class="dot" :class="s.is_active ? 'dot-green' : 'dot-red'"></text>
						<text :class="s.is_active ? 'text-primary' : 'text-danger'">{{ s.is_active ? '启用' : '停用' }}</text>
					</view>
					<text class="del" v-if="store.isPrincipal" @click="doDelete(s)">删除</text>
				</view>
			</view>
		</view>
		<view v-if="!subjects.length" class="card">
			<view class="card-title"><view class="bar"></view>学科列表</view>
			<view class="text-muted empty">暂无学科</view>
		</view>

		<view class="mask" v-if="showAdd" @click="showAdd=false">
			<view class="dialog" @click.stop>
				<view class="dialog-title">新增学科</view>
				<view class="field"><text class="label">学科名称</text><input class="input" v-model="form.name" /></view>
				<view class="field">
					<text class="label">分类</text>
					<picker :range="cats" @change="e => form.category=cats[e.detail.value]">
						<view class="input">{{ form.category }}</view>
					</picker>
				</view>
				<view class="dialog-btns">
					<button class="btn-cancel" @click="showAdd=false">取消</button>
					<button class="btn-primary" @click="doAdd">保存</button>
				</view>
			</view>
		</view>
	</view>
</template>

<script>
import { get, post, del } from '../../utils/request';
import { useUserStore } from '../../stores/user';

export default {
	data() {
		return {
			store: useUserStore(),
			subjects: [],
			cats: ['学科', '非学科'],
			showAdd: false,
			form: { name: '', category: '学科' }
		};
	},
	computed: {
		// 纯展示：概览统计
		subjectStats() {
			const list = this.subjects || [];
			const academic = list.filter(s => s.category === '学科').length;
			const active = list.filter(s => s.is_active).length;
			return {
				total: list.length,
				academic: academic,
				hobby: list.length - academic,
				active: active
			};
		}
	},
	onLoad() { this.loadSubjects(); },
	methods: {
		async loadSubjects() {
			try { this.subjects = await get('/subjects'); } catch (e) {}
		},
		async doAdd() {
			if (!this.form.name) {
				uni.showToast({ title: '请填写学科名', icon: 'none' });
				return;
			}
			await post('/subjects', this.form);
			uni.showToast({ title: '已添加', icon: 'success' });
			this.showAdd = false;
			this.form = { name: '', category: '学科' };
			this.loadSubjects();
		},
		doDelete(s) {
			uni.showModal({
				title: '提示',
				content: '确定删除学科 ' + s.name + ' 吗？将解除所有学生关联',
				success: async (res) => {
					if (res.confirm) {
						try {
							await del('/subjects/' + s.id);
							uni.showToast({ title: '已删除', icon: 'success' });
							this.loadSubjects();
						} catch (e) {}
					}
				}
			});
		}
	}
};
</script>

<style scoped>
.page { padding-bottom: 40rpx; }
.add-btn { margin: 20rpx; }

/* 学科卡片网格 */
.sub-grid {
	display: flex;
	flex-wrap: wrap;
	margin: 20rpx;
}
.sub-card {
	width: calc(50% - 10rpx);
	margin-right: 20rpx;
	margin-bottom: 20rpx;
	background: #fff;
	border-radius: 16rpx;
	padding: 24rpx;
	box-sizing: border-box;
	border: 1rpx solid #f0f0f0;
	position: relative;
	overflow: hidden;
	box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.04);
}
.sub-card:nth-child(2n) { margin-right: 0; }
.sub-card::before {
	content: '';
	position: absolute;
	left: 0;
	top: 0;
	bottom: 0;
	width: 8rpx;
}
.sub-card.is-academic::before { background: #10b981; }
.sub-card.is-hobby::before { background: #8b5cf6; }
.sub-card.is-academic { border-top: 4rpx solid #10b981; }
.sub-card.is-hobby { border-top: 4rpx solid #8b5cf6; }

.sub-head {
	display: flex;
	align-items: center;
	justify-content: space-between;
	margin-bottom: 20rpx;
}
.sub-name {
	display: flex;
	align-items: center;
	min-width: 0;
	flex: 1;
}
.sub-icon {
	width: 56rpx;
	height: 56rpx;
	border-radius: 14rpx;
	background: #ecfdf5;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 30rpx;
	margin-right: 14rpx;
	flex-shrink: 0;
}
.is-hobby .sub-icon { background: #f5f3ff; }
.sub-title {
	font-size: 28rpx;
	font-weight: 600;
	color: #303133;
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}
.sub-foot {
	display: flex;
	align-items: center;
	justify-content: space-between;
	border-top: 1rpx dashed #f0f0f0;
	padding-top: 16rpx;
}
.del { color: #f56c6c; font-size: 26rpx; }
.empty { text-align: center; padding: 30rpx 0; }
.mask { position: fixed; left:0; top:0; right:0; bottom:0; background: rgba(0,0,0,0.45); z-index:99; display:flex; align-items:center; justify-content:center; }
.dialog { width: 80%; background:#fff; border-radius:16rpx; padding:36rpx 32rpx; }
.dialog-title { font-size:32rpx; font-weight:600; margin-bottom:24rpx; }
.dialog-btns { display:flex; margin-top:20rpx; }
.dialog-btns button { flex:1; margin:0 8rpx; font-size:28rpx; }
.btn-cancel { background:#f5f7fa; color:#606266; border-radius:12rpx; }
.field { margin-bottom:20rpx; }
.label { display:block; font-size:24rpx; color:#606266; margin-bottom:8rpx; }
.input { background:#f5f7fa; border-radius:10rpx; padding:16rpx 20rpx; font-size:28rpx; }
</style>
