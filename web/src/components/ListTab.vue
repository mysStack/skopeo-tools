<template>
  <div class="list-tab">
    <el-card class="form-card">
      <template #header>
        <span>镜像标签列表</span>
      </template>

      <el-form :model="listForm" label-width="120px">
        <el-form-item label="仓库地址">
          <el-input 
            v-model="listForm.repository" 
            placeholder="例如: docker://registry.example.com/repository"
          />
        </el-form-item>

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

      <el-table :data="result.tags" style="width: 100%" max-height="500">
        <el-table-column prop="tag" label="标签" />
      </el-table>

      <div class="tag-count">
        共找到 {{ result.tags.length }} 个标签
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { List } from '@element-plus/icons-vue'
import skopeoApi from '../services/skopeoApi'

const loading = ref(false)
const result = ref(null)

const listForm = reactive({
  repository: ''
})

const listTags = async () => {
  if (!listForm.repository) {
    ElMessage.warning('请输入仓库地址')
    return
  }

  loading.value = true
  result.value = null

  try {
    result.value = await skopeoApi.listTags(listForm.repository)
    ElMessage.success('获取标签列表成功')
  } catch (error) {
    ElMessage.error(error.message)
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
}
</style>
