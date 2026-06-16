# OpenHW Group Repository Content Report

Source organization: https://github.com/openhwgroup
Public repositories discovered: 67
Scan date: 2026-06-16

## Executive Summary

The OpenHW Group account is already organized mostly as project-level repositories. Unlike the earlier OpenCores-style sources, it does not need branch-level or category-page reconstruction before extraction. The best approach is to treat each HDL/IP repository as its own project, then use subsystem grouping inside larger repos such as CVA6, CV32E40P, CV32E40X, CVFPU, CVW, and CORE-V MCU.

- Strong HDL extraction candidates: 24
- Additional HDL candidates: 3
- Verification/support candidates: 2
- Software/docs/infrastructure/manual-review repositories: 38

## Recommendation

Use normal `org` or `repo` extraction for OpenHW, with each GitHub repository mapped to one project folder. For large hardware repos, keep the new `Projects/<subsystem>/...` and `Extra/Additional_data/...` organization so docs, images, and RTL remain easy to trace. Avoid extracting software/toolchain forks such as Linux, GCC, LLVM, QEMU, U-Boot, and SDK-only repos into the HDL dataset unless a separate software-support dataset is needed.

## Strong HDL Extraction Candidates

| Repository | Language | HDL | Docs | Images | Build | Notes |
|---|---:|---:|---:|---:|---:|---|
| [cv32e40p](https://github.com/openhwgroup/cv32e40p) | SystemVerilog | 181 | 36 | 24 | 16 | CV32E40P is an in-order 4-stage RISC-V RV32IMFCXpulp CPU based on RI5CY from PULP-Platform |
| [cvw](https://github.com/openhwgroup/cvw) | SystemVerilog | 291 | 34 | 1 | 49 | CORE-V Wally is a configurable RISC-V Processor associated with RISC-V System-on-Chip Design textbook. Contains a 5-stage pipeline, support for A, B, C, D, F,  M and Q extensions, and optional caches, BP, FPU, VM/MMU, AHB, RAMs, and peripherals. |
| [cva6](https://github.com/openhwgroup/cva6) | Assembly | 470 | 181 | 182 | 58 | The CORE-V CVA6 is a highly configurable, 6-stage RISC-V core for both application and embedded applications. Application class configurations are capable of booting Linux. |
| [cv-hpdcache](https://github.com/openhwgroup/cv-hpdcache) | SystemVerilog | 82 | 35 | 19 | 3 | RTL sources of the High-Performance L1 Dcache (HPDcache) for OpenHW CV cores |
| [core-v-verif](https://github.com/openhwgroup/core-v-verif) | Assembly | 704 | 195 | 36 | 42 | Functional verification project for the CORE-V family of RISC-V cores. |
| [cv32e40x](https://github.com/openhwgroup/cv32e40x) | SystemVerilog | 80 | 31 | 25 | 1 | 4 stage, in-order, compute RISC-V core based on the CV32E40P |
| [cvfpu](https://github.com/openhwgroup/cvfpu) | SystemVerilog | 39 | 8 | 5 | 0 | Parametric floating-point unit with support for standard RISC-V formats and operations as well as transprecision formats. |
| [core-et](https://github.com/openhwgroup/core-et) | SystemVerilog | 721 | 183 | 0 | 0 | CORE-ET Silicon Platform  |
| [core-v-mcu](https://github.com/openhwgroup/core-v-mcu) | SystemVerilog | 540 | 135 | 122 | 47 | This is the CORE-V MCU project, hosting CORE-V's embedded-class cores. |
| [cvfpu-uvm](https://github.com/openhwgroup/cvfpu-uvm) | Perl | 26 | 4 | 1 | 0 | UVM Verification Environment for the CVFPU |
| [core-et-erbium](https://github.com/openhwgroup/core-et-erbium) | Verilog | 322 | 67 | 0 | 39 |  CORE-ET Silicon Platform  erbium |
| [cva5](https://github.com/openhwgroup/cva5) | SystemVerilog | 104 | 2 | 1 | 4 | The CORE-V CVA5 is an Application class 5-stage RISC-V CPU specifically targetting FPGA implementations. |
| [cve2](https://github.com/openhwgroup/cve2) | SystemVerilog | 437 | 85 | 13 | 31 | fork<br>The CORE-V CVE2 is a small 32 bit RISC-V CPU core (RV32IMC/EMC) with a two stage pipeline, based on the original zero-riscy work from ETH Zurich and Ibex work from lowRISC. |
| [cv32e40x-dv](https://github.com/openhwgroup/cv32e40x-dv) | Assembly | 119 | 50 | 1 | 15 | CV32E40X Design-Verification environment |
| [cv-hpdcache-verif](https://github.com/openhwgroup/cv-hpdcache-verif) | SystemVerilog | 96 | 4 | 2 | 5 | Verification environment for the OpenHW Group's CORE-V High Performance Data Cache controller. |
| [core-v-polara-apu](https://github.com/openhwgroup/core-v-polara-apu) | Assembly | 508 | 7 | 5 | 78 | fork<br>The OpenPiton Platform |
| [cv32e41p](https://github.com/openhwgroup/cv32e41p) | SystemVerilog | 45 | 30 | 22 | 4 | archived<br>4 stage, in-order, secure RISC-V core based on the CV32E40P with Zfinx and Zce ISA extentions |
| [cv32e40s](https://github.com/openhwgroup/cv32e40s) | SystemVerilog | 91 | 31 | 23 | 1 | 4 stage, in-order, secure RISC-V core based on the CV32E40P |
| [cvw-arch-verif](https://github.com/openhwgroup/cvw-arch-verif) | SystemVerilog | 124 | 553 | 1 | 2 | The purpose of the repo is to support CORE-V Wally architectural verification |
| [cva6-safe](https://github.com/openhwgroup/cva6-safe) | SystemVerilog | 39 | 8 | 3 | 14 | A dual-core lockstep (DCLS) subsystem for the CVA6.  Also supports dual-core asymmetric multi-processing (AMP) when lockstep in not needed. |
| [core-v-mcu-uvm](https://github.com/openhwgroup/core-v-mcu-uvm) | SystemVerilog | 641 | 100 | 19 | 0 | CORE-V MCU UVM Environment and Test Bench |
| [advanced-riscv-verification-methodologies](https://github.com/openhwgroup/advanced-riscv-verification-methodologies) | SystemVerilog | 40 | 31 | 4 | 0 | Advanced Verification Methodologies for RISC-V and related IP |
| [cva5-accelerators](https://github.com/openhwgroup/cva5-accelerators) | SystemVerilog | 101 | 9 | 10 | 11 |  |
| [cv32e40s-dv](https://github.com/openhwgroup/cv32e40s-dv) | Assembly | 135 | 47 | 0 | 14 | CV32E40S Design-Verification environment |

## Additional HDL Candidates

| Repository | Language | HDL | Docs | Images | Build | Notes |
|---|---:|---:|---:|---:|---:|---|
| [core-v-xif](https://github.com/openhwgroup/core-v-xif) | SystemVerilog | 2 | 7 | 4 | 0 | RISC-V eXtension interface that provides a generalized framework suitable to implement custom coprocessors and ISA extensions |
| [cv-mesh](https://github.com/openhwgroup/cv-mesh) | Verilog | 53 | 0 | 0 | 0 |  |
| [timer_unit](https://github.com/openhwgroup/timer_unit) | SystemVerilog | 4 | 2 | 0 | 0 | fork |

## Verification / DV / Support Candidates

| Repository | Language | HDL | Docs | Images | Build | Notes |
|---|---:|---:|---:|---:|---:|---|
| [cv32e20-dv](https://github.com/openhwgroup/cv32e20-dv) | Assembly | 0 | 0 | 0 | 0 |  |
| [cv32e40p-dv-review](https://github.com/openhwgroup/cv32e40p-dv-review) | Assembly | 0 | 0 | 0 | 0 | CV32E40P DV environment based on cv32e20-dv |

## Software, Documentation, Infrastructure, Or Manual Review

| Repository | Language | HDL | Docs | Images | Build | Notes |
|---|---:|---:|---:|---:|---:|---|
| [core-v-cores](https://github.com/openhwgroup/core-v-cores) | - | 0 | 2 | 6 | 0 | CORE-V Family of RISC-V Cores |
| [force-riscv](https://github.com/openhwgroup/force-riscv) | C++ | 0 | 55 | 0 | 0 | Instruction Set Generator initially contributed by Futurewei |
| [uap](https://github.com/openhwgroup/uap) | JavaScript | 0 | 2 | 16 | 0 | Unified RISC-V Access Platform (UAP) project repository |
| [cva6-dcls](https://github.com/openhwgroup/cva6-dcls) | - | 0 | 3 | 0 | 0 | Dual-Core-Lock-Step platform for the CVA6 RISC-V processor core |
| [core-v-mcu-sdk-examples](https://github.com/openhwgroup/core-v-mcu-sdk-examples) | C | 0 | 7 | 1 | 0 | Example SDK applications for DevKit |
| [openhwfoundation.org](https://github.com/openhwgroup/openhwfoundation.org) | HTML | 0 | 103 | 159 | 0 | OpenHW Group is a global, not-for-profit organization where hardware and software designers collaborate on open-source cores, IP, tools, and software. It provides infrastructure to host high-quality open-source hardware projects aligned with industry best practices. |
| [meta-cva6-yocto](https://github.com/openhwgroup/meta-cva6-yocto) | BitBake | 0 | 0 | 0 | 0 | fork<br>Yocto layer for CVA6 |
| [programs](https://github.com/openhwgroup/programs) | HTML | 0 | 1090 | 293 | 0 | Documentation for the OpenHW Group's set of CORE-V RISC-V cores |
| [core-v-mcu-cli-test](https://github.com/openhwgroup/core-v-mcu-cli-test) | C | 0 | 55 | 49 | 0 | Eclipse/FreeRTOS/core-v-mcu example program |
| [cva6-sdk](https://github.com/openhwgroup/cva6-sdk) | Makefile | 0 | 4 | 0 | 0 | CVA6 SDK containing RISC-V tools and Buildroot |
| [core-v-trusted-mcu](https://github.com/openhwgroup/core-v-trusted-mcu) | - | 0 | 1 | 0 | 0 | archived<br>RTL code for implementation of dual-core trusted MCU  |
| [osdforum.org](https://github.com/openhwgroup/osdforum.org) | HTML | 0 | 0 | 0 | 0 | The Open Source Developer Forum is a workshop that brings open source software and hardware (chips, boards and systems) developers together to collaborate and learn. |
| [.github](https://github.com/openhwgroup/.github) | - | 0 | 0 | 0 | 0 |  |
| [obi](https://github.com/openhwgroup/obi) | - | 0 | 0 | 0 | 0 | Repository that maintain the OpenBus Interface spec |
| [cva6-platform](https://github.com/openhwgroup/cva6-platform) | - | 0 | 1 | 3 | 0 | CVA6-platform is a multicore CVA6 with CV-MESH software and regression platform |
| [corev-llvm-project](https://github.com/openhwgroup/corev-llvm-project) | - | 0 | 0 | 0 | 0 |  |
| [riscv_vm](https://github.com/openhwgroup/riscv_vm) | Shell | 0 | 2 | 1 | 0 | archived<br>Instructions to import Ubuntu guest Virtual Machine for RISC-V development for the VEGA board |
| [corev-gcc](https://github.com/openhwgroup/corev-gcc) | C++ | 0 | 0 | 0 | 0 |  |
| [apb_interrupt_cntrl](https://github.com/openhwgroup/apb_interrupt_cntrl) | - | 0 | 0 | 0 | 0 | fork<br>Small and simple APB interrupt controller |
| [core-v-mcu-devkit](https://github.com/openhwgroup/core-v-mcu-devkit) | HTML | 0 | 17 | 14 | 0 | This is the CORE-V MCU DevKit project, hosting the open-source artifacts for the CORE-V MCU Development Kit. |
| [u-boot](https://github.com/openhwgroup/u-boot) | C | 0 | 0 | 0 | 0 | Unofficial development fork of U-Boot  |
| [core-v-sw](https://github.com/openhwgroup/core-v-sw) | - | 0 | 247 | 0 | 0 | Main Repo for the OpenHW Group Software Task Group |
| [core-v-sdk](https://github.com/openhwgroup/core-v-sdk) | Java | 0 | 2 | 29 | 0 |  |
| [core-v-freertos-kernel](https://github.com/openhwgroup/core-v-freertos-kernel) | C | 0 | 19 | 0 | 0 |  |
| [corev-qemu](https://github.com/openhwgroup/corev-qemu) | - | 0 | 0 | 0 | 0 | fork<br>Official QEMU mirror. Please see http://wiki.qemu.org/Contribute/SubmitAPatch for how to submit changes to QEMU. Pull Requests are ignored. Please only use release tarballs from the QEMU website. |
| [corev-binutils-gdb](https://github.com/openhwgroup/corev-binutils-gdb) | C | 0 | 0 | 0 | 0 |  |
| [core-v-ide-cdt](https://github.com/openhwgroup/core-v-ide-cdt) | Java | 0 | 1 | 13 | 0 | archived |
| [infra](https://github.com/openhwgroup/infra) | - | 0 | 0 | 0 | 0 | Issues related to the OpenHW Group infra (GtHub, Mattermost, ...) |
| [core-v-mcu-commonio](https://github.com/openhwgroup/core-v-mcu-commonio) | - | 0 | 1 | 0 | 0 | CORE-V MCU DevKit drivers written with AWS CommonIO approach |
| [riscv-ovpsim-corev](https://github.com/openhwgroup/riscv-ovpsim-corev) | - | 0 | 1 | 0 | 0 |  |
| [core-v-freertos](https://github.com/openhwgroup/core-v-freertos) | C | 0 | 30 | 0 | 2 |  |
| [embdebug-target-core-v](https://github.com/openhwgroup/embdebug-target-core-v) | C++ | 0 | 4 | 0 | 0 |  |
| [core-v-mcu-demo](https://github.com/openhwgroup/core-v-mcu-demo) | C | 0 | 50 | 51 | 0 |  |
| [aws-codebuild-run-build](https://github.com/openhwgroup/aws-codebuild-run-build) | JavaScript | 0 | 0 | 0 | 0 | fork<br>Run an AWS CodeBuild project as a step in a GitHub Actions workflow job. |
| [marketing](https://github.com/openhwgroup/marketing) | - | 0 | 0 | 0 | 0 |  |
| [downloads.openhwgroup.org](https://github.com/openhwgroup/downloads.openhwgroup.org) | SCSS | 0 | 0 | 0 | 0 | downloads.openhwgroup.org |
| [linux](https://github.com/openhwgroup/linux) | - | 0 | 0 | 0 | 0 | fork<br>Linux kernel source tree |
| [corev-elf-psabi-doc](https://github.com/openhwgroup/corev-elf-psabi-doc) | - | 0 | 0 | 0 | 0 | tree scan failed |

## Suggested Extraction Order

1. `cv32e40p` - 181 HDL files, 36 docs, 24 images
2. `cvw` - 291 HDL files, 34 docs, 1 images
3. `cva6` - 470 HDL files, 181 docs, 182 images
4. `cv-hpdcache` - 82 HDL files, 35 docs, 19 images
5. `core-v-verif` - 704 HDL files, 195 docs, 36 images
6. `cv32e40x` - 80 HDL files, 31 docs, 25 images
7. `cvfpu` - 39 HDL files, 8 docs, 5 images
8. `core-et` - 721 HDL files, 183 docs, 0 images
9. `core-v-mcu` - 540 HDL files, 135 docs, 122 images
10. `cvfpu-uvm` - 26 HDL files, 4 docs, 1 images
11. `core-et-erbium` - 322 HDL files, 67 docs, 0 images
12. `cva5` - 104 HDL files, 2 docs, 1 images
13. `cve2` - 437 HDL files, 85 docs, 13 images
14. `cv32e40x-dv` - 119 HDL files, 50 docs, 1 images
15. `cv-hpdcache-verif` - 96 HDL files, 4 docs, 2 images

## Dataset Organization

For each extracted OpenHW project, use this structure:

```text
<project_id>/
  PROJECT_REPORT.md
  WHAT_CONNECTS_TO_WHAT.md
  README.md
  meta.json
  references/links.json
  Projects/<subsystem>/docs|images|code/...
  Extra/Additional_data/docs|images|code/...
```

This keeps the repository-level project identity intact while still making image-to-document-to-code relationships readable for humans and useful for model training.