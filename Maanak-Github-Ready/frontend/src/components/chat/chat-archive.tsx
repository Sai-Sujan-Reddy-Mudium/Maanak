"use client";

import { MessageSquarePlus, MessagesSquare, Trash2, Pencil } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { ChatSession } from "@/lib/types";
import { useState } from "react";
import { Input } from "@/components/ui/input";

export function ChatArchive({
  sessions,
  activeId,
  onSelect,
  onCreate,
  onDelete,
  onRename,
}: {
  sessions: ChatSession[];
  activeId: string;
  onSelect: (id: string) => void;
  onCreate: () => void;
  onDelete: (id: string) => void;
  onRename?: (id: string, newTitle: string) => void;
}) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");

  const startEdit = (e: React.MouseEvent, id: string, title: string) => {
    e.stopPropagation();
    setEditingId(id);
    setEditTitle(title);
  };

  const saveEdit = () => {
    if (editingId && editTitle.trim() && onRename) {
      onRename(editingId, editTitle.trim());
    }
    setEditingId(null);
  };

  return (
    <div className="flex h-full flex-col border-r bg-sidebar">
      <div className="flex items-center justify-between px-3 py-3">
        <p className="text-[11px] tracking-[0.16em] text-muted-foreground uppercase">
          Archive
        </p>
        <Button size="sm" variant="outline" onClick={onCreate}>
          <MessageSquarePlus className="size-4" />
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
              const isEditing = editingId === session.id;

              return (
                <div
                  key={session.id}
                  className={`group flex items-start gap-1 rounded-lg ${
                    active ? "bg-background ring-1 ring-foreground/10" : "hover:bg-background/70"
                  }`}
                >
                  <button
                    type="button"
                    onClick={() => {
                      if (!isEditing) onSelect(session.id);
                    }}
                    className="flex min-w-0 flex-1 items-start gap-2 px-2 py-2 text-left"
                  >
                    <MessagesSquare className="mt-0.5 size-3.5 shrink-0 text-muted-foreground" />
                    <div className="min-w-0 flex-1">
                      {isEditing ? (
                        <Input
                          value={editTitle}
                          onChange={(e) => setEditTitle(e.target.value)}
                          onBlur={saveEdit}
                          onKeyDown={(e) => {
                            if (e.key === "Enter") saveEdit();
                            if (e.key === "Escape") setEditingId(null);
                          }}
                          autoFocus
                          className="h-6 w-full text-sm px-1 py-0 mb-1"
                          onClick={(e) => e.stopPropagation()}
                        />
                      ) : (
                        <span className="block truncate text-sm font-medium pr-1">{session.title}</span>
                      )}
                      <span className="block text-[11px] text-muted-foreground">
                        {new Date(session.updatedAt).toLocaleString()}
                      </span>
                    </div>
                  </button>
                  <div className="mt-1 flex flex-col gap-0 opacity-0 group-hover:opacity-100 transition-opacity">
                    <Button
                      size="icon-xs"
                      variant="ghost"
                      className="h-6 w-6 text-muted-foreground hover:text-foreground"
                      onClick={(e) => startEdit(e, session.id, session.title)}
                      aria-label="Rename archive"
                    >
                      <Pencil className="size-3" />
                    </Button>
                    <Button
                      size="icon-xs"
                      variant="ghost"
                      className="h-6 w-6 text-muted-foreground hover:text-destructive"
                      onClick={(e) => {
                        e.stopPropagation();
                        onDelete(session.id);
                      }}
                      aria-label="Delete archive"
                    >
                      <Trash2 className="size-3" />
                    </Button>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
