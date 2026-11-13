/** The document the inspector shows: the most recent docs-designer render. */
export type InspectedDoc = {
  title: string
  kind: string
  pdf: string
  spec: string
  version: string
}

/** An instruction the person sent from the inspector, as it was handed to Claude. */
export type SentAsk = {
  seq: number
  instruction: string
  where: string
  section: string
}

declare module 'claude-code' {
  interface PluginState {
    'docs-designer': {
      doc: Shaped<InspectedDoc | null>
      url: Shaped<string | null>
      problem: Shaped<string | null>
      sent: Shaped<SentAsk[]>
    }
  }
}
