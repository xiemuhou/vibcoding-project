<template>
  <div class="dashboard">
    <!-- 顶部导航 -->
    <header class="top-bar">
      <div class="top-left">
        <h1 class="logo">IP 地址管理系统</h1>
      </div>
      <div class="top-center">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索 IP / 姓名 / 部门 / MAC"
          prefix-icon="Search"
          clearable
          style="width: 360px"
          @input="handleSearch"
        />
        <div v-if="searchResults.length" class="search-dropdown">
          <div
            v-for="item in searchResults"
            :key="item.id"
            class="search-item"
            @click="jumpToIp(item)"
          >
            <span class="search-ip">{{ item.ip_address }}</span>
            <span class="search-info">
              {{ item.username || item.department || '空闲' }}
            </span>
            <span class="search-subnet">{{ item.subnet_name }}</span>
          </div>
        </div>
      </div>
      <div class="top-right">
        <span class="username">{{ username }}</span>
        <el-button text @click="handleExport">导出Excel</el-button>
        <el-button text type="warning" @click="handleReimport">重新导入</el-button>
        <el-button text type="danger" @click="handleLogout">退出</el-button>
      </div>
    </header>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-value">{{ totalStats.total }}</div>
        <div class="stat-label">IP 总数</div>
      </div>
      <div class="stat-card stat-free">
        <div class="stat-value">{{ totalStats.free }}</div>
        <div class="stat-label">空闲</div>
      </div>
      <div class="stat-card stat-occupied">
        <div class="stat-value">{{ totalStats.occupied }}</div>
        <div class="stat-label">已占用</div>
      </div>
      <div class="stat-card stat-reserved">
        <div class="stat-value">{{ totalStats.reserved }}</div>
        <div class="stat-label">保留</div>
      </div>
    </div>

    <!-- 子网段 Tab -->
    <div class="subnet-tabs">
      <el-tabs v-model="activeSubnet" @tab-change="onSubnetChange">
        <el-tab-pane
          v-for="s in subnets"
          :key="s.id"
          :label="formatTabLabel(s)"
          :name="String(s.id)"
        />
      </el-tabs>
    </div>

    <!-- 当前子网段信息 -->
    <div v-if="currentSubnet" class="subnet-info">
      <span class="subnet-name">{{ currentSubnet.name }}</span>
      <span class="subnet-cidr">({{ currentSubnet.cidr }})</span>
      <span class="subnet-stat free">空闲 {{ currentSubnet.free_count }}</span>
      <span class="subnet-stat occupied">占用 {{ currentSubnet.occupied_count }}</span>
      <span class="subnet-stat reserved">保留 {{ currentSubnet.reserved_count }}</span>
    </div>

    <!-- IP 网格 -->
    <div class="ip-grid" v-loading="loadingIps">
      <div
        v-for="ip in ips"
        :key="ip.id"
        :class="['ip-card', `ip-${ip.status}`, { 'ip-highlight': ip.id === highlightId }]"
        @click="handleCardClick(ip)"
      >
        <div class="ip-suffix">{{ ip.ip_suffix }}</div>
        <div class="ip-user" :title="ip.username">
          {{ ip.status === 'reserved' ? '保留' : (ip.username || '') }}
        </div>
      </div>
    </div>

    <!-- IP 详情/占用/编辑弹窗 -->
    <IpDialog
      v-model:visible="dialogVisible"
      :ip="selectedIp"
      @refresh="refreshCurrentSubnet"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getSubnets, getSubnetIps, searchIps, exportUrl, reimport } from '../api'
import IpDialog from '../components/IpDialog.vue'

const router = useRouter()
const username = ref(localStorage.getItem('username') || 'admin')

const subnets = ref([])
const activeSubnet = ref('')
const ips = ref([])
const loadingIps = ref(false)
const highlightId = ref(null)

const searchKeyword = ref('')
const searchResults = ref([])
let searchTimer = null

const dialogVisible = ref(false)
const selectedIp = ref(null)

const currentSubnet = computed(() =>
  subnets.value.find(s => String(s.id) === activeSubnet.value)
)

const totalStats = computed(() => {
  const all = subnets.value
  return {
    total: all.reduce((sum, s) => sum + s.total, 0),
    free: all.reduce((sum, s) => sum + s.free_count, 0),
    occupied: all.reduce((sum, s) => sum + s.occupied_count, 0),
    reserved: all.reduce((sum, s) => sum + s.reserved_count, 0)
  }
})

function formatTabLabel(s) {
  return s.cidr.replace('/24', '')
}

async function loadSubnets() {
  try {
    const { data } = await getSubnets()
    subnets.value = data
    if (data.length && !activeSubnet.value) {
      activeSubnet.value = String(data[0].id)
    }
  } catch (err) {
    ElMessage.error('加载子网段失败')
  }
}

async function loadIps(subnetId) {
  loadingIps.value = true
  try {
    const { data } = await getSubnetIps(subnetId)
    ips.value = data
  } catch (err) {
    ElMessage.error('加载IP列表失败')
  } finally {
    loadingIps.value = false
  }
}

function onSubnetChange(id) {
  highlightId.value = null
  loadIps(id)
}

async function refreshCurrentSubnet() {
  await loadSubnets()
  if (activeSubnet.value) {
    await loadIps(activeSubnet.value)
  }
}

function handleCardClick(ip) {
  selectedIp.value = ip
  dialogVisible.value = true
}

function handleSearch() {
  clearTimeout(searchTimer)
  const q = searchKeyword.value.trim()
  if (!q) {
    searchResults.value = []
    return
  }
  searchTimer = setTimeout(async () => {
    try {
      const { data } = await searchIps(q)
      searchResults.value = data
    } catch (err) {
      searchResults.value = []
    }
  }, 300)
}

function jumpToIp(item) {
  searchResults.value = []
  searchKeyword.value = ''
  activeSubnet.value = String(item.subnet_id)
  highlightId.value = item.id
  loadIps(item.subnet_id)
  setTimeout(() => {
    const el = document.querySelector('.ip-highlight')
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }, 300)
}

function handleExport() {
  const token = localStorage.getItem('token')
  const link = document.createElement('a')
  link.href = `${exportUrl}?token=${token}`
  link.click()
}

async function handleReimport() {
  try {
    await ElMessageBox.confirm(
      '将从 Excel 文件重新导入数据，当前数据库会被覆盖，确定继续？',
      '重新导入',
      { type: 'warning', confirmButtonText: '确定导入', cancelButtonText: '取消' }
    )
  } catch { return }
  try {
    const { data } = await reimport()
    ElMessage.success(data.message)
    await refreshCurrentSubnet()
  } catch (err) {
    ElMessage.error(err.response?.data?.error || '导入失败')
  }
}

function handleLogout() {
  localStorage.removeItem('token')
  localStorage.removeItem('username')
  router.push('/login')
}

onMounted(async () => {
  await loadSubnets()
  if (activeSubnet.value) {
    loadIps(activeSubnet.value)
  }
})

// 点击其他区域关闭搜索结果
document.addEventListener('click', (e) => {
  if (!e.target.closest('.top-center')) {
    searchResults.value = []
  }
})
</script>

<style scoped>
.dashboard {
  min-height: 100vh;
  background: #f0f2f5;
}

/* 顶部导航 */
.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  padding: 0 24px;
  height: 56px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  position: sticky;
  top: 0;
  z-index: 100;
}
.logo {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}
.top-center {
  position: relative;
}
.top-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.username {
  color: #606266;
  font-size: 14px;
}

/* 搜索下拉 */
.search-dropdown {
  position: absolute;
  top: 42px;
  left: 0;
  right: 0;
  background: #fff;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  max-height: 320px;
  overflow-y: auto;
  z-index: 200;
}
.search-item {
  padding: 10px 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid #f2f2f2;
}
.search-item:hover {
  background: #f5f7fa;
}
.search-ip {
  font-weight: 600;
  color: #303133;
  min-width: 120px;
}
.search-info {
  color: #606266;
  flex: 1;
}
.search-subnet {
  color: #909399;
  font-size: 12px;
}

/* 统计卡片 */
.stats-row {
  display: flex;
  gap: 16px;
  padding: 20px 24px 0;
}
.stat-card {
  flex: 1;
  background: #fff;
  border-radius: 8px;
  padding: 16px 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  border-left: 4px solid #909399;
}
.stat-card.stat-free {
  border-left-color: #67c23a;
}
.stat-card.stat-occupied {
  border-left-color: #e6a23c;
}
.stat-card.stat-reserved {
  border-left-color: #909399;
}
.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
}
.stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}

/* 子网段 Tab */
.subnet-tabs {
  padding: 16px 24px 0;
}
.subnet-tabs :deep(.el-tabs__item) {
  font-size: 14px;
}

/* 子网段信息栏 */
.subnet-info {
  padding: 8px 24px 12px;
  display: flex;
  align-items: center;
  gap: 12px;
}
.subnet-name {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}
.subnet-cidr {
  color: #909399;
  font-size: 13px;
}
.subnet-stat {
  font-size: 13px;
  padding: 2px 10px;
  border-radius: 12px;
}
.subnet-stat.free {
  background: #f0f9eb;
  color: #67c23a;
}
.subnet-stat.occupied {
  background: #fdf6ec;
  color: #e6a23c;
}
.subnet-stat.reserved {
  background: #f4f4f5;
  color: #909399;
}

/* IP 网格 */
.ip-grid {
  display: grid;
  grid-template-columns: repeat(16, 1fr);
  gap: 6px;
  padding: 0 24px 24px;
  min-height: 200px;
}
.ip-card {
  aspect-ratio: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
  min-height: 56px;
  position: relative;
}
.ip-card:hover {
  transform: scale(1.08);
  z-index: 10;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}
.ip-card.ip-free {
  background: #4caf50;
  border: 1px solid #388e3c;
  color: #fff;
}
.ip-card.ip-free:hover {
  background: #388e3c;
}
.ip-card.ip-free .ip-suffix,
.ip-card.ip-free .ip-user {
  color: #fff;
}
.ip-card.ip-occupied {
  background: #ef6c00;
  border: 1px solid #e65100;
  color: #fff;
}
.ip-card.ip-occupied:hover {
  background: #e65100;
}
.ip-card.ip-occupied .ip-suffix,
.ip-card.ip-occupied .ip-user {
  color: #fff;
}
.ip-card.ip-reserved {
  background: #f5f5f5;
  border: 1px solid #e0e0e0;
  cursor: default;
  opacity: 0.6;
}
.ip-card.ip-reserved:hover {
  transform: none;
  box-shadow: none;
}
.ip-card.ip-highlight {
  outline: 3px solid #409eff;
  outline-offset: 2px;
  animation: pulse 1s ease-in-out 3;
}
@keyframes pulse {
  0%, 100% { outline-color: #409eff; }
  50% { outline-color: transparent; }
}
.ip-suffix {
  font-size: 14px;
  font-weight: 700;
  color: #303133;
  line-height: 1.2;
}
.ip-user {
  font-size: 11px;
  color: #606266;
  margin-top: 2px;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 响应式 */
@media (max-width: 1200px) {
  .ip-grid {
    grid-template-columns: repeat(12, 1fr);
  }
}
@media (max-width: 800px) {
  .ip-grid {
    grid-template-columns: repeat(8, 1fr);
  }
  .stats-row {
    flex-wrap: wrap;
  }
  .stat-card {
    min-width: calc(50% - 8px);
  }
}
</style>
