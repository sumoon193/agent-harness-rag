import { expect, test, type Page } from '@playwright/test'

test.describe.configure({ mode: 'serial' })

async function createRun(page: Page, query = '新员工入职到转正要办哪些事项？') {
  await page.goto('/')
  await page.getByPlaceholder('输入 HR 流程问题').fill(query)
  await page.getByRole('button', { name: /创建 Run/ }).click()
  await expect(page.getByText('awaiting_approval').first()).toBeVisible({ timeout: 10_000 })
  await expect(page.getByTestId('approval-card')).toBeVisible()
}

async function openTab(page: Page, name: RegExp) {
  await page.getByRole('tab', { name }).click()
}

test('上传页显示真实入库任务状态', async ({ page }) => {
  await page.goto('/documents')

  const fileChooserPromise = page.waitForEvent('filechooser')
  await page.locator('.el-upload-dragger').click()
  const fileChooser = await fileChooserPromise
  await fileChooser.setFiles({
    name: `module11-${Date.now()}.md`,
    mimeType: 'text/markdown',
    buffer: Buffer.from('# 入职制度\n\n新员工入职当天提交材料并签署劳动合同。'),
  })

  const status = page.getByTestId('ingestion-status')
  await expect(status).toContainText('ready', { timeout: 10_000 })
  await expect(status).toContainText('Task ID')
  await expect(status).toContainText('Document ID')
  await expect(status).toContainText('Progress')
  await expect(status).toContainText('ing_')
  await expect(status).toContainText('doc_')
})

test('Agent 控制台能创建 Run 并显示 SSE 与 steps', async ({ page }) => {
  await createRun(page)

  const timeline = page.getByTestId('step-timeline')
  await expect(timeline).toContainText('run_created')
  await expect(timeline).toContainText('evidence_retrieved')
  await expect(timeline).toContainText('plan_created')
  await expect(timeline).toContainText('tool_approval_requested')
  await expect(timeline).toContainText('run_status', { timeout: 10_000 })
})

test('approval card 阻断写入工具执行并支持 Approve、Edit、Reject', async ({ page }) => {
  await createRun(page, '帮我创建入职到转正工单')
  await expect(page.getByTestId('approval-card')).not.toContainText('TK-')
  await page.getByTestId('approval-card').getByRole('button', { name: /Approve/ }).click()
  await expect(page.getByText('completed').first()).toBeVisible({ timeout: 10_000 })
  await openTab(page, /Tools/)
  await expect(page.getByTestId('tool-list')).toContainText('TK-')

  await createRun(page, '帮我创建转正复核工单')
  await page.getByTestId('approval-card').getByRole('button', { name: /Edit/ }).click()
  await expect(page.getByRole('dialog')).toBeVisible()
  await page.getByRole('dialog').locator('textarea').fill(JSON.stringify({
    title: 'E2E 修改后的工单',
    description: '通过审批编辑后执行',
    priority: 'high',
    category: '转正',
  }, null, 2))
  await page.getByRole('button', { name: /提交编辑/ }).click()
  await expect(page.getByText('completed').first()).toBeVisible({ timeout: 10_000 })
  await openTab(page, /Tools/)
  await expect(page.getByTestId('tool-list')).toContainText('E2E 修改后的工单')
  await expect(page.getByTestId('tool-list')).toContainText('high')
  await expect(page.getByTestId('tool-list')).toContainText('TK-')

  await createRun(page, '帮我创建请假工单')
  await page.getByTestId('approval-card').getByRole('button', { name: /Reject/ }).click()
  await expect(page.getByText('completed').first()).toBeVisible({ timeout: 10_000 })
  await expect(page.getByTestId('answer-text')).toContainText('已拒绝执行写入型工具')
  await openTab(page, /Approval/)
  await expect(page.getByTestId('approval-list')).toContainText('reject')
})

test('citations 面板显示来源、章节、页码和分数', async ({ page }) => {
  await createRun(page)
  await openTab(page, /Evidence/)

  const citations = page.getByTestId('citation-panel')
  await expect(citations).toContainText('员工入职与转正管理制度')
  await expect(citations).toContainText('第二章 入职办理')
  await expect(citations).toContainText('第3页')
  await expect(citations).toContainText('检索 0.92')
  await expect(citations).toContainText('重排 0.95')
})

test('trace 面板按顺序展示步骤', async ({ page }) => {
  await createRun(page)

  const timeline = page.getByTestId('step-timeline')
  await expect(timeline).toContainText('run_status', { timeout: 10_000 })

  const text = await timeline.innerText()
  const expectedOrder = [
    'run_created',
    'run_started',
    'evidence_retrieved',
    'plan_created',
    'tool_executed',
    'tool_approval_requested',
    'run_status',
  ]
  const positions = expectedOrder.map((name) => text.indexOf(name))

  for (const position of positions) {
    expect(position).toBeGreaterThanOrEqual(0)
  }
  for (let index = 1; index < positions.length; index += 1) {
    expect(positions[index]).toBeGreaterThan(positions[index - 1])
  }
})
