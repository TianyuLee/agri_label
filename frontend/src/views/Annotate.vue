<template>
  <div class="annotate-container">
    <header class="header">
      <div class="header-left">
        <div class="header-title">
          标注系统
          <span v-if="isRoot" class="root-badge">ROOT</span>
        </div>
        <!-- Root 用户切换视图 -->
        <div v-if="isRoot" class="view-switcher">
          <label>当前视图：</label>
          <select v-model="viewMode" @change="onViewModeChange">
            <option value="self">管理员视图</option>
            <option value="user">用户视图</option>
          </select>
          <select v-if="viewMode === 'user'" v-model="selectedUserId" @change="onUserChange">
            <option v-for="user in allUsers" :key="user.id" :value="user.id">
              {{ user.phone }} {{ user.is_root ? '(root)' : '' }}
            </option>
          </select>
          <button v-if="viewMode === 'user'" class="manage-btn" @click="showTaskAssignModal">
            管理任务分配
          </button>
        </div>
      </div>
      <div class="header-user">
        <span>{{ phone }}</span>
        <button class="logout-btn" @click="logout">退出</button>
      </div>
    </header>

    <div class="main-content">
      <!-- 第一列：任务集合 -->
      <div class="column column-1">
        <div class="column-header">
          <span>任务集合</span>
          <div v-if="isRoot" class="header-actions">
            <button class="import-btn" @click="showBatchImportModal" title="批量导入">
              📥
            </button>
            <button class="add-btn" @click="showAddTaskSetModal">+</button>
          </div>
        </div>
        <div class="column-content">
          <div
            v-for="set in taskSets"
            :key="set.id"
            class="task-set-item"
            :class="{ active: selectedSetId === set.id }"
            @click="selectTaskSet(set.id)"
          >
            <div class="task-set-info">
              <div class="task-set-name">{{ set.name }}</div>
              <div class="task-set-desc">{{ set.description }}</div>
            </div>
            <div v-if="isRoot" class="item-actions" @click.stop>
              <button class="action-btn edit" @click="editTaskSet(set)">✎</button>
              <button class="action-btn delete" @click="deleteTaskSet(set.id)">×</button>
            </div>
          </div>
        </div>
      </div>

      <!-- 第二列：任务列表 -->
      <div class="column column-2">
        <div class="column-header">
          <span>任务列表</span>
          <button v-if="isRoot && selectedSetId" class="add-btn" @click="showAddTaskModal">+</button>
        </div>
        <div class="column-content">
          <div
            v-for="task in tasks"
            :key="task.id"
            class="task-item"
            :class="{ active: selectedTaskId === task.id, completed: task.completed }"
            @click="selectTask(task.id)"
          >
            <div class="task-query">{{ task.query }}</div>
            <div class="task-actions">
              <div v-if="task.completed" class="completed-badge">已完成</div>
              <div v-if="isRoot" class="item-actions" @click.stop>
                <button class="action-btn edit" @click="editTask(task)">✎</button>
                <button class="action-btn delete" @click="deleteTask(task.id)">×</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 第三列：标注详情 -->
      <div class="column column-3">
        <div class="column-header">
          <span>标注详情</span>
        </div>
        <div class="column-content">
          <div v-if="currentTask" class="annotation-panel">
            <div class="query-title">{{ currentTask.query }}</div>

            <div class="rubrics-list">
              <div
                v-for="rubric in currentTask.rubrics"
                :key="rubric.id"
                class="rubric-item-v2"
                :class="{ selected: rubric.selected, editing: rubric.editingFieldV2, 'negative-score': parseRubricV2(rubric.content).score < 0 }"
              >
                  <!-- 编辑模式 -->
                  <template v-if="rubric.editingFieldV2">
                    <!-- 第一行：标题编辑 -->
                    <div class="rubric-v2-row">
                      <div class="checkbox" :class="{ checked: rubric.selected }" @click="toggleRubric(rubric)">
                        <span v-if="rubric.selected">✓</span>
                      </div>
                      <div class="rubric-v2-title-wrapper">
                        <textarea
                          v-if="rubric.editingFieldV2 === 'title'"
                          v-model="rubric.editTitleV2"
                          class="rubric-v2-title-input"
                          placeholder="请输入标题"
                          rows="2"
                          @keyup.ctrl.enter="saveRubricV2Field(rubric)"
                        ></textarea>
                        <div v-else class="rubric-v2-title readonly">{{ parseRubricV2(rubric.content).title || '点击添加标题' }}</div>
                      </div>
                      <div class="edit-actions">
                        <button class="btn-save" @click="saveRubricV2Field(rubric)">保存</button>
                        <button class="btn-cancel" @click="cancelEditRubricV2(rubric)">取消</button>
                      </div>
                    </div>

                    <!-- 第二行：维度 + 分数 -->
                    <div class="rubric-v2-row meta-row">
                      <div class="rubric-v2-dimension-wrapper" v-if="rubric.editingFieldV2 === 'dimension'">
                        <input
                          v-model="rubric.editDimensionV2"
                          class="rubric-v2-dimension-input"
                          placeholder="请输入维度"
                          @keyup.enter="saveRubricV2Field(rubric)"
                        />
                      </div>
                      <div class="rubric-v2-dimension-wrapper" v-else @click="startEditRubricV2Field(rubric, 'dimension')">
                        <div class="rubric-v2-dimension">
                          <span class="meta-label">维度:</span>
                          <span class="meta-value">{{ parseRubricV2(rubric.content).dimension || '点击添加' }}</span>
                        </div>
                      </div>

                      <div class="rubric-v2-score-wrapper" v-if="rubric.editingFieldV2 === 'score'">
                        <input
                          v-model.number="rubric.editScoreV2"
                          type="number"
                          class="rubric-v2-score-input"
                          placeholder="分数"
                          @keyup.enter="saveRubricV2Field(rubric)"
                        />
                      </div>
                      <div class="rubric-v2-score-wrapper" v-else @click="startEditRubricV2Field(rubric, 'score')">
                        <div class="rubric-v2-score">
                          <span class="meta-label">分数:</span>
                          <span class="meta-value">{{ parseRubricV2(rubric.content).score !== null ? parseRubricV2(rubric.content).score : '点击添加' }}</span>
                        </div>
                      </div>
                    </div>
                  </template>

                  <!-- 非编辑模式 -->
                  <template v-else>
                    <!-- 第一行：标题 + 操作按钮 -->
                    <div class="rubric-v2-row">
                      <div class="checkbox" :class="{ checked: rubric.selected }" @click="toggleRubric(rubric)">
                        <span v-if="rubric.selected">✓</span>
                      </div>
                      <div class="rubric-v2-title-wrapper" @click="startEditRubricV2Field(rubric, 'title')">
                        <div class="rubric-v2-title">
                          {{ parseRubricV2(rubric.content).title || '点击添加标题' }}
                      </div>
                    </div>
                    <div class="rubric-v2-actions">
                      <div class="rubric-actions">
                        <button class="action-btn edit small" @click.stop="startEditRubricV2Field(rubric, 'title')" title="编辑">✎</button>
                        <button class="action-btn delete small" @click.stop="deleteRubric(rubric.id)" title="删除">×</button>
                      </div>
                    </div>
                  </div>

                  <!-- 第二行：维度 + 分数 -->
                  <div class="rubric-v2-row meta-row">
                    <div class="rubric-v2-dimension-wrapper" @click="startEditRubricV2Field(rubric, 'dimension')">
                      <div class="rubric-v2-dimension">
                        <span class="meta-label">维度:</span>
                        <span class="meta-value">{{ parseRubricV2(rubric.content).dimension || '点击添加' }}</span>
                      </div>
                    </div>
                    <div class="rubric-v2-score-wrapper" @click="startEditRubricV2Field(rubric, 'score')">
                      <div class="rubric-v2-score">
                        <span class="meta-label">分数:</span>
                        <span class="meta-value">{{ parseRubricV2(rubric.content).score !== null ? parseRubricV2(rubric.content).score : '点击添加' }}</span>
                      </div>
                    </div>
                  </div>
                  </template>
              </div>

              <div v-if="selectedTaskId" class="add-rubric-item" @click="showAddRubricModal">
                <span class="add-icon">+</span>
                <span class="add-text">添加Rubric</span>
              </div>
            </div>

            <!-- 标准答案区域 -->
            <div class="reference-answers-section" v-if="currentTask.reference_answers && currentTask.reference_answers.length > 0 || selectedTaskId">
              <div class="section-divider">
                <span class="divider-text">标准答案</span>
              </div>
              <div class="reference-answers-list">
                <div
                  v-for="answer in currentTask.reference_answers"
                  :key="answer.id"
                  class="reference-answer-item"
                  :class="{ editing: answer.isEditing }"
                >
                  <!-- 编辑模式 -->
                  <template v-if="answer.isEditing">
                    <textarea
                      v-model="answer.editContent"
                      class="reference-answer-input"
                      placeholder="请输入标准答案内容"
                      rows="4"
                    ></textarea>
                    <div class="edit-actions-inline">
                      <button class="btn-save" @click="saveReferenceAnswerInline(answer)">保存</button>
                      <button class="btn-cancel" @click="cancelEditReferenceAnswer(answer)">取消</button>
                    </div>
                  </template>
                  <!-- 非编辑模式 -->
                  <template v-else>
                    <div class="reference-answer-content" @click="startEditReferenceAnswer(answer)">{{ answer.content }}</div>
                    <div class="reference-answer-actions">
                      <button class="action-btn edit small" @click.stop="startEditReferenceAnswer(answer)" title="编辑">✎</button>
                      <button class="action-btn delete small" @click.stop="deleteReferenceAnswer(answer.id)" title="删除">×</button>
                    </div>
                  </template>
                </div>
              </div>
              <div v-if="selectedTaskId" class="add-reference-answer-item" @click="showAddReferenceAnswerModal">
                <span class="add-icon">+</span>
                <span class="add-text">添加标准答案</span>
              </div>
            </div>

            <div class="action-buttons">
              <button
                class="complete-btn"
                :class="{ completed: currentTask.completed }"
                @click="toggleComplete"
              >
                {{ currentTask.completed ? '标记为未完成' : '标记为已完成' }}
              </button>
            </div>
          </div>

          <div v-else class="empty-state">
            <p v-if="viewMode === 'user' && !selectedUserId">请先选择一个用户</p>
            <p v-else>请从左侧选择一个任务开始标注</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 通用 Modal 弹窗 -->
    <div v-if="showModal" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <h3>{{ modalTitle }}</h3>
        <div class="modal-body">
          <div v-for="(field, index) in modalFields" :key="index" class="modal-field">
            <label>{{ field.label }}</label>
            <input
              v-if="field.type === 'text' || field.type === 'number'"
              v-model="field.value"
              :type="field.type"
              :placeholder="field.placeholder"
            />
            <textarea
              v-if="field.type === 'textarea'"
              v-model="field.value"
              :placeholder="field.placeholder"
              rows="4"
            ></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="closeModal">取消</button>
          <button class="btn-confirm" @click="confirmModal">确定</button>
        </div>
      </div>
    </div>

    <!-- 全屏编辑 Modal 弹窗 -->
    <div v-if="showFullscreenModal" class="modal-overlay fullscreen" @click="closeFullscreenModal">
      <div class="modal-content fullscreen" @click.stop>
        <div class="fullscreen-header">
          <h3>{{ fullscreenModalTitle }}</h3>
          <button class="btn-close" @click="closeFullscreenModal">✕</button>
        </div>
        <div class="fullscreen-body">
          <textarea
            v-model="fullscreenModalContent"
            :placeholder="fullscreenModalPlaceholder"
          ></textarea>
        </div>
        <div class="fullscreen-footer">
          <button class="btn-cancel" @click="closeFullscreenModal">取消</button>
          <button class="btn-confirm" @click="confirmFullscreenModal">确定</button>
        </div>
      </div>
    </div>

    <!-- 批量导入弹窗 -->
    <div v-if="showImportModal" class="modal-overlay" @click="closeImportModal">
      <div class="modal-content large" @click.stop>
        <h3>批量导入任务</h3>
        <div class="import-body">
          <div class="import-section">
            <label class="file-input-label">
              <input
                type="file"
                accept=".json"
                @change="handleFileSelect"
                ref="fileInput"
                style="display: none"
              />
              <span class="file-input-btn">选择 JSON 文件</span>
              <span class="file-name">{{ importFile?.name || '未选择文件' }}</span>
            </label>
            <div class="import-hint">
              <p>JSON 格式要求（rubric_output.json 格式）：</p>
              <pre style="background: #f5f5f5; padding: 12px; border-radius: 4px; overflow-x: auto; font-size: 12px;">
[
  {
    "user_name": "18222611632",
    "collection_name": "20260407",
    "prompt": "柑橘得了黄龙病怎么治疗",
    "rubrics": [
      { "criterion": "明确说明柑橘黄龙病目前无特效治愈药", "axis": "", "point": 5 },
      { "criterion": "建议尽快进行田间诊断与实验室检测", "axis": "", "point": 3 }
    ],
    "answers": ["标准答案内容..."]
  }
]</pre>
              <p class="hint-note">注：请使用UTF-8编码的JSON文件。每个任务通过 user_name + collection_name + prompt 定位，rubrics 为对象数组（含 criterion/axis/point），answers 为字符串数组。</p>
            </div>
          </div>

          <div v-if="importRubrics.length > 0 || importAnswers.length > 0" class="import-preview">
            <h4>预览 ({{ importRubrics.length }} 个 rubric, {{ importAnswers.length }} 个标准答案)</h4>
            <div class="preview-table-container">
              <table class="preview-table">
                <thead>
                  <tr>
                    <th>手机号</th>
                    <th>任务集合</th>
                    <th>任务名称</th>
                    <th>Rubric</th>
                    <th>维度</th>
                    <th>分数</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(item, index) in importPreview.slice(0, 10)" :key="index">
                    <td>{{ item.phone }}</td>
                    <td>{{ item.taskSetName }}</td>
                    <td>{{ item.taskName }}</td>
                    <td :title="item.rubric">{{ item.rubric.slice(0, 30) }}{{ item.rubric.length > 30 ? '...' : '' }}</td>
                    <td>{{ item.dimension || '-' }}</td>
                    <td>{{ item.score }}</td>
                  </tr>
                  <tr v-if="importPreview.length > 10">
                    <td colspan="6" class="more-rows">... 还有 {{ importPreview.length - 10 }} 条记录</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div v-if="importLoading" class="import-progress">
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: (importProgress.current / importProgress.total * 100) + '%' }"></div>
            </div>
            <span class="progress-text">{{ importProgress.current }} / {{ importProgress.total }}</span>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="closeImportModal" :disabled="importLoading">关闭</button>
          <button
            class="btn-confirm"
            @click="confirmImport"
            :disabled="(importRubrics.length === 0 && importAnswers.length === 0) || importLoading"
          >
            {{ importLoading ? '导入中...' : '确认导入' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 任务分配管理弹窗 -->
    <div v-if="showAssignModal" class="modal-overlay" @click="closeAssignModal">
      <div class="modal-content large" @click.stop>
        <h3>任务分配管理 - {{ getSelectedUserName() }}</h3>
        <div class="assign-body">
          <div class="assign-section">
            <h4>已分配的任务</h4>
            <div class="task-list">
              <div v-for="task in assignedTasks" :key="task.id" class="assign-task-item">
                <span class="task-set-tag">{{ task.task_set_name }}</span>
                <span class="task-query">{{ task.query }}</span>
                <button class="btn-remove" @click="unassignTask(task.id)">移除</button>
              </div>
              <div v-if="assignedTasks.length === 0" class="empty-hint">暂无分配任务</div>
            </div>
          </div>
          <div class="assign-section">
            <h4>未分配的任务</h4>
            <div class="task-list">
              <div v-for="task in unassignedTasks" :key="task.id" class="assign-task-item">
                <span class="task-set-tag">{{ task.task_set_name }}</span>
                <span class="task-query">{{ task.query }}</span>
                <button class="btn-add" @click="assignTask(task.id)">分配</button>
              </div>
              <div v-if="unassignedTasks.length === 0" class="empty-hint">所有任务都已分配</div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="closeAssignModal">关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

// JSON 解析函数（支持 rubric_output.json 格式）
const parseImportFile = (file) => {
  return new Promise((resolve, reject) => {
    const fileName = file.name.toLowerCase()
    const isJson = fileName.endsWith('.json')

    if (!isJson) {
      reject(new Error('请上传 .json 格式的文件'))
      return
    }

    const reader = new FileReader()
    reader.onload = (e) => {
      let data = e.target.result

      // 去除 UTF-8 BOM 标记
      if (data.charCodeAt(0) === 0xFEFF) {
        data = data.substring(1)
      }

      try {
        const jsonData = JSON.parse(data)
        // 支持数组格式
        const tasks = Array.isArray(jsonData) ? jsonData : [jsonData]

        // 解析 rubrics（去重：根据 user_name + collection_name + prompt + criterion）
        const rubricMap = new Map()
        // 解析 answers（去重：根据 user_name + collection_name + prompt + answer）
        const answerMap = new Map()

        tasks.forEach(task => {
          const userName = task.user_name?.trim() || ''
          const collectionName = task.collection_name?.trim() || ''
          const prompt = task.prompt?.trim() || ''

          // 解析 rubrics
          if (task.rubrics && Array.isArray(task.rubrics)) {
            task.rubrics.forEach(rubric => {
              const criterion = rubric.criterion?.trim() || ''
              if (!criterion) return

              const key = `${userName}|${collectionName}|${prompt}|${criterion}`
              if (!rubricMap.has(key)) {
                rubricMap.set(key, {
                  user_name: userName,
                  collection_name: collectionName,
                  prompt: prompt,
                  criterion: criterion,
                  axis: rubric.axis?.trim() || '',
                  point: String(rubric.point ?? '0')
                })
              }
            })
          }

          // 解析 answers
          if (task.answers && Array.isArray(task.answers)) {
            task.answers.forEach(answer => {
              const answerContent = answer?.trim()
              if (!answerContent) return

              const key = `${userName}|${collectionName}|${prompt}|${answerContent}`
              if (!answerMap.has(key)) {
                answerMap.set(key, {
                  user_name: userName,
                  collection_name: collectionName,
                  prompt: prompt,
                  answer: answerContent
                })
              }
            })
          }
        })

        const uniqueRubrics = Array.from(rubricMap.values())
        const uniqueAnswers = Array.from(answerMap.values())

        // 生成预览记录（用于表格展示）
        const previewRecords = uniqueRubrics.map(r => ({
          phone: r.user_name,
          taskSetName: r.collection_name,
          taskName: r.prompt,
          rubric: r.criterion,
          dimension: r.axis,
          score: r.point
        }))

        resolve({
          rubrics: uniqueRubrics,
          answers: uniqueAnswers,
          previewRecords: previewRecords
        })
      } catch (err) {
        reject(new Error('文件解析失败，请确保文件是有效的JSON格式'))
      }
    }
    reader.onerror = reject
    reader.readAsText(file, 'UTF-8')
  })
}

const router = useRouter()
const phone = ref(localStorage.getItem('phone') || '')
const userId = ref(parseInt(localStorage.getItem('userId') || '0'))
const isRoot = ref(localStorage.getItem('isRoot') === 'true')
const taskSets = ref([])
const tasks = ref([])
const currentTask = ref(null)
const selectedSetId = ref(null)
const selectedTaskId = ref(null)

// Root 用户相关
const viewMode = ref('self') // 'self' 或 'user'
const allUsers = ref([])
const selectedUserId = ref(null)

// 任务分配管理
const showAssignModal = ref(false)
const assignedTasks = ref([])
const unassignedTasks = ref([])

// 批量导入
const showImportModal = ref(false)
const importFile = ref(null)
const importPreview = ref([])
const importRubrics = ref([])
const importAnswers = ref([])
const importLoading = ref(false)
const importProgress = ref({ current: 0, total: 0, type: '' })

// Modal 相关
const showModal = ref(false)
const modalTitle = ref('')
const modalFields = ref([])
const modalAction = ref(null)

// 全屏 Modal 相关
const showFullscreenModal = ref(false)
const fullscreenModalTitle = ref('')
const fullscreenModalContent = ref('')
const fullscreenModalPlaceholder = ref('')
const fullscreenModalAction = ref(null)


// 设置axios默认配置
axios.defaults.headers.common['Authorization'] = `Bearer ${localStorage.getItem('token')}`

const logout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('userId')
  localStorage.removeItem('phone')
  localStorage.removeItem('isRoot')
  router.push('/login')
}

// 获取选中的用户名
const getSelectedUserName = () => {
  const user = allUsers.value.find(u => u.id === selectedUserId.value)
  return user ? user.phone : ''
}

// 视图模式切换
const onViewModeChange = () => {
  selectedUserId.value = null
  taskSets.value = []
  tasks.value = []
  currentTask.value = null
  selectedSetId.value = null
  selectedTaskId.value = null

  if (viewMode.value === 'self') {
    loadTaskSets()
  } else {
    loadAllUsers()
  }
}

// 用户切换
const onUserChange = () => {
  taskSets.value = []
  tasks.value = []
  currentTask.value = null
  selectedSetId.value = null
  selectedTaskId.value = null
  if (selectedUserId.value) {
    loadUserTaskSets(selectedUserId.value)
  }
}

// 加载所有用户（root 用）
const loadAllUsers = async () => {
  try {
    const res = await axios.get('/api/admin/users')
    allUsers.value = res.data.filter(u => !u.is_root)
  } catch (err) {
    console.error('加载用户列表失败:', err)
  }
}

// 加载指定用户的任务集合
const loadUserTaskSets = async (userId) => {
  try {
    const res = await axios.get(`/api/admin/users/${userId}/task-sets`)
    taskSets.value = res.data
    if (taskSets.value.length > 0) {
      selectTaskSet(taskSets.value[0].id)
    }
  } catch (err) {
    console.error('加载用户任务集合失败:', err)
  }
}

// 加载指定用户的任务
const loadUserTasks = async (userId, setId) => {
  try {
    const res = await axios.get(`/api/admin/users/${userId}/task-sets/${setId}/tasks`)
    tasks.value = res.data
  } catch (err) {
    console.error('加载用户任务失败:', err)
  }
}

// 任务分配管理
const showTaskAssignModal = async () => {
  if (!selectedUserId.value) {
    alert('请先选择一个用户')
    return
  }
  showAssignModal.value = true
  await loadAssignTasks()
}

const closeAssignModal = () => {
  showAssignModal.value = false
}

// ==================== 批量导入 ====================
const showBatchImportModal = async () => {
  showImportModal.value = true
  importFile.value = null
  importPreview.value = []
  importRubrics.value = []
  importAnswers.value = []
  importProgress.value = { current: 0, total: 0, type: '' }
  // 加载所有用户列表（用于手机号查找）
  if (allUsers.value.length === 0) {
    await loadAllUsers()
  }
}

const closeImportModal = () => {
  showImportModal.value = false
  importFile.value = null
  importPreview.value = []
  importRubrics.value = []
  importAnswers.value = []
}

const handleFileSelect = async (event) => {
  const file = event.target.files[0]
  if (!file) return

  importFile.value = file

  try {
    const { rubrics, answers, previewRecords } = await parseImportFile(file)
    importRubrics.value = rubrics
    importAnswers.value = answers
    importPreview.value = previewRecords

    if (rubrics.length === 0 && answers.length === 0) {
      alert('未解析到有效数据，请检查文件格式')
    }
  } catch (err) {
    console.error('解析文件失败:', err)
    alert('文件解析失败: ' + (err.message || '请确保文件格式正确'))
    // 清空文件选择，允许重新选择
    event.target.value = ''
    importFile.value = null
    importPreview.value = []
    importRubrics.value = []
    importAnswers.value = []
  }
}

const confirmImport = async () => {
  if (importRubrics.value.length === 0 && importAnswers.value.length === 0) return

  importLoading.value = true

  // 按 user_name + collection_name + prompt 分组
  const taskGroups = new Map()

  // 分组 rubrics
  importRubrics.value.forEach(rubric => {
    const key = `${rubric.user_name}|${rubric.collection_name}|${rubric.prompt}`
    if (!taskGroups.has(key)) {
      taskGroups.set(key, {
        user_name: rubric.user_name,
        collection_name: rubric.collection_name,
        prompt: rubric.prompt,
        rubrics: [],
        answers: []
      })
    }
    taskGroups.get(key).rubrics.push(rubric)
  })

  // 分组 answers
  importAnswers.value.forEach(answer => {
    const key = `${answer.user_name}|${answer.collection_name}|${answer.prompt}`
    if (!taskGroups.has(key)) {
      taskGroups.set(key, {
        user_name: answer.user_name,
        collection_name: answer.collection_name,
        prompt: answer.prompt,
        rubrics: [],
        answers: []
      })
    }
    taskGroups.get(key).answers.push(answer)
  })

  const uniqueTasks = Array.from(taskGroups.values())
  importProgress.value = { current: 0, total: uniqueTasks.length, type: 'task' }

  const errors = []
  // 缓存：任务集合名称 -> { id, 任务名称 -> 任务ID }
  const taskSetCache = {}
  // 缓存：任务ID -> 已存在的rubric标题集合（用于去重）
  const taskRubricsCache = {}
  // 缓存：任务ID -> 已存在的标准答案内容集合（用于去重）
  const taskAnswersCache = {}

  for (let i = 0; i < uniqueTasks.length; i++) {
    const taskGroup = uniqueTasks[i]
    importProgress.value.current = i + 1

    try {
      // 1. 获取或创建任务集合
      let taskSetId
      if (taskSetCache[taskGroup.collection_name]) {
        taskSetId = taskSetCache[taskGroup.collection_name].id
      } else {
        let taskSet = taskSets.value.find(ts => ts.name === taskGroup.collection_name)
        if (!taskSet) {
          const res = await axios.post('/api/admin/task-sets', {
            name: taskGroup.collection_name,
            description: '批量导入创建'
          })
          taskSetId = res.data.id
          // 刷新任务集合列表
          await loadTaskSets()
        } else {
          taskSetId = taskSet.id
        }
        // 初始化缓存
        taskSetCache[taskGroup.collection_name] = { id: taskSetId, tasks: {} }
      }

      // 2. 获取或创建任务
      let taskId
      const taskCacheKey = taskGroup.prompt
      if (taskSetCache[taskGroup.collection_name].tasks[taskCacheKey]) {
        taskId = taskSetCache[taskGroup.collection_name].tasks[taskCacheKey]
      } else {
        // 先检查该任务集合下是否已有同名任务
        let existingTask = null
        try {
          const tasksRes = await axios.get(`/api/task-sets/${taskSetId}/tasks`)
          existingTask = tasksRes.data.find(t => t.query === taskGroup.prompt)
        } catch (err) {
          console.log('获取任务列表失败，将创建新任务')
        }

        if (existingTask) {
          taskId = existingTask.id
        } else {
          const taskRes = await axios.post('/api/admin/tasks', {
            task_set_id: taskSetId,
            query: taskGroup.prompt
          })
          taskId = taskRes.data.id
        }
        taskSetCache[taskGroup.collection_name].tasks[taskCacheKey] = taskId
      }

      // 3. 导入 Rubrics（如果标题不存在则创建）
      if (taskGroup.rubrics.length > 0) {
        // 获取已有rubric标题
        if (!taskRubricsCache[taskId]) {
          try {
            const taskDetailRes = await axios.get(`/api/tasks/${taskId}`)
            const existingRubrics = taskDetailRes.data.rubrics || []
            const existingTitles = new Set()
            existingRubrics.forEach(r => {
              try {
                const parsed = JSON.parse(r.content)
                if (parsed.title) {
                  existingTitles.add(parsed.title)
                }
              } catch (e) {
                existingTitles.add(r.content)
              }
            })
            taskRubricsCache[taskId] = existingTitles
          } catch (err) {
            taskRubricsCache[taskId] = new Set()
          }
        }

        // 创建新的rubrics
        for (const rubric of taskGroup.rubrics) {
          const criterion = rubric.criterion?.trim()
          if (!criterion) continue

          // 检查标题是否已存在
          if (taskRubricsCache[taskId].has(criterion)) {
            continue
          }

          const rubricContent = JSON.stringify({
            title: criterion,
            score: parseInt(rubric.point) || 0,
            dimension: rubric.axis?.trim() || ''
          })

          await axios.post('/api/admin/rubrics', {
            task_id: taskId,
            content: rubricContent,
            version: 2
          })
          taskRubricsCache[taskId].add(criterion)
        }
      }

      // 4. 导入标准答案（如果内容不存在则创建）
      if (taskGroup.answers.length > 0) {
        // 获取已有标准答案
        if (!taskAnswersCache[taskId]) {
          try {
            const taskDetailRes = await axios.get(`/api/tasks/${taskId}`)
            const existingAnswers = taskDetailRes.data.reference_answers || []
            taskAnswersCache[taskId] = new Set(existingAnswers.map(a => a.content))
          } catch (err) {
            taskAnswersCache[taskId] = new Set()
          }
        }

        // 创建新的标准答案
        for (const answer of taskGroup.answers) {
          const content = answer.answer?.trim()
          if (!content) continue

          // 检查是否已存在
          if (taskAnswersCache[taskId].has(content)) {
            continue
          }

          await axios.post('/api/admin/reference-answers', {
            task_id: taskId,
            content: content,
            version: 2
          })
          taskAnswersCache[taskId].add(content)
        }
      }

      // 5. 分配给指定用户（根据手机号查找用户ID）
      const user = allUsers.value.find(u => u.phone === taskGroup.user_name)
      if (user) {
        await axios.post(`/api/admin/assign-task?user_id=${user.id}&task_id=${taskId}`)
      } else {
        errors.push(`任务 ${taskGroup.prompt}: 未找到手机号 ${taskGroup.user_name} 对应的用户`)
      }
    } catch (err) {
      errors.push(`任务 ${taskGroup.prompt}: ${err.response?.data?.detail || err.message}`)
    }
  }

  importLoading.value = false

  if (errors.length > 0) {
    alert(`导入完成，但有 ${errors.length} 个任务失败：\n${errors.slice(0, 5).join('\n')}${errors.length > 5 ? '\n...' : ''}`)
  } else {
    const taskCount = uniqueTasks.length
    const rubricCount = importRubrics.value.length
    const answerCount = importAnswers.value.length
    console.log('导入成功，准备关闭弹窗，showImportModal:', showImportModal.value)
    showImportModal.value = false
    importFile.value = null
    importPreview.value = []
    importRubrics.value = []
    importAnswers.value = []
    await nextTick()
    console.log('弹窗已关闭，showImportModal:', showImportModal.value)
    alert(`成功导入 ${taskCount} 个任务，${rubricCount} 个 rubric，${answerCount} 个标准答案！`)
    // 刷新任务列表
    if (selectedSetId.value) {
      await selectTaskSet(selectedSetId.value)
    }
  }
}

const loadAssignTasks = async () => {
  try {
    const [assignedRes, unassignedRes] = await Promise.all([
      axios.get(`/api/admin/users/${selectedUserId.value}/assigned-tasks`),
      axios.get(`/api/admin/users/${selectedUserId.value}/unassigned-tasks`)
    ])
    assignedTasks.value = assignedRes.data
    unassignedTasks.value = unassignedRes.data
  } catch (err) {
    console.error('加载任务分配数据失败:', err)
  }
}

const assignTask = async (taskId) => {
  try {
    await axios.post(`/api/admin/assign-task?user_id=${selectedUserId.value}&task_id=${taskId}`)
    await loadAssignTasks()
    // 刷新任务列表
    if (selectedSetId.value) {
      await loadUserTasks(selectedUserId.value, selectedSetId.value)
    }
  } catch (err) {
    alert('分配失败: ' + (err.response?.data?.detail || err.message))
  }
}

const unassignTask = async (taskId) => {
  if (!confirm('确定要取消该任务的分配吗？')) return
  try {
    await axios.delete(`/api/admin/assign-task?user_id=${selectedUserId.value}&task_id=${taskId}`)
    await loadAssignTasks()
    // 刷新任务列表
    if (selectedSetId.value) {
      await loadUserTasks(selectedUserId.value, selectedSetId.value)
    }
    // 如果当前查看的任务被取消了分配，清空详情
    if (selectedTaskId.value === taskId) {
      currentTask.value = null
      selectedTaskId.value = null
    }
  } catch (err) {
    alert('取消分配失败: ' + (err.response?.data?.detail || err.message))
  }
}

// Modal 操作
const openModal = (title, fields, action) => {
  modalTitle.value = title
  modalFields.value = fields
  modalAction.value = action
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
}

const confirmModal = async () => {
  if (modalAction.value) {
    await modalAction.value(modalFields.value)
  }
  closeModal()
}

// 全屏 Modal 操作
const openFullscreenModal = (title, content, placeholder, action) => {
  fullscreenModalTitle.value = title
  fullscreenModalContent.value = content
  fullscreenModalPlaceholder.value = placeholder
  fullscreenModalAction.value = action
  showFullscreenModal.value = true
}

const closeFullscreenModal = () => {
  showFullscreenModal.value = false
}

const confirmFullscreenModal = async () => {
  if (fullscreenModalAction.value) {
    await fullscreenModalAction.value(fullscreenModalContent.value)
  }
  closeFullscreenModal()
}

// ==================== 任务集合管理 ====================
const showAddTaskSetModal = () => {
  openModal('添加任务集合', [
    { label: '名称', type: 'text', value: '', placeholder: '请输入任务集合名称' },
    { label: '描述', type: 'textarea', value: '', placeholder: '请输入描述（可选）' }
  ], async (fields) => {
    try {
      await axios.post('/api/admin/task-sets', {
        name: fields[0].value,
        description: fields[1].value
      })
      await loadTaskSets()
    } catch (err) {
      alert('添加失败: ' + (err.response?.data?.detail || err.message))
    }
  })
}

const editTaskSet = (set) => {
  openModal('编辑任务集合', [
    { label: '名称', type: 'text', value: set.name, placeholder: '请输入任务集合名称' },
    { label: '描述', type: 'textarea', value: set.description || '', placeholder: '请输入描述（可选）' }
  ], async (fields) => {
    try {
      await axios.patch(`/api/admin/task-sets/${set.id}`, {
        name: fields[0].value,
        description: fields[1].value
      })
      await loadTaskSets()
    } catch (err) {
      alert('编辑失败: ' + (err.response?.data?.detail || err.message))
    }
  })
}

const deleteTaskSet = async (setId) => {
  if (!confirm('确定要删除这个任务集合吗？这将删除集合下的所有任务和标注数据。')) return
  try {
    await axios.delete(`/api/admin/task-sets/${setId}`)
    await loadTaskSets()
  } catch (err) {
    alert('删除失败: ' + (err.response?.data?.detail || err.message))
  }
}

// ==================== 任务管理 ====================
const showAddTaskModal = () => {
  openModal('添加任务', [
    { label: 'Query', type: 'textarea', value: '', placeholder: '请输入查询内容' }
  ], async (fields) => {
    try {
      await axios.post('/api/admin/tasks', {
        task_set_id: selectedSetId.value,
        query: fields[0].value
      })
      await selectTaskSet(selectedSetId.value)
    } catch (err) {
      alert('添加失败: ' + (err.response?.data?.detail || err.message))
    }
  })
}

const editTask = (task) => {
  openModal('编辑任务', [
    { label: 'Query', type: 'textarea', value: task.query, placeholder: '请输入查询内容' }
  ], async (fields) => {
    try {
      await axios.patch(`/api/admin/tasks/${task.id}`, {
        query: fields[0].value
      })
      await selectTaskSet(selectedSetId.value)
      if (selectedTaskId.value === task.id) {
        await selectTask(task.id)
      }
    } catch (err) {
      alert('编辑失败: ' + (err.response?.data?.detail || err.message))
    }
  })
}

const deleteTask = async (taskId) => {
  if (!confirm('确定要删除这个任务吗？')) return
  try {
    await axios.delete(`/api/admin/tasks/${taskId}`)
    await selectTaskSet(selectedSetId.value)
    if (selectedTaskId.value === taskId) {
      currentTask.value = null
      selectedTaskId.value = null
    }
  } catch (err) {
    alert('删除失败: ' + (err.response?.data?.detail || err.message))
  }
}

// ==================== Rubric 管理 ====================
const showAddRubricModal = async () => {
  // 先创建空的rubric（使用V2格式）
  const emptyContent = buildRubricV2Content({ title: '', dimension: '', score: null })

  try {
    const url = isRoot.value ? '/api/admin/rubrics' : '/api/rubrics'
    const res = await axios.post(url, {
      task_id: selectedTaskId.value,
      content: emptyContent,
      version: 2
    })

    if (res.data && res.data.id) {
      // 默认勾选新rubric
      await axios.patch(`/api/rubrics/${res.data.id}`, { selected: true })

      // 将新rubric添加到当前列表
      const newRubric = {
        ...res.data,
        selected: true,
        content: emptyContent
      }

      if (currentTask.value) {
        currentTask.value.rubrics.push(newRubric)

        // 自动进入编辑模式（标题字段）
        startEditRubricV2Field(newRubric, 'title')
      }
    }
  } catch (err) {
    alert('添加失败: ' + (err.response?.data?.detail || err.message))
  }
}

const deleteRubric = async (rubricId) => {
  if (!confirm('确定要删除这个rubric吗？')) return
  try {
    await axios.delete(`/api/rubrics/${rubricId}`)
    await selectTask(selectedTaskId.value)
  } catch (err) {
    alert('删除失败: ' + (err.response?.data?.detail || err.message))
  }
}

// ==================== V2 Rubric 行内编辑 ====================
const startEditRubricV2Field = (rubric, field) => {
  // 先取消其他所有rubric的编辑状态
  if (currentTask.value) {
    currentTask.value.rubrics.forEach(r => {
      r.editingFieldV2 = null
    })
  }

  const parsed = parseRubricV2(rubric.content)
  rubric.editingFieldV2 = field
  rubric.editTitleV2 = parsed.title
  rubric.editDimensionV2 = parsed.dimension
  rubric.editScoreV2 = parsed.score
}

const cancelEditRubricV2 = (rubric) => {
  rubric.editingFieldV2 = null
}

const saveRubricV2Field = async (rubric) => {
  const parsed = parseRubricV2(rubric.content)

  // 根据当前编辑的字段更新数据
  if (rubric.editingFieldV2 === 'title') {
    parsed.title = rubric.editTitleV2 || ''
  } else if (rubric.editingFieldV2 === 'dimension') {
    parsed.dimension = rubric.editDimensionV2 || ''
  } else if (rubric.editingFieldV2 === 'score') {
    parsed.score = rubric.editScoreV2 !== '' ? parseInt(rubric.editScoreV2) : null
  }

  const newContent = buildRubricV2Content(parsed)
  if (newContent !== rubric.content) {
    try {
      const url = isRoot.value ? `/api/admin/rubrics/${rubric.id}/content` : `/api/rubrics/${rubric.id}/content`
      await axios.patch(url, { content: newContent })
      rubric.content = newContent
    } catch (err) {
      console.error('保存失败:', err)
      alert('保存失败: ' + (err.response?.data?.detail || err.message))
    }
  }
  rubric.editingFieldV2 = null
}

// ==================== V2 Rubric 格式解析 ====================
const parseRubricV2 = (content) => {
  try {
    const parsed = JSON.parse(content)
    // V2格式检查：必须包含title, dimension, score字段
    if (parsed.title !== undefined && parsed.dimension !== undefined && parsed.score !== undefined) {
      return {
        title: parsed.title || '',
        dimension: parsed.dimension || '',
        score: parsed.score !== undefined ? parsed.score : null
      }
    }
  } catch (e) {
    // 如果不是JSON格式，返回默认值
  }
  // 返回V2默认值
  return {
    title: content,
    dimension: '',
    score: null
  }
}

const buildRubricV2Content = (data) => {
  return JSON.stringify({
    title: data.title || '',
    dimension: data.dimension || '',
    score: data.score !== undefined ? parseInt(data.score) : null
  })
}

// ==================== 标准答案行内编辑 ====================
const startEditReferenceAnswer = (answer) => {
  // 先取消其他所有答案的编辑状态
  if (currentTask.value && currentTask.value.reference_answers) {
    currentTask.value.reference_answers.forEach(a => {
      a.isEditing = false
    })
  }
  answer.isEditing = true
  answer.editContent = answer.content
}

const cancelEditReferenceAnswer = (answer) => {
  answer.isEditing = false
}

const saveReferenceAnswerInline = async (answer) => {
  if (answer.editContent !== answer.content) {
    try {
      const url = isRoot.value ? `/api/admin/reference-answers/${answer.id}` : `/api/reference-answers/${answer.id}`
      await axios.patch(url, {
        content: answer.editContent
      })
      answer.content = answer.editContent
    } catch (err) {
      console.error('保存失败:', err)
      alert('保存失败: ' + (err.response?.data?.detail || err.message))
    }
  }
  answer.isEditing = false
}

// ==================== 标准答案管理 ====================
const showAddReferenceAnswerModal = () => {
  openModal('添加标准答案', [
    { label: '内容', type: 'textarea', value: '', placeholder: '请输入标准答案内容' }
  ], async (fields) => {
    try {
      const url = isRoot.value ? '/api/admin/reference-answers' : '/api/reference-answers'
      await axios.post(url, {
        task_id: selectedTaskId.value,
        content: fields[0].value,
        version: 2
      })
      await selectTask(selectedTaskId.value)
    } catch (err) {
      alert('添加失败: ' + (err.response?.data?.detail || err.message))
    }
  })
}

const deleteReferenceAnswer = async (answerId) => {
  if (!confirm('确定要删除这个标准答案吗？')) return
  try {
    const url = isRoot.value ? `/api/admin/reference-answers/${answerId}` : `/api/reference-answers/${answerId}`
    await axios.delete(url)
    await selectTask(selectedTaskId.value)
  } catch (err) {
    alert('删除失败: ' + (err.response?.data?.detail || err.message))
  }
}

// 加载任务集合
const loadTaskSets = async () => {
  try {
    const res = await axios.get('/api/task-sets')
    taskSets.value = res.data
    if (taskSets.value.length > 0 && !selectedSetId.value) {
      selectTaskSet(taskSets.value[0].id)
    }
  } catch (err) {
    if (err.response?.status === 401) {
      logout()
    }
  }
}

// 选择任务集合
const selectTaskSet = async (setId) => {
  selectedSetId.value = setId
  selectedTaskId.value = null
  currentTask.value = null

  try {
    let res
    if (viewMode.value === 'user' && selectedUserId.value) {
      res = await axios.get(`/api/admin/users/${selectedUserId.value}/task-sets/${setId}/tasks`)
    } else {
      res = await axios.get(`/api/task-sets/${setId}/tasks`)
    }
    tasks.value = res.data
  } catch (err) {
    console.error('加载任务失败:', err)
  }
}

// 选择任务
const selectTask = async (taskId) => {
  selectedTaskId.value = taskId

  try {
    // 获取V2版本数据
    const res = await axios.get(`/api/tasks/${taskId}?version=2`)
    currentTask.value = res.data
  } catch (err) {
    console.error('加载任务详情失败:', err)
  }
}

// 切换rubric选择状态
const toggleRubric = async (rubric) => {
  try {
    await axios.patch(`/api/rubrics/${rubric.id}`, {
      selected: !rubric.selected
    })
    rubric.selected = !rubric.selected
  } catch (err) {
    console.error('更新rubric失败:', err)
  }
}

// 切换任务完成状态
const toggleComplete = async () => {
  if (!currentTask.value) return

  try {
    const newStatus = !currentTask.value.completed
    await axios.patch(`/api/tasks/${currentTask.value.id}/complete`, {
      completed: newStatus
    })

    currentTask.value.completed = newStatus

    const task = tasks.value.find(t => t.id === currentTask.value.id)
    if (task) {
      task.completed = newStatus
    }
  } catch (err) {
    console.error('更新任务状态失败:', err)
  }
}

onMounted(() => {
  loadTaskSets()
})
</script>

<style scoped>
.annotate-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.header {
  height: 60px;
  background: white;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 24px;
}

.header-title {
  font-size: 20px;
  font-weight: 600;
  color: #333;
  display: flex;
  align-items: center;
  gap: 10px;
}

.root-badge {
  background: #ff4d4f;
  color: white;
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
}

.view-switcher {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 16px;
  background: #f5f5f5;
  border-radius: 8px;
}

.view-switcher label {
  color: #666;
  font-size: 14px;
}

.view-switcher select {
  padding: 6px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
  background: white;
}

.manage-btn {
  padding: 6px 12px;
  background: #1890ff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.manage-btn:hover {
  background: #40a9ff;
}

.header-user {
  display: flex;
  align-items: center;
  gap: 16px;
  color: #666;
}

.logout-btn {
  padding: 6px 16px;
  background: #f5f5f5;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  color: #666;
  transition: all 0.2s;
}

.logout-btn:hover {
  background: #e0e0e0;
}

.main-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.column {
  display: flex;
  flex-direction: column;
  border-right: 1px solid #e0e0e0;
  background: white;
}

.column-1 {
  width: 300px;
  background: #fafafa;
}

.column-2 {
  width: 360px;
}

.column-3 {
  flex: 1;
  border-right: none;
}

.column-header {
  height: 48px;
  background: #f0f2f5;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  font-weight: 600;
  color: #333;
  border-bottom: 1px solid #e0e0e0;
}

.add-btn {
  width: 28px;
  height: 28px;
  background: #1890ff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.add-btn:hover {
  background: #40a9ff;
}

.column-content {
  flex: 1;
  overflow-y: auto;
}

/* 任务集合样式 */
.task-set-item {
  padding: 12px 16px;
  border-bottom: 1px solid #e8e8e8;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.task-set-item:hover {
  background: #f0f0f0;
}

.task-set-item.active {
  background: #e6f7ff;
  border-left: 3px solid #1890ff;
}

.task-set-info {
  flex: 1;
  min-width: 0;
}

.task-set-name {
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.task-set-desc {
  font-size: 13px;
  color: #999;
}

.item-actions {
  display: flex;
  gap: 4px;
  margin-left: 8px;
}

.action-btn {
  width: 24px;
  height: 24px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.action-btn.edit {
  background: #1890ff;
  color: white;
}

.action-btn.edit:hover {
  background: #40a9ff;
}

.action-btn.delete {
  background: #ff4d4f;
  color: white;
}

.action-btn.delete:hover {
  background: #ff7875;
}

.action-btn.small {
  width: 20px;
  height: 20px;
  font-size: 10px;
}

/* 任务列表样式 */
.task-item {
  padding: 12px 16px;
  border-bottom: 1px solid #e8e8e8;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.task-item:hover {
  background: #f5f5f5;
}

.task-item.active {
  background: #e6f7ff;
  border-left: 3px solid #1890ff;
}

.task-item.completed {
  background: #f6ffed;
}

.task-query {
  flex: 1;
  color: #333;
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.task-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: 8px;
}

.completed-badge {
  padding: 2px 8px;
  background: #52c41a;
  color: white;
  font-size: 12px;
  border-radius: 4px;
  white-space: nowrap;
}

/* 标注详情样式 */
.annotation-panel {
  padding: 24px;
}

.query-title {
  font-size: 20px;
  font-weight: 600;
  color: #333;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 2px solid #e8e8e8;
  line-height: 1.6;
}

.rubrics-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.add-rubric-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f6ffed;
  border: 2px dashed #b7eb8f;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  margin-top: 8px;
}

.add-rubric-item:hover {
  background: #d9f7be;
  border-color: #73d13d;
}

.add-icon {
  width: 24px;
  height: 24px;
  background: #52c41a;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: bold;
  flex-shrink: 0;
}

.add-text {
  color: #52c41a;
  font-weight: 500;
}

.rubric-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  background: #fafafa;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  min-height: 44px;
}

.rubric-item:hover {
  background: #f0f0f0;
}

.checkbox {
  width: 20px;
  height: 20px;
  border: 2px solid #d9d9d9;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 2px;
  transition: all 0.2s;
  flex-shrink: 0;
}

.checkbox.checked {
  background: #1890ff;
  border-color: #1890ff;
  color: white;
}

.checkbox span {
  font-size: 14px;
  font-weight: bold;
}

.rubric-content {
  flex: 1;
  color: #333;
  line-height: 1.6;
  word-wrap: break-word;
  white-space: pre-wrap;
  word-break: break-word;
  overflow-wrap: break-word;
  min-width: 0;
  padding-right: 8px;
}

.rubric-actions {
  display: flex;
  gap: 4px;
  margin-left: 8px;
  flex-shrink: 0;
  align-self: flex-start;
}

.action-buttons {
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid #e8e8e8;
}

.complete-btn {
  width: 100%;
  padding: 14px 24px;
  background: #1890ff;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.complete-btn:hover {
  background: #40a9ff;
}

.complete-btn.completed {
  background: #ff4d4f;
}

.complete-btn.completed:hover {
  background: #ff7875;
}

.empty-state {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
  font-size: 16px;
}

/* Modal 样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow: hidden;
}

.modal-content.large {
  max-width: 800px;
}

.modal-content h3 {
  padding: 20px;
  margin: 0;
  border-bottom: 1px solid #e8e8e8;
  font-size: 18px;
}

.modal-body {
  padding: 20px;
  overflow-y: auto;
}

.modal-field {
  margin-bottom: 16px;
}

.modal-field:last-child {
  margin-bottom: 0;
}

.modal-field label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #333;
}

.modal-field input,
.modal-field textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
}

.modal-field input:focus,
.modal-field textarea:focus {
  outline: none;
  border-color: #1890ff;
}

.modal-footer {
  padding: 16px 20px;
  border-top: 1px solid #e8e8e8;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.btn-cancel {
  padding: 8px 16px;
  background: white;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.btn-cancel:hover {
  border-color: #1890ff;
  color: #1890ff;
}

.btn-confirm {
  padding: 8px 16px;
  background: #1890ff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.btn-confirm:hover {
  background: #40a9ff;
}

/* 全屏 Modal 样式 */
.modal-overlay.fullscreen {
  padding: 0;
}

.modal-content.fullscreen {
  width: 100%;
  height: 100%;
  max-width: 100%;
  max-height: 100%;
  border-radius: 0;
  display: flex;
  flex-direction: column;
}

.fullscreen-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  border-bottom: 1px solid #e8e8e8;
  background: #fff;
}

.fullscreen-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.fullscreen-header .btn-close {
  width: 32px;
  height: 32px;
  background: none;
  border: none;
  font-size: 20px;
  color: #999;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s;
}

.fullscreen-header .btn-close:hover {
  background: #f0f0f0;
  color: #333;
}

.fullscreen-body {
  flex: 1;
  padding: 0;
  overflow: hidden;
}

.fullscreen-body textarea {
  width: 100%;
  height: 100%;
  padding: 24px;
  border: none;
  resize: none;
  font-size: 16px;
  line-height: 1.8;
  font-family: inherit;
  outline: none;
}

.fullscreen-footer {
  padding: 16px 24px;
  border-top: 1px solid #e8e8e8;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  background: #fff;
}

/* 任务分配管理样式 */
.assign-body {
  padding: 20px;
  display: flex;
  gap: 20px;
  max-height: 60vh;
  overflow: hidden;
}

.assign-section {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.assign-section h4 {
  margin: 0 0 12px 0;
  padding-bottom: 8px;
  border-bottom: 2px solid #e8e8e8;
  color: #333;
}

.task-list {
  flex: 1;
  overflow-y: auto;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  padding: 8px;
}

.assign-task-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  border-bottom: 1px solid #f0f0f0;
  font-size: 14px;
}

.assign-task-item:last-child {
  border-bottom: none;
}

.task-set-tag {
  background: #e6f7ff;
  color: #1890ff;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  white-space: nowrap;
}

.task-query {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.btn-add, .btn-remove {
  padding: 4px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.btn-add {
  background: #52c41a;
  color: white;
}

.btn-add:hover {
  background: #73d13d;
}

.btn-remove {
  background: #ff4d4f;
  color: white;
}

.btn-remove:hover {
  background: #ff7875;
}

.empty-hint {
  text-align: center;
  color: #999;
  padding: 20px;
}

/* 标准答案样式 */
.reference-answers-section {
  margin-top: 24px;
}

.section-divider {
  display: flex;
  align-items: center;
  margin: 24px 0 16px 0;
}

.section-divider::before,
.section-divider::after {
  content: '';
  flex: 1;
  border-bottom: 1px solid #e8e8e8;
}

.divider-text {
  padding: 0 16px;
  color: #666;
  font-size: 14px;
  font-weight: 500;
}

.reference-answers-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.reference-answer-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  background: #f6ffed;
  border: 1px solid #b7eb8f;
  border-radius: 8px;
  transition: all 0.2s;
}

.reference-answer-item:hover {
  background: #d9f7be;
}

.reference-answer-content {
  flex: 1;
  color: #333;
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 14px;
}

.reference-answer-actions {
  display: flex;
  gap: 4px;
  margin-left: 8px;
  flex-shrink: 0;
}

.add-reference-answer-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #fff7e6;
  border: 2px dashed #ffd591;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  margin-top: 12px;
}

.add-reference-answer-item:hover {
  background: #ffe7ba;
  border-color: #ffc53d;
}

.add-reference-answer-item .add-icon {
  width: 24px;
  height: 24px;
  background: #fa8c16;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: bold;
  flex-shrink: 0;
}

.add-reference-answer-item .add-text {
  color: #fa8c16;
  font-weight: 500;
}

/* 批量导入样式 */
.header-actions {
  display: flex;
  gap: 8px;
}

.import-btn {
  width: 28px;
  height: 28px;
  background: #52c41a;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.import-btn:hover {
  background: #73d13d;
}

.import-body {
  padding: 20px;
  max-height: 60vh;
  overflow-y: auto;
}

.import-section {
  margin-bottom: 20px;
}

.file-input-label {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  margin-bottom: 16px;
}

.file-input-btn {
  padding: 10px 20px;
  background: #1890ff;
  color: white;
  border-radius: 4px;
  font-size: 14px;
  transition: background 0.2s;
}

.file-input-btn:hover {
  background: #40a9ff;
}

.file-name {
  color: #666;
  font-size: 14px;
}

.import-hint {
  background: #f6ffed;
  border: 1px solid #b7eb8f;
  border-radius: 4px;
  padding: 16px;
  font-size: 14px;
}

.import-hint p {
  margin: 0 0 8px 0;
  font-weight: 500;
  color: #333;
}

.import-hint ul {
  margin: 0 0 8px 0;
  padding-left: 20px;
  color: #666;
}

.import-hint li {
  margin-bottom: 4px;
}

.hint-note {
  color: #999;
  font-size: 12px;
  margin-top: 8px;
}

.import-preview {
  margin-top: 20px;
}

.import-preview h4 {
  margin: 0 0 12px 0;
  color: #333;
}

.preview-table-container {
  max-height: 250px;
  overflow-y: auto;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
}

.preview-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.preview-table th,
.preview-table td {
  padding: 10px 12px;
  text-align: left;
  border-bottom: 1px solid #e8e8e8;
}

.preview-table th {
  background: #f0f2f5;
  font-weight: 500;
  color: #333;
  position: sticky;
  top: 0;
}

.preview-table td {
  color: #666;
}

.preview-table tr:hover td {
  background: #f5f5f5;
}

.more-rows {
  text-align: center;
  color: #999;
  font-style: italic;
}

.import-progress {
  margin-top: 20px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.progress-bar {
  flex: 1;
  height: 8px;
  background: #f0f0f0;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #52c41a;
  transition: width 0.3s;
}

.progress-text {
  font-size: 14px;
  color: #666;
  min-width: 60px;
}

/* 滚动条样式 */
.column-content::-webkit-scrollbar,
.task-list::-webkit-scrollbar {
  width: 6px;
}

.column-content::-webkit-scrollbar-track,
.task-list::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.column-content::-webkit-scrollbar-thumb,
.task-list::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.column-content::-webkit-scrollbar-thumb:hover,
.task-list::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* V2 Rubric 样式 */
.rubric-item-v2 {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px 16px;
  background: #fafafa;
  border-radius: 8px;
  border: 2px solid transparent;
  transition: all 0.2s;
}

.rubric-item-v2:hover {
  background: #f0f0f0;
  border-color: #d9d9d9;
}

.rubric-item-v2.selected {
  background: #e6f7ff;
  border-color: #1890ff;
}

/* 负分rubric样式 */
.rubric-item-v2.negative-score {
  border-color: #ff4d4f;
  background: #fff2f0;
}

.rubric-item-v2.negative-score:hover {
  border-color: #ff7875;
  background: #fff1f0;
}

.rubric-v2-row {
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: 32px;
}

.rubric-v2-title-wrapper {
  flex: 1;
  min-width: 0;
}

.rubric-v2-title {
  font-size: 15px;
  font-weight: 600;
  color: #333;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all 0.2s;
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.4;
}

.rubric-v2-title:hover {
  background: white;
}

.rubric-v2-title-input {
  width: 100%;
  font-size: 15px;
  font-weight: 600;
  padding: 4px 8px;
  border: 2px solid #1890ff;
  border-radius: 4px;
  outline: none;
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.4;
  resize: vertical;
  min-height: 40px;
  height: auto;
  overflow: hidden;
  field-sizing: content;
}

.rubric-v2-row.meta-row {
  margin-left: 32px;
  gap: 24px;
}

.rubric-v2-dimension-wrapper,
.rubric-v2-score-wrapper {
  flex-shrink: 0;
}

.rubric-v2-dimension,
.rubric-v2-score {
  font-size: 13px;
  cursor: pointer;
  padding: 2px 8px;
  border-radius: 4px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 4px;
  white-space: pre-wrap;
  word-break: break-word;
}

.rubric-v2-dimension:hover,
.rubric-v2-score:hover {
  background: white;
}

.rubric-v2-dimension-input,
.rubric-v2-score-input {
  font-size: 13px;
  padding: 2px 6px;
  border: 2px solid #1890ff;
  border-radius: 4px;
  outline: none;
  width: 100px;
  white-space: pre-wrap;
  word-break: break-word;
}

.rubric-v2-score-input {
  width: 60px;
  text-align: center;
}

.rubric-v2-actions {
  flex-shrink: 0;
}

.rubric-v2-actions .rubric-actions {
  display: flex;
  gap: 4px;
}

/* 编辑操作按钮样式 */
.edit-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.edit-actions-inline {
  display: flex;
  gap: 8px;
  margin-top: 8px;
  justify-content: flex-end;
}

.btn-save,
.btn-cancel {
  padding: 4px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}

.btn-save {
  background: #52c41a;
  color: white;
}

.btn-save:hover {
  background: #73d13d;
}

.btn-cancel {
  background: #f5f5f5;
  color: #666;
  border: 1px solid #d9d9d9;
}

.btn-cancel:hover {
  background: #e0e0e0;
  border-color: #999;
}

/* 编辑状态下的样式 */
.rubric-item-v2.editing {
  border-color: #1890ff;
  background: #e6f7ff;
}

.rubric-v2-title.readonly {
  color: #999;
  cursor: default;
}

/* 标准答案编辑样式 */
.reference-answer-item.editing {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.reference-answer-input {
  width: 100%;
  padding: 10px 12px;
  border: 2px solid #1890ff;
  border-radius: 4px;
  font-size: 14px;
  resize: vertical;
  min-height: 60px;
  height: auto;
  font-family: inherit;
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-word;
  overflow: hidden;
  field-sizing: content;
}

.reference-answer-input:focus {
  outline: none;
}
</style>
