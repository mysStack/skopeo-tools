<template>
  <div class="sync-tab">
    <el-card class="form-card">
      <template #header>
        <span>镜像同步</span>
      </template>

      <el-tabs v-model="activeTab">
        <el-tab-pane label="手动输入镜像" name="manual">
          <el-form :model="syncForm" label-width="120px">
            <el-form-item label="镜像列表">
              <el-input
                v-model="syncForm.imageList"
                type="textarea"
                :rows="5"
                placeholder="每行一个镜像，例如：nginx:latest&#10;redis:alpine&#10;postgres:14"
              />
            </el-form-item>

            <el-form-item label="源仓库">
              <el-input
                v-model="syncForm.sourceRegistry"
                placeholder="例如: docker.io/library"
              />
            </el-form-item>

            <el-form-item label="目标仓库">
              <el-input
                v-model="syncForm.destinationRegistry"
                placeholder="例如: docker.io/myusername"
              />
            </el-form-item>

            <el-form-item label="认证信息">
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-input
                    v-model="syncForm.srcCreds"
                    placeholder="源仓库认证 (用户名:密码)"
                    type="password"
                    show-password
                  />
                </el-col>
                <el-col :span="12">
                  <el-input
                    v-model="syncForm.destCreds"
                    placeholder="目标仓库认证 (用户名:密码)"
                    type="password"
                    show-password
                  />
                </el-col>
              </el-row>
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="syncImagesFromList" :loading="loading">
                <el-icon><Refresh /></el-icon>
                同步镜像
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="上传镜像列表文件" name="file">
          <el-form :model="fileForm" label-width="120px">
            <el-form-item label="镜像列表文件">
              <el-upload
                ref="upload"
                :auto-upload="false"
                :limit="1"
                :on-change="handleFileChange"
                :file-list="fileList"
                accept=".txt"
              >
                <el-button type="primary">选择文件</el-button>
                <template #tip>
                  <div class="el-upload__tip">
                    请上传包含镜像列表的文本文件，每行一个镜像
                  </div>
                </template>
              </el-upload>
            </el-form-item>

            <el-form-item label="源仓库">
              <el-input
                v-model="fileForm.sourceRegistry"
                placeholder="例如: docker.io/library"
              />
            </el-form-item>

            <el-form-item label="目标仓库">
              <el-input
                v-model="fileForm.destinationRegistry"
                placeholder="例如: docker.io/myusername"
              />
            </el-form-item>

            <el-form-item label="认证信息">
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-input
                    v-model="fileForm.srcCreds"
                    placeholder="源仓库认证 (用户名:密码)"
                    type="password"
                    show-password
                  />
                </el-col>
                <el-col :span="12">
                  <el-input
                    v-model="fileForm.destCreds"
                    placeholder="目标仓库认证 (用户名:密码)"
                    type="password"
                    show-password
                  />
                </el-col>
              </el-row>
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="syncImagesFromFile" :loading="loading" :disabled="!selectedFile">
                <el-icon><Refresh /></el-icon>
                同步镜像
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
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

      <div v-if="result.total !== undefined" class="sync-info">
        <h4>同步统计:</h4>
        <p>总镜像数量: {{ result.total }}</p>
        <p>成功同步数量: {{ result.success_count }}</p>
        <p>失败同步数量: {{ result.failed_count }}</p>

        <div v-if="result.results" class="sync-details">
          <h5>详细结果:</h5>
          <el-table :data="formatSyncResults(result.results)" style="width: 100%">
            <el-table-column prop="image" label="镜像" width="300" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="scope">
                <el-tag :type="scope.row.success ? 'success' : 'danger'">
                  {{ scope.row.success ? '成功' : '失败' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <div v-if="result.log_file" class="log-section">
          <h5>日志文件:</h5>
          <el-button type="text" @click="viewLogFile(result.log_file)">查看日志</el-button>
        </div>
      </div>
    </el-card>

    <!-- 日志查看对话框 -->
    <el-dialog v-model="logDialogVisible" title="同步日志" width="80%">
      <pre>{{ logContent }}</pre>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import skopeoApi from '../services/skopeoApi'

const loading = ref(false)
const result = ref(null)
const activeTab = ref('manual')
const fileList = ref([])
const selectedFile = ref(null)
const logDialogVisible = ref(false)
const logContent = ref('')

const syncForm = reactive({
  imageList: '',
  sourceRegistry: 'docker.io/library',
  destinationRegistry: '',
  srcCreds: '',
  destCreds: ''
})

const fileForm = reactive({
  sourceRegistry: 'docker.io/library',
  destinationRegistry: '',
  srcCreds: '',
  destCreds: ''
})

const handleFileChange = (file) => {
  selectedFile.value = file.raw
}

const syncImagesFromList = async () => {
  if (!syncForm.imageList || !syncForm.destinationRegistry) {
    ElMessage.warning('请输入镜像列表和目标仓库')
    return
  }

  loading.value = true
  result.value = null

  try {
    const images = syncForm.imageList.split('\n').filter(img => img.trim())
    const options = {
      sourceRegistry: syncForm.sourceRegistry,
      srcCreds: syncForm.srcCreds,
      destCreds: syncForm.destCreds
    }

    const response = await skopeoApi.syncImages(images, syncForm.destinationRegistry, options)
    result.value = {
      success: response.success,
      message: response.success ? '镜像同步成功' : '部分镜像同步失败',
      total: response.total,
      success_count: response.success_count,
      failed_count: response.failed_count,
      results: response.results,
      log_file: response.log_file
    }
    ElMessage.success('镜像同步请求已提交')
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

const syncImagesFromFile = async () => {
  if (!selectedFile.value || !fileForm.destinationRegistry) {
    ElMessage.warning('请选择文件和输入目标仓库')
    return
  }

  loading.value = true
  result.value = null

  try {
    const options = {
      sourceRegistry: fileForm.sourceRegistry,
      srcCreds: fileForm.srcCreds,
      destCreds: fileForm.destCreds
    }

    const response = await skopeoApi.syncImagesFromFile(selectedFile.value, fileForm.destinationRegistry, options)
    result.value = {
      success: response.success,
      message: response.success ? '镜像同步成功' : '部分镜像同步失败',
      total: response.total,
      success_count: response.success_count,
      failed_count: response.failed_count,
      results: response.results,
      log_file: response.log_file
    }
    ElMessage.success('镜像同步请求已提交')
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

const formatSyncResults = (results) => {
  return Object.entries(results).map(([image, success]) => ({
    image,
    success
  }))
}

const viewLogFile = async (logFile) => {
  try {
    const response = await skopeoApi.getLogFile(logFile)
    logContent.value = response
    logDialogVisible.value = true
  } catch (error) {
    ElMessage.error(`获取日志失败: ${error.message}`)
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

.sync-info h5 {
  margin: 15px 0 5px 0;
  color: #606266;
}

.sync-info p {
  margin: 5px 0;
}

.sync-details {
  margin-top: 15px;
}

.log-section {
  margin-top: 15px;
}

pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  background-color: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
  max-height: 400px;
  overflow-y: auto;
}
</style>
