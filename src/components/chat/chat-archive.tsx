"use client";

import { MessageSquarePlus, MessagesSquare, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { ChatSession } from "@/lib/types";

export function ChatArchive({
  sessions,
  activeId,
  onSelect,
  onCreate,
  onDelete,
}: {
  sessions: ChatSession[];
  activeId: string;
  onSelect: (id: string) => void;
  onCreate: () => void;
  onDelete: (id: string) => void;
}) {
  return (
    <div className="flex h-full flex-col border-r bg-sidebar">
      <div className="flex items-center justify-between px-3 py-3">
        <p className="text-[11px] tracking-[0.16em] text-muted-foreground uppercase">
          Archive
        </p>
        <Button size="sm" variant="outline" onClick={onCreate}>
          <MessageSquarePlus />
          New
        </Button>
      </div>
      <ScrollArea className="min-h-0 flex-1">
        <div className="space-y-1 p-2">
          {sessions.length === 0 ? (
            <div className="px-2 py-8 text-center text-xs text-muted-foreground">
              No consultations yet. Start a chat to archive it here.
            </div>
          ) : (
            sessions.map((session) => {
              const active = session.id === activeId;
              return (
                <div
                  key={session.id}
                  className={`group flex items-start gap-1 rounded-lg ${
                    active ? "bg-background ring-1 ring-foreground/10" : "hover:bg-background/70"
                  }`}
                >
                  <button
                    type="button"
                    onClick={() => onSelect(session.id)}
                    className="flex min-w-0 flex-1 items-start gap-2 px-2 py-2 text-left"
                  >
                    <MessagesSquare className="mt-0.5 size-3.5 shrink-0 text-muted-foreground" />
                    <span className="min-w-0">
                      <span className="block truncate text-sm font-medium">{session.title}</span>
                      <span className="block text-[11px] text-muted-foreground">
                        {new Date(session.updatedAt).toLocaleString()}
                      </span>
                    </span>
                  </button>
                  <Button
                    size="icon-xs"
                    variant="ghost"
                    className="mt-1 mr-1 opacity-0 group-hover:opacity-100"
                    onClick={() => onDelete(session.id)}
                    aria-label="Delete archive"
                  >
                    <Trash2 />
                  </Button>
                </div>
              );
            })
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
