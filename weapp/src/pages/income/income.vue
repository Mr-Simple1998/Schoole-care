<template>
	<view class="page">
		<button class="btn-primary add-fee" @click="showAdd=true" v-if="store.isPrincipal">新增收费</button>

		<view class="card" v-if="overdue.length && store.isPrincipal">
			<view class="card-title">欠费提醒</view>
			<view v-for="(o, i) in overdue" :key="i" class="overdue-item">
				<view class="flex">
					<text class="flex-1">{{ o.student_name }}</text>
					<text class="text-danger">欠费 {{ o.unpaid }}</text>
				</view>
				<view class="text-muted" style="font-size:24rpx">{{ o.item }} · {{ o.status }}</view>
			</view>
		</view>

		<view class="card">
			<view class="card-title">收费流水</view>
			<view v-for="f in fees" :key="f.id" class="fee-item">
				<view class="flex">
					<text class="flex-1">{{ f.student_name }} · {{ f.fee_type }}</text>
					<text class="text-primary">¥{{ f.amount }}</text>
				</view>
				<view class="text-muted" style="font-size:24rpx">
					{{ f.pay_date }} · {{ f.payment_period || '单次' }}
					<text v-if="f.total_sessions"> · 剩 {{ f.remaining_sessions }} 次</text>
				</view>
			</view>
			<view v-if="!fees.length" class="text-muted empty">暂无收费记录</view>
		</view>

		<!-- 新增收费弹窗 -->
		<view class="mask" v-if="showAdd" @click="showAdd=false">
			<view class="dialog" @click.stop>
				<view class="dialog-title">新增收费</view>
				<view class="field">
					<text class="label">选择学生</text>
					<picker :range="students.map(s=>s.name)" @change="e => feeForm.student_id=students[e.detail.value].id">
						<view class="input">{{ feeStudentName }}</view>
					</picker>
				</view>
				<view class="field"><text class="label">收费项目</text><input class="input" v-model="feeForm.fee_type" placeholder="如课时费" /></view>
				<view class="field"><text class="label">金额</text><input class="input" type="number" v-model="feeForm.amount" placeholder="金额" /></view>
				<view class="field">
					<text class="label">缴费时间段</text>
					<picker :range="periods" @change="e => feeForm.payment_period=periods[e.detail.value]">
						<view class="input">{{ feeForm.payment_period || '请选择' }}</view>
					</picker>
				</view>
				<view class="field"><text class="label">总次数（按次核销可填）</text><input class="input" type="number" v-model="feeForm.total_sessions" placeholder="可不填" /></view>
				<view class="dialog-btns">
					<button class="btn-cancel" @click="showAdd=false">取消</button>
					<button class="btn-primary" @click="doAddFee">保存</button>
				</view>
			</view>
		</view>
	</view>
</template>

<script>
import { useUserStore } from '../../stores/user';
import { get, post } from '../../utils/request';

const PERIODS = ['一月', '半学期', '一年'];

export default {
	data() {
		return {
			store: useUserStore(),
			fees: [],
			overdue: [],
			students: [],
			showAdd: false,
			periods: PERIODS,
			feeForm: { student_id: null, fee_type: '', amount: '', payment_period: '', total_sessions: '' }
		};
	},
	computed: {
		feeStudentName() {
			const s = this.students.find(x => x.id === this.feeForm.student_id);
			return s ? s.name : '请选择学生';
		}
	},
	onLoad() { this.loadAll(); },
	methods: {
		async loadAll() {
			try {
				this.fees = await get('/income/fees');
				this.overdue = await get('/income/overdue');
				this.students = await get('/students');
			} catch (e) {}
		},
		async doAddFee() {
			if (!this.feeForm.student_id || !this.feeForm.amount) {
				uni.showToast({ title: '请填写学生和金额', icon: 'none' });
				return;
			}
			await post('/income/fees', Object.assign({}, this.feeForm, {
				amount: Number(this.feeForm.amount),
				total_sessions: this.feeForm.total_sessions ? Number(this.feeForm.total_sessions) : null
			}));
			uni.showToast({ title: '已保存', icon: 'success' });
			this.showAdd = false;
			this.feeForm = { student_id: null, fee_type: '', amount: '', payment_period: '', total_sessions: '' };
			this.loadAll();
		}
	}
};
</script>

<style scoped>
.page { padding-bottom: 40rpx; }
.add-fee { margin: 20rpx; }
.fee-item, .overdue-item { padding: 16rpx 0; border-bottom: 1rpx solid #f5f5f5; }
.fee-item:last-child, .overdue-item:last-child { border-bottom: none; }
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