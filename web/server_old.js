const express = require('express')
const cors = require('cors')
const { exec, spawn } = require('child_process')
const util = require('util')
const execPromise = util.promisify(exec)
const app = express()
const port = 8080

// 启用 CORS
app.use(cors())
// 解析 JSON 请求体
app.use(express.json())

// 执行skopeo命令的辅助函数
const executeSkopeo = async (command, args) => {
  try {
    const { stdout, stderr } = await execPromise(`skopeo ${command} ${args.join(' ')}`)
    if (stderr && !stderr.includes('warning')) {
      console.error(`Skopeo stderr: ${stderr}`)
    }
    return stdout
  } catch (error) {
    console.error(`Skopeo error: ${error.message}`)
    throw new Error(`执行skopeo命令失败: ${error.message}`)
  }
}

// 流式执行skopeo命令的辅助函数（用于长时间运行的操作）
const streamSkopeo = (command, args, res) => {
  const process = spawn('skopeo', [command, ...args])
  
  res.writeHead(200, {
    'Content-Type': 'text/plain; charset=utf-8',
    'Transfer-Encoding': 'chunked'
  })
  
  process.stdout.on('data', (data) => {
    res.write(data.toString())
  })
  
  process.stderr.on('data', (data) => {
    // 将错误信息也输出到响应中，但标记为错误
    res.write(`ERROR: ${data.toString()}`)
  })
  
  process.on('close', (code) => {
    if (code !== 0) {
      res.write(`\n进程退出，代码: ${code}`)
    }
    res.end()
  })
  
  process.on('error', (error) => {
    res.write(`ERROR: ${error.message}`)
    res.end()
  })
}

// 模拟 Skopeo API 端点

// 镜像检查
app.post('/api/inspect', (req, res) => {
  const { imageName, options } = req.body

  if (!imageName) {
    return res.status(400).json({ error: '镜像名称是必需的' })
  }

  // 模拟响应
  const mockResponse = options?.raw ? 
    `{"schemaVersion":2,"mediaType":"application/vnd.docker.distribution.manifest.v2+json","config":{"mediaType":"application/vnd.docker.container.image.v1+json","size":7023,"digest":"sha256:b5b2b2c501a9a5497b6c7d7d6b8d8b9c6f6e6f6g6h6i6j6k6l6m6n6o6p6q6r6s6t6u6v6w6x6y6z"},"layers":[{"mediaType":"application/vnd.docker.image.rootfs.diff.tar.gzip","size":1261441,"digest":"sha256:a3b4c5d6e7f8g9h0i1j2k3l4m5n6o7p8q9r0s1t2u3v4w5x6y7z8"}]}` :
    {
      "Name": imageName,
      "Tag": "latest",
      "Digest": "sha256:abcdef123456789",
      "RepoTags": ["latest", "v1.0", "v2.0"],
      "Created": "2023-06-15T10:30:00.000000000Z",
      "DockerVersion": "20.10.7",
      "Labels": {
        "maintainer": "example@example.com",
        "version": "1.0"
      },
      "Architecture": "amd64",
      "Os": "linux",
      "Layers": [
        "sha256:a3b4c5d6e7f8g9h0i1j2k3l4m5n6o7p8q9r0s1t2u3v4w5x6y7z8"
      ],
      "Env": [
        "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
        "TERM=xterm"
      ]
    }

  res.json(mockResponse)
})

// 镜像复制
app.post('/api/copy', (req, res) => {
  const { sourceImage, destinationImage, options } = req.body

  if (!sourceImage || !destinationImage) {
    return res.status(400).json({ error: '源镜像和目标镜像都是必需的' })
  }

  // 模拟成功响应
  res.json({
    success: true,
    message: `成功将镜像从 ${sourceImage} 复制到 ${destinationImage}`,
    digest: "sha256:abcdef123456789"
  })
})

// 列出标签
app.post('/api/list-tags', (req, res) => {
  const { repository } = req.body

  if (!repository) {
    return res.status(400).json({ error: '仓库地址是必需的' })
  }

  // 模拟标签列表
  res.json({
    repository: repository,
    tags: ["latest", "v1.0", "v1.1", "v2.0", "stable", "beta"]
  })
})

// 镜像同步
app.post('/api/sync', (req, res) => {
  const { source, destination, options } = req.body

  if (!source || !destination) {
    return res.status(400).json({ error: '源和目标都是必需的' })
  }

  // 模拟同步结果
  res.json({
    success: true,
    imagesCount: 15,
    sourcesCount: 3
  })
})

// 镜像删除
app.post('/api/delete', (req, res) => {
  const { imageName } = req.body

  if (!imageName) {
    return res.status(400).json({ error: '镜像名称是必需的' })
  }

  // 模拟成功响应
  res.json({
    success: true,
    message: `成功删除镜像 ${imageName}`
  })
})

// 代理 API - 初始化
app.post('/api/proxy/initialize', (req, res) => {
  res.json("0.2.8")
})

// 代理 API - 打开镜像
app.post('/api/proxy/open-image', (req, res) => {
  const { imageName } = req.body

  if (!imageName) {
    return res.status(400).json({ error: '镜像名称是必需的' })
  }

  // 模拟返回镜像 ID
  res.json(12345)
})

// 代理 API - 获取清单
app.post('/api/proxy/get-manifest', (req, res) => {
  const { imageId } = req.body

  if (!imageId) {
    return res.status(400).json({ error: '镜像 ID 是必需的' })
  }

  // 模拟清单摘要
  res.json("sha256:abcdef123456789")
})

// 代理 API - 获取配置
app.post('/api/proxy/get-config', (req, res) => {
  const { imageId } = req.body

  if (!imageId) {
    return res.status(400).json({ error: '镜像 ID 是必需的' })
  }

  // 模拟配置
  res.json({
    "config": {
      "Env": ["PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"],
      "Cmd": ["/bin/sh"],
      "ExposedPorts": {"8080/tcp": {}}
    }
  })
})

// 代理 API - 获取数据块
app.post('/api/proxy/get-blob', (req, res) => {
  const { imageId, digest, size } = req.body

  if (!imageId || !digest) {
    return res.status(400).json({ error: '镜像 ID 和摘要都是必需的' })
  }

  // 模拟数据块大小
  res.json(size || 1024)
})

// 启动服务器
app.listen(port, () => {
  console.log(`Skopeo API 模拟服务器运行在 http://localhost:${port}`)
})
