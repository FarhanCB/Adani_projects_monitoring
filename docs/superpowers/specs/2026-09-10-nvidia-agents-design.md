# NVIDIA Agents for Ping Tester — Design Spec

**Date:** 2026-09-10  
**Status:** Approved

## Goal

Add LangChain-style NVIDIA NIM agents to Ping Tester: **Analyst** (failure diagnosis) and **Helper** (dashboard chat), plus richer project metadata (project URL, developers with emails) for downtime ownership context.

## Agents

| Agent | Trigger | Behavior |
|-------|---------|----------|
| Analyst | Every failed URL check | Diagnose using check result, history, project URL, developers; store `last_analysis` on URL |
| Helper | Chat UI | Tool-backed Q&A over projects, health, history, analyses, owners |

## Stack

- NVIDIA NIM OpenAI-compatible API (`https://integrate.api.nvidia.com/v1`)
- LangChain (`langchain-openai` + tools) inside Flask
- API key via `.env` (`NVIDIA_API_KEY`); `NVidiaAPI.txt` supported as fallback, both gitignored

## Project fields

- name, project_url, description
- developers: `[{ name, email }]`
- urls: monitored endpoints (unchanged) + `last_analysis`

## UI

- Professional project header with link + developer mailto chips
- Analysis card under failing URLs
- Helper chat drawer on authenticated pages
