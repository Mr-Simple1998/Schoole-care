<template>
	<view class="page">
		<button class="btn-primary add-btn" @click="showAdd=true">新增教师</button>

		<view class="card">
			<view class="card-title">教师列表</view>
			<view v-for="t in teachers" :key="t.id" class="user-item">
				<view class="flex">
					<text class="flex-1">{{ t.name }} <text class="text-muted" style="font-size:24rpx">@{{ t.username }}</text></text>
					<text :class="t.is_active ? 'text-primary' : 'text-danger'">{{ t.is_active ? '启用' : '停用' }}</text>
					<text class="del" @click="doDelete(t)">删除</text>
				</view>
			</view>
			<view v-if="!teachers.length" class="text-muted empty">暂无教师</view>
		</view>

		<view class="mask" v-if="showAdd" @click="showAdd=false">
			<view class="dialog" @click.stop>
				<view class="dialog-title">新增教师</view>
				<view class="field"><text class="label">姓名</text><input class="input" v-model="form.name" /></view>
				<view class="field"><text class="label">用户名</text><input class="input" v-model="form.username" /></view>
				<view class="field"><text class="label">密码</text><input class="input" password v-model="form.password" /></view>
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
			teachers: [],
			showAdd: false,
			form: { name: '', username: '', password: '' }
		};
	},
	onLoad() { this.loadTeachers(); },
	methods: {
		async loadTeachers() {
			try { this.teachers = await get('/auth/teachers'); } catch (e) {}
		},
		async doAdd() {
			if (!this.form.name || !this.form.username || !this.form.password) {
				uni.showToast({ title: '请填写完整', icon: 'none' });
				return;
			}
			await post('/auth/register', Object.assign({}, this.form, { role: 'teacher' }));
			uni.showToast({ title: '已添加', icon: 'success' });
			this.showAdd = false;
			this.form = { name: '', username: '', password: '' };
			this.loadTeachers();
		},
		doDelete(t) {
			uni.showModal({
				title: '提示',
				content: '确定删除教师 ' + t.name + ' 吗？',
				success: async (res) => {
					if (res.confirm) {
						try {
							await del('/auth/teachers/' + t.id);
							uni.showToast({ title: '已删除', icon: 'success' });
							this.loadTeachers();
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
.user-item { padding: 20rpx 0; border-bottom: 1rpx solid #f5f5f5; }
.user-item:last-child { border-bottom: none; }
.del { color: #f56c6c; margin-left: 20rpx; font-size: 26rpx; }
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