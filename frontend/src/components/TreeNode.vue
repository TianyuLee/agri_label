<template>
  <div v-if="isEditing" class="tree-node is-editing" :style="indentStyle">
    <textarea
      v-model="editClaim"
      class="tree-edit-claim"
      placeholder="请输入节点内容"
    ></textarea>
    <div v-if="isLeaf" class="tree-rubric-edit-section">
      <table class="tree-rubrics-table tree-rubrics-edit-table">
        <thead>
          <tr>
            <th>评分标准</th>
            <th>分数</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(r, idx) in editRubrics"
            :key="idx"
            :class="{ 'negative-score': Number(r.score) < 0 }"
          >
            <td>
              <input
                v-model="editRubrics[idx].criterion"
                class="tree-edit-input"
                placeholder="评分标准"
              />
            </td>
            <td>
              <input
                v-model.number="editRubrics[idx].score"
                type="number"
                class="tree-edit-input tree-edit-score"
                :class="{ 'negative-score': Number(r.score) < 0 }"
                placeholder="分数"
              />
            </td>
            <td>
              <button type="button" class="tree-btn tree-btn-remove" @click="removeRubric(idx)">
                删除
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      <button type="button" class="tree-btn tree-btn-add" @click="addRubric">+ 添加行</button>
    </div>
    <div class="tree-edit-actions">
      <button type="button" class="tree-btn tree-btn-save" @click="saveEdit">保存</button>
      <button type="button" class="tree-btn tree-btn-cancel" @click="cancelEdit">取消</button>
    </div>
  </div>

  <div v-else-if="isRoot" class="tree-node is-root">
    <div class="tree-summary">
      <span class="tree-summary-label">【总结】</span>
      <span class="tree-summary-text">{{ node.claim }}</span>
      <div class="tree-actions-vertical">
        <div class="tree-actions-primary" @click.stop>
          <button type="button" class="tree-btn tree-btn-edit" @click.stop="startEdit">编辑</button>
        </div>
        <div class="tree-actions-secondary">
          <button type="button" class="tree-btn tree-btn-add-branch" @click.stop="addBranchChild" title="添加分支子节点">分支</button>
          <button type="button" class="tree-btn tree-btn-add-leaf" @click.stop="addLeafChild" title="添加叶子子节点">叶子</button>
        </div>
      </div>
    </div>
    <div v-if="hasChildren" class="tree-children tree-children-root">
      <TreeNode
        v-for="(child, index) in node.nodes"
        :key="child.id || index"
        :node="child"
        :level="level + 1"
        @toggle="$emit('toggle', $event)"
        @update="$emit('update', $event)"
        @delete="$emit('delete', $event)"
        @add-child="$emit('add-child', $event)"
        @update-professional="$emit('update-professional', $event)"
        @update-required="$emit('update-required', $event)"
      />
    </div>
  </div>

  <!-- Branch 节点 -->
  <div v-else-if="node.type === 'branch'" class="tree-node is-branch-node">
    <div
      class="tree-node-header"
      :class="getLevelClass(level)"
      :style="indentStyle"
      @click="toggleExpand"
    >
      <label v-if="!isRoot" class="required-checkbox-label" :class="{ checked: node.required }" @click.stop>
        <input
          type="checkbox"
          :checked="node.required"
          @change="toggleRequired"
          class="required-checkbox"
        />
        <span class="required-pin">📌</span>
      </label>
      <span class="tree-expand-icon" :class="{ expanded: isExpanded }">▶</span>
      <div class="tree-claim">{{ node.claim }}</div>
      <div class="tree-actions-vertical">
        <div class="tree-actions-primary">
          <button type="button" class="tree-btn tree-btn-edit" @click.stop="startEdit">编辑</button>
          <button v-if="!isRoot" type="button" class="tree-btn tree-btn-delete" @click.stop="handleDelete">删除</button>
        </div>
        <div class="tree-actions-secondary">
          <button type="button" class="tree-btn tree-btn-add-branch" @click.stop="addBranchChild" title="添加分支子节点">分支</button>
          <button type="button" class="tree-btn tree-btn-add-leaf" @click.stop="addLeafChild" title="添加叶子子节点">叶子</button>
        </div>
      </div>
    </div>
    <!-- Branch 节点也可以有表格 -->
    <div v-if="node.rubrics && node.rubrics.length > 0" class="tree-branch-rubrics">
      <div class="tree-rubrics-wrapper">
        <table class="tree-rubrics-table">
          <thead>
            <tr>
              <th class="rubric-criterion">评分标准</th>
              <th class="rubric-score">分数</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(r, idx) in node.rubrics"
              :key="idx"
              :class="{ 'negative-score': Number(r.score) < 0 }"
            >
              <td class="rubric-criterion">{{ r.criterion }}</td>
              <td class="rubric-score" :class="{ 'negative-score': Number(r.score) < 0 }">
                {{ r.score }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    <div v-if="isExpanded" class="tree-children-container">
      <TreeNode
        v-for="(child, index) in node.nodes"
        :key="child.id || index"
        :node="child"
        :level="level + 1"
        @toggle="$emit('toggle', $event)"
        @update="$emit('update', $event)"
        @delete="$emit('delete', $event)"
        @add-child="$emit('add-child', $event)"
        @update-professional="$emit('update-professional', $event)"
        @update-required="$emit('update-required', $event)"
      />
    </div>
  </div>

  <!-- Leaf 节点 -->
  <div v-else-if="node.type === 'leaf'" class="tree-node is-leaf-node">
    <div class="tree-leaf-wrapper" :class="{ 'professional-active': node.professional }" :style="indentStyle">
      <div class="tree-leaf-header" @click="toggleLeafExpand">
        <label v-if="!isRoot" class="required-checkbox-label" :class="{ checked: node.required }" @click.stop>
          <input
            type="checkbox"
            :checked="node.required"
            @change="toggleRequired"
            class="required-checkbox"
          />
          <span class="required-pin">📌</span>
        </label>
        <span class="tree-expand-icon" :class="{ expanded: isLeafExpanded }">▶</span>
        <span class="tree-leaf-claim">{{ node.claim }}</span>
        <div class="tree-leaf-actions-wrapper" @click.stop>
          <div class="tree-actions">
            <button type="button" class="tree-btn tree-btn-edit" @click.stop="startEdit">编辑</button>
            <button v-if="!isRoot" type="button" class="tree-btn tree-btn-delete" @click.stop="handleDelete">删除</button>
          </div>
          <div class="tree-professional-tag">
            <label class="professional-label">
              <input
                type="checkbox"
                :checked="node.professional"
                @change="toggleProfessional"
                class="professional-checkbox"
              />
              <span class="professional-text">专业性</span>
            </label>
          </div>
        </div>
      </div>
      <div v-if="isLeafExpanded && node.rubrics && node.rubrics.length > 0" class="tree-rubrics-wrapper">
        <table class="tree-rubrics-table">
          <thead>
            <tr>
              <th class="rubric-criterion">评分标准</th>
              <th class="rubric-score">分数</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(r, idx) in node.rubrics"
              :key="idx"
              :class="{ 'negative-score': Number(r.score) < 0 }"
            >
              <td class="rubric-criterion">{{ r.criterion }}</td>
              <td class="rubric-score" :class="{ 'negative-score': Number(r.score) < 0 }">
                {{ r.score }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  node: {
    type: Object,
    required: true
  },
  level: {
    type: Number,
    default: 0
  }
})

const emit = defineEmits(['toggle', 'update', 'delete', 'add-child', 'update-professional', 'update-required'])

const isExpanded = ref(props.level === 0)
const isLeafExpanded = ref(false)  // 叶子节点表格展开状态，默认折叠
const isEditing = ref(false)
const editClaim = ref('')
const editRubrics = ref([])

const hasChildren = computed(() => props.node.nodes && props.node.nodes.length > 0)
const hasRubrics = computed(() => props.node.rubrics && props.node.rubrics.length > 0)
const isRoot = computed(() => props.level === 0)
const isLeaf = computed(() => !hasChildren.value)

const indentStyle = computed(() => ({
  marginLeft: props.level <= 1 ? '0' : `${(props.level - 1) * 24}px`
}))

const toggleExpand = () => {
  isExpanded.value = !isExpanded.value
}

const toggleLeafExpand = () => {
  isLeafExpanded.value = !isLeafExpanded.value
}

const handleToggle = () => {
  emit('toggle', props.node)
}

const startEdit = () => {
  editClaim.value = props.node.claim
  editRubrics.value = JSON.parse(JSON.stringify(props.node.rubrics || []))
  isEditing.value = true
}

const saveEdit = () => {
  const updatedNode = {
    ...props.node,
    claim: editClaim.value,
    rubrics: editRubrics.value
  }
  emit('update', updatedNode)
  isEditing.value = false
}

const cancelEdit = () => {
  isEditing.value = false
}

const handleDelete = () => {
  if (confirm('确定要删除这个节点吗？')) {
    emit('delete', props.node)
  }
}

// 切换专业性标记
const toggleProfessional = () => {
  const newProfessional = !props.node.professional
  emit('update-professional', {
    node: props.node,
    professional: newProfessional
  })
}

// 切换必答标记
const toggleRequired = () => {
  const newRequired = !props.node.required
  emit('update-required', {
    node: props.node,
    required: newRequired
  })
}

// 添加分支子节点
const addBranchChild = () => {
  console.log('addBranchChild clicked')
  const claim = prompt('请输入分支子节点的内容：')
  console.log('Prompt result:', claim)
  if (claim && claim.trim()) {
    console.log('Emitting add-child event')
    emit('add-child', {
      parentNode: props.node,
      childData: {
        claim: claim.trim(),
        type: 'branch',
        rubrics: [],
        nodes: []
      }
    })
  }
}

// 添加叶子子节点
const addLeafChild = () => {
  const claim = prompt('请输入叶子子节点的内容：')
  if (claim && claim.trim()) {
    emit('add-child', {
      parentNode: props.node,
      childData: {
        claim: claim.trim(),
        type: 'leaf',
        rubrics: [
          { criterion: '', score: 0 }
        ],
        nodes: []
      }
    })
  }
}

const updateRubric = (idx, field, value) => {
  editRubrics.value[idx][field] = value
}

const addRubric = () => {
  editRubrics.value.push({ criterion: '', score: 0 })
}

const removeRubric = (idx) => {
  editRubrics.value.splice(idx, 1)
}

const getLevelClass = (lvl) => {
  return `tree-level-${Math.min(lvl, 4)}`
}
</script>

<style scoped>
.tree-node {
  margin: 8px 0;
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
  color: #333;
  line-height: 1.5;
}

.tree-node-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: white;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.tree-node-header:hover {
  background: #f5f5f5;
  border-color: #1890ff;
}

.tree-expand-icon {
  font-size: 10px;
  color: #999;
  transition: transform 0.2s;
  width: 16px;
  text-align: center;
}

.tree-expand-icon.expanded {
  transform: rotate(90deg);
}

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
  font-size: 12px;
}

.tree-checkbox.checked {
  background: #1890ff;
  border-color: #1890ff;
  color: white;
}

.tree-claim {
  flex: 1;
  font-weight: 500;
  color: #333;
  line-height: 1.4;
}

.tree-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

.tree-btn {
  padding: 4px 8px;
  font-size: 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.tree-btn-edit {
  background: #e6f7ff;
  color: #1890ff;
}

.tree-btn-edit:hover {
  background: #1890ff;
  color: white;
}

.tree-btn-delete {
  background: #fff1f0;
  color: #ff4d4f;
}

.tree-btn-delete:hover {
  background: #ff4d4f;
  color: white;
}

.tree-children {
  margin-left: 16px;
  padding-left: 16px;
  border-left: 2px solid #e8e8e8;
}

/* 根节点下的一级子节点不缩进，与总结并列 */
.tree-children-root {
  margin-left: 0;
  padding-left: 0;
  border-left: none;
  margin-top: 12px;
}

.tree-children-container {
  margin-top: 8px;
  margin-left: 24px;
}

/* Leaf node */
.tree-leaf-wrapper {
  background: #fafafa;
  border: 2px solid #d9d9d9;
  border-radius: 8px;
  padding: 12px;
  margin: 8px 0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.06);
  transition: border-color 0.2s;
}

.tree-leaf-wrapper.professional-active {
  border-color: #ff4d4f;
  background: #fff1f0;
}

.tree-leaf-header {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 8px;
  cursor: pointer;
}

.tree-leaf-actions-wrapper {
  display: flex;
  flex-direction: column;
  gap: 6px;
  align-items: flex-end;
}

.tree-leaf-header:hover .tree-leaf-claim {
  color: #1890ff;
}

.tree-leaf-claim {
  flex: 1;
  font-weight: 500;
  color: #333;
  line-height: 1.4;
}

.tree-rubrics-wrapper {
  margin-top: 12px;
}

.tree-rubrics-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  border: 1px solid #d9d9d9;
}

.tree-rubrics-table th,
.tree-rubrics-table td {
  padding: 8px 12px;
  text-align: left;
  border: 1px solid #d9d9d9;
}

.tree-rubrics-table th {
  background: #f0f0f0;
  font-weight: 600;
  color: #333;
}

.tree-rubrics-table td {
  background: white;
}

.tree-rubrics-table .rubric-criterion {
  width: 85%;
}

.tree-rubrics-table .rubric-score {
  width: 15%;
  text-align: center;
  font-weight: 600;
  color: #1890ff;
}

.tree-rubrics-table tr.negative-score td {
  background: #ffcccc !important;
}

.tree-rubrics-table tr.negative-score .rubric-score {
  color: #cc0000 !important;
}

/* Edit mode */
.is-editing {
  background: #f6ffed;
  border: 2px solid #52c41a;
  border-radius: 8px;
  padding: 12px;
}

.tree-edit-claim {
  width: 100%;
  min-height: 60px;
  padding: 8px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
  resize: vertical;
  margin-bottom: 12px;
}

.tree-rubric-edit-section {
  margin-bottom: 12px;
}

.tree-rubrics-edit-table {
  margin-bottom: 8px;
}

.tree-edit-input {
  width: 100%;
  padding: 6px 8px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 13px;
}

.tree-edit-score {
  width: 80px;
  text-align: center;
}

.tree-edit-score.negative-score {
  background: #ffcccc;
  border-color: #ff4d4f;
  color: #cc0000;
}

.tree-edit-actions {
  display: flex;
  gap: 8px;
}

.tree-btn-save {
  background: #52c41a;
  color: white;
}

.tree-btn-save:hover {
  background: #73d13d;
}

.tree-btn-cancel {
  background: #f5f5f5;
  color: #666;
}

.tree-btn-cancel:hover {
  background: #d9d9d9;
}

.tree-btn-add {
  background: #e6f7ff;
  color: #1890ff;
  padding: 6px 12px;
}

.tree-btn-add:hover {
  background: #1890ff;
  color: white;
}

.tree-btn-add-branch {
  background: #fff7e6;
  color: #fa8c16;
  padding: 4px 8px;
  font-size: 12px;
}

.tree-btn-add-branch:hover {
  background: #fa8c16;
  color: white;
}

.tree-btn-add-leaf {
  background: #f6ffed;
  color: #52c41a;
  padding: 4px 8px;
  font-size: 12px;
}

.tree-btn-add-leaf:hover {
  background: #52c41a;
  color: white;
}

/* 垂直排列的按钮组 */
.tree-actions-vertical {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: flex-end;
}

.tree-actions-primary {
  display: flex;
  gap: 4px;
}

.tree-actions-secondary {
  display: flex;
  gap: 4px;
}

.tree-btn-remove {
  background: #fff1f0;
  color: #ff4d4f;
}

.tree-btn-remove:hover {
  background: #ff4d4f;
  color: white;
}

/* Level colors */
.tree-node-header.tree-level-1 {
  background-color: #e6f7ff;
  border-color: #1890ff;
}

.tree-node-header.tree-level-1:hover {
  background-color: #bae7ff;
}

.tree-node-header.tree-level-2 {
  background-color: #f6ffed;
  border-color: #52c41a;
}

.tree-node-header.tree-level-2:hover {
  background-color: #d9f7be;
}

.tree-node-header.tree-level-3 {
  background-color: #fff7e6;
  border-color: #fa8c16;
}

.tree-node-header.tree-level-3:hover {
  background-color: #ffe7ba;
}

.tree-node-header.tree-level-4 {
  background-color: #f9f0ff;
  border-color: #722ed1;
}

.tree-node-header.tree-level-4:hover {
  background-color: #efdbff;
}

/* Branch 节点的表格样式 */
.tree-branch-rubrics {
  margin: 12px 0 12px 24px;
  padding: 12px;
  background: #fafafa;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
}

.tree-branch-rubrics .tree-rubrics-wrapper {
  margin-top: 0;
}

/* 专业性标签样式 */
.tree-professional-tag {
  display: flex;
  justify-content: flex-end;
}

.professional-label {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  padding: 4px 8px;
  background: #f0f0f0;
  border-radius: 4px;
  font-size: 12px;
  transition: all 0.2s;
}

.professional-label:hover {
  background: #e0e0e0;
}

.professional-checkbox {
  width: 14px;
  height: 14px;
  cursor: pointer;
  margin: 0;
}

.professional-text {
  color: #666;
  user-select: none;
}

.professional-label:has(.professional-checkbox:checked) {
  background: #e6f7ff;
  border-color: #1890ff;
}

.professional-label:has(.professional-checkbox:checked) .professional-text {
  color: #1890ff;
  font-weight: 500;
}

/* 必答复选框样式 */
.required-checkbox-label {
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  width: 22px;
  height: 22px;
  background: #f5f5f5;
  border-radius: 4px;
  margin-right: 4px;
  transition: all 0.2s;
  position: relative;
}

.required-checkbox-label:hover {
  background: #e0e0e0;
}

.required-checkbox {
  width: 16px;
  height: 16px;
  cursor: pointer;
  margin: 0;
  opacity: 0.3;
  transition: opacity 0.2s;
}

.required-checkbox-label.checked .required-checkbox,
.required-checkbox-label:has(.required-checkbox:checked) .required-checkbox {
  opacity: 1;
}

.required-pin {
  position: absolute;
  font-size: 12px;
  opacity: 0;
  transition: opacity 0.2s;
  pointer-events: none;
}

.required-checkbox-label.checked .required-pin,
.required-checkbox-label:has(.required-checkbox:checked) .required-pin {
  opacity: 1;
}
</style>
