<template>
  <div class="delete-tab">
    <el-card class="form-card">
      <template #header>
        <span>镜像删除</span>
      </template>

      <el-form :model="deleteForm" label-width="120px">
        <el-form-item label="镜像名称">
          <el-input 
            v-model="deleteForm.imageName" 
            placeholder="例如: docker://registry.example.com/image:tag"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="danger" @click="deleteImage" :loading="loading">
            <el-icon><Delete /></el-icon>
            删除镜像
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="result" class="result-card">
      <template #header>
        <span>删除结果</span>
      </template>

      <el-alert 
        :title="result.success ? '删除成功' : '删除失败'"
        :type="result.success ? 'success' : 'error'"
        :description="result.message"
        show-icon
        :closable="false"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete } from '@element-plus/icons-vue'
import skopeoApi from '../services/skopeoApi'

const loading = ref(false)
const result = ref(null)

const deleteForm = reactive({
  imageName: ''
})

const deleteImage = async () => {
  if (!deleteForm.imageName) {
    ElMessage.warning('请输入镜像名称')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除镜像 "${deleteForm.imageName}" 吗？此操作不可逆！`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
  } catch {
    // 用户取消删除
    return
  }

  loading.value = true
  result.value = null

  try {
    await skopeoApi.deleteImage(deleteForm.imageName)
    result.value = {
      success: true,
      message: `成功删除镜像 ${deleteForm.imageName}`
    }
    ElMessage.success('镜像删除成功')
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
.delete-tab {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-card, .result-card {
  margin-bottom: 20px;
}
</style>
