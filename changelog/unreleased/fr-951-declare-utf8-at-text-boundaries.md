---
type: fix
scope: encoding
req: REQ-YG-638
---
- **FR-951 Declare UTF-8 at first-party text boundaries**: text crossed YAMLGraph's boundaries in whatever codec the host preferred, so a graph, prompt or schema containing a curly quote or a euro sign either crashed on Windows (`U+201D`'s trailing byte `0x9d` is undefined in cp1252) or, worse, decoded successfully into mojibake that passed every type and shape check on its way to the LLM. The CLI's own error handler then destroyed its diagnostic by writing `❌` to the same inherited stream. Every first-party read and write now states `encoding="utf-8"`, the CLI declares UTF-8 on its own stdout and stderr at `main()`, and a dedicated blocking `ruff check --select PLW1514 --preview .` step plus a focused `windows-latest` witness job keep the class closed. (REQ-YG-638)
