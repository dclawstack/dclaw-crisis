"use client"

import { useEffect, useRef, useState } from "react"
import { usePathname } from "next/navigation"
import { MessageCircle, Send, X, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { copilotChat, type CopilotChatMessage } from "@/lib/api"
import { cn } from "@/lib/utils"

interface CopilotProps {
  focusedCrisisId?: string
}

function deriveFocusFromPath(pathname: string | null): string | undefined {
  if (!pathname) return undefined
  const match = pathname.match(/^\/crisis\/([^/]+)$/)
  return match ? match[1] : undefined
}

export function Copilot({ focusedCrisisId: focusedCrisisIdProp }: CopilotProps) {
  const pathname = usePathname()
  const focusedCrisisId = focusedCrisisIdProp ?? deriveFocusFromPath(pathname)
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState<CopilotChatMessage[]>([
    {
      role: "assistant",
      content:
        "I'm your DClaw Crisis Copilot. Ask about active incidents, recommend actions, or draft updates.",
    },
  ])
  const [input, setInput] = useState("")
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" })
  }, [messages, open])

  async function send() {
    const text = input.trim()
    if (!text || busy) return
    const next: CopilotChatMessage[] = [...messages, { role: "user", content: text }]
    setMessages(next)
    setInput("")
    setBusy(true)
    setError(null)
    try {
      const res = await copilotChat(
        next.filter((m) => m.role === "user" || m.role === "assistant"),
        focusedCrisisId,
      )
      setMessages([...next, { role: "assistant", content: res.reply }])
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to reach copilot"
      setError(message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      {!open && (
        <button
          onClick={() => setOpen(true)}
          className="fixed bottom-6 right-6 z-50 h-14 w-14 rounded-full bg-pink-600 text-white shadow-lg hover:bg-pink-700 flex items-center justify-center"
          aria-label="Open AI Copilot"
        >
          <MessageCircle className="h-6 w-6" />
        </button>
      )}

      {open && (
        <div className="fixed bottom-6 right-6 z-50 w-[380px] max-w-[calc(100vw-2rem)] h-[560px] max-h-[calc(100vh-3rem)] bg-white rounded-xl shadow-2xl border border-slate-200 flex flex-col">
          <header className="flex items-center justify-between px-4 py-3 border-b border-slate-200 bg-gradient-to-r from-pink-600 to-rose-500 text-white rounded-t-xl">
            <div>
              <div className="font-semibold text-sm">AI Crisis Copilot</div>
              <div className="text-xs opacity-90">
                {focusedCrisisId ? "Focused on this crisis" : "Org-wide view"}
              </div>
            </div>
            <button onClick={() => setOpen(false)} aria-label="Close copilot" className="text-white/90 hover:text-white">
              <X className="h-5 w-5" />
            </button>
          </header>

          <div ref={scrollRef} className="flex-1 overflow-y-auto p-3 space-y-3 bg-slate-50">
            {messages.map((m, i) => (
              <div
                key={i}
                className={cn(
                  "max-w-[85%] rounded-lg px-3 py-2 text-sm whitespace-pre-wrap",
                  m.role === "user"
                    ? "ml-auto bg-pink-600 text-white"
                    : "bg-white border border-slate-200 text-slate-800",
                )}
              >
                {m.content}
              </div>
            ))}
            {busy && (
              <div className="bg-white border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-500 flex items-center gap-2">
                <Loader2 className="h-3 w-3 animate-spin" /> Thinking…
              </div>
            )}
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-3 py-2 text-xs">
                {error}
              </div>
            )}
          </div>

          <div className="p-3 border-t border-slate-200">
            <div className="flex gap-2">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault()
                    send()
                  }
                }}
                placeholder="Ask the copilot…"
                disabled={busy}
                className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-pink-500"
              />
              <Button onClick={send} disabled={busy || !input.trim()} size="sm" aria-label="Send">
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
