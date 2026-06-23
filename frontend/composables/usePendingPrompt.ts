/** Pass a prompt from the home hero to the chat page (one-shot). */
export function usePendingPrompt() {
  return useState<string | null>('pending-prompt', () => null)
}
