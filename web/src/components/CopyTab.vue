<template>
  <div class="copy-tab">
    <el-card class="form-card">
      <template #header>
        <span>镜像复制</span>
      </template>

      <el-form :model="copyForm" label-width="120px">
        <el-form-item label="源镜像">
          <el-input 
            v-model="copyForm.sourceImage" 
            placeholder="例如: docker://registry.example.com/source-image:tag"
          />
        </el-form-item>

        <el-form-item label="目标镜像">
          <el-input 
            v-model="copyForm.destinationImage" 
            placeholder="例如: docker://registry.example.com/dest-image:tag"
          />
        </el-form-item>

        <el-form-item label="选项">
          <el-checkbox v-model="copyForm.quiet">静默模式</el-checkbox>
          <el-checkbox v-model="copyForm.all">复制所有标签</el-checkbox>
        </el-form-item>

        <el-form-item label="多架构处理">
          <el-select v-model="copyForm.multiArch" placeholder="选择多架构处理方式">
            <el-option label="系统默认" value="system" />
            <el-option label="全部" value="all" />
            <el-option label="仅索引" value="index-only" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="copyImage" :loading="loading">
            <el-icon><CopyDocument /></el-icon>
            复制镜像
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="result" class="result-card">
      <template #header>
        <span>复制结果</span>
      </template>

      <el-alert 
        :title="result.success ? '复制成功' : '复制失败'"
        :type="result.success ? 'success' : 'error'"
        :description="result.message"
        show-icon
        :closable="false"
      />

      <div v-if="result.digest" class="digest-info">
        <h4>镜像摘要:</h4>
        <p>{{ result.digest }}</p>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { CopyDocument } from '@element-plus/icons-vue'
import skopeoApi from '../services/skopeoApi'

const loading = ref(false)
const result = ref(null)

const copyForm = reactive({
  sourceImage: '',
  destinationImage: '',
  quiet: false,
  all: false,
  multiArch: 'system'
})

const copyImage = async () => {
  if (!copyForm.sourceImage || !copyForm.destinationImage) {
    ElMessage.warning('请输入源镜像和目标镜像')
    return
  }

  loading.value = true
  result.value = null

  try {
    const options = {
      quiet: copyForm.quiet,
      all: copyForm.all
    }

    if (copyForm.multiArch !== 'system') {
      options.multiArch = copyForm.multiArch
    }

    await skopeoApi.copyImage(copyForm.sourceImage, copyForm.destinationImage, options)
    result.value = {
      success: true,
      message: `成功将镜像从 ${copyForm.sourceImage} 复制到 ${copyForm.destinationImage}`
    }
    ElMessage.success('镜像复制成功')
  } catch (error) {
    result.value = {
      success: false,
      message: error.message
    }
    ElMessage.error(error.message)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.copy-tab {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-card, .result-card {
  margin-bottom: 20px;
}

.digest-info {
  margin-top: 15px;
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.digest-info h4 {
  margin: 0 0 10px 0;
  color: #409EFF;
}

.digest-info p {
  margin: 0;
  word-break: break-all;
  font-family: monospace;
}
</style>
