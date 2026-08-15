<template>
	<view class="page">
		<button class="btn-primary add-fee" @click="showAdd=true" v-if="store.isPrincipal">＋ 新增收费</button>

		<!-- 统计卡片（纯展示，数据来自 fees / overdue） -->
		<view class="stat-grid">
			<view class="stat-card is-green">
				<view class="stat-top">
					<text class="stat-label">本月收入</text>
					<text class="stat-emoji">💰</text>
				</view>
				<text class="stat-num">¥{{ monthIncome }}</text>
				<text class="stat-sub">{{ monthFeeCount }} 笔收费</text>
			</view>
			<view class="stat-card is-red">
				<view class="stat-top">
					<text class="stat-label">欠费总额</text>
					<text class="stat-emoji">⚠️</text>
				</view>
				<text class="stat-num">¥{{ totalOverdue }}</text>
				<text class="stat-sub">{{ overdue.length }} 笔待缴</text>
			</view>
			<view class="stat-card is-purple">
				<view class="stat-top">
					<text class="stat-label">退费</text>
					<text class="stat-emoji">↩️</text>
				</view>
				<text class="stat-num">¥{{ monthRefund }}</text>
				<text class="stat-sub">本月合计</text>
			</view>
		</view>

		<!-- 欠费提醒横幅 -->
		<view v-if="overdue.length && store.isPrincipal" class="banner is-danger">
			<view>
				<view class="banner-title">⚠️ 有 {{ overdue.length }} 笔欠费待收</view>
				<view class="banner-desc">合计欠费 ¥{{ totalOverdue }}，请及时联系家长缴费</view>
			</view>
		</view>

		<!-- 欠费明细 -->
		<view class="card" v-if="overdue.length && store.isPrincipal">
			<view class="card-title"><text class="bar"></text>欠费明细</view>
			<view v-for="(o, i) in overdue" :key="i" class="info-row">
				<view class="ir-left">
					<view class="ir-title">{{ o.student_name }}</view>
					<view class="ir-sub">{{ o.item }} · 应缴 ¥{{ o.amount }}</view>
				</view>
				<view class="ir-right">
					<text class="tag" :class="o.status === '部分缴纳' ? 'tag-warn' : 'tag-danger'">{{ o.status }}</text>
					<text class="amount">欠 ¥{{ o.unpaid }}</text>
				</view>
			</view>
		</view>

		<!-- 收费流水 -->
		<view class="card">
			<view class="card-title"><text class="bar"></text>收费流水</view>
			<view v-for="f in fees" :key="f.id" class="info-row">
				<view class="ir-left">
					<view class="ir-title">{{ f.student_name }} · {{ f.fee_type }}</view>
					<view class="ir-sub">
						<text>{{ f.pay_date }} · {{ f.payment_period || '单次' }}</text>
						<text class="tag tag-plain">{{ f.payment_method }}</text>
						<text v-if="f.total_sessions" class="tag" :class="sessionTagClass(f)">剩 {{ f.remaining_sessions }} 次</text>
					</view>
					<view v-if="f.total_sessions" class="session-progress">
						<view class="progress" :class="sessionProgressClass(f)">
							<view class="progress-inner" :style="{ width: sessionPercent(f) + '%' }"></view>
						</view>
						<text class="progress-text">已核 {{ f.used_sessions || 0 }} / {{ f.total_sessions }}</text>
					</view>
				</view>
				<view class="ir-right">
					<text class="amount income">¥{{ f.amount }}</text>
				</view>
			</view>
			<view v-if="!fees.length" class="empty">暂无收费记录</view>
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
		},
		/* ===== 纯展示统计（不改动任何请求/提交逻辑） ===== */
		currentMonth() {
			const d = new Date();
			const m = d.getMonth() + 1;
			return d.getFullYear() + '-' + (m < 10 ? '0' + m : m);
		},
		monthFees() {
			const ym = this.currentMonth;
			return (this.fees || []).filter(f => (f.pay_date || '').slice(0, 7) === ym);
		},
		monthIncome() {
			return this.round2(this.monthFees.reduce((s, f) => s + Number(f.amount || 0), 0));
		},
		monthFeeCount() {
			return this.monthFees.length;
		},
		// 退费：页面未加载 /income/refunds，按本月负数流水汇总展示
		monthRefund() {
			return this.round2(this.monthFees.filter(f => Number(f.amount) < 0).reduce((s, f) => s + Math.abs(Number(f.amount)), 0));
		},
		totalOverdue() {
			return this.round2((this.overdue || []).reduce((s, o) => s + Number(o.unpaid || 0), 0));
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
		},
		/* ===== 纯展示 helper ===== */
		round2(n) {
			return Math.round(n * 100) / 100;
		},
		sessionPercent(f) {
			const total = Number(f.total_sessions) || 0;
			const used = Number(f.used_sessions) || 0;
			if (!total) return 0;
			return Math.min(100, Math.round((used / total) * 100));
		},
		sessionProgressClass(f) {
			const total = Number(f.total_sessions) || 0;
			const remaining = Number(f.remaining_sessions);
			const ratio = total ? remaining / total : 1;
			if (ratio < 0.2) return 'is-danger';
			if (ratio < 0.5) return 'is-warn';
			return '';
		},
		sessionTagClass(f) {
			const total = Number(f.total_sessions) || 0;
			const remaining = Number(f.remaining_sessions);
			const ratio = total ? remaining / total : 1;
			if (ratio < 0.2) return 'tag-danger';
			if (ratio < 0.5) return 'tag-warn';
			return 'tag-success';
		}
	}
};
</script>

<style scoped>
.page { padding-bottom: 40rpx; }
.add-fee { margin: 20rpx; width: calc(100% - 40rpx); display: block; padding: 22rpx 0; font-size: 30rpx; }
.session-progress { display: flex; align-items: center; margin-top: 12rpx; }
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
