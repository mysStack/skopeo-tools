<template>
  <div class="list-tab">
    <el-card class="form-card">
      <template #header>
        <div>
          <span>镜像标签列表</span>
          <el-tooltip content="获取仓库中所有可用的标签列表" placement="top">
            <el-icon style="margin-left: 8px; color: #909399;"><InfoFilled /></el-icon>
          </el-tooltip>
        </div>
      </template>

      <el-form :model="listForm" label-width="120px">
        <el-form-item label="仓库地址">
          <el-input 
            v-model="listForm.repository" 
            placeholder="例如: docker://registry.example.com/repository"
          />
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="listForm.useStream">
            使用流式处理（适用于大型仓库）
          </el-checkbox>
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="listForm.usePagination">
            使用分页（减少加载时间）
          </el-checkbox>
        </el-form-item>
        <el-form-item v-if="listForm.usePagination" label="每页显示数量">
          <el-select v-model="listForm.limit" placeholder="选择每页显示数量">
            <el-option label="20" :value="20" />
            <el-option label="50" :value="50" />
            <el-option label="100" :value="100" />
          </el-select>
        </el-form-item>

        <el-alert
          title="提示"
          type="info"
          :closable="false"
          show-icon
          style="margin-bottom: 15px;"
        >
          获取大型仓库（如Docker Hub上的官方镜像）的标签列表可能需要较长时间，请耐心等待。<br/>
          请输入完整的仓库地址，不包括标签。例如: docker://docker.io/library/nginx
        </el-alert>
        <el-form-item>
          <el-button type="primary" @click="listTags" :loading="loading">
            <el-icon><List /></el-icon>
            获取标签列表
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="result" class="result-card">
      <template #header>
        <span>标签列表结果</span>
      </template>

      <div class="repository-info">
        <h4>仓库: {{ result.repository }}</h4>
      </div>

      <el-table :data="getTableData()" style="width: 100%" max-height="500">
        <el-table-column prop="tag" label="标签" />
      </el-table>

      <div class="tag-count">
        <span v-if="result.pagination">
          显示第 {{ (result.pagination.page * result.pagination.limit) + 1 }} - {{ Math.min((result.pagination.page + 1) * result.pagination.limit, result.pagination.total) }} 项，共 {{ result.pagination.total }} 个标签
        </span>
        <span v-else>
          共找到 {{ getTableData().length }} 个标签
        </span>
      </div>
      
      <!-- 分页控件 -->
      <div v-if="result.pagination" class="pagination-controls">
        <el-pagination
          @current-change="handlePageChange"
          :current-page="result.pagination.page + 1"
          :page-size="result.pagination.limit"
          :total="result.pagination.total"
          layout="prev, pager, next, jumper, total"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { List, InfoFilled } from '@element-plus/icons-vue'
import skopeoApi from '../services/skopeoApi'

const loading = ref(false)
const result = ref(null)

const listForm = reactive({
  repository: '',
  useStream: false, // 默认不使用流式处理
  usePagination: true, // 默认使用分页
  page: 0, // 当前页码
  limit: 50, // 每页显示数量
  tagCount: 0 // 标签总数
})

// 处理表格数据，统一格式
const getTableData = () => {
  if (!result.value) {
    return []
  }
  
  // 如果result.value是字符串，尝试解析为JSON
  let data = result.value
  if (typeof result.value === 'string') {
    try {
      data = JSON.parse(result.value)
    } catch (e) {
      return []
    }
  }
  
  // 如果有分页信息，使用分页后的标签
  if (data.pagination && data.Tags) {
    return data.Tags.map(tag => ({ tag }))
  }
  
  // 如果有Tags数组，转换格式
  if (Array.isArray(data.Tags)) {
    return data.Tags.map(tag => ({ tag }))
  }
  
  // 如果有tags数组，转换格式
  if (Array.isArray(data.tags)) {
    return data.tags.map(tag => ({ tag }))
  }
  
  // 如果数据本身就是数组（字符串数组），直接转换
  if (Array.isArray(data)) {
    return data.map(tag => ({ tag }))
  }
  
  // 其他情况，返回空数组
  return []
}

// 获取标签数量
const getTagCount = async () => {
  if (!listForm.repository) {
    return
  }
  
  try {
    const countResult = await skopeoApi.getTagCount(listForm.repository)
    listForm.tagCount = countResult.tagCount || 0
    
    // 如果标签数量很多，建议使用分页
    if (listForm.tagCount > 100 && !listForm.usePagination) {
      ElMessage({
        message: `该仓库有 ${listForm.tagCount} 个标签，建议使用分页功能以加快加载速度。`,
        type: 'warning',
        duration: 5000
      })
    }
  } catch (error) {
    console.error('获取标签数量失败:', error)
  }
}

// 处理分页变化
const handlePageChange = (newPage) => {
  listForm.page = newPage - 1 // Element Plus分页组件从1开始，我们的逻辑从0开始
  listTags() // 重新获取数据
}

const listTags = async () => {
  if (!listForm.repository) {
    ElMessage.warning('请输入仓库地址')
    return
  }

  loading.value = true
  result.value = null
  
  // 显示加载提示
  const loadingMessage = ElMessage({
    message: listForm.useStream 
      ? '正在连接仓库并获取标签列表，这可能需要一些时间...' 
      : '正在获取标签列表，请稍候...',
    type: 'info',
    duration: 0, // 不自动关闭
    showClose: false
  })

  try {
    // 如果使用分页，传递分页参数
    if (listForm.usePagination) {
      result.value = await skopeoApi.listTags(listForm.repository, { 
        useStream: listForm.useStream,
        page: listForm.page,
        limit: listForm.limit
      })
    } else {
      result.value = await skopeoApi.listTags(listForm.repository, { useStream: listForm.useStream })
    }
    
    // 尝试调用getTableData获取表格数据
    const tableData = getTableData()
    
    loadingMessage.close()
    ElMessage.success('获取标签列表成功')
  } catch (error) {
    loadingMessage.close()
    
    // 提供更友好的错误信息
    let friendlyError = error.message
    if (error.message.includes('超时')) {
      friendlyError = '请求超时，可能是网络连接问题或仓库响应缓慢。您可以尝试勾选"使用流式处理"选项。'
    } else if (error.message.includes('无法连接')) {
      friendlyError = '无法连接到仓库，请检查仓库地址是否正确。'
    } else if (error.message.includes('manifest unknown')) {
      friendlyError = '仓库中没有找到默认标签(latest)，但这不影响获取所有标签列表。请继续尝试获取标签列表。'
    }
    
    ElMessage.error(friendlyError)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.list-tab {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-card, .result-card {
  margin-bottom: 20px;
}

.repository-info {
  margin-bottom: 15px;
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.repository-info h4 {
  margin: 0;
  color: #409EFF;
}

.tag-count {
  margin-top: 15px;
  text-align: right;
  color: #909399;
  margin-bottom: 15px;
}

.pagination-controls {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}
</style>
