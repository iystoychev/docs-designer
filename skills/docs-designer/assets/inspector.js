// docs-designer inspector: point at an element, edit it in place or ask Claude about it.
// Served by scripts/inspect_server.py; never part of a printed PDF.
(() => {
  const version = document.querySelector('meta[name="dd-version"]')?.content || ''
  let pop = null
  let selected = null
  let editing = null

  const el = (tag, attrs = {}, ...kids) => {
    const node = document.createElement(tag)
    for (const [k, v] of Object.entries(attrs)) {
      if (k.startsWith('on')) node.addEventListener(k.slice(2), v)
      else node.setAttribute(k, v)
    }
    node.append(...kids)
    return node
  }

  function toast(text, isError = false) {
    document.querySelector('.dd-toast')?.remove()
    const t = el('div', { class: 'dd-toast' + (isError ? ' dd-error' : ''), role: 'status' }, text)
    document.body.append(t)
    setTimeout(() => t.remove(), isError ? 6000 : 3000)
  }

  async function post(path, payload) {
    const res = await fetch(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...payload, version }),
    })
    const data = await res.json().catch(() => ({ error: `HTTP ${res.status}` }))
    if (!res.ok || data.error) throw new Error(data.error || `HTTP ${res.status}`)
    return data
  }

  function reload() {
    sessionStorage.setItem('dd-scroll', String(window.scrollY))
    location.reload()
  }

  function close() {
    pop?.remove()
    pop = null
    selected?.classList.remove('dd-selected')
    selected = null
  }

  function place(node, target) {
    const r = target.getBoundingClientRect()
    document.body.append(node)
    const width = node.offsetWidth
    const left = Math.min(Math.max(8, r.left + window.scrollX), window.scrollX + window.innerWidth - width - 8)
    node.style.left = `${left}px`
    node.style.top = `${r.bottom + window.scrollY + 8}px`
  }

  function describe(target) {
    const ref = target.dataset.dd
    if (ref.startsWith('spec:') || ref.startsWith('meta:')) return `Front page · ${ref.slice(5)}`
    const names = { p: 'Paragraph', li: 'List item', h2: 'Section heading', h3: 'Sub-heading', h4: 'Heading',
      td: 'Table cell', th: 'Table header', dt: 'Fact label', dd: 'Fact value', caption: 'Table caption',
      cite: 'Citation', figcaption: 'Figure caption', pre: 'Code block', blockquote: 'Quote', div: 'Block' }
    const tag = target.tagName.toLowerCase()
    return names[tag] || tag
  }

  function menu(target) {
    close()
    selected = target
    target.classList.add('dd-selected')
    const edit = el('button', { class: 'dd-btn dd-primary', onclick: () => startEdit(target) }, 'Edit text')
    pop = el('div', { class: 'dd-pop', role: 'dialog' },
      el('p', { class: 'dd-where' }, describe(target)),
      el('div', { class: 'dd-row' },
        edit,
        el('button', { class: 'dd-btn', onclick: () => askForm(target) }, 'Ask Claude…'),
        el('span', { class: 'dd-keys' }, 'Esc to close')))
    place(pop, target)
    edit.focus()
  }

  function startEdit(target) {
    pop?.remove()
    pop = null
    editing = { target, before: target.innerHTML }
    if (target.tagName === 'PRE') target.textContent = target.innerText
    target.contentEditable = 'true'
    target.focus()
    const range = document.createRange()
    range.selectNodeContents(target)
    getSelection().removeAllRanges()
    getSelection().addRange(range)

    pop = el('div', { class: 'dd-pop', role: 'dialog' },
      el('p', { class: 'dd-where' }, `Editing: ${describe(target)}`),
      el('div', { class: 'dd-row' },
        el('button', { class: 'dd-btn dd-primary', onclick: save }, 'Save and re-render'),
        el('button', { class: 'dd-btn', onclick: cancelEdit }, 'Cancel'),
        el('span', { class: 'dd-keys' }, '⌘↵ save · Esc cancel')))
    place(pop, target)
    // keep the toolbar under the text as it grows or shrinks while typing
    const follow = () => editing?.target === target && pop && place(pop, target)
    target.addEventListener('input', follow)
  }

  function cancelEdit() {
    if (!editing) return
    editing.target.contentEditable = 'false'
    editing.target.innerHTML = editing.before
    editing = null
    close()
  }

  async function save() {
    if (!editing) return
    const { target } = editing
    const html = target.tagName === 'PRE' ? target.innerText : target.innerHTML
    target.contentEditable = 'false'
    document.body.classList.add('dd-busy')
    toast('Saving and re-rendering the PDF…')
    try {
      await post('/api/edit', { id: target.dataset.dd, html })
      editing = null
      reload()
    } catch (err) {
      document.body.classList.remove('dd-busy')
      target.contentEditable = 'true'
      toast(err.message, true)
    }
  }

  function askForm(target) {
    pop?.remove()
    const box = el('textarea', {
      'aria-label': 'Instruction for Claude',
      placeholder: 'What should Claude change here? For example: "Make this shorter" or "Turn this into a table".',
    })
    const send = async () => {
      const instruction = box.value.trim()
      if (!instruction) return box.focus()
      try {
        await post('/api/ask', { id: target.dataset.dd, instruction })
        close()
        toast('Sent to Claude, with a reference to this element.')
      } catch (err) {
        toast(err.message, true)
      }
    }
    box.addEventListener('keydown', e => {
      if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) { e.preventDefault(); send() }
    })
    pop = el('div', { class: 'dd-pop', role: 'dialog' },
      el('p', { class: 'dd-where' }, `Ask Claude about this: ${describe(target)}`),
      box,
      el('div', { class: 'dd-row' },
        el('button', { class: 'dd-btn dd-primary', onclick: send }, 'Send to Claude'),
        el('button', { class: 'dd-btn', onclick: close }, 'Cancel'),
        el('span', { class: 'dd-keys' }, '⌘↵ send')))
    place(pop, target)
    box.focus()
  }

  document.addEventListener('click', e => {
    if (e.target.closest('.dd-pop, .dd-bar, .dd-toast')) return
    if (editing) {
      if (!editing.target.contains(e.target)) cancelEdit()
      return
    }
    const target = e.target.closest('[data-dd]')
    e.preventDefault()
    if (target) menu(target)
    else close()
  }, true)

  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') { editing ? cancelEdit() : close() }
    if (editing && e.key === 'Enter' && (e.metaKey || e.ctrlKey)) { e.preventDefault(); save() }
  })

  // the top bar
  document.body.prepend(el('div', { class: 'dd-bar' },
    el('span', { class: 'dd-kind' }, document.querySelector('.masthead .kind')?.textContent || 'Document'),
    el('span', { class: 'dd-title' }, document.title),
    el('a', { href: '/pdf', target: '_blank' }, 'Open PDF'),
    el('span', { class: 'dd-hint' }, 'Click any text to edit it or ask Claude about it')))

  // keep the place across reloads, and reload when the document changes on disk (Claude edits it too)
  const y = Number(sessionStorage.getItem('dd-scroll') || 0)
  if (y) { window.scrollTo(0, y); sessionStorage.removeItem('dd-scroll') }
  setInterval(async () => {
    if (editing || pop) return
    try {
      const state = await (await fetch('/api/state', { cache: 'no-store' })).json()
      if (state.version && state.version !== version) reload()
    } catch { /* the server is restarting */ }
  }, 1500)
})()
