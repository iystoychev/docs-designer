import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { InspectedDoc, SentAsk } from '../types'

// The inspector itself is a small local server that ships with the docs-designer
// skill (scripts/inspect_server.py). This mod runs it, shows the current document
// in a pane, opens the interactive page in the app's browser, and hands every
// "Ask Claude" instruction from that page to Claude as a prompt that references
// the exact element.

const PANE = 'docs-inspector'
const TITLE = 'Document'

// Change a tag when that value's fields change: it declines what an earlier version stored.
const doc = atom({ plugin: 'docs-designer', key: 'doc' } as const, null as InspectedDoc | null, { shape: 'doc-1' })
const url = atom({ plugin: 'docs-designer', key: 'url' } as const, null as string | null, { shape: 'url-1' })
const problem = atom({ plugin: 'docs-designer', key: 'problem' } as const, null as string | null, { shape: 'problem-1' })
const sent = atom({ plugin: 'docs-designer', key: 'sent' } as const, [] as SentAsk[], { shape: 'sent-1' })

type Ask = {
  seq: number
  id: string
  instruction: string
  title: string
  pdf: string
  where: string
  text: string
  source?: string
  file: string
  section: string
}

type State = { empty?: true; title?: string; kind?: string; pdf?: string; spec?: string; version?: string }

const KIND_NAMES: Record<string, string> = {
  report: 'Report', memo: 'Memo', guide: 'Guide', proposal: 'Proposal', requirements: 'Technical requirements',
}

function promptFor(ask: Ask): string {
  const lines = [
    `Change request from the document inspector for "${ask.title}".`,
    '',
    `Element: ${ask.where}, section "${ask.section}"`,
    `File: ${ask.file}`,
    `Current text: "${ask.text}"`,
  ]
  if (ask.source && ask.source !== ask.text) lines.push(`Current source: ${ask.source}`)
  lines.push(
    '',
    `Instruction: ${ask.instruction}`,
    '',
    `Apply this to that element in the document's source, using the docs-designer vocabulary, ` +
      `then re-render the PDF to ${ask.pdf} with the docs-designer render script.`,
  )
  return lines.join('\n')
}

// Per load: a reload restarts the server and these start over with it.
let base: string | null = null // http://127.0.0.1:<port> once the server listens
let lastSeq = 0
let lastVersion = ''
let seenSpec = ''

async function openInspector($: EngineInterface): Promise<string> {
  if (!base) return 'The inspector server is not running yet.'
  try {
    const result = await $.mcp.call('Claude_Browser', 'preview_start', { url: `${base}/` })
    if (!result.isError) return 'Opened the inspector in the browser pane.'
  } catch {
    // the app's browser is not available here: fall back to the system browser
  }
  await $.process.run(['open', `${base}/`])
  return `Opened the inspector in your browser: ${base}/`
}

async function poll($: EngineInterface): Promise<void> {
  if (!base) return
  try {
    const state = JSON.parse((await $.http.fetch(`${base}/api/state`)).text) as State
    if (!state.empty && state.version && state.version !== lastVersion) {
      lastVersion = state.version
      await update($, doc, () => ({
        title: state.title ?? '', kind: state.kind ?? '', pdf: state.pdf ?? '',
        spec: state.spec ?? '', version: state.version ?? '',
      }))
      if (state.spec && state.spec !== seenSpec) {
        // a new document was rendered: show it beside the chat
        seenSpec = state.spec
        void $.ui.open({ id: PANE, title: TITLE })
      }
    }
    const asks = JSON.parse((await $.http.fetch(`${base}/api/asks?after=${lastSeq}`)).text) as Ask[]
    for (const ask of asks) {
      lastSeq = Math.max(lastSeq, ask.seq)
      void $.prompt.submit({ text: promptFor(ask) })
      await update($, sent, list =>
        [...list, { seq: ask.seq, instruction: ask.instruction, where: ask.where, section: ask.section }].slice(-20),
      )
      $.ui.toast('Sent your instruction to Claude')
    }
  } catch {
    // the server is restarting; the next tick tries again
  }
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    const started = await next(e)
    await $.command.register({
      name: 'docs-inspect',
      description: 'Open the docs-designer inspector for the most recent document',
    })
    await update($, url, () => null)
    await update($, problem, () => null)

    // The skill ships inside this plugin; a copy in ~/.claude/skills works too.
    const home = await $.env.get('HOME')
    const candidates = [
      `${$.plugin.root}/skills/docs-designer/scripts/inspect_server.py`,
      `${home}/.claude/skills/docs-designer/scripts/inspect_server.py`,
    ]
    let server: string | null = null
    for (const path of candidates) {
      try {
        await $.fs.stat(path)
        server = path
        break
      } catch {
        // try the next place
      }
    }
    if (!server) {
      await update($, problem, () => 'The docs-designer skill was not found next to this plugin or in ~/.claude/skills.')
      return started
    }

    // The server lives as long as this module: the loop below is its life.
    void (async () => {
      try {
        for await (const { stream, text } of $.process.spawn({ argv: ['python3', server, '--port', '8765'] })) {
          const port = stream === 'stdout' ? /LISTENING (\d+)/.exec(text)?.[1] : undefined
          if (port && !base) {
            base = `http://127.0.0.1:${port}`
            await update($, url, () => base)
            $.clock.every(1500, () => void poll($))
            void poll($)
          } else if (stream === 'stderr') {
            $.ui.log(`docs-designer inspector: ${text.trim()}`, { to: 'debug' })
          }
        }
        base = null
        await update($, problem, () => 'The inspector server stopped. Start a new session to restart it.')
      } catch (err) {
        await update($, problem, () => `The inspector server could not start: ${String(err)}`)
      }
    })()

    return started
  })

  on('command.run', { command: 'docs-inspect' }, async $ => {
    await $.ui.open({ id: PANE, title: TITLE, focus: true })
    return { text: await openInspector($) }
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Text, Button } = $.ui.resolve(e)
    const current = await read($, doc)
    const address = await read($, url)
    const issue = await read($, problem)
    const asks = await read($, sent)

    if (issue) {
      return (
        <Box flexDirection="column" gap="sm">
          <Text bold>Document inspector</Text>
          <Text>{issue}</Text>
        </Box>
      )
    }
    if (!current) {
      return (
        <Box flexDirection="column" gap="sm">
          <Text bold>Document inspector</Text>
          <Text dimColor>
            {address ? 'No document yet. Ask Claude to make one with docs-designer and it shows up here.' : 'Starting…'}
          </Text>
        </Box>
      )
    }

    const pdfName = current.pdf.split('/').pop() ?? current.pdf
    return (
      <Box flexDirection="column" gap="md">
        <Box flexDirection="column">
          <Text dimColor>{KIND_NAMES[current.kind] ?? current.kind}</Text>
          <Text bold>{current.title}</Text>
          <Text dimColor>{pdfName}</Text>
        </Box>
        <Box flexDirection="row" gap="sm" flexWrap="wrap">
          <Button key="inspect" variant="primary" onPress={async () => $.ui.toast(await openInspector($))}>
            Inspect and edit
          </Button>
          <Button key="pdf" onPress={() => void $.process.run(['open', current.pdf])}>
            Open PDF
          </Button>
        </Box>
        <Text dimColor>
          In the inspector, click any text to edit it in place, or choose Ask Claude to send an instruction that
          points at that exact element.
        </Text>
        {asks.length > 0 && (
          <Box flexDirection="column">
            <Text bold>Sent to Claude</Text>
            {asks
              .slice(-5)
              .reverse()
              .map(ask => (
                <Text key={`ask-${ask.seq}`}>
                  “{ask.instruction}” <Text dimColor>· {ask.section}</Text>
                </Text>
              ))}
          </Box>
        )}
      </Box>
    )
  })
}
