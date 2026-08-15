<template>
	<view class="page">
		<!-- 统计概览（与 PC 端机构开户管理一致） -->
		<view class="stat-grid">
			<view class="stat-card is-blue">
				<view class="stat-top"><text class="stat-label">机构总数</text><text class="stat-emoji">🏢</text></view>
				<text class="stat-num">{{ organizations.length }}</text>
				<text class="stat-sub">已开户机构</text>
			</view>
			<view class="stat-card is-green">
				<view class="stat-top"><text class="stat-label">累计交费(元)</text><text class="stat-emoji">💰</text></view>
				<text class="stat-num">¥{{ fmt(totalPaid) }}</text>
				<text class="stat-sub">全部机构累计</text>
			</view>
			<view class="stat-card is-orange">
				<view class="stat-top"><text class="stat-label">即将到期</text><text class="stat-emoji">⏰</text></view>
				<text class="stat-num">{{ expiringCount }}</text>
				<text class="stat-sub">剩 7 天内到期</text>
			</view>
			<view class="stat-card is-red">
				<view class="stat-top"><text class="stat-label">已到期</text><text class="stat-emoji">⚠️</text></view>
				<text class="stat-num">{{ expiredCount }}</text>
				<text class="stat-sub">待续费机构</text>
			</view>
		</view>

		<!-- 操作 -->
		<view class="action-bar">
			<button class="btn-primary action-btn" @click="openCreate">＋ 新校长开户</button>
		</view>

		<!-- 机构列表 -->
		<view class="card org-card" v-for="o in organizations" :key="o.id">
			<view class="org-head">
				<view class="org-title">
					<text class="org-name">{{ o.name }}</text>
					<text class="org-code">{{ o.code }}</text>
				</view>
				<text :class="'tag ' + statusTagType(o.expire_status)">{{ statusText(o) }}</text>
			</view>
			<view class="org-meta">
				<text v-if="o.principal">👤 校长：{{ o.principal.name }}（{{ o.principal.username }}）</text>
				<text v-else class="text-muted">👤 校长：未分配</text>
				<text>🧾 计费：{{ o.plan_type_text || '-' }}</text>
				<text>📅 {{ o.payment_period || '未设时间段' }}</text>
			</view>
			<view class="org-stats">
				<view class="os-item">
					<text class="os-label">交费金额</text>
					<text class="os-value warn">¥{{ fmt(o.fee_amount) }}</text>
				</view>
				<view class="os-item">
					<text class="os-label">累计交费</text>
					<text class="os-value income">¥{{ fmt(o.total_paid) }}</text>
				</view>
				<view class="os-item">
					<text class="os-label">状态</text>
					<text :class="o.status ? 'tag tag-success' : 'tag tag-grey'">{{ o.status ? '启用' : '停用' }}</text>
				</view>
			</view>
			<view class="org-info">
				<text>到期日 <text class="num">{{ o.expire_date || '-' }}</text></text>
				<text>开户 <text class="num">{{ o.created_at ? o.created_at.slice(0, 10) : '-' }}</text></text>
			</view>
			<!-- 机构运营情况（资金/教师/学生） -->
			<view class="org-oper">
				<view class="op-title">运营情况</view>
				<view class="op-row">
					<view class="op-item">
						<text class="op-label">本月收入</text>
						<text class="op-value income">¥{{ fmt(ov(o).month_income) }}</text>
					</view>
					<view class="op-item">
						<text class="op-label">本月支出</text>
						<text class="op-value expense">¥{{ fmt(ov(o).month_expense) }}</text>
					</view>
					<view class="op-item">
						<text class="op-label">待缴</text>
						<text class="op-value unpaid">¥{{ fmt(ov(o).unpaid) }}</text>
					</view>
				</view>
				<view class="op-row">
					<view class="op-item">
						<text class="op-label">学生</text>
						<text class="op-value">{{ ov(o).student_count || 0 }}<text class="op-sub">（在读 {{ ov(o).active_student_count || 0 }}）</text></text>
					</view>
					<view class="op-item">
						<text class="op-label">教师</text>
						<text class="op-value">{{ ov(o).teacher_count || 0 }}</text>
					</view>
					<view class="op-item">
						<text class="op-label">今日打卡</text>
						<text class="op-value">{{ ov(o).today_attendance || 0 }}</text>
					</view>
				</view>
			</view>
			<view class="org-actions">
				<text class="link" @click="openEdit(o)">编辑</text>
				<text class="link success" @click="openRenew(o)">交费/续费</text>
				<text class="link" @click="openPayments(o)">流水</text>
				<text class="link warn" @click="openResetPwd(o)">重置密码</text>
				<text class="link danger" @click="toggleStatus(o)">{{ o.status ? '停用' : '启用' }}</text>
			</view>
		</view>
		<view v-if="!organizations.length" class="empty">暂无机构，点击上方「新校长开户」创建</view>

		<!-- 开户流水统计 -->
		<view class="card">
			<view class="card-title"><text class="bar"></text>开户流水统计</view>
			<view class="stat-grid no-margin">
				<view class="stat-card is-green">
					<view class="stat-top"><text class="stat-label">总交费金额</text><text class="stat-emoji">💵</text></view>
					<text class="stat-num">¥{{ fmt(stat.total_amount) }}</text>
				</view>
				<view class="stat-card is-blue">
					<view class="stat-top"><text class="stat-label">开户机构数</text><text class="stat-emoji">🏢</text></view>
					<text class="stat-num">{{ stat.org_count || 0 }}</text>
				</view>
				<view class="stat-card is-red">
					<view class="stat-top"><text class="stat-label">待收款/已到期</text><text class="stat-emoji">⏳</text></view>
					<text class="stat-num">{{ (stat.due_list || []).length }}</text>
				</view>
			</view>

			<view v-if="stat.by_org && stat.by_org.length" class="due-block">
				<view class="section-title"><text class="bar"></text>按机构汇总</view>
				<view v-for="(o, i) in stat.by_org" :key="i" class="info-row">
					<view class="ir-left">
						<view class="ir-title">{{ o.name }}</view>
						<view class="ir-sub">{{ o.payment_period || '未设时间段' }} · 到期 {{ o.expire_date || '-' }}</view>
					</view>
					<view class="ir-right">
						<text class="amount income">¥{{ fmt(o.total_paid) }}</text>
						<text :class="'tag ' + orgStatusTag(o.expire_status)">{{ orgStatusText(o.expire_status) }}</text>
					</view>
				</view>
			</view>

			<view v-if="stat.due_list && stat.due_list.length" class="due-block">
				<view class="section-title"><text class="bar"></text>待收款 / 已到期机构</view>
				<view v-for="d in stat.due_list" :key="d.org_id" class="info-row">
					<view class="ir-left">
						<view class="ir-title">{{ d.name }}</view>
						<view class="ir-sub">{{ d.payment_period || '未设时间段' }} · 到期 {{ d.expire_date || '-' }}</view>
					</view>
					<view class="ir-right">
						<text :class="d.days_left < 0 ? 'tag tag-danger' : 'tag tag-warn'">
							{{ d.days_left < 0 ? '已到期 ' + (-d.days_left) + '天' : '剩 ' + d.days_left + ' 天' }}
						</text>
						<text class="link success" @click="openRenewById(d.org_id)">去续费</text>
					</view>
				</view>
			</view>
			<view v-else class="empty">暂无待收款 / 已到期机构</view>
		</view>

		<!-- 新校长开户弹层 -->
		<view v-if="showCreate" class="overlay" @click="showCreate = false">
			<view class="sheet" @click.stop>
				<view class="sheet-title">新校长开户</view>
				<view class="field">
					<text class="label">机构名称 *</text>
					<input class="input" v-model="createForm.org_name" placeholder="如：阳光教育培训学校" />
				</view>
				<view class="field">
					<text class="label">校长姓名 *</text>
					<input class="input" v-model="createForm.contact" placeholder="校长姓名" />
				</view>
				<view class="field">
					<text class="label">登录账号 *</text>
					<input class="input" v-model="createForm.username" placeholder="校长登录账号（唯一）" />
				</view>
				<view class="field">
					<text class="label">登录密码 *</text>
					<input class="input" v-model="createForm.password" password placeholder="至少 6 位" />
				</view>
				<view class="field">
					<text class="label">联系电话</text>
					<input class="input" v-model="createForm.phone" placeholder="选填" />
				</view>
				<view class="divider"></view>
				<view class="sheet-sub">开户交费</view>
				<view class="field">
					<text class="label">计费方式</text>
					<picker :range="planTypeLabels" @change="e => createForm.plan_type = planTypeValues[e.detail.value]">
						<view class="input picker-box">{{ planTypeText(createForm.plan_type) }}<text class="arrow">›</text></view>
					</picker>
				</view>
				<view class="field">
					<text class="label">交费金额(元)</text>
					<input class="input" type="digit" v-model="createForm.fee_amount" placeholder="选填" />
				</view>
				<view class="field">
					<text class="label">交费时间段</text>
					<picker :range="periodLabels" @change="e => createForm.payment_period = periodValues[e.detail.value]">
						<view class="input picker-box">{{ createForm.payment_period || '请选择（自动推算到期日）' }}<text class="arrow">›</text></view>
					</picker>
					<view v-if="createForm.payment_period" class="hint">到期日期：{{ calcExpire(createForm.payment_period) }}</view>
				</view>
				<view class="head-tip">开户后，该校长登录系统数据为空白，需自行录入学生、学科等信息。</view>
				<button class="btn-primary sheet-btn" :loading="saving" @click="handleCreate">确认开户</button>
			</view>
		</view>

		<!-- 编辑机构弹层 -->
		<view v-if="showEdit" class="overlay" @click="showEdit = false">
			<view class="sheet" @click.stop>
				<view class="sheet-title">编辑机构</view>
				<view class="field">
					<text class="label">机构名称</text>
					<input class="input" v-model="editForm.name" />
				</view>
				<view class="field">
					<text class="label">联系人</text>
					<input class="input" v-model="editForm.contact" />
				</view>
				<view class="field">
					<text class="label">电话</text>
					<input class="input" v-model="editForm.phone" />
				</view>
				<view class="field" v-if="editTarget && editTarget.status !== undefined">
					<text class="label">状态</text>
					<switch :checked="editForm.status" color="#10b981" @change="e => editForm.status = e.detail.value" />
				</view>
				<button class="btn-primary sheet-btn" :loading="saving" @click="handleEditSave">保存</button>
			</view>
		</view>

		<!-- 交费/续费弹层 -->
		<view v-if="showRenew" class="overlay" @click="showRenew = false">
			<view class="sheet" @click.stop>
				<view class="sheet-title">机构交费 / 续费</view>
				<view class="kv-row">
					<text class="kv-label">机构</text>
					<text class="kv-value">{{ renewTarget && renewTarget.name }}</text>
				</view>
				<view class="field">
					<text class="label">计费方式</text>
					<picker :range="planTypeLabels" @change="e => renewForm.plan_type = planTypeValues[e.detail.value]">
						<view class="input picker-box">{{ planTypeText(renewForm.plan_type) }}<text class="arrow">›</text></view>
					</picker>
				</view>
				<view class="field">
					<text class="label">交费金额(元)</text>
					<input class="input" type="digit" v-model="renewForm.amount" placeholder="0.00" />
				</view>
				<view class="field">
					<text class="label">交费时间段</text>
					<picker :range="periodLabels" @change="e => renewForm.payment_period = periodValues[e.detail.value]">
						<view class="input picker-box">{{ renewForm.payment_period || '请选择（自动顺延到期日）' }}<text class="arrow">›</text></view>
					</picker>
					<view v-if="renewForm.payment_period" class="hint">续费后到期日期：{{ calcExpire(renewForm.payment_period, renewTarget && renewTarget.expire_date) }}</view>
				</view>
				<view class="field">
					<text class="label">备注</text>
					<input class="input" v-model="renewForm.remark" placeholder="选填" />
				</view>
				<button class="btn-primary sheet-btn" :loading="saving" @click="handleRenew">确认交费</button>
			</view>
		</view>

		<!-- 流水明细弹层 -->
		<view v-if="showPayments" class="overlay" @click="showPayments = false">
			<view class="sheet" @click.stop>
				<view class="sheet-title">开户流水明细</view>
				<view class="kv-row">
					<text class="kv-label">机构</text>
					<text class="kv-value">{{ paymentsTarget && paymentsTarget.name }}</text>
				</view>
				<view v-if="paymentRows.length" class="pay-list">
					<view v-for="(p, i) in paymentRows" :key="i" class="pay-item">
						<view class="pay-head">
							<text class="pay-amount">¥{{ fmt(p.amount) }}</text>
							<text class="tag tag-plain">{{ p.plan_type_text || '-' }}</text>
						</view>
						<view class="pay-meta">
							<text>{{ p.created_at || '-' }}</text>
							<text>到期 {{ p.expire_date || '-' }}</text>
						</view>
						<view v-if="p.remark" class="pay-remark">备注：{{ p.remark }}</view>
					</view>
				</view>
				<view v-else class="empty">暂无交费流水</view>
				<button class="btn-ghost sheet-btn" @click="showPayments = false">关闭</button>
			</view>
		</view>

		<!-- 重置校长密码弹层 -->
		<view v-if="showPwd" class="overlay" @click="showPwd = false">
			<view class="sheet" @click.stop>
				<view class="sheet-title">重置校长密码</view>
				<view class="kv-row">
					<text class="kv-label">机构</text>
					<text class="kv-value">{{ pwdTarget && pwdTarget.name }}</text>
				</view>
				<view class="field">
					<text class="label">新密码</text>
					<input class="input" v-model="pwdForm.password" password placeholder="至少 6 位" />
				</view>
				<button class="btn-primary sheet-btn" :loading="saving" @click="handleResetPwd">确认重置</button>
			</view>
		</view>

		<button class="logout-btn" @click="doLogout">退出登录</button>
	</view>
</template>

<script>
import { useUserStore } from '../../stores/user';
import { get, post, put } from '../../utils/request';

const PLAN_TYPES = [
	{ label: '按年', value: 'annual' },
	{ label: '按次/阶段', value: 'stage' },
	{ label: '自定义', value: 'custom' }
];
const PERIODS = ['半年', '一年'];
const PERIOD_DAYS = { '半年': 180, '一年': 365 };

export default {
	data() {
		return {
			store: useUserStore(),
			organizations: [],
			stat: {},
			saving: false,
			showCreate: false,
			showEdit: false,
			showRenew: false,
			showPayments: false,
			showPwd: false,
			editTarget: null,
			renewTarget: null,
			paymentsTarget: null,
			pwdTarget: null,
			paymentRows: [],
			createForm: { org_name: '', contact: '', username: '', password: '', phone: '', plan_type: '', fee_amount: '', payment_period: '' },
			editForm: { name: '', contact: '', phone: '', status: true },
			renewForm: { plan_type: 'annual', amount: '', payment_period: '', remark: '' },
			pwdForm: { password: '' }
		};
	},
	computed: {
		planTypeLabels() { return PLAN_TYPES.map(t => t.label); },
		planTypeValues() { return PLAN_TYPES.map(t => t.value); },
		periodLabels() { return PERIODS; },
		periodValues() { return PERIODS; },
		totalPaid() {
			return this.organizations.reduce((s, o) => s + (o.total_paid || 0), 0);
		},
		expiringCount() {
			return this.organizations.filter(o => o.expire_status === 'expiring').length;
		},
		expiredCount() {
			return this.organizations.filter(o => o.expire_status === 'expired').length;
		}
	},
	onShow() {
		this.loadData();
	},
	onPullDownRefresh() {
		this.loadData().then(() => uni.stopPullDownRefresh());
	},
	methods: {
		fmt(n) {
			return Number(n || 0).toLocaleString('zh-CN', { maximumFractionDigits: 2 });
		},
		planTypeText(v) {
			const t = PLAN_TYPES.find(x => x.value === v);
			return t ? t.label : '请选择';
		},
		calcExpire(period, base) {
			const days = PERIOD_DAYS[period];
			if (!days) return '';
			const d = base ? new Date(base) : new Date();
			d.setDate(d.getDate() + days);
			const m = String(d.getMonth() + 1).padStart(2, '0');
			const dd = String(d.getDate()).padStart(2, '0');
			return `${d.getFullYear()}-${m}-${dd}`;
		},
		statusTagType(st) {
			if (st === 'expired') return 'tag-danger';
			if (st === 'expiring') return 'tag-warn';
			if (st === 'normal') return 'tag-success';
			return 'tag-grey';
		},
		statusText(o) {
			if (o.expire_status === 'expired') return '已到期';
			if (o.expire_status === 'expiring') return `剩${o.days_left}天`;
			if (o.expire_status === 'normal') return '正常';
			return '未设置';
		},
		orgStatusTag(st) {
			if (st === 'expired') return 'tag-danger';
			if (st === 'expiring') return 'tag-warn';
			if (st === 'normal') return 'tag-success';
			return 'tag-grey';
		},
		orgStatusText(st) {
			if (st === 'expired') return '已到期';
			if (st === 'expiring') return '即将到期';
			if (st === 'normal') return '正常';
			return '未设置';
		},
		ov(o) {
			// 机构运营概况（兼容旧后端无 overview 字段）
			return (o && o.overview) || {};
		},
		async loadData() {
			try {
				this.organizations = await get('/platform/organizations');
				this.stat = await get('/platform/payments/statistics');
			} catch (e) {}
		},
		// ---- 新校长开户 ----
		openCreate() {
			this.createForm = { org_name: '', contact: '', username: '', password: '', phone: '', plan_type: '', fee_amount: '', payment_period: '' };
			this.showCreate = true;
		},
		async handleCreate() {
			if (!this.createForm.org_name.trim()) {
				uni.showToast({ title: '请输入机构名称', icon: 'none' });
				return;
			}
			if (!this.createForm.contact.trim()) {
				uni.showToast({ title: '请输入校长姓名', icon: 'none' });
				return;
			}
			if (!this.createForm.username.trim()) {
				uni.showToast({ title: '请输入登录账号', icon: 'none' });
				return;
			}
			if (!this.createForm.password || this.createForm.password.length < 6) {
				uni.showToast({ title: '密码至少 6 位', icon: 'none' });
				return;
			}
			this.saving = true;
			try {
				const payload = Object.assign({}, this.createForm, {
					fee_amount: this.createForm.fee_amount === '' || this.createForm.fee_amount === null ? null : Number(this.createForm.fee_amount)
				});
				await post('/platform/organizations', payload);
				uni.showToast({ title: '开户成功，新校长账号已创建', icon: 'success', duration: 2500 });
				this.showCreate = false;
				this.loadData();
			} catch (e) {
			} finally {
				this.saving = false;
			}
		},
		// ---- 编辑机构 ----
		openEdit(o) {
			this.editTarget = o;
			this.editForm = { name: o.name, contact: o.contact || '', phone: o.phone || '', status: o.status };
			this.showEdit = true;
		},
		async handleEditSave() {
			this.saving = true;
			try {
				await put(`/platform/organizations/${this.editTarget.id}`, {
					name: this.editForm.name,
					contact: this.editForm.contact,
					phone: this.editForm.phone,
					status: this.editForm.status
				});
				uni.showToast({ title: '机构信息已更新', icon: 'success' });
				this.showEdit = false;
				this.loadData();
			} catch (e) {
			} finally {
				this.saving = false;
			}
		},
		// ---- 启停用 ----
		toggleStatus(o) {
			const action = o.status ? '停用' : '启用';
			uni.showModal({
				title: '提示',
				content: `确定${action}机构「${o.name}」吗？`,
				success: async (res) => {
					if (!res.confirm) return;
					try {
						await put(`/platform/organizations/${o.id}`, { status: !o.status });
						uni.showToast({ title: `已${action}`, icon: 'success' });
						this.loadData();
					} catch (e) {}
				}
			});
		},
		// ---- 交费/续费 ----
		openRenew(o) {
			this.renewTarget = o;
			this.renewForm = { plan_type: o.plan_type || 'annual', amount: '', payment_period: o.payment_period || '', remark: '' };
			this.showRenew = true;
		},
		openRenewById(orgId) {
			const o = this.organizations.find(x => x.id === orgId);
			if (o) this.openRenew(o);
		},
		async handleRenew() {
			const amount = Number(this.renewForm.amount);
			if ((!amount || amount <= 0) && !this.renewForm.payment_period) {
				uni.showToast({ title: '请填写交费金额或选择交费时间段', icon: 'none' });
				return;
			}
			this.saving = true;
			try {
				await post(`/platform/organizations/${this.renewTarget.id}/payments`, {
					plan_type: this.renewForm.plan_type,
					amount: amount > 0 ? amount : null,
					payment_period: this.renewForm.payment_period || null,
					remark: this.renewForm.remark || null
				});
				uni.showToast({ title: '交费成功，流水已记录', icon: 'success' });
				this.showRenew = false;
				this.loadData();
			} catch (e) {
			} finally {
				this.saving = false;
			}
		},
		// ---- 流水明细 ----
		async openPayments(o) {
			this.paymentsTarget = o;
			this.paymentRows = [];
			this.showPayments = true;
			try {
				this.paymentRows = await get(`/platform/organizations/${o.id}/payments`);
			} catch (e) {}
		},
		// ---- 重置密码 ----
		openResetPwd(o) {
			this.pwdTarget = o;
			this.pwdForm.password = '';
			this.showPwd = true;
		},
		async handleResetPwd() {
			if (!this.pwdForm.password || this.pwdForm.password.length < 6) {
				uni.showToast({ title: '请输入至少 6 位的新密码', icon: 'none' });
				return;
			}
			const principal = this.pwdTarget && this.pwdTarget.principal;
			if (!principal) {
				uni.showToast({ title: '该机构暂无校长账号可重置', icon: 'none' });
				return;
			}
			this.saving = true;
			try {
				await put(`/platform/principals/${principal.id}/reset-password`, { password: this.pwdForm.password });
				uni.showToast({ title: '校长密码已重置', icon: 'success' });
				this.showPwd = false;
			} catch (e) {
			} finally {
				this.saving = false;
			}
		},
		doLogout() {
			uni.showModal({
				title: '提示',
				content: '确定退出登录吗？',
				success: (res) => { if (res.confirm) this.store.logout(); }
			});
		}
	}
};
</script>

<style scoped>
.page { padding-bottom: 60rpx; }
.action-bar {
	display: flex;
	gap: 16rpx;
	margin: 20rpx 0 0;
	padding: 0 20rpx;
}
.action-btn { flex: 1; font-size: 28rpx; }
.org-card { margin: 20rpx; }
.org-head {
	display: flex;
	justify-content: space-between;
	align-items: center;
	gap: 10rpx;
	margin-bottom: 12rpx;
}
.org-title { display: flex; align-items: center; gap: 10rpx; min-width: 0; }
.org-name { font-size: 32rpx; font-weight: 700; color: #303133; }
.org-code {
	font-size: 20rpx;
	color: #909399;
	background: #f5f7fa;
	border-radius: 8rpx;
	padding: 2rpx 10rpx;
}
.org-meta {
	display: flex;
	flex-wrap: wrap;
	gap: 12rpx;
	font-size: 24rpx;
	color: #6b7280;
	margin-bottom: 14rpx;
}
.org-stats { display: flex; gap: 10rpx; margin-bottom: 14rpx; }
.os-item {
	flex: 1;
	background: #f5f7fa;
	border-radius: 12rpx;
	padding: 14rpx 10rpx;
	text-align: center;
}
.os-label { display: block; font-size: 22rpx; color: #909399; margin-bottom: 6rpx; }
.os-value { font-size: 26rpx; font-weight: 700; color: #303133; }
.os-value.warn { color: #e6a23c; }
.os-value.income { color: #10b981; }
.org-info {
	display: flex;
	flex-wrap: wrap;
	gap: 20rpx;
	font-size: 24rpx;
	color: #6b7280;
	margin-bottom: 14rpx;
}
.org-info .num { color: #303133; font-weight: 600; }
.org-oper {
	background: #f5f7fa;
	border-radius: 12rpx;
	padding: 16rpx 18rpx;
	margin-bottom: 14rpx;
}
.op-title { font-size: 22rpx; color: #909399; margin-bottom: 10rpx; }
.op-row { display: flex; gap: 10rpx; margin-bottom: 10rpx; }
.op-row:last-child { margin-bottom: 0; }
.op-item { flex: 1; }
.op-label { display: block; font-size: 20rpx; color: #909399; margin-bottom: 4rpx; }
.op-value { font-size: 26rpx; font-weight: 700; color: #303133; }
.op-value.income { color: #10b981; }
.op-value.expense { color: #e6a23c; }
.op-value.unpaid { color: #ef4444; }
.op-sub { font-size: 20rpx; color: #909399; font-weight: 400; }
.org-actions {
	display: flex;
	flex-wrap: wrap;
	gap: 24rpx;
	border-top: 1rpx dashed #e5e7eb;
	padding-top: 14rpx;
}
.link { font-size: 26rpx; color: #6b7280; }
.link.success { color: #10b981; }
.link.warn { color: #e6a23c; }
.link.danger { color: #ef4444; }
.empty { text-align: center; color: #c0c4cc; padding: 40rpx 0; font-size: 26rpx; }
.no-margin { margin: 0; }
.due-block { margin-top: 8rpx; }

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
.sheet-sub {
	font-size: 26rpx;
	font-weight: 600;
	color: #909399;
	margin-bottom: 20rpx;
}
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
.hint { font-size: 22rpx; color: #c0c4cc; margin-top: 8rpx; }
.sheet-btn { margin-top: 10rpx; }
.btn-ghost {
	background: #f5f7fa;
	color: #606266;
	border-radius: 12rpx;
	margin-top: 10rpx;
}
.head-tip {
	font-size: 22rpx;
	color: #909399;
	background: #f5f7fa;
	border-radius: 12rpx;
	padding: 14rpx 20rpx;
	margin-bottom: 20rpx;
	line-height: 1.5;
}
/* 流水明细 */
.pay-item {
	padding: 20rpx 0;
	border-bottom: 1rpx solid #f5f5f5;
}
.pay-item:last-child { border-bottom: none; }
.pay-head { display: flex; align-items: center; gap: 12rpx; margin-bottom: 6rpx; }
.pay-amount { font-size: 30rpx; font-weight: 700; color: #10b981; }
.pay-meta {
	display: flex;
	flex-wrap: wrap;
	gap: 16rpx;
	font-size: 22rpx;
	color: #909399;
}
.pay-remark { font-size: 22rpx; color: #6b7280; margin-top: 6rpx; }
.logout-btn {
	margin: 40rpx 20rpx;
	background: #fff;
	color: #f56c6c;
	border: 1rpx solid #f56c6c;
	border-radius: 12rpx;
	font-size: 28rpx;
}
</style>
