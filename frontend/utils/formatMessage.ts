const ASTERISK_LIKE = /[\uFF0A\u2217\u204E\u066D]/g

/** Escape HTML, then light markdown: ### headings, **bold**, * bullets. */
export function formatMessageHtml(content: string): string {
  if (!content) return ''

  const normalized = content.replace(ASTERISK_LIKE, '*')

  const escaped = normalized
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')

  const withHeadings = escaped.replace(
    /(^|\n)###\s+(.+?)(?=\n|$)/g,
    '$1<h3 class="msg-h3">$2</h3>',
  )

  const withBold = withHeadings.replace(/\*\*([^*]+?)\*\*/g, '<strong>$1</strong>')

  const withLinks = withBold.replace(
    /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g,
    '<a href="$2" target="_blank" rel="noopener noreferrer" class="msg-link">$1</a>',
  )

  return withLinks.replace(/(^|\n)\*(\s+)/g, '$1-$2')
}
