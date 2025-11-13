import axios from 'axios'

// 创建 axios 实例
const api = axios.create({
  baseURL: '/api',
  timeout: 120000, // 增加到120秒，适应长时间运行的镜像列表操作
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
      // 对于大型仓库，使用流式处理
      if (options.useStream) {
        const response = await api.post('/list-tags', {
          repository,
          ...options
        }, {
          responseType: 'text',
          timeout: 300000 // 流式请求设置更长的超时时间，5分钟
        })
        console.log('[API流式响应] 类型:', typeof response.data)
        console.log('[API流式响应] 内容:', response.data.substring(0, 200) + '...')
        return response.data
      } else {
        const response = await api.post('/list-tags', {
          repository,
          ...options
        })
        // 确保返回的是解析后的JSON对象，而不是字符串
        if (typeof response.data === 'string') {
          try {
            return JSON.parse(response.data)
          } catch (e) {
            return response.data
          }
        }
        
        return response.data
      }
    } catch (error) {
      console.error('[API错误]', error)
      throw new Error(`列出标签失败: ${error.message}`)
    }
  },
  
  // 获取标签数量
  async getTagCount(repository) {
    try {
      const response = await api.post('/list-tags', {
        repository,
        countOnly: true
      })
      return response.data
    } catch (error) {
      throw new Error(`获取标签数量失败: ${error.message}`)
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
