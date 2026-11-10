# Work Log Archive — 2026-11-10

This directory preserves a snapshot of the accessible Turn-Table-Test work history. File names and archive documentation are English; conversation messages retain their original language.

## Conversation and execution transcripts

- [Project conversation](project-conversation.md): the ongoing project discussion, including the vertical RMS work, with recorded tool calls and outputs.
- [Initial analysis](initial-analysis.md): the earlier thread that created the original turn-table analysis.
- Matching `.jsonl` files contain the same selected records for automated processing.
- [Manifest](manifest.json): export timestamp, source paths, record counts, source snapshot hashes, and archived-file hashes.

The export includes recorded user/assistant messages and tool activity. System/developer instructions, internal reasoning, encrypted reasoning, internal session metadata, and compaction context are excluded. Unrelated Codex threads are excluded. This is a point-in-time export, not a continuously updated log, and it does not include later messages or the final confirmation of this export.

Tool output that was truncated when originally recorded remains truncated. These files are not an independent, complete shell-session recording; commands whose output was redirected to temporary files may only have their invocation in the transcript. The additional files below preserve available outputs from the vertical analysis.

## Analysis, test and PDF logs

`build-logs/` contains the available November 10 analysis outputs, final test log, PDF command logs, PDF metadata, and both datasets' final LaTeX/build logs. These are copies: subsequent runs may overwrite the originals under `results/<dataset-id>/report/`, and temporary logs under `/tmp/` are not durable.

For the existing live Codex source location, see `source_path` in the manifest. The application also maintains local history databases under `/home/sok/.codex/`; those databases are not copied into this repository.

## Documentation

The official OpenAI documentation describes a session transcript path as `transcript_path`: [Hooks](https://learn.chatgpt.com/docs/hooks). This archive's actual source paths and export scope were verified against the local installation, rather than inferred from the documentation.
