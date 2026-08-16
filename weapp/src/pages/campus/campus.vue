<template>
	<view class="page">
		<!-- 汇总统计卡（校长=全机构；负责人=本校区） -->
		<view class="stat-grid" v-if="summary">
			<view class="stat-card is-green">
				<view class="stat-top"><text class="stat-label">本月收入</text><text class="stat-emoji">💰</text></view>
				<text class="stat-num">¥{{ fmt(summary.month_income) }}</text>
				<text class="stat-sub">学费自动归属 + 手工登记</text>
			</view>
			<view class="stat-card is-red">
				<view class="stat-top"><text class="stat-label">本月支出</text><text class="stat-emoji">📤</text></view>
				<text class="stat-num">¥{{ fmt(summary.month_expense) }}</text>
				<text class="stat-sub">房租/工资/水电等</text>
			</view>
			<view class="stat-card" :class="summary.month_balance >= 0 ? 'is-blue' : 'is-orange'">
				<view class="stat-top"><text class="stat-label">本月结余</text><text class="stat-emoji">⚖️</text></view>
				<text class="stat-num">¥{{ fmt(summary.month_balance) }}</text>
				<text class="stat-sub">收入 - 支出</text>
			</view>
			<view class="stat-card is-purple">
				<view class="stat-top"><text class="stat-label">在读学生</text><text class="stat-emoji">🏫</text></view>
				<text class="stat-num">{{ summary.student_count }}</text>
				<text class="stat-sub">今日打卡 {{ summary.today_attendance }}</text>
			</view>
		</view>

		<!-- 操作 -->
		<view class="action-bar">
			<button class="btn-primary action-btn" @click="openTxn(null)">＋ 登记收支</button>
			<button v-if="canManage" class="btn-ghost action-btn" @click="openCampus()">设置校区</button>
		</view>

		<!-- 校区卡片 -->
		<view class="card campus-card" v-for="c in items" :key="c.id">
			<view class="campus-head">
				<view class="campus-title">
					<text class="campus-name">{{ c.name }}</text>
					<text v-if="c.status === false" class="tag tag-grey">已停用</text>
				</view>
				<view class="head-tags" v-if="c.heads && c.heads.length">
					<text v-for="h in c.heads" :key="h.id" class="tag" :class="h.role === 'principal' ? 'tag-danger' : 'tag-success'">{{ h.name }}{{ h.role === 'principal' ? '·总校长' : '' }}</text>
				</view>
				<text v-else-if="canManage" class="tag tag-plain">未设负责人</text>
			</view>
			<view v-if="c.address || c.phone" class="campus-meta">
				<text v-if="c.address">📍 {{ c.address }}</text>
				<text v-if="c.phone">📞 {{ c.phone }}</text>
			</view>
			<view class="campus-stats">
				<view class="cs-item">
					<text class="cs-label">本月收入</text>
					<text class="cs-value income">¥{{ fmt(c.month_income) }}</text>
				</view>
				<view class="cs-item">
					<text class="cs-label">本月支出</text>
					<text class="cs-value expense">¥{{ fmt(c.month_expense) }}</text>
				</view>
				<view class="cs-item">
					<text class="cs-label">结余</text>
					<text class="cs-value" :class="c.month_balance >= 0 ? 'income' : 'expense'">¥{{ fmt(c.month_balance) }}</text>
				</view>
			</view>
			<view class="campus-info">
				<text>学生 <text class="num">{{ c.student_count }}</text></text>
				<text>教师 <text class="num">{{ c.teacher_count }}</text></text>
				<text>今日打卡 <text class="num">{{ c.today_attendance }}</text></text>
				<text :class="c.unpaid > 0 ? 'unpaid' : ''">待缴 ¥{{ fmt(c.unpaid) }}</text>
			</view>
			<view class="campus-actions">
				<text class="link primary" @click="goTxn(c)">收支明细 ›</text>
				<text class="link" @click="openTxn(c)">登记收支</text>
				<template v-if="canManage">
					<text class="link" @click="openHead(c)">负责人</text>
					<text class="link" @click="openCampus(c)">编辑</text>
					<text class="link danger" @click="delCampus(c)">删除</text>
				</template>
			</view>
		</view>

		<!-- 未分校区（校长可见） -->
		<view v-if="uncategorized" class="card campus-card uncat">
			<view class="campus-head">
				<view class="campus-title">
					<text class="campus-name">未分校区</text>
					<text class="tag tag-grey">未归属数据</text>
				</view>
			</view>
			<view class="campus-stats">
				<view class="cs-item">
					<text class="cs-label">本月学费收入</text>
					<text class="cs-value income">¥{{ fmt(uncategorized.month_income) }}</text>
				</view>
				<view class="cs-item">
					<text class="cs-label">在读学生</text>
					<text class="cs-value">{{ uncategorized.student_count }}</text>
				</view>
				<view class="cs-item">
					<text class="cs-label">今日打卡</text>
					<text class="cs-value">{{ uncategorized.today_attendance }}</text>
				</view>
			</view>
			<view class="campus-actions">
				<text class="link primary" @click="goTxn(null)">收支明细 ›</text>
			</view>
		</view>

		<view v-if="!items.length && !uncategorized" class="empty">暂无校区，点击右上角「设置校区」创建</view>

		<!-- 设置校区弹层 -->
		<view v-if="showCampusForm" class="overlay" @click="closeAll">
			<view class="sheet" @click.stop>
				<view class="sheet-title">{{ campusForm.id ? '编辑校区' : '新增校区' }}</view>
				<view class="field">
					<text class="label">校区名称 *</text>
					<input class="input" v-model="campusForm.name" placeholder="如：总校 / 一分校" />
				</view>
				<view class="field">
					<text class="label">地址</text>
					<input class="input" v-model="campusForm.address" placeholder="校区地址" />
				</view>
				<view class="field">
					<text class="label">联系电话</text>
					<input class="input" v-model="campusForm.phone" placeholder="联系电话" />
				</view>
				<view class="field">
					<text class="label">备注</text>
					<input class="input" v-model="campusForm.remark" placeholder="备注信息" />
				</view>
				<view class="field" v-if="campusForm.id">
					<text class="label">状态</text>
					<switch :checked="campusForm.status" color="#10b981" @change="e => campusForm.status = e.detail.value" />
				</view>
				<button class="btn-primary sheet-btn" :loading="saving" @click="saveCampus">保存</button>
			</view>
		</view>

		<!-- 负责人设置弹层（总校长；可多选，含总校长；支持离职办理） -->
		<view v-if="showHeadForm" class="overlay" @click="closeAll">
			<view class="sheet" @click.stop>
				<view class="sheet-title">设置「{{ headCampus && headCampus.name }}」负责人（可多选）</view>
				<view class="field">
					<text class="label">当前负责人</text>
					<view v-if="headCampus && headCampus.heads && headCampus.heads.length" class="head-list">
						<view v-for="h in headCampus.heads" :key="h.id" class="head-item">
							<text class="head-item-name">{{ h.name }}（{{ h.username }}）<text v-if="h.role === 'principal'" class="tag tag-danger">总校长</text></text>
							<text class="link danger" @click="resignHead(h)">办理离职</text>
						</view>
					</view>
					<text v-else class="kv-value text-muted">未设置</text>
				</view>
				<view class="field">
					<text class="label">选择负责人（可多选）</text>
					<checkbox-group class="head-check-group" @change="e => headForm.user_ids = (e.detail.value || []).map(Number)">
						<label v-for="t in headCandidates" :key="t.id" class="check-item">
							<checkbox :value="String(t.id)" :checked="headForm.user_ids.indexOf(t.id) > -1" :disabled="t.resigned || !t.is_active" />
							<text class="check-label" :class="{ muted: t.resigned || !t.is_active }">{{ t.name }}（{{ t.username }}）{{ t.role === 'principal' ? '·总校长' : '' }}{{ t.resigned ? '·已离职' : '' }}{{ !t.is_active && !t.resigned ? '·已停用' : '' }}</text>
						</label>
					</checkbox-group>
					<view class="head-tip">保存后校区负责人更新为所选账号，未选中的原负责人自动降为教师；可同时选择总校长本人。</view>
				</view>
				<view class="field">
					<text class="label">同时新建负责人账号</text>
					<switch :checked="headForm.createMode" color="#10b981" @change="e => headForm.createMode = e.detail.value" />
				</view>
				<template v-if="headForm.createMode">
					<view class="field">
						<text class="label">负责人姓名 *</text>
						<input class="input" v-model="headForm.name" placeholder="如：王小明" />
					</view>
					<view class="field">
						<text class="label">登录账号 *</text>
						<input class="input" v-model="headForm.username" placeholder="用于负责人登录" />
					</view>
					<view class="field">
						<text class="label">登录密码 *</text>
						<input class="input" v-model="headForm.password" password placeholder="至少 6 位" />
					</view>
					<view class="field">
						<text class="label">联系电话</text>
						<input class="input" v-model="headForm.phone" placeholder="负责人电话（可选）" />
					</view>
				</template>
				<view class="head-tip">负责人离职后：账号停用、校区全部数据保留；重新指定/新建负责人即自动完成数据交接（学生、收支、收费记录全部移交）。</view>
				<button class="btn-primary sheet-btn" :loading="saving" @click="saveHead">保存</button>
			</view>
		</view>

		<!-- 收支登记弹层 -->
		<view v-if="showTxnForm" class="overlay" @click="closeAll">
			<view class="sheet" @click.stop>
				<view class="sheet-title">登记收支</view>
				<view class="field">
					<text class="label">校区 *</text>
					<picker :range="txnCampusLabels" @change="e => txnForm.campus_id = txnCampusOptions[e.detail.value]">
						<view class="input picker-box">{{ txnCampusName }}<text class="arrow">›</text></view>
					</picker>
				</view>
				<view class="field">
					<text class="label">类型 *</text>
					<radio-group class="flex" @change="e => onKindChange(e.detail.value)">
						<label class="radio-item"><radio value="income" :checked="txnForm.kind === 'income'" />收入</label>
						<label class="radio-item"><radio value="expense" :checked="txnForm.kind === 'expense'" />支出</label>
					</radio-group>
				</view>
				<view class="field">
					<text class="label">分类 *</text>
					<picker :range="categoryOptions" @change="e => txnForm.category = categoryOptions[e.detail.value]">
						<view class="input picker-box">{{ txnForm.category || '请选择' }}<text class="arrow">›</text></view>
					</picker>
				</view>
				<view class="field">
					<text class="label">金额 *</text>
					<input class="input" type="digit" v-model="txnForm.amount" placeholder="0.00" />
				</view>
				<view class="field">
					<text class="label">日期 *</text>
					<picker mode="date" :value="txnForm.record_date" @change="e => txnForm.record_date = e.detail.value">
						<view class="input picker-box">{{ txnForm.record_date || '请选择' }}<text class="arrow">›</text></view>
					</picker>
				</view>
				<view class="field">
					<text class="label">备注</text>
					<input class="input" v-model="txnForm.remark" placeholder="备注信息" />
				</view>
				<button class="btn-primary sheet-btn" :loading="saving" @click="saveTxn">保存</button>
			</view>
		</view>
	</view>
</template>

<script>
import { get, post, put, del } from '../../utils/request';

const INCOME_CATS = ['餐费', '杂费', '其他'];
const EXPENSE_CATS = ['房租', '工资', '水电', '其他'];

export default {
	data() {
		return {
			overview: null,
			items: [],
			uncategorized: null,
			canManage: false,
			showCampusForm: false,
			showTxnForm: false,
			showHeadForm: false,
			headCampus: null,
			headCandidates: [],
			headForm: { user_ids: [], createMode: false, name: '', username: '', password: '', phone: '' },
			saving: false,
			campusForm: { id: null, name: '', address: '', phone: '', remark: '', status: true },
			txnForm: { campus_id: null, kind: 'income', category: '', amount: '', record_date: '', remark: '' },
			INCOME_CATS,
			EXPENSE_CATS
		};
	},
	computed: {
		summary() {
			return this.overview && this.overview.summary;
		},
		txnCampusOptions() {
			return this.items.map(c => c.id);
		},
		txnCampusLabels() {
			return this.items.map(c => c.name);
		},
		txnCampusName() {
			const c = this.items.find(x => x.id === this.txnForm.campus_id);
			return c ? c.name : '请选择';
		},
		categoryOptions() {
			return this.txnForm.kind === 'income' ? this.INCOME_CATS : this.EXPENSE_CATS;
		}
	},
	onShow() {
		this.loadAll();
	},
	methods: {
		fmt(n) {
			return Number(n || 0).toLocaleString('zh-CN', { maximumFractionDigits: 2 });
		},
		todayStr() {
			const d = new Date();
			const m = String(d.getMonth() + 1).padStart(2, '0');
			const dd = String(d.getDate()).padStart(2, '0');
			return `${d.getFullYear()}-${m}-${dd}`;
		},
		async loadAll() {
			try {
				this.overview = await get('/campuses');
				this.items = this.overview.items || [];
				this.uncategorized = this.overview.uncategorized || null;
				this.canManage = !!this.overview.canManage;
				if (this.canManage) {
					try {
						this.headCandidates = await get('/campuses/head-candidates');
					} catch (e) {
						this.headCandidates = [];
					}
				}
			} catch (e) {}
		},
		// ---- 设置负责人（总校长；多选含总校长，支持离职办理） ----
		openHead(c) {
			this.headCampus = c;
			this.headForm = { user_ids: (c.heads || []).map(h => h.id), createMode: false, name: '', username: '', password: '', phone: '' };
			this.showHeadForm = true;
		},
		async saveHead() {
			if (this.headForm.createMode) {
				if (!this.headForm.name.trim()) {
					uni.showToast({ title: '请输入负责人姓名', icon: 'none' });
					return;
				}
				if (!this.headForm.username.trim()) {
					uni.showToast({ title: '请输入登录账号', icon: 'none' });
					return;
				}
				if (!this.headForm.password || this.headForm.password.length < 6) {
					uni.showToast({ title: '密码至少 6 位', icon: 'none' });
					return;
				}
			}
			this.saving = true;
			try {
				const payload = { user_ids: this.headForm.user_ids };
				if (this.headForm.createMode) {
					Object.assign(payload, {
						username: this.headForm.username.trim(),
						password: this.headForm.password,
						name: this.headForm.name.trim(),
						phone: this.headForm.phone || null
					});
				}
				await post(`/campuses/${this.headCampus.id}/head`, payload);
				uni.showToast({ title: '负责人已设置', icon: 'success' });
				this.showHeadForm = false;
				this.loadAll();
			} catch (e) {
			} finally {
				this.saving = false;
			}
		},
		resignHead(h) {
			uni.showModal({
				title: '负责人离职',
				content: `确定办理「${h.name}」的离职吗？离职后账号停用，校区全部数据（学生、教师、收支、收费记录）都会保留；之后新建/指定负责人即可自动接管全部数据。`,
				confirmText: '办理离职',
				success: async (res) => {
					if (!res.confirm) return;
					try {
						const r = await post(`/campuses/${this.headCampus.id}/head/resign`, { user_id: h.id });
						uni.showToast({ title: '离职办理完成', icon: 'success' });
						this.showHeadForm = false;
						this.loadAll();
					} catch (e) {}
				}
			});
		},
		// ---- 设置校区 ----
		openCampus(c) {
			this.campusForm = c
				? { id: c.id, name: c.name, address: c.address || '', phone: c.phone || '', remark: c.remark || '', status: c.status }
				: { id: null, name: '', address: '', phone: '', remark: '', status: true };
			this.showCampusForm = true;
		},
		async saveCampus() {
			if (!this.campusForm.name.trim()) {
				uni.showToast({ title: '请输入校区名称', icon: 'none' });
				return;
			}
			this.saving = true;
			try {
				const payload = {
					name: this.campusForm.name.trim(),
					address: this.campusForm.address || null,
					phone: this.campusForm.phone || null,
					remark: this.campusForm.remark || null
				};
				if (this.campusForm.id) {
					payload.status = this.campusForm.status;
					await put(`/campuses/${this.campusForm.id}`, payload);
				} else {
					await post('/campuses', payload);
				}
				uni.showToast({ title: '保存成功', icon: 'success' });
				this.showCampusForm = false;
				this.loadAll();
			} catch (e) {
			} finally {
				this.saving = false;
			}
		},
		delCampus(c) {
			uni.showModal({
				title: '提示',
				content: `确定删除校区「${c.name}」吗？`,
				success: async (res) => {
					if (!res.confirm) return;
					try {
						await del(`/campuses/${c.id}`);
						uni.showToast({ title: '已删除', icon: 'success' });
						this.loadAll();
					} catch (e) {}
				}
			});
		},
		// ---- 收支登记 ----
		openTxn(c) {
			this.txnForm = {
				campus_id: c ? c.id : null,
				kind: 'income',
				category: '',
				amount: '',
				record_date: this.todayStr(),
				remark: ''
			};
			this.showTxnForm = true;
		},
		onKindChange(kind) {
			this.txnForm.kind = kind;
			this.txnForm.category = '';
		},
		async saveTxn() {
			if (this.txnForm.campus_id === null || this.txnForm.campus_id === undefined) {
				uni.showToast({ title: '请选择校区', icon: 'none' });
				return;
			}
			if (!this.txnForm.category) {
				uni.showToast({ title: '请选择分类', icon: 'none' });
				return;
			}
			const amount = Number(this.txnForm.amount);
			if (!amount || amount <= 0) {
				uni.showToast({ title: '请输入有效金额', icon: 'none' });
				return;
			}
			if (!this.txnForm.record_date) {
				uni.showToast({ title: '请选择日期', icon: 'none' });
				return;
			}
			this.saving = true;
			try {
				await post('/campuses/transactions', {
					campus_id: this.txnForm.campus_id,
					kind: this.txnForm.kind,
					category: this.txnForm.category,
					amount: amount,
					record_date: this.txnForm.record_date,
					remark: this.txnForm.remark || null
				});
				uni.showToast({ title: '登记成功', icon: 'success' });
				this.showTxnForm = false;
				this.loadAll();
			} catch (e) {
			} finally {
				this.saving = false;
			}
		},
		goTxn(c) {
			const campusId = c ? c.id : '';
			uni.navigateTo({ url: `/pages/campus/transactions?campus_id=${campusId}` });
		},
		closeAll() {
			this.showCampusForm = false;
			this.showTxnForm = false;
			this.showHeadForm = false;
		}
	}
};
</script>

<style scoped>
.page { padding-bottom: 60rpx; }
.action-bar {
	display: flex;
	gap: 16rpx;
	margin: 20rpx 0;
	padding: 0 20rpx;
}
.action-btn { flex: 1; font-size: 28rpx; }
.btn-ghost {
	background: #fff;
	color: #10b981;
	border: 1rpx solid #10b981;
	border-radius: 12rpx;
}
.campus-card { margin-bottom: 20rpx; }
.campus-card.uncat { border-style: dashed; background: #fafafa; }
.campus-head {
	display: flex;
	justify-content: space-between;
	align-items: center;
	gap: 10rpx;
	margin-bottom: 12rpx;
}
.head-tags {
	display: flex;
	flex-wrap: wrap;
	gap: 8rpx;
	justify-content: flex-end;
	max-width: 55%;
}
.head-list { display: flex; flex-direction: column; gap: 10rpx; width: 100%; }
.head-item {
	display: flex;
	align-items: center;
	justify-content: space-between;
	background: #f5f7fa;
	border-radius: 12rpx;
	padding: 14rpx 20rpx;
}
.head-item-name { font-size: 26rpx; color: #303133; }
.head-check-group { display: flex; flex-direction: column; gap: 8rpx; }
.check-item { display: flex; align-items: center; gap: 10rpx; padding: 8rpx 0; }
.check-label { font-size: 26rpx; color: #303133; }
.check-label.muted { color: #c0c4cc; }
.campus-title { display: flex; align-items: center; gap: 10rpx; min-width: 0; }
.campus-name { font-size: 32rpx; font-weight: 700; color: #303133; }
.campus-meta {
	display: flex;
	flex-wrap: wrap;
	gap: 16rpx;
	font-size: 24rpx;
	color: #909399;
	margin-bottom: 14rpx;
}
.campus-stats { display: flex; gap: 10rpx; margin-bottom: 14rpx; }
.cs-item {
	flex: 1;
	background: #f5f7fa;
	border-radius: 12rpx;
	padding: 14rpx 10rpx;
	text-align: center;
}
.cs-label { display: block; font-size: 22rpx; color: #909399; margin-bottom: 6rpx; }
.cs-value { font-size: 28rpx; font-weight: 700; color: #303133; }
.cs-value.income { color: #10b981; }
.cs-value.expense { color: #ef4444; }
.campus-info {
	display: flex;
	flex-wrap: wrap;
	gap: 20rpx;
	font-size: 24rpx;
	color: #6b7280;
	margin-bottom: 14rpx;
}
.campus-info .num { color: #303133; font-weight: 600; }
.campus-info .unpaid { color: #ef4444; font-weight: 600; }
.campus-actions {
	display: flex;
	gap: 24rpx;
	border-top: 1rpx dashed #e5e7eb;
	padding-top: 14rpx;
}
.link { font-size: 26rpx; color: #6b7280; }
.link.primary { color: #10b981; font-weight: 500; }
.link.danger { color: #ef4444; }
.empty { text-align: center; color: #c0c4cc; padding: 60rpx 0; font-size: 26rpx; }

/* 弹层 */
.overlay {
	position: fixed;
	top: 0;
	left: 0;
	right: 0;
	bottom: 0;
	background: rgba(0, 0, 0, 0.45);
	z-index: 100;
	display: flex;
	align-items: flex-end;
}
.sheet {
	width: 100%;
	background: #fff;
	border-radius: 24rpx 24rpx 0 0;
	padding: 30rpx 30rpx 40rpx;
	max-height: 82vh;
	overflow-y: auto;
}
.sheet-title { font-size: 32rpx; font-weight: 700; margin-bottom: 24rpx; }
.field { margin-bottom: 24rpx; }
.label { display: block; font-size: 26rpx; color: #303133; font-weight: 500; margin-bottom: 10rpx; }
.input {
	background: #f5f7fa;
	border-radius: 12rpx;
	padding: 18rpx 24rpx;
	font-size: 28rpx;
}
.picker-box { display: flex; align-items: center; justify-content: space-between; }
.picker-box .arrow { color: #c0c4cc; font-size: 32rpx; line-height: 1; }
.radio-item { margin-right: 30rpx; font-size: 28rpx; }
.sheet-btn { margin-top: 10rpx; }
.head-tip {
	font-size: 22rpx;
	color: #909399;
	background: #f5f7fa;
	border-radius: 12rpx;
	padding: 14rpx 20rpx;
	margin-bottom: 20rpx;
	line-height: 1.5;
}
</style>
