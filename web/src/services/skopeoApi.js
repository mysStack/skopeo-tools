import axios from 'axios'

// 创建 axios 实例
const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 响应拦截器
api.interceptors.response.use(
  response => response,
  error => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export default {
  // 镜像检查
  async inspectImage(imageName, options = {}) {
    try {
      const response = await api.post('/inspect', { 
        imageName,
        ...options 
      })
      return response.data
    } catch (error) {
      throw new Error(`检查镜像失败: ${error.message}`)
    }
  },

  // 镜像复制
  async copyImage(sourceImage, destinationImage, options = {}) {
    try {
      const response = await api.post('/copy', {
        sourceImage,
        destinationImage,
        ...options
      })
      return response.data
    } catch (error) {
      throw new Error(`复制镜像失败: ${error.message}`)
    }
  },

  // 列出镜像标签
  async listTags(repository, options = {}) {
    try {
      const response = await api.post('/list-tags', {
        repository,
        ...options
      })
      return response.data
    } catch (error) {
      throw new Error(`列出标签失败: ${error.message}`)
    }
  },

  // 同步镜像
  async syncImages(source, destination, options = {}) {
    try {
      const response = await api.post('/sync', {
        source,
        destination,
        ...options
      })
      return response.data
    } catch (error) {
      throw new Error(`同步镜像失败: ${error.message}`)
    }
  },

  // 删除镜像
  async deleteImage(imageName, options = {}) {
    try {
      const response = await api.post('/delete', {
        imageName,
        ...options
      })
      return response.data
    } catch (error) {
      throw new Error(`删除镜像失败: ${error.message}`)
    }
  },

  // 代理 API - 初始化
  async proxyInitialize() {
    try {
      const response = await api.post('/proxy/initialize', {})
      return response.data
    } catch (error) {
      throw new Error(`初始化代理失败: ${error.message}`)
    }
  },

  // 代理 API - 打开镜像
  async proxyOpenImage(imageName) {
    try {
      const response = await api.post('/proxy/open-image', { imageName })
      return response.data
    } catch (error) {
      throw new Error(`打开镜像失败: ${error.message}`)
    }
  },

  // 代理 API - 获取清单
  async proxyGetManifest(imageId) {
    try {
      const response = await api.post('/proxy/get-manifest', { imageId })
      return response.data
    } catch (error) {
      throw new Error(`获取清单失败: ${error.message}`)
    }
  },

  // 代理 API - 获取配置
  async proxyGetConfig(imageId) {
    try {
      const response = await api.post('/proxy/get-config', { imageId })
      return response.data
    } catch (error) {
      throw new Error(`获取配置失败: ${error.message}`)
    }
  },

  // 代理 API - 获取数据块
  async proxyGetBlob(imageId, digest, size) {
    try {
      const response = await api.post('/proxy/get-blob', { 
        imageId, 
        digest, 
        size 
      })
      return response.data
    } catch (error) {
      throw new Error(`获取数据块失败: ${error.message}`)
    }
  }
}
