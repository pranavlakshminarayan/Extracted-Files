# lowRISC Ibex Extraction Report

Source repository: https://github.com/lowrisc/ibex
Extraction date: 2026-06-15T09:03:32Z
Extraction mode: repo
Quality tier: A - README + (PDF or images) + 3+ HDL files
Detected license: Apache-2.0

## What Was Found

The lowRISC Ibex repository is a mature open-source RISC-V CPU core project. The extraction found a strong HDL-centered project with SystemVerilog source code, technical documentation, build/configuration collateral, markdown reports, and image assets. This makes it a high-value reference repository for hardware design analysis because it contains both implementation files and enough surrounding documentation to understand the design intent.

## Extracted Content Summary

- README present: yes
- Verilog/SystemVerilog files: 646
- VHDL files: 0
- Other HDL/model/build-related files: 2
- PDF files: 0
- Markdown documentation files: 115
- Text documentation files: 7
- Image/block-diagram assets: 18
- Total scanned bytes: 42157527
- Languages seen: Verilog
- References/links extracted: 256

## Folder Layout

- `README.md`: root project README copied from the source repository.
- `docs/`: extracted PDFs, markdown, text documentation, and readable PDF text previews where available.
- `images/`: image assets such as PNG/JPG/SVG/GIF files that may include diagrams, figures, and documentation visuals.
- `code/verilog/`: Verilog/SystemVerilog implementation and header files.
- `code/vhdl/`: VHDL files, if present.
- `code/other/`: related hardware/build collateral such as TCL, SDC, XDC, file lists, Chisel/Scala/BSV/MyHDL where present.
- `references/links.json`: URLs discovered from README/docs/PDF text extraction.
- `meta.json`: machine-readable extraction metadata.

## Artifact Counts By Folder

- `readme`: 1 files
- `docs`: 122 files
- `images`: 18 files
- `code/verilog`: 646 files
- `code/vhdl`: 0 files
- `code/other`: 38 files

## Notes For Report Use

Ibex is best described as a documentation-rich HDL project. The strongest extracted material is the SystemVerilog implementation under `code/verilog/`, supported by project documentation under `docs/` and visual assets under `images/`. The extracted structure is suitable for reading, dataset construction, or further filtering into HDL-only, HDL-plus-documentation, or HDL-plus-visual subsets.
