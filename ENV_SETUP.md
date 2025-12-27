# 环境变量配置指南 🔧

## ⚠️ 重要：你的项目无法运行是因为缺少环境变量配置！

请按照以下步骤创建 `.env` 文件：

---

## 📁 第一步：创建 `client/.env` 文件

在 `client` 文件夹下创建一个名为 `.env` 的文件，填入以下内容：

```env
# Clerk Authentication (从 https://dashboard.clerk.com/ 获取)
VITE_CLERK_PUBLISHABLE_KEY=你的-clerk-publishable-key

# ImageKit (从 https://imagekit.io/dashboard/ 获取)
VITE_IMAGE_KIT_ENDPOINT=你的-imagekit-endpoint
VITE_IMAGE_KIT_PUBLIC_KEY=你的-imagekit-public-key

# Google Gemini API (从 https://makersuite.google.com/app/apikey 获取)
VITE_GEMINI_PUBLIC_KEY=你的-google-gemini-api-key

# Backend API URL
VITE_API_URL=http://localhost:3000
```

---

## 📁 第二步：创建 `backend/.env` 文件

在 `backend` 文件夹下创建一个名为 `.env` 的文件，填入以下内容：

```env
# ImageKit (从 https://imagekit.io/dashboard/ 获取)
IMAGE_KIT_ENDPOINT=你的-imagekit-endpoint
IMAGE_KIT_PUBLIC_KEY=你的-imagekit-public-key
IMAGE_KIT_PRIVATE_KEY=你的-imagekit-private-key

# Frontend URL
CLIENT_URL=http://localhost:5173

# MongoDB (从 https://www.mongodb.com/cloud/atlas 获取)
MONGO=你的-mongodb-connection-uri

# Clerk Authentication (从 https://dashboard.clerk.com/ 获取)
CLERK_PUBLISHABLE_KEY=你的-clerk-publishable-key
```

---

## 🔑 如何获取各个 API Key

### 1. **Google Gemini API Key** (最重要！)
- 访问：https://makersuite.google.com/app/apikey
- 登录 Google 账号
- 点击 "Create API Key"
- 复制生成的 key 到 `VITE_GEMINI_PUBLIC_KEY`

### 2. **Clerk Authentication**
- 访问：https://dashboard.clerk.com/
- 注册/登录账号
- 创建新应用
- 在 API Keys 页面找到 `Publishable Key`
- 复制到两个 env 文件中

### 3. **MongoDB**
- 访问：https://www.mongodb.com/cloud/atlas
- 注册/登录账号
- 创建免费集群
- 点击 "Connect" → "Connect your application"
- 复制连接字符串到 `MONGO`

### 4. **ImageKit** (可选，如果不需要图片上传功能可以暂时跳过)
- 访问：https://imagekit.io/dashboard/
- 注册/登录账号
- 在 Dashboard 找到 API Keys
- 复制相关 keys

---

## ✅ 验证配置

创建好 `.env` 文件后：

1. 重启开发服务器
2. 检查浏览器控制台是否有错误
3. 尝试发送消息给 AI

---

## 📝 快速测试配置（仅需 Gemini API）

如果你只想快速测试 AI 功能，最少只需要配置：

**client/.env**
```env
VITE_GEMINI_PUBLIC_KEY=你的-gemini-api-key
VITE_API_URL=http://localhost:3000
```

但这样会缺少用户认证和数据库功能。

