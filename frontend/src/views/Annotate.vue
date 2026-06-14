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
            管理集合分配
          </button>
        </div>
      </div>
      <div class="header-user">
        <span>{{ phone }}</span>
        <button class="change-password-btn" @click="showChangePasswordModal = true">修改密码</button>
        <button class="logout-btn" @click="logout">退出</button>
      </div>
    </header>

    <div class="main-content">
      <!-- 第一列：任务集合 -->
      <div class="column column-1" :class="{ collapsed: isTaskSetCollapsed }">
        <div class="collapse-toggle" @click="toggleTaskSetColumn" :title="isTaskSetCollapsed ? '展开' : '收起'">
          <span class="collapse-arrow" :class="{ collapsed: isTaskSetCollapsed }">◀</span>
        </div>
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
              <button class="action-btn export" @click="exportTaskSet(set)" title="导出">⬇</button>
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
            <div class="task-query" :title="task.query">{{ task.query }}</div>
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

            <!-- 普通 rubrics 列表 - 只有在没有 tree 时才显示 -->
            <div v-if="!currentTask.tree" class="rubrics-list">
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

            <!-- Tree 评分区域 -->
            <div class="tree-section" v-if="currentTask.tree">
              <div class="section-title">树形评分标准</div>
              <div class="tree-container">
                <TreeNode
                  v-if="currentTask.tree"
                  :node="currentTask.tree"
                  :level="0"
                  :dragging-index="treeDraggingIndex"
                  :drag-over-index="treeDragOverIndex"
                  @toggle="toggleTreeNode"
                  @update="handleTreeUpdate"
                  @delete="deleteTreeNode"
                  @add-child="addTreeNodeChild"
                  @update-professional="updateTreeNodeProfessional"
                  @update-required="updateTreeNodeRequired"
                  @drag-start="handleTreeDragStart"
                  @drag-over="handleTreeDragOver"
                  @drag-end="handleTreeDragEnd"
                />
              </div>
            </div>

            <!-- 参考答案区域 -->
            <div class="reference-answers-section" v-if="currentTask.reference_answers && currentTask.reference_answers.length > 0 || selectedTaskId">
              <div class="section-divider">
                <span class="divider-text">参考答案</span>
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
                      placeholder="请输入参考答案内容"
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
                <span class="add-text">添加参考答案</span>
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
    "collection_name": "20260407",
    "prompt": "柑橘得了黄龙病怎么治疗",
    "rubrics": [
      { "criterion": "明确说明柑橘黄龙病目前无特效治愈药", "axis": "", "point": 5 },
      { "criterion": "建议尽快进行田间诊断与实验室检测", "axis": "", "point": 3 }
    ],
    "answers": ["参考答案内容..."]
  }
]</pre>
              <p class="hint-note">注：请使用UTF-8编码的JSON文件。每个任务通过 collection_name + prompt 定位，rubrics 为对象数组（含 criterion/axis/point），answers 为字符串数组。</p>
            </div>
          </div>

          <div v-if="importRubrics.length > 0 || importAnswers.length > 0 || importTrees.length > 0" class="import-preview">
            <h4>预览 ({{ importRubrics.length }} 个 rubric, {{ importAnswers.length }} 个参考答案, {{ importTrees.length }} 个树形结构)</h4>
            <div class="preview-table-container">
              <table class="preview-table">
                <thead>
                  <tr>
                    <th>任务集合</th>
                    <th>任务名称</th>
                    <th>Rubric</th>
                    <th>维度</th>
                    <th>分数</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(item, index) in importPreview.slice(0, 10)" :key="index">
                    <td>{{ item.taskSetName }}</td>
                    <td>{{ item.taskName }}</td>
                    <td :title="item.rubric">{{ item.rubric.slice(0, 30) }}{{ item.rubric.length > 30 ? '...' : '' }}</td>
                    <td>{{ item.dimension || '-' }}</td>
                    <td>{{ item.score }}</td>
                  </tr>
                  <tr v-if="importPreview.length > 10">
                    <td colspan="5" class="more-rows">... 还有 {{ importPreview.length - 10 }} 条记录</td>
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
            :disabled="(importRubrics.length === 0 && importAnswers.length === 0 && importTrees.length === 0) || importLoading"
          >
            {{ importLoading ? '导入中...' : '确认导入' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 任务集合分配管理弹窗 -->
    <div v-if="showAssignModal" class="modal-overlay" @click="closeAssignModal">
      <div class="modal-content large" @click.stop>
        <h3>任务集合分配管理 - {{ getSelectedUserName() }}</h3>
        <div class="assign-body">
          <div class="assign-section">
            <h4>已分配的任务集合</h4>
            <div class="task-list">
              <div v-for="taskSet in assignedTaskSets" :key="taskSet.id" class="assign-taskset-item">
                <div class="taskset-info">
                  <span class="taskset-name">{{ taskSet.name }}</span>
                  <span v-if="taskSet.description" class="taskset-desc">{{ taskSet.description }}</span>
                </div>
                <button class="btn-remove" @click="unassignTaskSet(taskSet.id)">移除</button>
              </div>
              <div v-if="assignedTaskSets.length === 0" class="empty-hint">暂无分配任务集合</div>
            </div>
          </div>
          <div class="assign-section">
            <h4>未分配的任务集合</h4>
            <div class="task-list">
              <div v-for="taskSet in unassignedTaskSets" :key="taskSet.id" class="assign-taskset-item">
                <div class="taskset-info">
                  <span class="taskset-name">{{ taskSet.name }}</span>
                  <span v-if="taskSet.description" class="taskset-desc">{{ taskSet.description }}</span>
                </div>
                <button class="btn-add" @click="assignTaskSet(taskSet.id)">分配</button>
              </div>
              <div v-if="unassignedTaskSets.length === 0" class="empty-hint">所有任务集合都已分配</div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="closeAssignModal">关闭</button>
        </div>
      </div>
    </div>

    <!-- 修改密码弹窗 -->
    <div v-if="showChangePasswordModal" class="modal-overlay" @click.self="closeChangePasswordModal">
      <div class="modal change-password-modal">
        <div class="modal-header">
          <h3>修改密码</h3>
          <button class="close-btn" @click="closeChangePasswordModal">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>旧密码</label>
            <input
              v-model="passwordForm.oldPassword"
              type="password"
              placeholder="请输入旧密码"
            >
          </div>
          <div class="form-group">
            <label>新密码</label>
            <input
              v-model="passwordForm.newPassword"
              type="password"
              placeholder="请输入新密码（至少6位）"
            >
          </div>
          <div class="form-group">
            <label>确认新密码</label>
            <input
              v-model="passwordForm.confirmPassword"
              type="password"
              placeholder="请再次输入新密码"
            >
          </div>
          <div v-if="passwordError" class="error-message">{{ passwordError }}</div>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="closeChangePasswordModal">取消</button>
          <button class="btn-confirm" @click="changePassword" :disabled="passwordLoading">
            {{ passwordLoading ? '修改中...' : '确认修改' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 导入历史弹窗 -->
    <div v-if="showHistoryModal" class="modal-overlay" @click.self="closeHistoryModal">
      <div class="modal-content large">
        <div class="modal-header">
          <h3>导入历史 - {{ currentHistoryTaskSet?.name }}</h3>
          <button class="close-btn" @click="closeHistoryModal">×</button>
        </div>
        <div class="modal-body">
          <div v-if="importBatches.length === 0" class="empty-hint">暂无导入记录</div>
          <div v-else class="history-list">
            <div v-for="batch in importBatches" :key="batch.batch_id" class="history-item">
              <div class="history-info">
                <div class="history-time">{{ new Date(batch.import_time).toLocaleString() }}</div>
                <div class="history-meta">
                  <span class="history-user">导入者: {{ batch.imported_by_name }}</span>
                  <span class="history-count">任务数: {{ batch.task_count }}</span>
                </div>
              </div>
              <button class="btn-view-diff" @click="viewBatchDiff(batch)">查看变更</button>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="closeHistoryModal">关闭</button>
        </div>
      </div>
    </div>

    <!-- Diff对比弹窗 -->
    <div v-if="showDiffModal" class="modal-overlay" @click.self="closeDiffModal">
      <div class="modal-content large fullscreen-modal">
        <div class="modal-header">
          <h3>变更对比 - {{ currentDiff?.prompt }}</h3>
          <button class="close-btn" @click="closeDiffModal">×</button>
        </div>
        <div class="modal-body diff-body">
          <div v-if="!currentDiff?.task_exists" class="diff-warning">
            ⚠️ 该任务已被删除，以下显示的是导入时的原始数据
          </div>

          <!-- Rubrics对比 -->
          <div class="diff-section">
            <h4>Rubrics 对比</h4>
            <div v-if="currentDiff?.rubrics?.length === 0" class="empty-hint">暂无 Rubric 数据</div>
            <div v-else class="diff-list">
              <div v-for="(rubric, idx) in currentDiff?.rubrics" :key="idx" class="diff-item" :class="rubric.change_type">
                <div class="diff-header">
                  <span class="diff-badge" :class="rubric.change_type">{{ getChangeTypeText(rubric.change_type) }}</span>
                  <span class="diff-title">{{ rubric.criterion }}</span>
                </div>
                <div class="diff-content">
                  <div v-if="rubric.change_type === 'removed'" class="diff-old">
                    <div class="diff-label">原始值:</div>
                    <div class="diff-value">分数: {{ rubric.old?.point }}, 维度: {{ rubric.old?.axis || '-' }}, 勾选: {{ rubric.old?.selected ? '是' : '否' }}</div>
                  </div>
                  <div v-else-if="rubric.change_type === 'added'" class="diff-new">
                    <div class="diff-label">当前值:</div>
                    <div class="diff-value">分数: {{ rubric.new?.point }}, 维度: {{ rubric.new?.axis || '-' }}, 勾选: {{ rubric.new?.selected ? '是' : '否' }}</div>
                  </div>
                  <div v-else-if="rubric.change_type === 'modified'" class="diff-modified">
                    <div class="diff-old">
                      <div class="diff-label">原始值:</div>
                      <div class="diff-value">
                        分数: {{ rubric.old?.point }}
                        <span v-if="rubric.old?.point !== rubric.new?.point" class="changed">→ {{ rubric.new?.point }}</span>
                        , 维度: {{ rubric.old?.axis || '-' }}
                        <span v-if="rubric.old?.axis !== rubric.new?.axis" class="changed">→ {{ rubric.new?.axis || '-' }}</span>
                        , 勾选: {{ rubric.old?.selected ? '是' : '否' }}
                        <span v-if="rubric.old?.selected !== rubric.new?.selected" class="changed">→ {{ rubric.new?.selected ? '是' : '否' }}</span>
                      </div>
                    </div>
                  </div>
                  <div v-else class="diff-unchanged">
                    <div class="diff-value">分数: {{ rubric.old?.point }}, 维度: {{ rubric.old?.axis || '-' }}, 勾选: {{ rubric.old?.selected ? '是' : '否' }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Answers对比 -->
          <div class="diff-section">
            <h4>参考答案对比</h4>
            <div class="diff-summary">
              原始: {{ currentDiff?.answers?.original_count }}条，当前: {{ currentDiff?.answers?.current_count }}条
            </div>
            <div v-if="currentDiff?.answers?.removed?.length > 0" class="diff-subsection">
              <h5 class="diff-subtitle removed">已删除 ({{ currentDiff?.answers?.removed?.length }})</h5>
              <div v-for="(answer, idx) in currentDiff?.answers?.removed" :key="'removed-'+idx" class="diff-answer-item removed">
                {{ answer.slice(0, 100) }}{{ answer.length > 100 ? '...' : '' }}
              </div>
            </div>
            <div v-if="currentDiff?.answers?.added?.length > 0" class="diff-subsection">
              <h5 class="diff-subtitle added">新增 ({{ currentDiff?.answers?.added?.length }})</h5>
              <div v-for="(answer, idx) in currentDiff?.answers?.added" :key="'added-'+idx" class="diff-answer-item added">
                {{ answer.slice(0, 100) }}{{ answer.length > 100 ? '...' : '' }}
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="closeDiffModal">关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, computed, h, defineComponent, resolveComponent } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import TreeNode from '../components/TreeNode.vue'

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

        // 解析 rubrics（去重：根据 collection_name + prompt + criterion）
        const rubricMap = new Map()
        // 解析 answers（去重：根据 collection_name + prompt + answer）
        const answerMap = new Map()
        // 存储任务的 completed 状态
        const taskCompletedMap = new Map()
        // 存储任务的 tree 数据
        const taskTreeMap = new Map()

        tasks.forEach(task => {
          const collectionName = task.collection_name?.trim() || ''
          const prompt = task.prompt?.trim() || ''
          const taskKey = `${collectionName}|${prompt}`

          // 保存任务的 completed 状态
          taskCompletedMap.set(taskKey, task.completed === true)

          // 保存任务的 tree 数据
          if (task.tree && task.tree.tree) {
            taskTreeMap.set(taskKey, {
              collection_name: collectionName,
              prompt: prompt,
              tree: task.tree
            })
          }

          // 解析 rubrics
          if (task.rubrics && Array.isArray(task.rubrics)) {
            task.rubrics.forEach(rubric => {
              const criterion = rubric.criterion?.trim() || ''
              if (!criterion) return

              const key = `${collectionName}|${prompt}|${criterion}`
              if (!rubricMap.has(key)) {
                rubricMap.set(key, {
                  collection_name: collectionName,
                  prompt: prompt,
                  criterion: criterion,
                  axis: rubric.axis?.trim() || '',
                  point: parseInt(rubric.point) || 0,
                  selected: rubric.selected === true
                })
              }
            })
          }

          // 解析 answers
          if (task.answers && Array.isArray(task.answers)) {
            task.answers.forEach(answer => {
              const answerContent = answer?.trim()
              if (!answerContent) return

              const key = `${collectionName}|${prompt}|${answerContent}`
              if (!answerMap.has(key)) {
                answerMap.set(key, {
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
          taskSetName: r.collection_name,
          taskName: r.prompt,
          rubric: r.criterion,
          dimension: r.axis,
          score: r.point
        }))

        resolve({
          rubrics: uniqueRubrics,
          answers: uniqueAnswers,
          previewRecords: previewRecords,
          taskCompleted: Object.fromEntries(taskCompletedMap),
          trees: Array.from(taskTreeMap.values())
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

// Tree 拖拽排序状态
const treeDraggingIndex = ref(null)
const treeDragOverIndex = ref(null)
const treeDragParentId = ref(null)

// 任务集合栏折叠状态
const isTaskSetCollapsed = ref(false)
const toggleTaskSetColumn = () => {
  isTaskSetCollapsed.value = !isTaskSetCollapsed.value
}

// Root 用户相关
const viewMode = ref('self') // 'self' 或 'user'
const allUsers = ref([])
const selectedUserId = ref(null)

// 任务分配管理
const showAssignModal = ref(false)
const assignedTaskSets = ref([])
const unassignedTaskSets = ref([])

// 批量导入
const showImportModal = ref(false)
const importFile = ref(null)
const importPreview = ref([])
const importRubrics = ref([])
const importAnswers = ref([])
const importTaskCompleted = ref({})
const importTrees = ref([])
const importLoading = ref(false)
const importProgress = ref({ current: 0, total: 0, type: '' })

// 修改密码
const showChangePasswordModal = ref(false)
const passwordForm = ref({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})
const passwordError = ref('')
const passwordLoading = ref(false)

// 导入历史相关
const showHistoryModal = ref(false)
const showDiffModal = ref(false)
const currentHistoryTaskSet = ref(null)
const importBatches = ref([])
const currentDiff = ref(null)
const currentBatchHistory = ref([])

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

// 修改密码
const closeChangePasswordModal = () => {
  showChangePasswordModal.value = false
  passwordForm.value = { oldPassword: '', newPassword: '', confirmPassword: '' }
  passwordError.value = ''
}

const changePassword = async () => {
  const { oldPassword, newPassword, confirmPassword } = passwordForm.value

  if (!oldPassword || !newPassword || !confirmPassword) {
    passwordError.value = '请填写所有字段'
    return
  }

  if (newPassword.length < 6) {
    passwordError.value = '新密码至少6位'
    return
  }

  if (newPassword !== confirmPassword) {
    passwordError.value = '两次输入的新密码不一致'
    return
  }

  passwordLoading.value = true
  passwordError.value = ''

  try {
    await axios.post('/api/change-password', {
      old_password: oldPassword,
      new_password: newPassword
    })
    passwordLoading.value = false
    alert('密码修改成功，请使用新密码重新登录')
    closeChangePasswordModal()
    logout()
  } catch (err) {
    passwordLoading.value = false
    passwordError.value = err.response?.data?.detail || '密码修改失败'
  }
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
  await loadAssignTaskSets()
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
  importTaskCompleted.value = {}
  importTrees.value = []
}

const handleFileSelect = async (event) => {
  const file = event.target.files[0]
  if (!file) return

  importFile.value = file

  try {
    const { rubrics, answers, previewRecords, taskCompleted, trees } = await parseImportFile(file)
    importRubrics.value = rubrics
    importAnswers.value = answers
    importPreview.value = previewRecords
    importTaskCompleted.value = taskCompleted || {}
    importTrees.value = trees || []

    if (rubrics.length === 0 && answers.length === 0 && trees.length === 0) {
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
    importTaskCompleted.value = {}
    importTrees.value = []
  }
}

const confirmImport = async () => {
  if (importRubrics.value.length === 0 && importAnswers.value.length === 0 && importTrees.value.length === 0) return

  importLoading.value = true
  importProgress.value = { current: 0, total: 1, type: 'import' }

  try {
    // 按 collection_name + prompt 分组
    const taskGroups = new Map()

    // 分组 rubrics
    importRubrics.value.forEach(rubric => {
      const key = `${rubric.collection_name}|${rubric.prompt}`
      if (!taskGroups.has(key)) {
        taskGroups.set(key, {
          collection_name: rubric.collection_name,
          prompt: rubric.prompt,
          rubrics: [],
          answers: [],
          tree: null
        })
      }
      taskGroups.get(key).rubrics.push(rubric)
    })

    // 分组 answers
    importAnswers.value.forEach(answer => {
      const key = `${answer.collection_name}|${answer.prompt}`
      if (!taskGroups.has(key)) {
        taskGroups.set(key, {
          collection_name: answer.collection_name,
          prompt: answer.prompt,
          rubrics: [],
          answers: [],
          tree: null
        })
      }
      taskGroups.get(key).answers.push(answer)
    })

    // 分组 trees
    importTrees.value.forEach(treeData => {
      const key = `${treeData.collection_name}|${treeData.prompt}`
      if (!taskGroups.has(key)) {
        taskGroups.set(key, {
          collection_name: treeData.collection_name,
          prompt: treeData.prompt,
          rubrics: [],
          answers: [],
          tree: null
        })
      }
      taskGroups.get(key).tree = treeData.tree
    })

    const uniqueTasks = Array.from(taskGroups.values())

    // 准备批量导入数据（一次性提交所有数据）
    const batchTasks = uniqueTasks.map(taskGroup => {
      const taskKey = `${taskGroup.collection_name}|${taskGroup.prompt}`
      const taskData = {
        collection_name: taskGroup.collection_name,
        prompt: taskGroup.prompt,
        completed: importTaskCompleted.value[taskKey] || false,
        rubrics: taskGroup.rubrics.map(r => ({
          criterion: r.criterion,
          axis: r.axis || '',
          point: parseInt(r.point) || 0,
          selected: r.selected === true
        })),
        answers: taskGroup.answers.map(a => a.answer)
      }
      // 如果有 tree 数据，添加到任务中
      if (taskGroup.tree) {
        taskData.tree = taskGroup.tree
      }
      return taskData
    })

    // 一次性批量导入所有数据
    const res = await axios.post('/api/admin/batch-import', { tasks: batchTasks })

    importLoading.value = false
    showImportModal.value = false
    importFile.value = null
    importPreview.value = []
    importRubrics.value = []
    importAnswers.value = []
    importTaskCompleted.value = {}
    importTrees.value = []

    alert(res.data.message)

    // 刷新任务列表
    await loadTaskSets()
    if (selectedSetId.value) {
      await selectTaskSet(selectedSetId.value)
    }
  } catch (err) {
    importLoading.value = false
    importTaskCompleted.value = {}
    importTrees.value = []
    alert('导入失败: ' + (err.response?.data?.detail || err.message))
  }
}

const loadAssignTaskSets = async () => {
  try {
    const [assignedRes, unassignedRes] = await Promise.all([
      axios.get(`/api/admin/users/${selectedUserId.value}/assigned-task-sets`),
      axios.get(`/api/admin/users/${selectedUserId.value}/unassigned-task-sets`)
    ])
    assignedTaskSets.value = assignedRes.data
    unassignedTaskSets.value = unassignedRes.data
  } catch (err) {
    console.error('加载任务集合分配数据失败:', err)
  }
}

const assignTaskSet = async (taskSetId) => {
  try {
    await axios.post(`/api/admin/assign-task-set?user_id=${selectedUserId.value}&task_set_id=${taskSetId}`)
    await loadAssignTaskSets()
    // 刷新任务列表
    if (selectedSetId.value) {
      await loadUserTaskSets(selectedUserId.value)
    }
  } catch (err) {
    alert('分配失败: ' + (err.response?.data?.detail || err.message))
  }
}

const unassignTaskSet = async (taskSetId) => {
  if (!confirm('确定要取消该任务集合的分配吗？')) return
  try {
    await axios.delete(`/api/admin/assign-task-set?user_id=${selectedUserId.value}&task_set_id=${taskSetId}`)
    await loadAssignTaskSets()
    // 刷新任务列表
    if (selectedSetId.value) {
      await loadUserTaskSets(selectedUserId.value)
    }
    // 如果当前查看的任务集合被取消了分配，清空详情
    if (selectedSetId.value === taskSetId) {
      currentTask.value = null
      selectedTaskId.value = null
      tasks.value = []
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

const exportTaskSet = async (set) => {
  try {
    const res = await axios.get(`/api/admin/task-sets/${set.id}/export`)
    const exportData = res.data

    // 创建并下载 JSON 文件
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${set.name}_export_${new Date().toISOString().slice(0, 10)}.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  } catch (err) {
    alert('导出失败: ' + (err.response?.data?.detail || err.message))
  }
}

// ==================== 导入历史与版本控制 ====================
const showImportHistory = async (set) => {
  currentHistoryTaskSet.value = set
  showHistoryModal.value = true
  await loadImportBatches(set.id)
}

const closeHistoryModal = () => {
  showHistoryModal.value = false
  currentHistoryTaskSet.value = null
  importBatches.value = []
}

const loadImportBatches = async (taskSetId) => {
  try {
    const res = await axios.get(`/api/admin/task-sets/${taskSetId}/import-batches`)
    importBatches.value = res.data
  } catch (err) {
    alert('加载导入历史失败: ' + (err.response?.data?.detail || err.message))
  }
}

const viewBatchDiff = async (batch) => {
  // 获取该批次下的所有历史记录
  try {
    const res = await axios.get(`/api/admin/task-sets/${currentHistoryTaskSet.value.id}/import-history`)
    currentBatchHistory.value = res.data.filter(h => h.import_batch_id === batch.batch_id)

    // 如果只有一条记录，直接显示diff
    if (currentBatchHistory.value.length === 1) {
      await viewSingleDiff(currentBatchHistory.value[0].id)
    } else if (currentBatchHistory.value.length > 1) {
      // 多条记录，让用户选择（简化处理：显示第一条）
      await viewSingleDiff(currentBatchHistory.value[0].id)
    }
  } catch (err) {
    alert('加载变更对比失败: ' + (err.response?.data?.detail || err.message))
  }
}

const viewSingleDiff = async (historyId) => {
  try {
    const res = await axios.get(`/api/admin/task-sets/${currentHistoryTaskSet.value.id}/import-history/${historyId}/diff`)
    currentDiff.value = res.data
    showDiffModal.value = true
  } catch (err) {
    alert('加载对比失败: ' + (err.response?.data?.detail || err.message))
  }
}

const closeDiffModal = () => {
  showDiffModal.value = false
  currentDiff.value = null
  currentBatchHistory.value = []
}

const getChangeTypeText = (type) => {
  const typeMap = {
    'added': '新增',
    'removed': '删除',
    'modified': '修改',
    'unchanged': '未变更'
  }
  return typeMap[type] || type
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

// ==================== 参考答案行内编辑 ====================
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

// ==================== 参考答案管理 ====================
const showAddReferenceAnswerModal = () => {
  openModal('添加参考答案', [
    { label: '内容', type: 'textarea', value: '', placeholder: '请输入参考答案内容' }
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
  if (!confirm('确定要删除这个参考答案吗？')) return
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
    console.log('任务详情返回:', res.data)
    currentTask.value = res.data
  } catch (err) {
    console.error('加载任务详情失败:', err)
  }
}

// 切换 tree node 选择状态
const toggleTreeNode = async (node) => {
  try {
    await axios.patch(`/api/tree-nodes/${node.id}/selection`, {
      selected: !node.selected
    })
    node.selected = !node.selected
  } catch (err) {
    console.error('更新 tree node 失败:', err)
  }
}

// 更新 tree node
const updateTreeNode = async (updatedNode) => {
  try {
    // 调用后端 API 更新节点
    const res = await axios.patch(`/api/tree-nodes/${updatedNode.id}`, {
      claim: updatedNode.claim,
      rubrics: updatedNode.rubrics
    })

    // 递归查找并更新本地节点
    const updateNodeInTree = (node) => {
      if (node.id === updatedNode.id) {
        // 更新当前节点
        node.claim = res.data.claim
        node.rubrics = res.data.rubrics
        return true
      }
      // 递归查找子节点
      if (node.nodes) {
        for (const child of node.nodes) {
          if (updateNodeInTree(child)) {
            return true
          }
        }
      }
      return false
    }

    if (currentTask.value && currentTask.value.tree) {
      updateNodeInTree(currentTask.value.tree)
    }
  } catch (err) {
    console.error('更新节点失败:', err)
    alert('更新节点失败: ' + (err.response?.data?.detail || err.message))
  }
}

// 删除 tree node
const deleteTreeNode = async (nodeToDelete) => {
  try {
    // 调用后端 API 删除节点
    await axios.delete(`/api/tree-nodes/${nodeToDelete.id}`)

    // 递归查找并从本地树中删除节点
    const deleteNodeInTree = (node) => {
      if (node.nodes) {
        const index = node.nodes.findIndex(n => n.id === nodeToDelete.id)
        if (index !== -1) {
          node.nodes.splice(index, 1)
          return true
        }
        // 递归查找子节点
        for (const child of node.nodes) {
          if (deleteNodeInTree(child)) {
            return true
          }
        }
      }
      return false
    }

    if (currentTask.value && currentTask.value.tree) {
      deleteNodeInTree(currentTask.value.tree)
    }
  } catch (err) {
    console.error('删除节点失败:', err)
    alert('删除节点失败: ' + (err.response?.data?.detail || err.message))
  }
}

// 新增 tree node 子节点
const addTreeNodeChild = async ({ parentNode, childData }) => {
  console.log('addTreeNodeChild called:', { parentNode, childData })
  try {
    // 调用后端 API 添加子节点
    console.log('Sending POST to:', `/api/tree-nodes/${parentNode.id}/children`, 'with data:', childData)
    const res = await axios.post(`/api/tree-nodes/${parentNode.id}/children`, childData)
    console.log('Response:', res.data)
    const newChild = res.data

    // 递归查找父节点并添加子节点到本地树
    const addChildToNode = (node) => {
      if (node.id === parentNode.id) {
        // 找到父节点，添加子节点
        if (!node.nodes) {
          node.nodes = []
        }
        node.nodes.push(newChild)
        // 如果父节点是 leaf 类型，转换为 branch
        if (node.type === 'leaf') {
          node.type = 'branch'
        }
        return true
      }
      // 递归查找子节点
      if (node.nodes) {
        for (const child of node.nodes) {
          if (addChildToNode(child)) {
            return true
          }
        }
      }
      return false
    }

    if (currentTask.value && currentTask.value.tree) {
      addChildToNode(currentTask.value.tree)
    }
  } catch (err) {
    console.error('添加子节点失败:', err)
    alert('添加子节点失败: ' + (err.response?.data?.detail || err.message))
  }
}

// 更新树节点专业性标记
const updateTreeNodeProfessional = async ({ node, professional }) => {
  try {
    await axios.patch(`/api/tree-nodes/${node.id}/professional`, {
      professional
    })
    // 递归查找并更新本地状态 - 深拷贝并替换整个树来强制触发 Vue 响应式更新
    const updateNodeInTree = (n) => {
      if (n.id === node.id) {
        return { ...n, professional }
      }
      if (n.nodes && n.nodes.length > 0) {
        return { ...n, nodes: n.nodes.map(updateNodeInTree) }
      }
      return n
    }
    if (currentTask.value && currentTask.value.tree) {
      currentTask.value.tree = updateNodeInTree(currentTask.value.tree)
    }
  } catch (err) {
    console.error('更新专业性标记失败:', err)
    alert('更新失败: ' + (err.response?.data?.detail || err.message))
  }
}

// 更新树节点必答标记
const updateTreeNodeRequired = async ({ node, required }) => {
  try {
    await axios.patch(`/api/tree-nodes/${node.id}/required`, {
      required
    })
    // 递归查找并更新本地状态（包括所有子节点）
    const updateNodeInTree = (n) => {
      if (n.id === node.id) {
        // 更新当前节点及其所有后代
        const updateDescendants = (desc) => {
          const updated = { ...desc, required }
          if (desc.nodes && desc.nodes.length > 0) {
            updated.nodes = desc.nodes.map(updateDescendants)
          }
          return updated
        }
        return updateDescendants(n)
      }
      if (n.nodes && n.nodes.length > 0) {
        return { ...n, nodes: n.nodes.map(updateNodeInTree) }
      }
      return n
    }
    if (currentTask.value && currentTask.value.tree) {
      currentTask.value.tree = updateNodeInTree(currentTask.value.tree)
    }
  } catch (err) {
    console.error('更新必答标记失败:', err)
    alert('更新失败: ' + (err.response?.data?.detail || err.message))
  }
}

// 重新排序子节点
const reorderTreeNode = async ({ parentId, fromIndex, toIndex }) => {
  if (!parentId || fromIndex === undefined || toIndex === undefined || fromIndex === toIndex) return

  try {
    // 先更新本地状态
    const updateNodeInTree = (n) => {
      if (n.id === parentId && n.nodes) {
        const children = [...n.nodes]
        const [movedNode] = children.splice(fromIndex, 1)
        children.splice(toIndex > fromIndex ? toIndex - 1 : toIndex, 0, movedNode)
        return { ...n, nodes: children }
      }
      if (n.nodes) {
        return { ...n, nodes: n.nodes.map(updateNodeInTree) }
      }
      return n
    }

    if (currentTask.value && currentTask.value.tree) {
      currentTask.value.tree = updateNodeInTree(currentTask.value.tree)
    }

    // 调用后端 API 保存新顺序
    await axios.post(`/api/tree-nodes/${parentId}/reorder`, {
      from_index: fromIndex,
      to_index: toIndex > fromIndex ? toIndex - 1 : toIndex
    })
  } catch (err) {
    console.error('重新排序失败:', err)
    alert('排序保存失败: ' + (err.response?.data?.detail || err.message))
    // 刷新数据以恢复正确状态
    await fetchCurrentTask()
  }
}

// 处理 Tree 更新事件
const handleTreeUpdate = async (data) => {
  // 检查是否是重排序操作
  if (data && data.reorder) {
    const { parentId, fromIndex, toIndex } = data
    await reorderTreeNode({ parentId, fromIndex, toIndex })
    return
  }

  // 普通更新
  await updateTreeNode(data)
}

// Tree 拖拽开始
const handleTreeDragStart = ({ parentId, index }) => {
  treeDragParentId.value = parentId
  treeDraggingIndex.value = index
  treeDragOverIndex.value = null
}

// Tree 拖拽经过
const handleTreeDragOver = ({ parentId, index }) => {
  // 只允许在同一父节点内拖拽
  if (parentId === treeDragParentId.value && index !== treeDraggingIndex.value) {
    treeDragOverIndex.value = index
  }
}

// Tree 拖拽结束
const handleTreeDragEnd = () => {
  treeDraggingIndex.value = null
  treeDragOverIndex.value = null
  treeDragParentId.value = null
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

.change-password-btn {
  padding: 6px 16px;
  background: #1890ff;
  border: 1px solid #1890ff;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  color: white;
  transition: all 0.2s;
}

.change-password-btn:hover {
  background: #40a9ff;
  border-color: #40a9ff;
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
  position: relative;
  transition: width 0.3s ease;
}

.column-1.collapsed {
  width: 24px;
  min-width: 24px;
}

.column-1.collapsed .column-header,
.column-1.collapsed .column-content {
  display: none;
}

/* 折叠切换按钮 */
.collapse-toggle {
  position: absolute;
  right: -12px;
  top: 50%;
  transform: translateY(-50%);
  width: 12px;
  height: 60px;
  background: #d9d9d9;
  border-radius: 0 4px 4px 0;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
  transition: background 0.2s;
}

.collapse-toggle:hover {
  background: #1890ff;
}

.collapse-arrow {
  font-size: 8px;
  color: white;
  transition: transform 0.3s ease;
}

.collapse-arrow.collapsed {
  transform: rotate(180deg);
}

.column-1.collapsed .collapse-toggle {
  right: 0;
  border-radius: 0 4px 4px 0;
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
  margin-left: 4px;
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

.action-btn.export {
  background: #52c41a;
  color: white;
}

.action-btn.export:hover {
  background: #73d13d;
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

/* 任务集合分配样式 */
.assign-taskset-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 8px;
  border-bottom: 1px solid #f0f0f0;
  font-size: 14px;
}

.assign-taskset-item:last-child {
  border-bottom: none;
}

.taskset-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.taskset-name {
  font-weight: 500;
  color: #333;
}

.taskset-desc {
  font-size: 12px;
  color: #666;
}

/* 参考答案样式 */
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
  color: #333;
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

/* 参考答案编辑样式 */
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

/* 修改密码弹窗样式 */
.change-password-modal {
  background: white;
  border-radius: 8px;
  width: 90%;
  max-width: 400px;
  overflow: hidden;
}

.change-password-modal .modal-header {
  padding: 20px;
  border-bottom: 1px solid #e8e8e8;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.change-password-modal .modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.change-password-modal .modal-header .close-btn {
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
  transition: color 0.2s;
}

.change-password-modal .modal-header .close-btn:hover {
  color: #333;
}

.change-password-modal .modal-body {
  padding: 20px;
}

.change-password-modal .form-group {
  margin-bottom: 16px;
}

.change-password-modal .form-group:last-child {
  margin-bottom: 0;
}

.change-password-modal .form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #333;
  font-size: 14px;
}

.change-password-modal .form-group input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
  transition: border-color 0.2s;
}

.change-password-modal .form-group input:focus {
  outline: none;
  border-color: #1890ff;
}

.change-password-modal .error-message {
  color: #ff4d4f;
  font-size: 14px;
  text-align: center;
  margin-top: 8px;
}

.change-password-modal .modal-footer {
  padding: 16px 20px;
  border-top: 1px solid #e8e8e8;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.change-password-modal .modal-footer .btn-confirm:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

/* 导入历史弹窗样式 */
.history-list {
  max-height: 400px;
  overflow-y: auto;
}

.history-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid #e8e8e8;
  transition: background-color 0.2s;
}

.history-item:hover {
  background-color: #f5f5f5;
}

.history-info {
  flex: 1;
}

.history-time {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
}

.history-meta {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: #666;
}

.btn-view-diff {
  padding: 6px 16px;
  background: #1890ff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  transition: background-color 0.2s;
}

.btn-view-diff:hover {
  background: #40a9ff;
}

/* Diff对比弹窗样式 */
.diff-body {
  max-height: 60vh;
  overflow-y: auto;
  padding: 20px;
}

.diff-warning {
  background: #fff7e6;
  border: 1px solid #ffd591;
  border-radius: 4px;
  padding: 12px 16px;
  margin-bottom: 20px;
  color: #d46b08;
  font-size: 14px;
}

.diff-section {
  margin-bottom: 24px;
}

.diff-section h4 {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin: 0 0 12px 0;
  padding-bottom: 8px;
  border-bottom: 2px solid #e8e8e8;
}

.diff-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.diff-item {
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid #e8e8e8;
}

.diff-item.added {
  border-color: #b7eb8f;
  background: #f6ffed;
}

.diff-item.removed {
  border-color: #ffccc7;
  background: #fff2f0;
}

.diff-item.modified {
  border-color: #ffe58f;
  background: #fffbe6;
}

.diff-item.unchanged {
  background: #fafafa;
}

.diff-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: rgba(0, 0, 0, 0.03);
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.diff-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.diff-badge.added {
  background: #52c41a;
  color: white;
}

.diff-badge.removed {
  background: #ff4d4f;
  color: white;
}

.diff-badge.modified {
  background: #faad14;
  color: white;
}

.diff-badge.unchanged {
  background: #d9d9d9;
  color: #666;
}

.diff-title {
  font-weight: 500;
  color: #333;
  flex: 1;
}

.diff-content {
  padding: 12px;
  font-size: 13px;
}

.diff-label {
  color: #666;
  margin-bottom: 4px;
}

.diff-value {
  color: #333;
}

.diff-value .changed {
  color: #ff4d4f;
  font-weight: 500;
}

.diff-old {
  color: #666;
}

.diff-new {
  color: #52c41a;
}

.diff-summary {
  font-size: 14px;
  color: #666;
  margin-bottom: 12px;
  padding: 8px 12px;
  background: #f5f5f5;
  border-radius: 4px;
}

.diff-subsection {
  margin-top: 16px;
}

.diff-subtitle {
  font-size: 14px;
  font-weight: 600;
  margin: 0 0 8px 0;
  padding: 6px 10px;
  border-radius: 4px;
}

.diff-subtitle.removed {
  background: #fff2f0;
  color: #cf1322;
}

.diff-subtitle.added {
  background: #f6ffed;
  color: #389e0d;
}

.diff-answer-item {
  padding: 10px 12px;
  margin-bottom: 8px;
  border-radius: 4px;
  font-size: 13px;
  line-height: 1.5;
}

.diff-answer-item.removed {
  background: #fff2f0;
  border-left: 3px solid #ff4d4f;
}

.diff-answer-item.added {
  background: #f6ffed;
  border-left: 3px solid #52c41a;
}

/* 模态框头部样式 */
.modal-header {
  padding: 16px 20px;
  border-bottom: 1px solid #e8e8e8;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.modal-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.modal-header .close-btn {
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
  transition: color 0.2s;
}

.modal-header .close-btn:hover {
  color: #333;
}

.fullscreen-modal {
  width: 90%;
  max-width: 900px;
  max-height: 80vh;
}

/* Tree 组件样式 */
.tree-section {
  margin-top: 24px;
}

.section-title {
  margin: 16px 0;
  color: #666;
  font-size: 14px;
  font-weight: 500;
}

.tree-container {
  padding: 16px;
  background: #f5f5f5;
  border-radius: 8px;
}

/* Root 节点样式 */
.tree-node.is-root {
  background: white;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.tree-summary {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 12px;
  background: #f6ffed;
  border: 1px solid #b7eb8f;
  border-radius: 6px;
  margin-bottom: 12px;
  cursor: pointer;
}

.tree-summary-label {
  font-weight: 600;
  color: #52c41a;
  flex-shrink: 0;
}

.tree-summary-text {
  flex: 1;
  font-size: 14px;
  line-height: 1.6;
  color: #262626;
}

/* 展开图标 */
.tree-expand-icon {
  font-size: 12px;
  color: #1890ff;
  transition: transform 0.2s;
  margin-top: 4px;
  flex-shrink: 0;
}

.tree-expand-icon.expanded {
  transform: rotate(90deg);
}

.tree-expand-icon-placeholder {
  width: 12px;
  flex-shrink: 0;
}

/* 节点头部 - 层级背景色 - 使用 :deep 确保应用到子组件 */
:deep(.tree-node-header) {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 12px;
  margin: 4px 0;
  border-radius: 6px;
  transition: all 0.2s;
  cursor: pointer;
  border: 2px solid;
  pointer-events: auto;
}

:deep(.tree-node-header > *) {
  pointer-events: auto;
}

/* Level 1 - 浅蓝色 */
:deep(.tree-node-header.tree-level-1) {
  background-color: #e6f7ff !important;
  border-color: #1890ff !important;
}

:deep(.tree-node-header.tree-level-1:hover) {
  background-color: #bae7ff !important;
}

/* Level 2 - 浅绿色 */
:deep(.tree-node-header.tree-level-2) {
  background-color: #f6ffed !important;
  border-color: #52c41a !important;
}

:deep(.tree-node-header.tree-level-2:hover) {
  background-color: #d9f7be !important;
}

/* Level 3 - 浅橙色 */
:deep(.tree-node-header.tree-level-3) {
  background-color: #fff7e6 !important;
  border-color: #fa8c16 !important;
}

:deep(.tree-node-header.tree-level-3:hover) {
  background-color: #ffe7ba !important;
}

/* Level 4+ - 浅紫色 */
:deep(.tree-node-header.tree-level-4) {
  background-color: #f9f0ff !important;
  border-color: #722ed1 !important;
}

:deep(.tree-node-header.tree-level-4:hover) {
  background-color: #efdbff !important;
}

/* Leaf 节点 - 整体包裹样式 */
:deep(.tree-leaf-wrapper) {
  background: #fafafa;
  border: 2px solid #d9d9d9;
  border-radius: 8px;
  padding: 12px;
  margin: 8px 0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.06);
}

/* 叶子节点标题（claim） */
:deep(.tree-leaf-title) {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px 0;
  margin-bottom: 12px;
  border-bottom: 1px solid #e8e8e8;
}

:deep(.tree-leaf-claim) {
  flex: 1;
  font-size: 14px;
  line-height: 1.6;
  color: #262626;
  font-weight: 500;
}

/* 叶子节点样式 */
:deep(.tree-node.is-leaf-node) {
  margin: 8px 0;
}

/* 操作按钮 */
:deep(.tree-actions) {
  display: flex;
  gap: 4px;
  pointer-events: auto;
}

:deep(.tree-btn) {
  padding: 4px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  pointer-events: auto;
  position: relative;
  z-index: 10;
  white-space: nowrap;
  line-height: 1.5;
}

:deep(.tree-btn-edit) {
  background: #1890ff;
  color: white;
}

:deep(.tree-btn-edit:hover) {
  background: #40a9ff;
}

:deep(.tree-btn-delete) {
  background: #ff4d4f;
  color: white;
}

:deep(.tree-btn-delete:hover) {
  background: #ff7875;
}

:deep(.tree-btn-add) {
  background: #52c41a;
  color: white;
  width: auto;
  padding: 0 12px;
  height: 28px;
}

:deep(.tree-btn-add:hover) {
  background: #73d13d;
}

:deep(.tree-btn-remove) {
  background: #ff4d4f;
  color: white;
  font-size: 12px;
}

:deep(.tree-btn-save) {
  background: #52c41a;
  color: white;
  width: auto;
  padding: 0 16px;
}

:deep(.tree-btn-cancel) {
  background: #d9d9d9;
  color: #333;
  width: auto;
  padding: 0 16px;
}

/* 编辑模式 */
:deep(.tree-node.is-editing) {
  background: #fff;
  border: 2px solid #1890ff;
  border-radius: 8px;
  padding: 16px;
  margin: 8px 0;
}

:deep(.tree-edit-claim-wrapper) {
  margin-bottom: 12px;
}

:deep(.tree-edit-claim) {
  width: 100%;
  min-height: 60px;
  padding: 8px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
  line-height: 1.5;
  resize: vertical;
}

:deep(.tree-edit-claim:focus) {
  outline: none;
  border-color: #1890ff;
}

:deep(.tree-edit-input) {
  width: 100%;
  padding: 6px 8px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 13px;
}

:deep(.tree-edit-input:focus) {
  outline: none;
  border-color: #1890ff;
}

:deep(.tree-edit-score.negative-score) {
  background: #fff1f0;
  border-color: #ff4d4f;
  color: #cf1322;
}

:deep(.tree-rubric-edit-section) {
  margin: 12px 0;
}

:deep(.tree-rubrics-edit-table) {
  margin-bottom: 8px;
}

:deep(.tree-rubrics-edit-table td) {
  padding: 8px;
}

:deep(.tree-rubric-add-btn) {
  text-align: center;
  margin-top: 8px;
}

:deep(.tree-edit-actions) {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #e8e8e8;
}

/* 负分数红色背景 */
:deep(.rubric-score.negative-score) {
  background: #ffcccc !important;
  color: #cc0000 !important;
  font-weight: bold;
}

/* 复选框 */
.tree-checkbox {
  width: 18px;
  height: 18px;
  border: 2px solid #d9d9d9;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
  background: white;
  transition: all 0.2s;
  font-size: 12px;
}

.tree-checkbox:hover {
  border-color: #1890ff;
}

.tree-checkbox.checked {
  background: #1890ff;
  border-color: #1890ff;
  color: white;
}

/* Claim 文本 */
.tree-claim {
  flex: 1;
  font-size: 14px;
  line-height: 1.5;
  color: #262626;
}

/* 子节点容器 */
.tree-children {
  margin-top: 4px;
}

/* Rubric 表格 - 使用 :deep 确保应用到子组件 */
:deep(.tree-rubrics-wrapper) {
  margin: 8px 0 16px;
}

:deep(.tree-rubrics-table) {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  background: white;
  border: 2px solid #333 !important;
}

:deep(.tree-rubrics-table th),
:deep(.tree-rubrics-table td) {
  padding: 10px 12px;
  text-align: left;
  border: 1px solid #333 !important;
}

:deep(.tree-rubrics-table th) {
  background: #f0f0f0;
  font-weight: 600;
  color: #333;
  border-bottom: 2px solid #333 !important;
}

:deep(.tree-rubrics-table td) {
  color: #262626;
  border: 1px solid #999 !important;
}

:deep(.tree-rubrics-table .rubric-criterion) {
  width: auto;
}

:deep(.tree-rubrics-table .rubric-score) {
  width: 80px;
  text-align: center;
  font-weight: 500;
  border-left: 2px solid #333 !important;
}

:deep(.tree-rubrics-table tr:hover td) {
  background: #f5f5f5;
}

:deep(.tree-rubrics-table tr.negative-score td) {
  background: #ffcccc;
  color: #cc0000;
}

:deep(.tree-rubrics-table tr.negative-score .rubric-score) {
  font-weight: bold;
}
</style>
