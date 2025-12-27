# MongoDB Atlas 快速设置指南 🗄️

## 🚀 5 分钟获取免费 MongoDB 数据库

### 步骤 1：注册 MongoDB Atlas

1. 访问：**https://www.mongodb.com/cloud/atlas/register**
2. 使用 Google 账号快速注册（或邮箱注册）
3. 选择 **FREE** 计划（永久免费！）

---

### 步骤 2：创建集群

1. 选择云服务商：**AWS**（默认即可）
2. 选择区域：**Singapore (ap-southeast-1)** 或离你最近的地区
3. 集群名称：保持默认或改为 `CheerCloud`
4. 点击 **Create Deployment**
5. 等待 1-3 分钟

---

### 步骤 3：创建数据库用户

创建完成后会弹出：

1. **Username**: 输入 `cheercloud`（或你喜欢的用户名）
2. **Password**: 点击 **Autogenerate Secure Password**，然后**复制密码！**
3. 点击 **Create Database User**

⚠️ **重要：保存好密码！**

---

### 步骤 4：设置网络访问

1. 在 "Network Access" 页面
2. 点击 **Add IP Address**
3. 选择 **Allow Access from Anywhere** (0.0.0.0/0)
4. 点击 **Confirm**

---

### 步骤 5：获取连接字符串

1. 返回 **Database** 页面
2. 点击 **Connect**
3. 选择 **Drivers**
4. 选择 **Node.js** 和最新版本
5. 复制连接字符串，类似：
   ```
   mongodb+srv://cheercloud:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```

6. **替换 `<password>` 为你刚才复制的密码**

---

### 步骤 6：更新 backend/.env

将获取到的连接字符串添加到 `backend/.env`：

```env
MONGO=mongodb+srv://cheercloud:你的密码@cluster0.xxxxx.mongodb.net/cheercloud?retryWrites=true&w=majority
```

⚠️ **注意**：
- 确保替换 `<password>` 为实际密码
- 在末尾添加数据库名 `/cheercloud`

---

### ✅ 完成！

保存文件后，重启后端服务器，MongoDB 就配置好了！

