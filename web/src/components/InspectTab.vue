<template>
  <div class="inspect-tab">
    <el-card class="form-card">
      <template #header>
        <div>
          <span>镜像检查</span>
          <el-tooltip content="检查单个镜像的详细信息，如配置、清单等" placement="top">
            <el-icon style="margin-left: 8px; color: #909399;"><InfoFilled /></el-icon>
          </el-tooltip>
        </div>
      </template>

      <el-form :model="inspectForm" label-width="120px">
        <el-form-item label="镜像名称">
          <el-input 
            v-model="inspectForm.imageName" 
            placeholder="例如: docker://registry.example.com/image:tag"
          />
        </el-form-item>

        <el-form-item>
          <div>
            <el-checkbox v-model="inspectForm.raw">
              输出原始清单
              <el-tooltip content="获取镜像的原始清单，包含层信息、配置摘要等元数据" placement="top">
                <el-icon style="margin-left: 4px; color: #909399;"><QuestionFilled /></el-icon>
              </el-tooltip>
            </el-checkbox>
          </div>
          <div style="margin-top: 8px;">
            <el-checkbox v-model="inspectForm.config">
              输出配置
              <el-tooltip content="获取镜像的配置信息，包含环境变量、入口点、工作目录等运行时设置" placement="top">
                <el-icon style="margin-left: 4px; color: #909399;"><QuestionFilled /></el-icon>
              </el-tooltip>
            </el-checkbox>
          </div>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="inspectImage" :loading="loading">
            <el-icon><Search /></el-icon>
            检查镜像
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="result" class="result-card">
      <template #header>
        <span>检查结果</span>
      </template>

      <pre v-if="typeof result === 'string'">{{ result }}</pre>
      <json-viewer v-else :value="result" :expand-depth="3"></json-viewer>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, InfoFilled, QuestionFilled } from '@element-plus/icons-vue'
import JsonViewer from 'vue-json-viewer'
import skopeoApi from '../services/skopeoApi'

const loading = ref(false)
const result = ref(null)

const inspectForm = reactive({
  imageName: '',
  raw: false,
  config: false
})

const inspectImage = async () => {
  if (!inspectForm.imageName) {
    ElMessage.warning('请输入镜像名称')
    return
  }

  // 验证镜像名称格式
  const imagePattern = /^(docker|oci|dir|docker-archive|docker-daemon|oci-archive|ostree|sif|tarball):\/\/[^\s]+$/
  if (!imagePattern.test(inspectForm.imageName)) {
    ElMessage.warning('镜像名称格式不正确，请使用正确的传输协议格式，例如: docker://registry.example.com/image:tag')
    return
  }

  loading.value = true
  result.value = null

  try {
    const options = {}
    if (inspectForm.raw) options.raw = true
    if (inspectForm.config) options.config = true
    
    // 添加调试日志
    console.log('发送的选项:', JSON.stringify(options))
    console.log('镜像名称:', inspectForm.imageName)
    
    result.value = await skopeoApi.inspectImage(inspectForm.imageName, options)
    ElMessage.success('镜像检查成功')
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.inspect-tab {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-card, .result-card {
  margin-bottom: 20px;
}

pre {
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 500px;
  overflow: auto;
}
</style>
