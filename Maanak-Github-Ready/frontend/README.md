# MAANAK Frontend

AI-powered BIS compliance assistant. Next.js App Router, Tailwind, shadcn/ui, Supabase Auth, and a FastAPI RAG backend.

## Setup

1. Copy `.env.example` to `.env.local`.
2. Set:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - `NEXT_PUBLIC_FASTAPI_URL` (no trailing slash)
3. `npm install`
4. `npm run dev`

Signup stores `role` (`citizen` | `manufacturer` | `auditor`) in Supabase `user_metadata`. Middleware blocks unauthenticated routes and sends non-auditors away from `/auditor-dashboard`.
