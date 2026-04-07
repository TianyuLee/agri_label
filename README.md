# 标注系统

## 功能介绍

一个简洁的数据标注系统，支持：

1. **用户注册登录**：使用手机号（11位）和密码注册和登录
2. **三列式任务界面**：
   - 第一列：标注任务集合
   - 第二列：任务列表
   - 第三列：标注详情
3. **Rubric标注**：对query进行多维度评估，支持勾选/取消
4. **任务完成标记**：可将任务标记为已完成

## 技术栈

- 前端：Vue 3 + Vue Router + Axios
- 后端：Python + FastAPI + SQLite3

## 目录结构

```
.
├── backend/           # 后端代码
│   ├── main.py        # FastAPI主入口
│   ├── database.py    # 数据库初始化
│   ├── models.py      # Pydantic模型
│   └── requirements.txt
├── frontend/          # 前端代码
│   ├── src/
│   │   ├── views/     # 页面组件
│   │   ├── router/    # 路由配置
│   │   ├── App.vue
│   │   └── main.js
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
└── README.md
```

## 启动步骤

### 1. 启动后端

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

后端服务将在 `http://localhost:8000` 启动。

### 2. 启动前端

新开一个终端：

```bash
cd frontend
npm install
npm run dev
```

前端服务将在 `http://localhost:5173` 启动。

### 3. 访问系统

在浏览器中打开 `http://localhost:5173`

## 使用说明

1. 注册账号：使用11位手机号和6位以上密码注册
2. 登录系统
3. 点击第一列的任务集合，第二列显示该集合下的任务
4. 点击第二列的任务，第三列显示标注详情
5. 在第三列勾选/取消勾选rubric
6. 点击"标记为已完成"完成任务
