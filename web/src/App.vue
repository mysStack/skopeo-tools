<template>
  <div class="container">
    <el-container>
      <el-header class="header">
        <h1>Skopeo Web UI</h1>
      </el-header>
      <el-main>
        <el-tabs v-model="activeTab" type="card">
          <el-tab-pane label="镜像检查" name="inspect">
            <inspect-tab />
          </el-tab-pane>
          <el-tab-pane label="镜像复制" name="copy">
            <copy-tab />
          </el-tab-pane>
          <el-tab-pane label="镜像列表" name="list">
            <list-tab />
          </el-tab-pane>
          <el-tab-pane label="镜像同步" name="sync">
            <sync-tab />
          </el-tab-pane>
          <el-tab-pane label="镜像删除" name="delete">
            <delete-tab />
          </el-tab-pane>
        </el-tabs>
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import InspectTab from './components/InspectTab.vue'
import CopyTab from './components/CopyTab.vue'
import ListTab from './components/ListTab.vue'
import SyncTab from './components/SyncTab.vue'
import DeleteTab from './components/DeleteTab.vue'

const activeTab = ref('inspect')
</script>

<style scoped>
.container {
  max-width: 1200px;
  margin: 0 auto;
}

.header {
  background-color: #409EFF;
  color: white;
  display: flex;
  align-items: center;
  padding: 0 20px;
}

.header h1 {
  margin: 0;
  font-size: 24px;
}

.el-main {
  padding: 20px;
}
</style>
