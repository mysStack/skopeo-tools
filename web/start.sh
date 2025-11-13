#!/bin/bash

# 安装依赖
echo "安装前端依赖..."
npm install

# 安装服务器依赖
echo "安装服务器依赖..."
npm install express cors

# 启动前端和服务器
echo "启动应用..."
npm run dev
