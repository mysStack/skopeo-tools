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
            :class="{ 'is-error': copyForm.sourceImage && !validateImageAddress(copyForm.sourceImage) }"
          />
          <div v-if="copyForm.sourceImage && !validateImageAddress(copyForm.sourceImage)" class="error-message">
            {{ getFormatErrorMessage('image') }}
          </div>
        </el-form-item>

        <el-form-item label="目标镜像">
          <el-input
            v-model="copyForm.destinationImage"
            placeholder="例如: docker://registry.example.com/dest-image:tag"
            :class="{ 'is-error': copyForm.destinationImage && !validateImageAddress(copyForm.destinationImage) }"
          />
          <div v-if="copyForm.destinationImage && !validateImageAddress(copyForm.destinationImage)" class="error-message">
            {{ getFormatErrorMessage('image') }}
          </div>
        </el-form-item>

        <el-form-item label="选项">
          <el-checkbox v-model="copyForm.quiet">静默模式</el-checkbox>
          <el-checkbox v-model="copyForm.all">复制所有标签</el-checkbox>
        </el-form-item>

        <el-form-item label="源认证信息">
          <el-input
            v-model="copyForm.srcCreds"
            placeholder="用户名:密码 (例如: username:password)"
            type="password"
            show-password
            :class="{ 'is-error': copyForm.srcCreds && !validateAuthInfo(copyForm.srcCreds) }"
          />
          <div v-if="copyForm.srcCreds && !validateAuthInfo(copyForm.srcCreds)" class="error-message">
            {{ getFormatErrorMessage('auth') }}
          </div>
        </el-form-item>

        <el-form-item label="目标认证信息">
          <el-input
            v-model="copyForm.destCreds"
            placeholder="用户名:密码 (例如: username:password)"
            type="password"
            show-password
            :class="{ 'is-error': copyForm.destCreds && !validateAuthInfo(copyForm.destCreds) }"
          />
          <div v-if="copyForm.destCreds && !validateAuthInfo(copyForm.destCreds)" class="error-message">
            {{ getFormatErrorMessage('auth') }}
          </div>
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
import { validateImageAddress, validateAuthInfo, getFormatErrorMessage } from '../utils/validators'

const loading = ref(false)
const result = ref(null)

const copyForm = reactive({
  sourceImage: '',
  destinationImage: '',
  quiet: false,
  all: false,
  multiArch: 'system',
  srcCreds: '',
  destCreds: ''
})

const copyImage = async () => {
  // 验证镜像地址格式
  if (!copyForm.sourceImage || !copyForm.destinationImage) {
    ElMessage.warning('请输入源镜像和目标镜像')
    return
  }

  if (!validateImageAddress(copyForm.sourceImage)) {
    ElMessage.error(getFormatErrorMessage('image'))
    return
  }

  if (!validateImageAddress(copyForm.destinationImage)) {
    ElMessage.error(getFormatErrorMessage('image'))
    return
  }

  // 验证认证信息格式（如果提供了）
  if (copyForm.srcCreds && !validateAuthInfo(copyForm.srcCreds)) {
    ElMessage.error(getFormatErrorMessage('auth'))
    return
  }

  if (copyForm.destCreds && !validateAuthInfo(copyForm.destCreds)) {
    ElMessage.error(getFormatErrorMessage('auth'))
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

    await skopeoApi.copyImage(copyForm.sourceImage, copyForm.destinationImage, options, copyForm.srcCreds, copyForm.destCreds)
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

.error-message {
  color: #F56C6C;
  font-size: 12px;
  margin-top: 5px;
}
</style>