import { expect, test } from 'claude-code/testing'

const STDOUT = [
  'PDF: /tmp/docs/guide.pdf',
  'Title: Commit и push от терминала',
  'Spec: /tmp/docs/doc.json',
  'Kind: guide | Author: Ivan Stoychev | Date: 13 November 2026',
].join('\n')

const row = (output: unknown, extra: Record<string, unknown> = {}) =>
  ({
    plugin: 'docs-designer',
    component: 'ToolUse',
    requestId: 'toolu_1',
    props: {
      tool_use_id: 'toolu_1',
      tool: 'Bash',
      input: { command: 'python3 render.py doc.json' },
      isRunning: false,
      isErrored: false,
      isInterrupted: false,
      output,
      ...extra,
    },
  }) as const

test('a finished render gets a document card in the chat', async ($, on) => {
  on('ui.render', ($, e) => $.ui.resolve(e).Text({ children: 'engine row' }))
  for (const surface of ['desktop', 'terminal'] as const) {
    const ui = await $.ui.mount({ ...row({ stdout: STDOUT, stderr: '' }), surface })
    expect((await ui.find({ type: 'Text', text: /Commit и push от терминала/ }))?.text).toBe('Commit и push от терминала')
    expect((await ui.find({ type: 'Text', text: /^Guide$/ }))?.text).toBe('Guide')
    expect((await ui.find({ type: 'Text', text: /guide\.pdf/ }))?.text).toBe('guide.pdf')
    expect(await ui.find({ type: 'Button', key: 'inspect-toolu_1' })).toBeTruthy()
    expect(await ui.find({ type: 'Text', text: 'engine row' })).toBeTruthy()
    await ui.unmount()
  }
})

test('other commands, running and failed renders get no card', async ($, on) => {
  on('ui.render', ($, e) => $.ui.resolve(e).Text({ children: 'engine row' }))
  for (const props of [
    row({ stdout: 'hello', stderr: '' }),
    row(undefined, { isRunning: true }),
    row({ stdout: STDOUT, stderr: '' }, { isErrored: true }),
  ]) {
    const ui = await $.ui.mount({ ...props, surface: 'desktop' })
    expect(await ui.find({ type: 'Button', key: 'inspect-toolu_1' })).toBeFalsy()
    await ui.unmount()
  }
})
