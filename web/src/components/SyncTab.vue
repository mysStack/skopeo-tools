<template>
  <div class="sync-tab">
    <el-card class="form-card">
      <template #header>
        <span>镜像同步</span>
      </template>

      <el-form :model="syncForm" label-width="120px">
        <el-form-item label="源类型">
          <el-select v-model="syncForm.sourceType" placeholder="选择源类型">
            <el-option label="Docker 注册表" value="docker" />
            <el-option label="目录" value="dir" />
            <el-option label="YAML 配置" value="yaml" />
          </el-select>
        </el-form-item>

        <el-form-item label="源地址">
          <el-input 
            v-model="syncForm.source" 
            :placeholder="sourcePlaceholder"
          />
        </el-form-item>

        <el-form-item label="目标类型">
          <el-select v-model="syncForm.destinationType" placeholder="选择目标类型">
            <el-option label="Docker 注册表" value="docker" />
            <el-option label="目录" value="dir" />
          </el-select>
        </el-form-item>

        <el-form-item label="目标地址">
          <el-input 
            v-model="syncForm.destination" 
            placeholder="例如: /path/to/destination 或 registry.example.com/repository"
          />
        </el-form-item>

        <el-form-item label="选项">
          <el-checkbox v-model="syncForm.scoped">使用源路径作为范围</el-checkbox>
          <el-checkbox v-model="syncForm.all">同步所有镜像</el-checkbox>
          <el-checkbox v-model="syncForm.dryRun">试运行模式</el-checkbox>
        </el-form-item>

        <el-form-item label="后缀">
          <el-input 
            v-model="syncForm.appendSuffix" 
            placeholder="添加到目标标签的后缀"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="syncImages" :loading="loading">
            <el-icon><Refresh /></el-icon>
            同步镜像
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="result" class="result-card">
      <template #header>
        <span>同步结果</span>
      </template>

      <el-alert 
        :title="result.success ? '同步成功' : '同步失败'"
        :type="result.success ? 'success' : 'error'"
        :description="result.message"
        show-icon
        :closable="false"
      />

      <div v-if="result.imagesCount !== undefined" class="sync-info">
        <h4>同步统计:</h4>
        <p>已同步镜像数量: {{ result.imagesCount }}</p>
        <p>源仓库数量: {{ result.sourcesCount }}</p>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import skopeoApi from '../services/skopeoApi'

const loading = ref(false)
const result = ref(null)

const syncForm = reactive({
  sourceType: 'docker',
  source: '',
  destinationType: 'docker',
  destination: '',
  scoped: false,
  all: false,
  dryRun: false,
  appendSuffix: ''
})

const sourcePlaceholder = computed(() => {
  switch (syncForm.sourceType) {
    case 'docker':
      return '例如: registry.example.com/repository'
    case 'dir':
      return '例如: /path/to/source/directory'
    case 'yaml':
      return '例如: /path/to/config.yaml'
    default:
      return '请输入源地址'
  }
})

const syncImages = async () => {
  if (!syncForm.source || !syncForm.destination) {
    ElMessage.warning('请输入源地址和目标地址')
    return
  }

  loading.value = true
  result.value = null

  try {
    const options = {
      source: syncForm.sourceType,
      destination: syncForm.destinationType,
      scoped: syncForm.scoped,
      all: syncForm.all,
      dryRun: syncForm.dryRun
    }

    if (syncForm.appendSuffix) {
      options.appendSuffix = syncForm.appendSuffix
    }

    const response = await skopeoApi.syncImages(syncForm.source, syncForm.destination, options)
    result.value = {
      success: true,
      message: `成功从 ${syncForm.source} 同步到 ${syncForm.destination}`,
      imagesCount: response.imagesCount,
      sourcesCount: response.sourcesCount
    }
    ElMessage.success('镜像同步成功')
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
.sync-tab {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-card, .result-card {
  margin-bottom: 20px;
}

.sync-info {
  margin-top: 15px;
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.sync-info h4 {
  margin: 0 0 10px 0;
  color: #409EFF;
}

.sync-info p {
  margin: 5px 0;
}
</style>
