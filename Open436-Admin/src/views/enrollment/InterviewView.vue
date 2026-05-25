<template>
  <div class="interview-view">
    <div class="page-header"><h2>面试管理</h2></div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" style="margin-bottom:20px">
      <el-col :span="6">
        <StatCard label="待面试总人数" :value="stats.total" icon="User" icon-bg="#e3f2fd" icon-color="#1976D2" />
      </el-col>
      <el-col :span="6">
        <StatCard label="待面试" :value="stats.pending" icon="Clock" icon-bg="#fff3e0" icon-color="#ff9800" />
      </el-col>
      <el-col :span="6">
        <StatCard label="已通过" :value="stats.passed" icon="CircleCheck" icon-bg="#e8f5e9" icon-color="#4caf50" />
      </el-col>
      <el-col :span="6">
        <StatCard label="通过率" :value="stats.passRate + '%'" icon="TrendCharts" icon-bg="#f3e5f5" icon-color="#9c27b0" />
      </el-col>
    </el-row>

    <!-- 筛选与操作 -->
    <div class="toolbar">
      <el-input v-model="keyword" placeholder="搜索姓名/学号/专业" clearable style="width:240px" prefix-icon="Search" @input="loadList" />
      <el-radio-group v-model="statusFilter" @change="loadList">
        <el-radio-button value="">全部</el-radio-button>
        <el-radio-button value="pending">待面试</el-radio-button>
        <el-radio-button value="passed">已通过</el-radio-button>
        <el-radio-button value="failed">未通过</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 数据表格 -->
    <el-table :data="list" stripe v-loading="loading">
      <el-table-column prop="enrollmentId" label="报名ID" width="80" />
      <el-table-column prop="realName" label="姓名" width="90" />
      <el-table-column prop="username" label="用户名" width="120" />
      <el-table-column prop="studentId" label="学号" width="130" />
      <el-table-column prop="major" label="专业" width="140" />
      <el-table-column label="面试轮次" width="90" align="center">
        <template #default="{ row }">
          <span v-if="row.round">{{ row.round }}</span>
          <span v-else style="color:#c0c4cc">-</span>
        </template>
      </el-table-column>
      <el-table-column label="面试官" width="90">
        <template #default="{ row }">
          <span v-if="row.interviewer">{{ row.interviewer }}</span>
          <span v-else style="color:#c0c4cc">-</span>
        </template>
      </el-table-column>
      <el-table-column label="评分" width="80" align="center">
        <template #default="{ row }">
          <el-tag v-if="row.score" :type="scoreTagType(row.score)" size="small">{{ row.score }}</el-tag>
          <span v-else style="color:#c0c4cc">-</span>
        </template>
      </el-table-column>
      <el-table-column label="面试状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="statusTagType[row.status]" size="small">{{ statusLabels[row.status] }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link size="small" @click="openDetail(row)">查看详情</el-button>
          <el-button type="warning" link size="small" @click="openRecordDialog(row)">面试记录</el-button>
          <template v-if="row.status === 'pending' || row.status === 'interviewed'">
            <el-button type="success" link size="small" @click="handleStatusUpdate(row, 'passed')">通过</el-button>
            <el-button type="danger" link size="small" @click="handleStatusUpdate(row, 'failed')">未通过</el-button>
          </template>
        </template>
      </el-table-column>
    </el-table>

    <div style="display:flex;justify-content:flex-end;margin-top:16px">
      <el-pagination v-model:current-page="page" :page-size="10" :total="total" layout="total, prev, pager, next" @current-change="loadList" />
    </div>

    <!-- 详情抽屉 -->
    <el-drawer v-model="drawerVisible" :title="`面试详情 - ${currentItem?.realName || ''}`" size="560px">
      <template v-if="currentItem">
        <!-- 基本信息 -->
        <h4 style="margin-bottom:12px">基本信息</h4>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="姓名">{{ currentItem.realName }}</el-descriptions-item>
          <el-descriptions-item label="用户名">{{ currentItem.username }}</el-descriptions-item>
          <el-descriptions-item label="学号">{{ currentItem.studentId }}</el-descriptions-item>
          <el-descriptions-item label="专业">{{ currentItem.major }}</el-descriptions-item>
          <el-descriptions-item label="联系方式">{{ currentItem.phone }}</el-descriptions-item>
          <el-descriptions-item label="面试状态">
            <el-tag :type="statusTagType[currentItem.status]" size="small">{{ statusLabels[currentItem.status] }}</el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <div style="margin-top:16px">
          <h4 style="margin-bottom:8px">自我介绍</h4>
          <p style="color:#666;line-height:1.6">{{ currentItem.selfIntro || '暂无' }}</p>
        </div>
        <div style="margin-top:12px">
          <h4 style="margin-bottom:8px">技能标签</h4>
          <div>
            <el-tag v-for="skill in currentItem.skills?.split(',')" :key="skill" style="margin:2px 4px">{{ skill.trim() }}</el-tag>
            <span v-if="!currentItem.skills" style="color:#c0c4cc">暂无</span>
          </div>
        </div>

        <!-- 面试记录时间线 -->
        <div style="margin-top:20px">
          <h4 style="margin-bottom:12px">面试记录</h4>
          <el-empty v-if="!currentItem.rounds?.length" description="暂无面试记录" :image-size="60" />
          <el-timeline v-else>
            <el-timeline-item
              v-for="r in currentItem.rounds"
              :key="r.id"
              :timestamp="r.interviewDate"
              placement="top"
              :type="roundTimelineType(r.status)">
              <el-card shadow="never" style="padding:4px">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
                  <span><b>第{{ r.round }}轮</b></span>
                  <el-tag :type="statusTagType[r.status]" size="small">{{ statusLabels[r.status] }}</el-tag>
                </div>
                <el-descriptions :column="2" size="small" border>
                  <el-descriptions-item label="面试官">{{ r.interviewer || '-' }}</el-descriptions-item>
                  <el-descriptions-item label="评分">
                    <el-tag v-if="r.score" :type="scoreTagType(r.score)" size="small">{{ r.score }}/10</el-tag>
                    <span v-else>-</span>
                  </el-descriptions-item>
                  <el-descriptions-item label="推荐方向" :span="2">{{ r.direction || '-' }}</el-descriptions-item>
                </el-descriptions>
                <div v-if="r.summary" style="margin-top:8px">
                  <span style="color:#909399;font-size:13px">总结：</span>
                  <span style="font-size:13px">{{ r.summary }}</span>
                </div>
                <div v-if="r.strengths" style="margin-top:4px">
                  <span style="color:#67c23a;font-size:13px">优点：</span>
                  <span style="font-size:13px">{{ r.strengths }}</span>
                </div>
                <div v-if="r.weaknesses" style="margin-top:4px">
                  <span style="color:#f56c6c;font-size:13px">不足：</span>
                  <span style="font-size:13px">{{ r.weaknesses }}</span>
                </div>
              </el-card>
            </el-timeline-item>
          </el-timeline>
        </div>

        <!-- 操作按钮 -->
        <div v-if="currentItem.status === 'pending' || currentItem.status === 'interviewed'" style="margin-top:24px;display:flex;gap:12px">
          <el-button type="warning" @click="drawerVisible = false; openRecordDialog(currentItem)">新增面试记录</el-button>
          <el-button type="success" @click="handleStatusUpdate(currentItem, 'passed'); drawerVisible = false">面试通过</el-button>
          <el-button type="danger" @click="handleStatusUpdate(currentItem, 'failed'); drawerVisible = false">面试未通过</el-button>
        </div>
      </template>
    </el-drawer>

    <!-- 面试记录对话框 -->
    <el-dialog v-model="recordDialogVisible" title="记录面试结果" width="560px" :close-on-click-modal="false">
      <el-form :model="recordForm" label-width="90px">
        <el-form-item label="候选人">
          <span>{{ recordTarget?.realName }} ({{ recordTarget?.studentId }})</span>
        </el-form-item>
        <el-form-item label="面试轮次">
          <el-input-number v-model="recordForm.round" :min="1" :max="10" />
          <span style="margin-left:8px;color:#909399;font-size:13px">
            已有 {{ recordTarget?.rounds?.length || 0 }} 轮记录
          </span>
        </el-form-item>
        <el-form-item label="面试官">
          <el-input v-model="recordForm.interviewer" placeholder="面试官姓名" />
        </el-form-item>
        <el-form-item label="评分">
          <el-rate v-model="recordForm.score" :max="10" show-score />
        </el-form-item>
        <el-form-item label="推荐方向">
          <el-input v-model="recordForm.direction" placeholder="如：前端/后端/算法/运维" />
        </el-form-item>
        <el-form-item label="面试总结">
          <el-input v-model="recordForm.summary" type="textarea" :rows="3" placeholder="综合评价" />
        </el-form-item>
        <el-form-item label="优点">
          <el-input v-model="recordForm.strengths" type="textarea" :rows="2" placeholder="候选人优点" />
        </el-form-item>
        <el-form-item label="不足">
          <el-input v-model="recordForm.weaknesses" type="textarea" :rows="2" placeholder="待改进方面" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="recordDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitRecord">保存记录</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import StatCard from '@/components/StatCard.vue'
import { getInterviewList, recordInterview, updateInterviewStatus, getInterviewStatistics } from '@/api/interview'

const loading = ref(false)
const list = ref([])
const total = ref(0)
const page = ref(1)
const keyword = ref('')
const statusFilter = ref('')
const stats = ref({ total: 0, pending: 0, passed: 0, failed: 0, passRate: 0 })

const drawerVisible = ref(false)
const currentItem = ref(null)

const recordDialogVisible = ref(false)
const recordTarget = ref(null)
const recordForm = ref({
  enrollmentId: null,
  round: 1,
  interviewer: '',
  score: 0,
  direction: '',
  summary: '',
  strengths: '',
  weaknesses: ''
})

const statusLabels = { pending: '待面试', passed: '已通过', failed: '未通过', interviewed: '面试中' }
const statusTagType = { pending: 'warning', passed: 'success', failed: 'danger', interviewed: '' }

function scoreTagType(score) {
  if (score >= 8) return 'success'
  if (score >= 5) return 'warning'
  return 'danger'
}

function roundTimelineType(status) {
  if (status === 'passed') return 'success'
  if (status === 'failed') return 'danger'
  return 'warning'
}

async function loadStats() {
  try {
    const res = await getInterviewStatistics()
    stats.value = res.data
  } catch {}
}

async function loadList() {
  loading.value = true
  try {
    const res = await getInterviewList({
      page: page.value,
      size: 10,
      status: statusFilter.value,
      keyword: keyword.value
    })
    list.value = res.data.list
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

async function openDetail(row) {
  try {
    const res = await getInterviewDetail(row.enrollmentId)
    currentItem.value = res.data
    drawerVisible.value = true
  } catch (e) {
    ElMessage.error('加载详情失败')
  }
}

function openRecordDialog(row) {
  recordTarget.value = row
  recordForm.value = {
    enrollmentId: row.enrollmentId,
    round: (row.rounds?.length || 0) + 1,
    interviewer: '',
    score: 0,
    direction: '',
    summary: '',
    strengths: '',
    weaknesses: ''
  }
  recordDialogVisible.value = true
}

async function submitRecord() {
  const form = recordForm.value
  if (!form.summary && !form.score) {
    ElMessage.warning('请至少填写评分或面试总结')
    return
  }
  try {
    await recordInterview({
      enrollmentId: form.enrollmentId,
      round: form.round,
      interviewer: form.interviewer,
      score: form.score || null,
      direction: form.direction,
      summary: form.summary,
      strengths: form.strengths,
      weaknesses: form.weaknesses
    })
    ElMessage.success('面试记录已保存')
    recordDialogVisible.value = false
    loadList()
    loadStats()
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

async function handleStatusUpdate(row, status) {
  if (!row.id) {
    ElMessage.warning('该候选人暂无面试记录，请先记录面试结果')
    return
  }
  const label = status === 'passed' ? '通过' : '不通过'
  try {
    await ElMessageBox.confirm(`确定标记「${row.realName}」面试${label}？`, '确认', {
      type: status === 'passed' ? 'success' : 'warning'
    })
    await updateInterviewStatus(row.id, status)
    ElMessage.success(`已标记为面试${label}`)
    loadList()
    loadStats()
  } catch {}
}

onMounted(() => {
  loadStats()
  loadList()
})
</script>

<style scoped>
.interview-view {
  padding: 20px;
}
.page-header {
  margin-bottom: 20px;
}
.page-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}
.toolbar {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
</style>
