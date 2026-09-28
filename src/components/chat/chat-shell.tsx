"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  FlaskConical,
  Languages,
  Loader2,
  LogOut,
  Mic,
  SendHorizonal,
  ShieldCheck,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ChatArchive } from "@/components/chat/chat-archive";
import { MarkdownMessage } from "@/components/chat/markdown-message";
import { MetricsDrawer } from "@/components/chat/metrics-drawer";
import { SourceInspector } from "@/components/chat/source-inspector";
import { AudioPlayerButton } from "@/components/chat/audio-player-button";
import { BrandMark } from "@/components/brand-mark";
import { Button, buttonVariants } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { loadArchives, saveArchives, titleFromQuery } from "@/lib/archive";
import { useAuth } from "@/hooks/use-auth";
import { useAudioRecorder } from "@/hooks/use-audio-recorder";
import {
  DEFAULT_LANGUAGE,
  SUPPORTED_LANGUAGES,
  getLanguageName,
  type LanguageCode,
} from "@/lib/languages";
import { roleLabel } from "@/lib/roles";
import { streamChat } from "@/lib/sse";
import { createClient } from "@/lib/supabase/client";
import {
  USER_ROLES,
  type ChatMessage,
  type ChatSession,
  type Citation,
  type UserRole,
} from "@/lib/types";

function newSession(): ChatSession {
  return {
    id: crypto.randomUUID(),
    title: "New consultation",
    messages: [],
    updatedAt: Date.now(),
  };
}

export function ChatShell() {
  const router = useRouter();
  const { user, role: authRole, loading, configured } = useAuth();
  const archiveKey = user?.id ?? "local-preview";
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeId, setActiveId] = useState<string>("");
  const [input, setInput] = useState("");
  const [selectedLang, setSelectedLang] = useState<LanguageCode>(DEFAULT_LANGUAGE);
  const [roleOverride, setRoleOverride] = useState<UserRole | "auth">("auth");
  const [activeCitation, setActiveCitation] = useState<Citation | null>(null);
  const [sending, setSending] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const loadedRef = useRef(false);

  const {
    isRecording,
    recordingDuration,
    isProcessing: isAudioProcessing,
    error: recorderError,
    startRecording,
    stopRecording,
    cancelRecording,
  } = useAudioRecorder();

  const effectiveRole: UserRole = roleOverride === "auth" ? authRole : roleOverride;
  const active = sessions.find((session) => session.id === activeId) ?? sessions[0];

  useEffect(() => {
    const stored = loadArchives(archiveKey);
    if (stored.length > 0) {
      setSessions(stored);
      setActiveId(stored[0].id);
    } else {
      const fresh = newSession();
      setSessions([fresh]);
      setActiveId(fresh.id);
    }
    loadedRef.current = true;
  }, [archiveKey]);

  useEffect(() => {
    if (!loadedRef.current) return;
    saveArchives(archiveKey, sessions);
  }, [archiveKey, sessions]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [active?.messages]);

  function patchActive(updater: (session: ChatSession) => ChatSession) {
    setSessions((current) =>
      current.map((session) => (session.id === activeId ? updater(session) : session)),
    );
  }

  async function executeStream(params: {
    inputType: "text" | "audio";
    data: string;
    displayText: string;
  }) {
    if (!active || sending) return;

    setSending(true);

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: params.displayText,
      inputType: params.inputType,
      sourceLang: selectedLang,
    };

    const assistantId = crypto.randomUUID();
    const assistantMessage: ChatMessage = {
      id: assistantId,
      role: "assistant",
      content: "",
      citations: [],
      isStreaming: true,
      sourceLang: selectedLang,
    };

    patchActive((session) => ({
      ...session,
      title:
        session.messages.length === 0
          ? titleFromQuery(params.displayText)
          : session.title,
      updatedAt: Date.now(),
      messages: [...session.messages, userMessage, assistantMessage],
    }));

    let citations: Citation[] = [];

    try {
      await streamChat({
        sessionId: active.id,
        inputType: params.inputType,
        data: params.data,
        sourceLang: selectedLang,
        role: effectiveRole,
        handlers: {
          onToken: (chunk) => {
            patchActive((session) => ({
              ...session,
              messages: session.messages.map((message) =>
                message.id === assistantId
                  ? { ...message, content: message.content + chunk }
                  : message,
              ),
            }));
          },
          onMetadata: (next) => {
            citations = next;
            patchActive((session) => ({
              ...session,
              messages: session.messages.map((message) =>
                message.id === assistantId
                  ? { ...message, citations: next }
                  : message,
              ),
            }));
          },
          onDone: () => {
            patchActive((session) => ({
              ...session,
              updatedAt: Date.now(),
              messages: session.messages.map((message) =>
                message.id === assistantId
                  ? { ...message, isStreaming: false, citations }
                  : message,
              ),
            }));
          },
        },
      });
    } catch (err) {
      patchActive((session) => ({
        ...session,
        messages: session.messages.map((message) =>
          message.id === assistantId
            ? {
                ...message,
                isStreaming: false,
                error:
                  err instanceof Error
                    ? err.message
                    : "Gateway chat stream failed.",
              }
            : message,
        ),
      }));
    } finally {
      setSending(false);
    }
  }

  async function onSendText() {
    const query = input.trim();
    if (!query || sending || !active) return;
    setInput("");
    await executeStream({
      inputType: "text",
      data: query,
      displayText: query,
    });
  }

  async function handleMicPress() {
    if (sending || isAudioProcessing) return;
    await startRecording();
  }

  async function handleMicRelease() {
    if (!isRecording) return;
    const base64Audio = await stopRecording();
    if (base64Audio) {
      await executeStream({
        inputType: "audio",
        data: base64Audio,
        displayText: `Voice consultation in ${getLanguageName(selectedLang)}`,
      });
    }
  }

  async function onSignOut() {
    if (configured) {
      const supabase = createClient();
      await supabase.auth.signOut();
    }
    router.replace("/login");
    router.refresh();
  }

  function onCreate() {
    const fresh = newSession();
    setSessions((current) => [fresh, ...current]);
    setActiveId(fresh.id);
    setActiveCitation(null);
  }

  function onDelete(id: string) {
    setSessions((current) => {
      const next = current.filter((session) => session.id !== id);
      if (next.length === 0) {
        const fresh = newSession();
        setActiveId(fresh.id);
        return [fresh];
      }
      if (id === activeId) setActiveId(next[0].id);
      return next;
    });
  }

  return (
    <div className="flex h-svh flex-col overflow-hidden">
      <header className="flex items-center justify-between gap-3 border-b bg-background/90 px-4 py-2.5 backdrop-blur">
        <BrandMark compact />
        <div className="flex items-center gap-2">
          <div className="hidden items-center gap-2 md:flex">
            <span className="text-[11px] tracking-[0.14em] text-muted-foreground uppercase">
              Role
            </span>
            <Select
              value={roleOverride}
              onValueChange={(value) => {
                if (value) setRoleOverride(value as UserRole | "auth");
              }}
            >
              <SelectTrigger className="h-8 w-40 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="auth">Auth ({roleLabel(authRole)})</SelectItem>
                {USER_ROLES.map((item) => (
                  <SelectItem key={item} value={item}>
                    Simulate {roleLabel(item)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <Link
            href="/labs"
            className={buttonVariants({ variant: "outline", size: "sm" })}
          >
            <FlaskConical />
            Labs
          </Link>
          {effectiveRole === "auditor" ? (
            <Link
              href="/auditor-dashboard"
              className={buttonVariants({ variant: "outline", size: "sm" })}
            >
              Auditor
            </Link>
          ) : null}
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={onSignOut}
            aria-label="Sign out"
          >
            <LogOut />
          </Button>
        </div>
      </header>

      <div className="flex min-h-0 flex-1">
        <section className="flex min-w-0 basis-[60%] border-r">
          <div className="hidden w-60 shrink-0 md:block">
            <ChatArchive
              sessions={sessions}
              activeId={activeId}
              onSelect={(id) => {
                setActiveId(id);
                setActiveCitation(null);
              }}
              onCreate={onCreate}
              onDelete={onDelete}
            />
          </div>
          <div className="flex min-w-0 flex-1 flex-col">
            <ScrollArea className="min-h-0 flex-1">
              <div className="mx-auto flex w-full max-w-3xl flex-col gap-4 px-4 py-6">
                {loading ? (
                  <p className="text-sm text-muted-foreground">
                    Restoring session…
                  </p>
                ) : null}
                {(active?.messages.length ?? 0) === 0 ? (
                  <div className="rounded-2xl border bg-card p-6 shadow-xs">
                    <p className="font-heading text-2xl">Ask an Indian Standard</p>
                    <p className="mt-2 text-sm text-muted-foreground">
                      Ask about clauses, specifications, test methods, or mandatory BIS compliance.
                      You can type your query or hold the microphone button to speak in your preferred Indian language.
                    </p>
                    <div className="mt-4 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                      <span className="font-medium text-foreground">Available Inputs:</span>
                      <span className="rounded-md bg-muted px-2 py-1">⌨️ Text Query</span>
                      <span className="rounded-md bg-muted px-2 py-1">🎙️ Hold-to-Talk Voice</span>
                      <span className="rounded-md bg-muted px-2 py-1">🌐 12 Indian Languages</span>
                      <span className="rounded-md bg-muted px-2 py-1">🔊 On-Demand TTS</span>
                    </div>
                  </div>
                ) : null}

                {active?.messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${
                      message.role === "user" ? "justify-end" : "justify-start"
                    }`}
                  >
                    <div
                      className={`max-w-[92%] rounded-2xl px-4 py-3 shadow-xs ${
                        message.role === "user"
                          ? "bg-primary text-primary-foreground"
                          : "bg-card ring-1 ring-foreground/10"
                      }`}
                    >
                      {message.role === "assistant" ? (
                        <>
                          {message.error ? (
                            <p className="text-sm text-destructive">{message.error}</p>
                          ) : (
                            <MarkdownMessage
                              content={
                                message.content ||
                                (message.isStreaming
                                  ? "▍"
                                  : "No response tokens received.")
                              }
                              onCitationClick={(inlineCitation) => {
                                setActiveCitation({
                                  is_number: inlineCitation.is_number,
                                  clause: inlineCitation.clause,
                                });
                              }}
                            />
                          )}

                          {/* Citation Badges */}
                          {message.citations && message.citations.length > 0 ? (
                            <div className="mt-3.5 space-y-1.5 border-t border-border/50 pt-2.5">
                              <p className="text-[10px] font-semibold tracking-wider text-emerald-800 uppercase dark:text-emerald-400">
                                Verified BIS Legal Citations
                              </p>
                              <div className="flex flex-wrap gap-1.5">
                                {message.citations.map((citation, index) => {
                                  const isSelected =
                                    activeCitation?.is_number === citation.is_number &&
                                    activeCitation?.clause === citation.clause;
                                  return (
                                    <button
                                      key={`${citation.is_number}-${citation.clause}-${index}`}
                                      type="button"
                                      onClick={() => setActiveCitation(citation)}
                                      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold transition-all ${
                                        isSelected
                                          ? "border-emerald-600 bg-emerald-600 text-white shadow-xs"
                                          : "border-emerald-500/30 bg-emerald-500/10 text-emerald-800 hover:bg-emerald-500/20 dark:border-emerald-500/40 dark:text-emerald-300"
                                      }`}
                                    >
                                      <ShieldCheck className="size-3 text-emerald-600 dark:text-emerald-400" />
                                      <span>
                                        {citation.is_number} · Clause {citation.clause}
                                      </span>
                                    </button>
                                  );
                                })}
                              </div>
                            </div>
                          ) : null}

                          {/* On-Demand Audio Button (TTS) */}
                          {!message.isStreaming && message.content ? (
                            <div className="mt-3 flex items-center justify-between border-t border-border/40 pt-2">
                              <AudioPlayerButton
                                text={message.content}
                                targetLang={message.sourceLang || selectedLang}
                                cachedAudio={message.audioBase64}
                                onAudioFetched={(base64) => {
                                  patchActive((session) => ({
                                    ...session,
                                    messages: session.messages.map((m) =>
                                      m.id === message.id
                                        ? { ...m, audioBase64: base64 }
                                        : m,
                                    ),
                                  }));
                                }}
                              />
                              <span className="text-[10px] text-muted-foreground uppercase tracking-wider">
                                {getLanguageName(message.sourceLang || selectedLang)}
                              </span>
                            </div>
                          ) : null}
                        </>
                      ) : (
                        <div>
                          {message.inputType === "audio" ? (
                            <div className="mb-1 inline-flex items-center gap-1 rounded bg-primary-foreground/20 px-1.5 py-0.5 text-[10px] font-semibold tracking-wide text-primary-foreground uppercase">
                              <Mic className="size-3" /> Voice Query (
                              {message.sourceLang?.toUpperCase()})
                            </div>
                          ) : null}
                          <p className="text-sm leading-6 whitespace-pre-wrap">
                            {message.content}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                <div ref={bottomRef} />
              </div>
            </ScrollArea>

            {/* Input Controls Area */}
            <div className="border-t bg-background p-3">
              <div className="mx-auto max-w-3xl space-y-2">
                {/* Language selection bar */}
                <div className="flex items-center justify-between gap-2 px-1 text-xs">
                  <div className="flex items-center gap-1.5">
                    <Languages className="size-3.5 text-muted-foreground" />
                    <span className="text-muted-foreground">Input Language:</span>
                    <Select
                      value={selectedLang}
                      onValueChange={(val) => {
                        if (val) setSelectedLang(val as LanguageCode);
                      }}
                    >
                      <SelectTrigger className="h-7 w-36 gap-1 text-xs font-medium">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {SUPPORTED_LANGUAGES.map((lang) => (
                          <SelectItem
                            key={lang.code}
                            value={lang.code}
                            className="text-xs"
                          >
                            {lang.name} ({lang.code})
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <span className="text-[11px] text-muted-foreground hidden sm:inline">
                    Hold Mic to speak or type text
                  </span>
                </div>

                {/* Recording indicator banner */}
                {isRecording ? (
                  <div className="flex items-center gap-2 rounded-xl border border-destructive/30 bg-destructive/10 px-3.5 py-2 text-xs text-destructive animate-pulse">
                    <span className="relative flex size-2.5">
                      <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-destructive opacity-75" />
                      <span className="relative inline-flex size-2.5 rounded-full bg-destructive" />
                    </span>
                    <span className="font-semibold">Recording voice…</span>
                    <span>Release to send in {getLanguageName(selectedLang)}</span>
                    <span className="ml-auto font-mono tabular-nums font-bold">
                      {recordingDuration}s
                    </span>
                  </div>
                ) : null}

                {/* Translating & Processing indicator */}
                {isAudioProcessing ? (
                  <div className="flex items-center gap-2 rounded-xl border border-primary/20 bg-primary/10 px-3.5 py-2 text-xs text-primary">
                    <Loader2 className="size-3.5 animate-spin" />
                    <span className="font-medium">
                      Translating & Processing audio query…
                    </span>
                  </div>
                ) : null}

                {recorderError ? (
                  <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-1.5 text-xs text-destructive">
                    {recorderError}
                  </div>
                ) : null}

                {/* Form with textarea, Hold-to-Talk Mic button, and Send button */}
                <form
                  className="flex items-end gap-2"
                  onSubmit={(event) => {
                    event.preventDefault();
                    void onSendText();
                  }}
                >
                  <Textarea
                    value={input}
                    onChange={(event) => setInput(event.target.value)}
                    placeholder={`Ask about BIS clauses in ${getLanguageName(selectedLang)}…`}
                    className="min-h-12 max-h-40 flex-1 resize-none py-2.5 text-sm"
                    disabled={isRecording || isAudioProcessing || sending}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" && !event.shiftKey) {
                        event.preventDefault();
                        void onSendText();
                      }
                    }}
                  />

                  {/* Hold-to-Talk Mic button */}
                  <Button
                    type="button"
                    variant={isRecording ? "destructive" : "outline"}
                    className={`h-11 px-3 transition-all select-none touch-none ${
                      isRecording
                        ? "bg-destructive text-destructive-foreground ring-4 ring-destructive/30"
                        : "hover:bg-accent"
                    }`}
                    onMouseDown={handleMicPress}
                    onMouseUp={handleMicRelease}
                    onMouseLeave={() => {
                      if (isRecording) cancelRecording();
                    }}
                    onTouchStart={handleMicPress}
                    onTouchEnd={handleMicRelease}
                    disabled={sending || isAudioProcessing}
                    title="Hold to speak in selected language, release to send"
                  >
                    <Mic className="size-4" />
                    <span className="hidden md:inline text-xs font-semibold">
                      {isRecording ? "Listening…" : "Hold to Talk"}
                    </span>
                  </Button>

                  {/* Send text button */}
                  <Button
                    type="submit"
                    className="h-11 px-4"
                    disabled={sending || !input.trim() || isRecording || isAudioProcessing}
                  >
                    <SendHorizonal className="size-4" />
                    <span className="hidden sm:inline">Send</span>
                  </Button>
                </form>
              </div>
            </div>
          </div>
        </section>

        {/* Source Inspector on the right */}
        <aside className="hidden min-w-0 basis-[40%] bg-muted/20 lg:block">
          <SourceInspector citation={activeCitation} />
        </aside>
      </div>

      <footer className="flex items-center justify-between border-t px-4 py-1.5 text-[11px] text-muted-foreground">
        <span>
          Streaming to <code>/api/gateway/chat/stream</code> · Language:{" "}
          <strong>{getLanguageName(selectedLang)} ({selectedLang})</strong> · Role:{" "}
          <code>{effectiveRole}</code>
        </span>
        {effectiveRole === "auditor" ? (
          <MetricsDrawer />
        ) : (
          <span>Citizen / manufacturer view</span>
        )}
      </footer>
    </div>
  );
}
