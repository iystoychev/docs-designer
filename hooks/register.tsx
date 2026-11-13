import type { EngineInterface, Register } from 'claude-code'

// The inspector is a small local server that ships with the docs-designer skill
// (scripts/inspect_server.py). This mod runs it, puts a card for every rendered
// document into the chat (right under the call that rendered it), opens the
// interactive page in the app's browser, and hands every "Ask Claude"
// instruction from that page to Claude as a prompt naming the exact element.

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

/** A document as render.py reports it on stdout (PDF:, Title:, Spec:, Kind: ... | Author: ...). */
type Rendered = { pdf: string; title: string; spec: string; kind: string; author: string }

type ElementTable = ReturnType<EngineInterface['ui']['resolve']>

const KIND_NAMES: Record<string, string> = {
  report: 'Report', memo: 'Memo', guide: 'Guide', proposal: 'Proposal', requirements: 'Technical requirements',
}

// Per load: a reload restarts the server and these start over with it.
let base: string | null = null // http://127.0.0.1:<port> once the server listens
let problem: string | null = null
let lastSeq = 0

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

/** The document a finished render.py call produced, read from its output; null for anything else. */
function renderedBy(call: { tool: string; output?: unknown; isRunning: boolean; isErrored: boolean }): Rendered | null {
  if (call.tool !== 'Bash' || call.isRunning || call.isErrored) return null
  const stdout = (call.output as { stdout?: unknown } | undefined)?.stdout
  if (typeof stdout !== 'string' || !stdout.includes('PDF: ')) return null
  const line = (label: string) => new RegExp(`^${label}: (.+)$`, 'm').exec(stdout)?.[1]?.trim()
  const pdf = line('PDF'), spec = line('Spec'), meta = line('Kind')
  if (!pdf || !spec || !meta) return null
  const kind = meta.split('|')[0]?.trim() ?? ''
  const author = /Author: ([^|]+)/.exec(meta)?.[1]?.trim() ?? ''
  return { pdf, spec, kind, author, title: line('Title') ?? pdf.split('/').pop() ?? pdf }
}

async function openInspector($: EngineInterface, doc?: Rendered): Promise<string> {
  if (!base) return problem ?? 'The inspector is still starting. Try again in a moment.'
  if (doc) {
    // show this card's document, not whichever was rendered last
    const res = await $.http.fetch(`${base}/api/select`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ spec: doc.spec, pdf: doc.pdf, author: doc.author }),
    })
    if (!res.ok) return (JSON.parse(res.text) as { error?: string }).error ?? `The inspector answered ${res.status}.`
  }
  try {
    const result = await $.mcp.call('Claude_Browser', 'preview_start', { url: `${base}/` })
    if (!result.isError) return 'Opened the inspector in the browser pane.'
  } catch {
    // the app's browser is not available here: fall back to the system browser
  }
  await $.process.run(['open', `${base}/`])
  return `Opened the inspector in your browser: ${base}/`
}

/** The card shown in the chat for one rendered document. `key` keeps its buttons apart from other cards'. */
function docCard($: EngineInterface, { Box, Text, Button }: ElementTable, doc: Rendered, key: string) {
  return (
    <Box key={`card-${key}`} flexDirection="column" gap="md" borderStyle="round" paddingX={2} paddingY={1}>
      <Box flexDirection="column">
        <Text dimColor>{KIND_NAMES[doc.kind] ?? doc.kind}</Text>
        <Text bold>{doc.title}</Text>
        <Text dimColor>{doc.pdf.split('/').pop()}</Text>
      </Box>
      <Box flexDirection="row" gap="sm" flexWrap="wrap">
        <Button key={`inspect-${key}`} variant="primary" onPress={async () => $.ui.toast(await openInspector($, doc))}>
          Inspect and edit
        </Button>
        <Button key={`pdf-${key}`} onPress={() => void $.process.run(['open', doc.pdf])}>
          Open PDF
        </Button>
      </Box>
      <Text dimColor>
        In the inspector, click any text to edit it in place, or choose Ask Claude to send an instruction that points at
        that exact element.
      </Text>
    </Box>
  )
}

async function pollAsks($: EngineInterface): Promise<void> {
  if (!base) return
  try {
    const asks = JSON.parse((await $.http.fetch(`${base}/api/asks?after=${lastSeq}`)).text) as Ask[]
    for (const ask of asks) {
      lastSeq = Math.max(lastSeq, ask.seq)
      void $.prompt.submit({ text: promptFor(ask) })
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
      problem = 'The docs-designer skill was not found next to this plugin or in ~/.claude/skills.'
      return started
    }

    // The server lives as long as this module: the loop below is its life.
    void (async () => {
      try {
        for await (const { stream, text } of $.process.spawn({ argv: ['python3', server, '--port', '8765'] })) {
          const port = stream === 'stdout' ? /LISTENING (\d+)/.exec(text)?.[1] : undefined
          if (port && !base) {
            base = `http://127.0.0.1:${port}`
            $.clock.every(1500, () => void pollAsks($))
          } else if (stream === 'stderr') {
            $.ui.log(`docs-designer inspector: ${text.trim()}`, { to: 'debug' })
          }
        }
        base = null
        problem = 'The inspector server stopped. Start a new session to restart it.'
      } catch (err) {
        problem = `The inspector server could not start: ${String(err)}`
      }
    })()

    return started
  })

  on('command.run', { command: 'docs-inspect' }, async $ => ({ text: await openInspector($) }))

  // The card for a document, right under the call that rendered it.
  on('ui.render', { component: 'ToolUse' }, async ($, e, next) => {
    const row = await next(e)
    const doc = renderedBy(e.props)
    if (!doc) return row
    const { Box } = $.ui.resolve(e)
    return (
      <Box flexDirection="column" gap="sm">
        {row}
        {docCard($, $.ui.resolve(e), doc, e.props.tool_use_id)}
      </Box>
    )
  })

  // Shell calls folded into one group line hide their own rows: put the cards under the group.
  on('ui.render', { component: 'ToolGroup' }, async ($, e, next) => {
    const row = await next(e)
    if (e.props.isExpanded) return row // each call draws its own row, and its own card
    const cards = e.props.calls.flatMap((call, i) => {
      const doc = renderedBy(call)
      return doc ? [docCard($, $.ui.resolve(e), doc, call.tool_use_id ?? `${i}-${doc.pdf}`)] : []
    })
    if (cards.length === 0) return row
    const { Box } = $.ui.resolve(e)
    return (
      <Box flexDirection="column" gap="sm">
        {row}
        {cards}
      </Box>
    )
  })
}
