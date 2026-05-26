<template>
  <el-dialog
    :model-value="visible"
    @update:model-value="$emit('update:visible', $event)"
    :title="dialogTitle"
    width="480px"
    :close-on-click-modal="false"
    destroy-on-close
  >
    <!-- 空闲IP → 占用表单 -->
    <div v-if="ip && ip.status === 'free'">
      <el-form :model="form" label-width="80px" label-position="left">
        <el-form-item label="IP 地址">
          <span style="font-weight: 600">{{ ip.ip_address }}</span>
        </el-form-item>
        <el-form-item label="使用人" required>
          <el-input v-model="form.username" placeholder="请输入使用人" />
        </el-form-item>
        <el-form-item label="使用部门">
          <el-input v-model="form.department" placeholder="请输入部门" />
        </el-form-item>
        <el-form-item label="使用设备">
          <el-input v-model="form.device" placeholder="如：台式电脑、笔记本" />
        </el-form-item>
        <el-form-item label="设备型号">
          <el-input v-model="form.device_model" placeholder="请输入设备型号" />
        </el-form-item>
        <el-form-item label="MAC地址">
          <el-input v-model="form.mac_address" placeholder="如：6C:83:75:48:3B:DB" />
        </el-form-item>
        <el-form-item label="位置">
          <el-input v-model="form.location" placeholder="如：A1大办公室" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" placeholder="备注信息" />
        </el-form-item>
      </el-form>
    </div>

    <!-- 已占用IP → 详情查看 -->
    <div v-else-if="ip && ip.status === 'occupied' && !editing">
      <div class="detail-grid">
        <div class="detail-row">
          <span class="detail-label">IP 地址</span>
          <span class="detail-value bold">{{ ip.ip_address }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">状态</span>
          <el-tag type="warning" size="small">已占用</el-tag>
        </div>
        <div class="detail-row">
          <span class="detail-label">使用人</span>
          <span class="detail-value">{{ ip.username || '—' }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">使用部门</span>
          <span class="detail-value">{{ ip.department || '—' }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">使用设备</span>
          <span class="detail-value">{{ ip.device || '—' }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">设备型号</span>
          <span class="detail-value">{{ ip.device_model || '—' }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">MAC地址</span>
          <span class="detail-value">{{ ip.mac_address || '—' }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">位置</span>
          <span class="detail-value">{{ ip.location || '—' }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">备注</span>
          <span class="detail-value">{{ ip.remark || '—' }}</span>
        </div>
      </div>
    </div>

    <!-- 已占用IP → 编辑模式 -->
    <div v-else-if="ip && ip.status === 'occupied' && editing">
      <el-form :model="form" label-width="80px" label-position="left">
        <el-form-item label="IP 地址">
          <span style="font-weight: 600">{{ ip.ip_address }}</span>
        </el-form-item>
        <el-form-item label="使用人">
          <el-input v-model="form.username" />
        </el-form-item>
        <el-form-item label="使用部门">
          <el-input v-model="form.department" />
        </el-form-item>
        <el-form-item label="使用设备">
          <el-input v-model="form.device" />
        </el-form-item>
        <el-form-item label="设备型号">
          <el-input v-model="form.device_model" />
        </el-form-item>
        <el-form-item label="MAC地址">
          <el-input v-model="form.mac_address" />
        </el-form-item>
        <el-form-item label="位置">
          <el-input v-model="form.location" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
    </div>

    <!-- 保留IP -->
    <div v-else-if="ip && ip.status === 'reserved'">
      <div class="detail-grid">
        <div class="detail-row">
          <span class="detail-label">IP 地址</span>
          <span class="detail-value bold">{{ ip.ip_address }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">状态</span>
          <el-tag type="info" size="small">保留地址</el-tag>
        </div>
        <div class="detail-row">
          <span class="detail-label">说明</span>
          <span class="detail-value">.1 / .254 / .255 为保留地址，不可分配</span>
        </div>
      </div>
    </div>

    <!-- 统一 footer -->
    <template #footer>
      <div v-if="ip && ip.status === 'free'">
        <el-button @click="close">取 消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleOccupy">确认占用</el-button>
      </div>
      <div v-else-if="ip && ip.status === 'occupied' && !editing">
        <el-button type="danger" plain :loading="submitting" @click="handleRelease">释放 IP</el-button>
        <el-button type="primary" plain @click="startEdit">编 辑</el-button>
        <el-button @click="close">关 闭</el-button>
      </div>
      <div v-else-if="ip && ip.status === 'occupied' && editing">
        <el-button @click="editing = false">取 消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleUpdate">保 存</el-button>
      </div>
      <div v-else>
        <el-button @click="close">关 闭</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { occupyIp, releaseIp, updateIp } from '../api'

const props = defineProps({
  visible: Boolean,
  ip: Object
})
const emit = defineEmits(['update:visible', 'refresh'])

const submitting = ref(false)
const editing = ref(false)
const form = reactive({
  username: '',
  department: '',
  device: '',
  device_model: '',
  mac_address: '',
  location: '',
  remark: ''
})

const dialogTitle = ref('')

watch(() => props.ip, (ip) => {
  editing.value = false
  if (!ip) return
  if (ip.status === 'free') {
    dialogTitle.value = `占用 IP: ${ip.ip_address}`
    resetForm()
  } else if (ip.status === 'occupied') {
    dialogTitle.value = `IP: ${ip.ip_address}`
    fillForm(ip)
  } else {
    dialogTitle.value = `IP: ${ip.ip_address}`
  }
})

function resetForm() {
  Object.keys(form).forEach(k => form[k] = '')
}

function fillForm(ip) {
  form.username = ip.username || ''
  form.department = ip.department || ''
  form.device = ip.device || ''
  form.device_model = ip.device_model || ''
  form.mac_address = ip.mac_address || ''
  form.location = ip.location || ''
  form.remark = ip.remark || ''
}

function startEdit() {
  fillForm(props.ip)
  editing.value = true
}

function close() {
  emit('update:visible', false)
}

async function handleOccupy() {
  if (!form.username.trim()) {
    ElMessage.warning('请填写使用人')
    return
  }
  submitting.value = true
  try {
    await occupyIp(props.ip.id, { ...form })
    ElMessage.success('占用成功')
    close()
    emit('refresh')
  } catch (err) {
    ElMessage.error(err.response?.data?.error || '操作失败')
  } finally {
    submitting.value = false
  }
}

async function handleRelease() {
  try {
    await ElMessageBox.confirm(
      `确定要释放 ${props.ip.ip_address} 吗？释放后所有使用信息将被清空。`,
      '释放确认',
      { type: 'warning', confirmButtonText: '确定释放', cancelButtonText: '取消' }
    )
  } catch {
    return
  }
  submitting.value = true
  try {
    await releaseIp(props.ip.id)
    ElMessage.success('释放成功')
    close()
    emit('refresh')
  } catch (err) {
    ElMessage.error(err.response?.data?.error || '操作失败')
  } finally {
    submitting.value = false
  }
}

async function handleUpdate() {
  submitting.value = true
  try {
    await updateIp(props.ip.id, { ...form })
    ElMessage.success('更新成功')
    close()
    emit('refresh')
  } catch (err) {
    ElMessage.error(err.response?.data?.error || '操作失败')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.detail-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.detail-row {
  display: flex;
  align-items: center;
  padding: 4px 0;
  border-bottom: 1px solid #f5f5f5;
}
.detail-label {
  width: 80px;
  color: #909399;
  font-size: 14px;
  flex-shrink: 0;
}
.detail-value {
  color: #303133;
  font-size: 14px;
}
.detail-value.bold {
  font-weight: 600;
}
</style>
