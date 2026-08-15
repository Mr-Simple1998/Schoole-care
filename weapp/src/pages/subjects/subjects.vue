<template>
	<view class="page">
		<button class="btn-primary add-btn" @click="showAdd=true">新增学科</button>

		<view class="card">
			<view class="card-title">学科列表</view>
			<view v-for="s in subjects" :key="s.id" class="sub-item">
				<view class="flex">
					<text class="flex-1">{{ s.name }}
						<text class="tag">{{ s.category }}</text>
					</text>
					<text class="del" @click="doDelete(s)">删除</text>
				</view>
			</view>
			<view v-if="!subjects.length" class="text-muted empty">暂无学科</view>
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

export default {
	data() {
		return {
			subjects: [],
			cats: ['学科', '非学科'],
			showAdd: false,
			form: { name: '', category: '学科' }
		};
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
.add-btn { margin: 20rpx; }
.sub-item { padding: 20rpx 0; border-bottom: 1rpx solid #f5f5f5; }
.sub-item:last-child { border-bottom: none; }
.tag { font-size: 22rpx; color: #909399; background: #f0f0f0; border-radius: 6rpx; padding: 2rpx 12rpx; margin-left: 10rpx; }
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