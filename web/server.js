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

// Skopeo API 端点

// 镜像检查
app.post('/api/inspect', async (req, res) => {
  const { imageName, options } = req.body

  if (!imageName) {
    return res.status(400).json({ error: '镜像名称是必需的' })
  }

  try {
    // 构建skopeo inspect命令参数
    const args = [imageName]

    // 添加选项参数
    if (options?.raw) {
      args.push('--raw')
    }

    if (options?.config) {
      args.push('--config')
    }

    // 执行skopeo inspect命令
    const output = await executeSkopeo('inspect', args)

    // 如果是原始输出，直接返回字符串
    if (options?.raw) {
      res.type('text/plain').send(output.trim())
    } else {
      // 尝试解析JSON输出
      try {
        const jsonData = JSON.parse(output.trim())
        res.json(jsonData)
      } catch (parseError) {
        // 如果解析失败，返回原始文本
        res.type('text/plain').send(output.trim())
      }
    }
  } catch (error) {
    res.status(500).json({ error: error.message })
  }
})

// 镜像复制
app.post('/api/copy', async (req, res) => {
  const { sourceImage, destinationImage, options } = req.body

  if (!sourceImage || !destinationImage) {
    return res.status(400).json({ error: '源镜像和目标镜像都是必需的' })
  }

  try {
    // 构建skopeo copy命令参数
    const args = [sourceImage, destinationImage]

    // 添加选项参数
    if (options?.all) {
      args.unshift('--all')
    }

    if (options?.quiet) {
      args.unshift('--quiet')
    }

    // 执行skopeo copy命令
    const output = await executeSkopeo('copy', args)

    // 返回成功结果
    res.json({
      success: true,
      message: `成功将镜像从 ${sourceImage} 复制到 ${destinationImage}`,
      output: output.trim()
    })
  } catch (error) {
    res.status(500).json({ error: error.message })
  }
})

// 列出标签
app.post('/api/list-tags', async (req, res) => {
  const { repository, options } = req.body

  if (!repository) {
    return res.status(400).json({ error: '仓库地址是必需的' })
  }

  try {
    // 构建skopeo list-tags命令参数
    const args = [repository]

    // 执行skopeo list-tags命令
    const output = await executeSkopeo('list-tags', args)

    // 尝试解析JSON输出
    try {
      const jsonData = JSON.parse(output.trim())
      res.json(jsonData)
    } catch (parseError) {
      // 如果解析失败，返回原始文本
      res.type('text/plain').send(output.trim())
    }
  } catch (error) {
    res.status(500).json({ error: error.message })
  }
})

// 镜像同步
app.post('/api/sync', async (req, res) => {
  const { source, destination, options } = req.body

  if (!source || !destination) {
    return res.status(400).json({ error: '源和目标都是必需的' })
  }

  try {
    // 构建skopeo sync命令参数
    const args = [source, destination]

    // 添加选项参数
    if (options?.all) {
      args.unshift('--all')
    }

    if (options?.scoped) {
      args.unshift('--scoped')
    }

    // 执行skopeo sync命令
    const output = await executeSkopeo('sync', args)

    // 返回同步结果
    res.json({
      success: true,
      output: output.trim()
    })
  } catch (error) {
    res.status(500).json({ error: error.message })
  }
})

// 镜像删除
app.post('/api/delete', async (req, res) => {
  const { imageName, options } = req.body

  if (!imageName) {
    return res.status(400).json({ error: '镜像名称是必需的' })
  }

  try {
    // 构建skopeo delete命令参数
    const args = [imageName]

    // 执行skopeo delete命令
    const output = await executeSkopeo('delete', args)

    // 返回成功结果
    res.json({
      success: true,
      message: `成功删除镜像 ${imageName}`,
      output: output.trim()
    })
  } catch (error) {
    res.status(500).json({ error: error.message })
  }
})

// 代理 API - 初始化
app.post('/api/proxy/initialize', (req, res) => {
  // 代理API暂时保留模拟数据，因为skopeo没有直接的代理初始化命令
  res.json("0.2.8")
})

// 代理 API - 打开镜像
app.post('/api/proxy/open-image', (req, res) => {
  const { imageName } = req.body

  if (!imageName) {
    return res.status(400).json({ error: '镜像名称是必需的' })
  }

  // 代理API暂时保留模拟数据
  res.json(12345)
})

// 代理 API - 获取清单
app.post('/api/proxy/get-manifest', (req, res) => {
  const { imageId } = req.body

  if (!imageId) {
    return res.status(400).json({ error: '镜像 ID 是必需的' })
  }

  // 代理API暂时保留模拟数据
  res.json("sha256:abcdef123456789")
})

// 代理 API - 获取配置
app.post('/api/proxy/get-config', (req, res) => {
  const { imageId } = req.body

  if (!imageId) {
    return res.status(400).json({ error: '镜像 ID 是必需的' })
  }

  // 代理API暂时保留模拟数据
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

  // 代理API暂时保留模拟数据
  res.json(size || 1024)
})

// 启动服务器
app.listen(port, () => {
  console.log(`Skopeo API 服务器运行在 http://localhost:${port}`)
})
