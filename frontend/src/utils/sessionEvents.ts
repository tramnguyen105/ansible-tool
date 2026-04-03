const UNAUTHORIZED_EVENT = 'ansible-tool:unauthorized'

let lastUnauthorizedAt = 0

export function emitUnauthorizedSession() {
  const now = Date.now()
  if (now - lastUnauthorizedAt < 1000) {
    return
  }
  lastUnauthorizedAt = now
  window.dispatchEvent(new CustomEvent(UNAUTHORIZED_EVENT))
}

export function onUnauthorizedSession(handler: () => void) {
  window.addEventListener(UNAUTHORIZED_EVENT, handler)
  return () => window.removeEventListener(UNAUTHORIZED_EVENT, handler)
}
