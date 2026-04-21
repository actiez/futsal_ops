# Futsal Ops

## Overview
Futsal Ops is a system to manage futsal games, player registrations, and slot allocation.

It is designed to be simple for players while maintaining control and flexibility for admins.

---

## Core Features
- Player registration and login
- Join / Leave game via unique link
- Player categorisation (core, regular, new, naughty)
- Slot allocation (playing, waiting, backup)
- Event lifecycle (open → completed)
- WhatsApp-friendly game summaries

---

## Player Experience
- Players join games via link
- Status shown as:
  - Pending
  - Confirmed
- Internal categories (waiting/backup) are hidden

---

## Tech Stack
- Django (Backend)
- Supabase (Database)
- Render (Hosting)

---

## Status
MVP Live