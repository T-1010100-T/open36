<template>
  <div class="user-view">
    <div class="page-header">
      <h2>用户管理</h2>
    </div>
    <div class="toolbar">
      <el-input v-model="keyword" placeholder="搜索用户名/昵称" clearable style="width:240px" prefix-icon="Search" @input="handleSearch" />
      <el-select v-model="roleFilter" placeholder="角色筛选" clearable style="width:140px" @change="handleSearch">
        <el-option label="管理员" value="admin" />
        <el-option label="普通用户" value="user" />
      </el-select>
      <el-select v-model="statusFilter" placeholder="状态筛选" clearable style="width:140px" @change="handleSearch">
        <el-option label="待审核" value="pending" />
        <el-option label="启用" value="active" />
        <el-option label="禁用" value="disabled" />
      </el-select>
      <el-select v-model="permissionFilter" placeholder="权限筛选" clearable style="width:160px" @change="handleSearch">
        <el-option label="全部权限" value="all" />
        <el-option label="仅论坛" value="forum" />
        <el-option label="仅算法" value="algo" />
        <el-option label="无权限" value="none" />
      </el-select>
      <el-button type="primary" @click="showCreateDialog = true"><el-icon><Plus /></el-icon>创建用户</el-button>
      <el-button type="danger" :disabled="!selectedIds.length" @click="handleBatchDelete"><el-icon><Delete /></el-icon>批量删除</el-button>
    </div>

    <el-table :data="filteredUsers" stripe v-loading="loading" @selection-change="handleSelectionChange">
      <el-table-column type="selection" width="55" />
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column label="用户" min-width="200">
        <template #default="{ row }">
          <div style="display:flex;align-items:center;gap:10px">
            <el-avatar :size="32" :src="row.avatar">{{ row.username[0] }}</el-avatar>
            <div>
              <div style="font-weight:500">{{ row.nickname || row.username }}</div>
              <div style="font-size:12px;color:#909399">@{{ row.username }}</div>
            </div>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="realName" label="真实姓名" width="100" />
      <el-table-column prop="studentId" label="学号" width="120" />
      <el-table-column prop="major" label="专业" width="120" />
      <el-table-column prop="phone" label="电话" width="120" />
      <el-table-column prop="role" label="角色" width="100">
        <template #default="{ row }">
          <el-tag :type="row.role === 'admin' ? 'danger' : ''" size="small">
            {{ row.role === 'admin' ? '管理员' : '用户' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="120">
        <template #default="{ row }">
          <el-tag v-if="row.status === 'pending'" type="warning" size="small">待审核</el-tag>
          <el-tag v-else-if="row.status === 'active'" type="success" size="small">启用</el-tag>
          <el-tag v-else type="info" size="small">禁用</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="clientPermission" label="客户端权限" width="120">
        <template #default="{ row }">
          <el-tag v-if="row.clientPermission === 'forum'" type="primary" size="small">仅论坛</el-tag>
          <el-tag v-else-if="row.clientPermission === 'algo'" type="success" size="small">仅算法</el-tag>
          <el-tag v-else-if="row.clientPermission === 'none'" type="info" size="small">无权限</el-tag>
          <el-tag v-else type="warning" size="small">全部权限</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="createdAt" label="注册时间" width="180" />
      <el-table-column label="操作" width="300" fixed="right">
        <template #default="{ row }">
          <el-button v-if="row.status === 'pending'" type="success" link size="small" @click="handleApprove(row)">审核通过</el-button>
          <el-button v-if="row.status === 'active'" type="danger" link size="small" @click="handleDisable(row)">禁用</el-button>
          <el-button v-if="row.status === 'disabled'" type="primary" link size="small" @click="handleEnable(row)">启用</el-button>
          <el-button type="primary" link size="small" @click="handleEditPermission(row)">权限</el-button>
          <el-button type="primary" link size="small" @click="handleResetPwd(row)">重置密码</el-button>
          <el-button type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div style="display:flex;justify-content:flex-end;margin-top:16px">
      <el-pagination
        v-model:current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="loadUsers"
      />
    </div>

    <!-- 创建用户对话框 -->
    <el-dialog v-model="showCreateDialog" title="创建用户" width="460px" destroy-on-close>
      <el-form ref="createFormRef" :model="createForm" :rules="createRules" label-width="80px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="createForm.username" placeholder="3-20个字符" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="createForm.password" type="password" placeholder="6-32个字符" show-password />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="createForm.role" style="width:100%">
            <el-option label="管理员" value="admin" />
            <el-option label="普通用户" value="user" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="createForm.status" style="width:100%">
            <el-option label="待审核" value="pending" />
            <el-option label="启用" value="active" />
            <el-option label="禁用" value="disabled" />
          </el-select>
        </el-form-item>
        <el-form-item label="学号" prop="studentId">
          <el-input v-model="createForm.studentId" placeholder="学号" />
        </el-form-item>
        <el-form-item label="真实姓名" prop="realName">
          <el-input v-model="createForm.realName" placeholder="真实姓名" />
        </el-form-item>
        <el-form-item label="电话" prop="phone">
          <el-input v-model="createForm.phone" placeholder="电话号码" />
        </el-form-item>
        <el-form-item label="专业" prop="major">
          <el-input v-model="createForm.major" placeholder="专业名称" />
        </el-form-item>
        <el-form-item label="客户端权限" prop="clientPermission">
          <el-select v-model="createForm.clientPermission" style="width:100%">
            <el-option label="全部权限（论坛+算法）" value="all" />
            <el-option label="仅论坛" value="forum" />
            <el-option label="仅算法" value="algo" />
            <el-option label="无权限" value="none" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleCreate">确定</el-button>
      </template>
    </el-dialog>

    <!-- 重置密码对话框 -->
    <el-dialog v-model="showResetDialog" title="重置密码" width="460px" destroy-on-close>
      <el-form ref="resetFormRef" :model="resetForm" :rules="resetRules" label-width="80px">
        <el-form-item label="新密码" prop="newPassword">
          <el-input v-model="resetForm.newPassword" type="password" placeholder="6-32个字符" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showResetDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleResetSubmit">确定</el-button>
      </template>
    </el-dialog>

    <!-- 编辑权限对话框 -->
    <el-dialog v-model="showPermissionDialog" title="编辑客户端权限" width="460px" destroy-on-close>
      <el-form label-width="100px">
        <el-form-item label="当前用户">
          <span>{{ permissionTarget?.nickname || permissionTarget?.username }}</span>
        </el-form-item>
        <el-form-item label="客户端权限">
          <el-select v-model="permissionForm.clientPermission" style="width:100%">
            <el-option label="全部权限（论坛+算法）" value="all" />
            <el-option label="仅论坛" value="forum" />
            <el-option label="仅算法" value="algo" />
            <el-option label="无权限" value="none" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showPermissionDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handlePermissionSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getUserList, createUser, updateUserStatus, resetPassword, deleteUser, updateUserPermission, batchDeleteUsers } from '@/api/users'

const loading = ref(false)
const submitting = ref(false)
const users = ref([])
const keyword = ref('')
const roleFilter = ref('')
const statusFilter = ref('')
const permissionFilter = ref('')
const page = ref(1)
const pageSize = 10
const total = ref(0)
const selectedIds = ref([])

const showCreateDialog = ref(false)
const showResetDialog = ref(false)
const showPermissionDialog = ref(false)
const createFormRef = ref(null)
const resetFormRef = ref(null)
const resetTarget = ref(null)
const permissionTarget = ref(null)
const permissionForm = reactive({ clientPermission: 'all' })

function handleSelectionChange(rows) {
  selectedIds.value = rows.map(r => r.id)
}

const createForm = reactive({ username: '', password: '', role: 'user', status: 'pending', studentId: '', realName: '', phone: '', major: '', clientPermission: 'all' })
const createRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }, { min: 3, max: 20, message: '3-20个字符', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }, { min: 6, max: 32, message: '6-32个字符', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }]
}

const resetForm = reactive({ newPassword: '' })
const resetRules = {
  newPassword: [{ required: true, message: '请输入新密码', trigger: 'blur' }, { min: 6, max: 32, message: '6-32个字符', trigger: 'blur' }]
}

const filteredUsers = computed(() => {
  let list = users.value
  if (keyword.value) {
    const kw = keyword.value.toLowerCase()
    list = list.filter(u => u.username.toLowerCase().includes(kw) || (u.nickname || '').toLowerCase().includes(kw))
  }
  if (roleFilter.value) list = list.filter(u => u.role === roleFilter.value)
  if (statusFilter.value) list = list.filter(u => u.status === statusFilter.value)
  if (permissionFilter.value) list = list.filter(u => u.clientPermission === permissionFilter.value)
  return list
})

function handleSearch() {
  page.value = 1
}

async function loadUsers() {
  loading.value = true
  try {
    const res = await getUserList({ page: page.value, size: pageSize })
    const data = res.data || res
    users.value = data.list || data.records || data || []
    total.value = data.total || users.value.length
  } catch (e) {
    ElMessage.error(e?.message || '加载用户列表失败')
  } finally {
    loading.value = false
  }
}

async function handleApprove(row) {
  try {
    await ElMessageBox.confirm(`确定通过用户 ${row.username} 的注册申请？`, '审核确认', { type: 'warning' })
    await updateUserStatus(row.id, { status: 'active' })
    row.status = 'active'
    ElMessage.success('审核通过')
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error(e?.message || '审核失败')
    }
  }
}

async function handleEnable(row) {
  try {
    await ElMessageBox.confirm(`确定启用用户 ${row.username}？`, '提示', { type: 'warning' })
    await updateUserStatus(row.id, { status: 'active' })
    row.status = 'active'
    ElMessage.success('启用成功')
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error(e?.message || '启用失败')
    }
  }
}

async function handleDisable(row) {
  try {
    await ElMessageBox.confirm(`确定禁用用户 ${row.username}？`, '提示', { type: 'warning' })
    await updateUserStatus(row.id, { status: 'disabled' })
    row.status = 'disabled'
    ElMessage.success('禁用成功')
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error(e?.message || '禁用失败')
    }
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定删除用户 ${row.username}？此操作不可恢复！`, '删除确认', { type: 'warning' })
    await deleteUser(row.id)
    ElMessage.success('删除成功')
    loadUsers()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error(e?.message || '删除失败')
    }
  }
}

async function handleBatchDelete() {
  if (!selectedIds.value.length) return
  try {
    await ElMessageBox.confirm(`确定删除选中的 ${selectedIds.value.length} 位用户？此操作不可恢复！`, '批量删除确认', { type: 'warning' })
    await batchDeleteUsers(selectedIds.value)
    ElMessage.success('批量删除成功')
    selectedIds.value = []
    loadUsers()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error(e?.message || '批量删除失败')
    }
  }
}

async function handleCreate() {
  const valid = await createFormRef.value.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    await createUser(createForm)
    ElMessage.success('创建成功')
    showCreateDialog.value = false
    Object.assign(createForm, { username: '', password: '', role: 'user', status: 'pending', studentId: '', realName: '', phone: '', major: '', clientPermission: 'all' })
    loadUsers()
  } catch (e) {
    ElMessage.error(e?.message || '创建失败')
  } finally {
    submitting.value = false
  }
}

function handleResetPwd(row) {
  resetTarget.value = row
  resetForm.newPassword = ''
  showResetDialog.value = true
}

function handleEditPermission(row) {
  permissionTarget.value = row
  permissionForm.clientPermission = row.clientPermission || 'all'
  showPermissionDialog.value = true
}

async function handlePermissionSubmit() {
  submitting.value = true
  try {
    await updateUserPermission(permissionTarget.value.id, { clientPermission: permissionForm.clientPermission })
    permissionTarget.value.clientPermission = permissionForm.clientPermission
    ElMessage.success('权限修改成功')
    showPermissionDialog.value = false
  } catch (e) {
    ElMessage.error(e?.message || '权限修改失败')
  } finally {
    submitting.value = false
  }
}

async function handleResetSubmit() {
  const valid = await resetFormRef.value.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    await resetPassword(resetTarget.value.id, { newPassword: resetForm.newPassword })
    ElMessage.success('密码已重置')
    showResetDialog.value = false
  } catch (e) {
    ElMessage.error(e?.message || '重置失败')
  } finally {
    submitting.value = false
  }
}

onMounted(loadUsers)
</script>
