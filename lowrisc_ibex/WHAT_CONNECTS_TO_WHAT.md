# What Connects To What: lowrisc_ibex

This file maps images and documentation to likely related HDL/code files.
Confidence is heuristic: high means a documentation reference and subsystem/code match; medium means path/name matching; low means weak or incomplete evidence.

## blockdiagram

- Subject: `doc/03_reference/images/blockdiagram.svg`
  Confidence: low
  Reason: Files share subsystem keywords or path proximity.
  Images:
  - `doc/03_reference/images/blockdiagram.svg`

## branch_predict

- Subject: `branch_predict`
  Confidence: low
  Reason: Documentation and code were grouped by shared subsystem keywords or path proximity.
  Likely related code:
  - `rtl/ibex_branch_predict.sv`

## bus

- Subject: `bus`
  Confidence: low
  Reason: Documentation and code were grouped by shared subsystem keywords or path proximity.
  Likely related code:
  - `shared/rtl/bus.sv`

## clkgen_xil7series

- Subject: `clkgen_xil7series`
  Confidence: low
  Reason: Documentation and code were grouped by shared subsystem keywords or path proximity.
  Likely related code:
  - `shared/rtl/fpga/xilinx/clkgen_xil7series.sv`

## clock_gating

- Subject: `clock_gating`
  Confidence: low
  Reason: Documentation and code were grouped by shared subsystem keywords or path proximity.
  Likely related code:
  - `syn/rtl/prim_clock_gating.v`

## controller

- Subject: `controller`
  Confidence: low
  Reason: Documentation and code were grouped by shared subsystem keywords or path proximity.
  Likely related code:
  - `rtl/ibex_controller.sv`

## core

- Subject: `core`
  Confidence: low
  Reason: Documentation and code were grouped by shared subsystem keywords or path proximity.
  Likely related code:
  - `rtl/ibex_core.sv`

## counter

- Subject: `counter`
  Confidence: low
  Reason: Documentation and code were grouped by shared subsystem keywords or path proximity.
  Likely related code:
  - `rtl/ibex_counter.sv`

## cs_registers

- Subject: `cs_registers`
  Confidence: medium
  Reason: Documentation and code were grouped by shared subsystem keywords or path proximity.
  Docs:
  - `doc/03_reference/cs_registers.rst`
  - `dv/cs_registers/README.md`
  Likely related code:
  - `dv/cs_registers/env/env_dpi.sv`
  - `dv/cs_registers/reg_driver/reg_dpi.sv`
  - `dv/cs_registers/rst_driver/rst_dpi.sv`
  - `dv/cs_registers/tb/tb_cs_registers.sv`
  - `dv/uvm/core_ibex/env/core_ibex_csr_if.sv`
  - `dv/uvm/core_ibex/fcov/core_ibex_csr_categories.svh`
  - `rtl/ibex_cs_registers.sv`
  - `rtl/ibex_csr.sv`

## debug

- Subject: `debug`
  Confidence: medium
  Reason: Documentation and code were grouped by shared subsystem keywords or path proximity.
  Docs:
  - `doc/03_reference/debug.rst`
  Likely related code:
  - `dv/uvm/core_ibex/riscv_dv_extension/ibex_debug_triggers_overrides.sv`

## dummy_instr

- Subject: `dummy_instr`
  Confidence: low
  Reason: Documentation and code were grouped by shared subsystem keywords or path proximity.
  Likely related code:
  - `rtl/ibex_dummy_instr.sv`

## dv_flow

- Subject: `doc/03_reference/images/dv-flow.png`
  Confidence: low
  Reason: Files share subsystem keywords or path proximity.
  Images:
  - `doc/03_reference/images/dv-flow.png`

## icache

- Subject: `doc/03_reference/images/icache_block.svg`
  Confidence: medium
  Reason: Files share subsystem keywords or path proximity.
  Docs:
  - `doc/03_reference/icache.rst`
  - `dv/uvm/icache/doc/ibex_icache_dv_plan.md`
  - `dv/uvm/icache/dv/ibex_icache_core_agent/README.md`
  - `dv/uvm/icache/dv/ibex_icache_mem_agent/README.md`
  - `formal/icache/README.md`
  Images:
  - `doc/03_reference/images/icache_block.svg`
  Likely related code:
  - `dv/uvm/icache/dv/env/ibex_icache_env.sv`
  - `dv/uvm/icache/dv/env/ibex_icache_env_cfg.sv`
  - `dv/uvm/icache/dv/env/ibex_icache_env_cov.sv`
  - `dv/uvm/icache/dv/env/ibex_icache_env_pkg.sv`
  - `dv/uvm/icache/dv/env/ibex_icache_ram_if.sv`
  - `dv/uvm/icache/dv/env/ibex_icache_scoreboard.sv`
  - `dv/uvm/icache/dv/env/ibex_icache_virtual_sequencer.sv`
  - `dv/uvm/icache/dv/env/seq_lib/ibex_icache_back_line_vseq.sv`
  - `dv/uvm/icache/dv/env/seq_lib/ibex_icache_base_vseq.sv`
  - `dv/uvm/icache/dv/env/seq_lib/ibex_icache_caching_vseq.sv`
  - `dv/uvm/icache/dv/env/seq_lib/ibex_icache_combo_vseq.sv`
  - `dv/uvm/icache/dv/env/seq_lib/ibex_icache_ecc_vseq.sv`

- Subject: `doc/03_reference/images/icache_mux.svg`
  Confidence: medium
  Reason: Files share subsystem keywords or path proximity.
  Docs:
  - `doc/03_reference/icache.rst`
  - `dv/uvm/icache/doc/ibex_icache_dv_plan.md`
  - `dv/uvm/icache/dv/ibex_icache_core_agent/README.md`
  - `dv/uvm/icache/dv/ibex_icache_mem_agent/README.md`
  - `formal/icache/README.md`
  Images:
  - `doc/03_reference/images/icache_mux.svg`
  Likely related code:
  - `dv/uvm/icache/dv/env/ibex_icache_env.sv`
  - `dv/uvm/icache/dv/env/ibex_icache_env_cfg.sv`
  - `dv/uvm/icache/dv/env/ibex_icache_env_cov.sv`
  - `dv/uvm/icache/dv/env/ibex_icache_env_pkg.sv`
  - `dv/uvm/icache/dv/env/ibex_icache_ram_if.sv`
  - `dv/uvm/icache/dv/env/ibex_icache_scoreboard.sv`
  - `dv/uvm/icache/dv/env/ibex_icache_virtual_sequencer.sv`
  - `dv/uvm/icache/dv/env/seq_lib/ibex_icache_back_line_vseq.sv`
  - `dv/uvm/icache/dv/env/seq_lib/ibex_icache_base_vseq.sv`
  - `dv/uvm/icache/dv/env/seq_lib/ibex_icache_caching_vseq.sv`
  - `dv/uvm/icache/dv/env/seq_lib/ibex_icache_combo_vseq.sv`
  - `dv/uvm/icache/dv/env/seq_lib/ibex_icache_ecc_vseq.sv`

- Subject: `doc/03_reference/images/tb.svg`
  Confidence: high
  Reason: Image is referenced by documentation in this subsystem and matched to code by subsystem name.
  Docs:
  - `dv/uvm/icache/doc/ibex_icache_dv_plan.md`
  Images:
  - `doc/03_reference/images/tb.svg`
  Likely related code:
  - `dv/uvm/icache/dv/env/ibex_icache_env.sv`
  - `dv/uvm/icache/dv/env/ibex_icache_env_cfg.sv`
  - `dv/uvm/icache/dv/env/ibex_icache_env_cov.sv`
  - `dv/uvm/icache/dv/env/ibex_icache_env_pkg.sv`
  - `dv/uvm/icache/dv/env/ibex_icache_ram_if.sv`
  - `dv/uvm/icache/dv/env/ibex_icache_scoreboard.sv`
  - `dv/uvm/icache/dv/env/ibex_icache_virtual_sequencer.sv`
  - `dv/uvm/icache/dv/env/seq_lib/ibex_icache_back_line_vseq.sv`
  - `dv/uvm/icache/dv/env/seq_lib/ibex_icache_base_vseq.sv`
  - `dv/uvm/icache/dv/env/seq_lib/ibex_icache_caching_vseq.sv`
  - `dv/uvm/icache/dv/env/seq_lib/ibex_icache_combo_vseq.sv`
  - `dv/uvm/icache/dv/env/seq_lib/ibex_icache_ecc_vseq.sv`

- Subject: `dv/uvm/icache/doc/tb.svg`
  Confidence: high
  Reason: Image is referenced by documentation in this subsystem and matched to code by subsystem name.
  Docs:
  - `dv/uvm/icache/doc/ibex_icache_dv_plan.md`
  Images:
  - `dv/uvm/icache/doc/tb.svg`
  Likely related code:
  - `dv/uvm/icache/dv/env/ibex_icache_env.sv`
  - `dv/uvm/icache/dv/env/ibex_icache_env_cfg.sv`
  - `dv/uvm/icache/dv/env/ibex_icache_env_cov.sv`
  - `dv/uvm/icache/dv/env/ibex_icache_env_pkg.sv`
  - `dv/uvm/icache/dv/env/ibex_icache_ram_if.sv`
  - `dv/uvm/icache/dv/env/ibex_icache_scoreboard.sv`
  - `dv/uvm/icache/dv/env/ibex_icache_virtual_sequencer.sv`
  - `dv/uvm/icache/dv/env/seq_lib/ibex_icache_back_line_vseq.sv`
  - `dv/uvm/icache/dv/env/seq_lib/ibex_icache_base_vseq.sv`
  - `dv/uvm/icache/dv/env/seq_lib/ibex_icache_caching_vseq.sv`
  - `dv/uvm/icache/dv/env/seq_lib/ibex_icache_combo_vseq.sv`
  - `dv/uvm/icache/dv/env/seq_lib/ibex_icache_ecc_vseq.sv`

## id_stage

- Subject: `id_stage`
  Confidence: low
  Reason: Documentation and code were grouped by shared subsystem keywords or path proximity.
  Likely related code:
  - `rtl/ibex_id_stage.sv`

## instruction_decode_execute

- Subject: `doc/03_reference/images/de_ex_stage.svg`
  Confidence: medium
  Reason: Files share subsystem keywords or path proximity.
  Docs:
  - `doc/03_reference/instruction_decode_execute.rst`
  Images:
  - `doc/03_reference/images/de_ex_stage.svg`
  Likely related code:
  - `rtl/ibex_alu.sv`
  - `rtl/ibex_compressed_decoder.sv`
  - `rtl/ibex_decoder.sv`
  - `rtl/ibex_ex_block.sv`
  - `rtl/ibex_multdiv_fast.sv`
  - `rtl/ibex_multdiv_slow.sv`

## instruction_fetch

- Subject: `doc/03_reference/images/if_stage.svg`
  Confidence: medium
  Reason: Files share subsystem keywords or path proximity.
  Docs:
  - `doc/03_reference/instruction_fetch.rst`
  Images:
  - `doc/03_reference/images/if_stage.svg`
  Likely related code:
  - `rtl/ibex_fetch_fifo.sv`
  - `rtl/ibex_if_stage.sv`
  - `rtl/ibex_prefetch_buffer.sv`

## latch_map

- Subject: `latch_map`
  Confidence: low
  Reason: Documentation and code were grouped by shared subsystem keywords or path proximity.
  Likely related code:
  - `syn/rtl/latch_map.v`

## load_store_unit

- Subject: `load_store_unit`
  Confidence: medium
  Reason: Documentation and code were grouped by shared subsystem keywords or path proximity.
  Docs:
  - `doc/03_reference/load_store_unit.rst`
  Likely related code:
  - `dv/formal/check/peek/alt_lsu.sv`
  - `rtl/ibex_load_store_unit.sv`

## lockstep

- Subject: `lockstep`
  Confidence: low
  Reason: Documentation and code were grouped by shared subsystem keywords or path proximity.
  Likely related code:
  - `rtl/ibex_lockstep.sv`

## pkg

- Subject: `pkg`
  Confidence: low
  Reason: Documentation and code were grouped by shared subsystem keywords or path proximity.
  Likely related code:
  - `rtl/ibex_pkg.sv`

## pmp

- Subject: `pmp`
  Confidence: medium
  Reason: Documentation and code were grouped by shared subsystem keywords or path proximity.
  Docs:
  - `doc/03_reference/pmp.rst`
  Likely related code:
  - `dv/uvm/core_ibex/common/ibex_cosim_agent/core_ibex_ifetch_pmp_if.sv`
  - `dv/uvm/core_ibex/common/ibex_cosim_agent/ibex_ifetch_pmp_monitor.sv`
  - `dv/uvm/core_ibex/common/ibex_cosim_agent/ibex_ifetch_pmp_seq_item.sv`
  - `dv/uvm/core_ibex/fcov/core_ibex_pmp_fcov_if.sv`
  - `rtl/ibex_pmp.sv`

## ram_1p

- Subject: `ram_1p`
  Confidence: low
  Reason: Documentation and code were grouped by shared subsystem keywords or path proximity.
  Likely related code:
  - `shared/rtl/ram_1p.sv`

## ram_2p

- Subject: `ram_2p`
  Confidence: low
  Reason: Documentation and code were grouped by shared subsystem keywords or path proximity.
  Likely related code:
  - `shared/rtl/ram_2p.sv`

## register_file

- Subject: `register_file`
  Confidence: medium
  Reason: Documentation and code were grouped by shared subsystem keywords or path proximity.
  Docs:
  - `doc/03_reference/register_file.rst`
  Likely related code:
  - `rtl/ibex_register_file_ff.sv`
  - `rtl/ibex_register_file_fpga.sv`
  - `rtl/ibex_register_file_latch.sv`

## simple_system

- Subject: `simple_system`
  Confidence: medium
  Reason: Documentation and code were grouped by shared subsystem keywords or path proximity.
  Docs:
  - `examples/simple_system/README.md`
  Likely related code:
  - `examples/simple_system/rtl/ibex_simple_system.sv`

## simulator_ctrl

- Subject: `simulator_ctrl`
  Confidence: low
  Reason: Documentation and code were grouped by shared subsystem keywords or path proximity.
  Likely related code:
  - `shared/rtl/sim/simulator_ctrl.sv`

## synthesis

- Subject: `synthesis`
  Confidence: low
  Reason: Documentation and code were grouped by shared subsystem keywords or path proximity.
  Likely related code:
  - `syn/ibex_top.nangate.sdc`
  - `syn/ibex_top_abc.nangate.sdc`
  - `syn/tcl/sta_common.tcl`
  - `syn/tcl/sta_open_design.tcl`
  - `syn/tcl/sta_run_reports.tcl`
  - `syn/tcl/sta_utils.tcl`
  - `syn/tcl/yosys_common.tcl`
  - `syn/tcl/yosys_post_synth.tcl`
  - `syn/tcl/yosys_pre_map.tcl`
  - `syn/tcl/yosys_run_synth.tcl`

## timer

- Subject: `timer`
  Confidence: low
  Reason: Documentation and code were grouped by shared subsystem keywords or path proximity.
  Likely related code:
  - `shared/rtl/timer.sv`

## top

- Subject: `top`
  Confidence: low
  Reason: Documentation and code were grouped by shared subsystem keywords or path proximity.
  Likely related code:
  - `rtl/ibex_top.sv`

## top_tracing

- Subject: `top_tracing`
  Confidence: low
  Reason: Documentation and code were grouped by shared subsystem keywords or path proximity.
  Likely related code:
  - `rtl/ibex_top_tracing.sv`

## tracer

- Subject: `tracer`
  Confidence: medium
  Reason: Documentation and code were grouped by shared subsystem keywords or path proximity.
  Docs:
  - `doc/03_reference/tracer.rst`
  Likely related code:
  - `rtl/ibex_tracer.sv`
  - `rtl/ibex_tracer_pkg.sv`

## verification

- Subject: `verification`
  Confidence: medium
  Reason: Documentation and code were grouped by shared subsystem keywords or path proximity.
  Docs:
  - `doc/01_overview/verification_overview.rst`
  - `doc/03_reference/verification.rst`
  - `doc/03_reference/verification_stages.rst`
  - `dv/formal/README.md`
  - `dv/riscv_compliance/README.md`
  - `dv/uvm/bus_params_pkg/README.md`
  - `dv/uvm/core_ibex/README.md`
  - `dv/uvm/core_ibex/directed_tests/README.md`
  Likely related code:
  - `dv/cosim/cosim_dpi.svh`
  - `dv/formal/check/encodings.sv`
  - `dv/formal/check/peek/abs.sv`
  - `dv/formal/check/peek/compare_helper.sv`
  - `dv/formal/check/peek/follower.sv`
  - `dv/formal/check/peek/mem.sv`
  - `dv/formal/check/protocol/irqs.sv`
  - `dv/formal/check/protocol/mem.sv`
  - `dv/formal/check/spec_instance.sv`
  - `dv/formal/check/top.sv`
  - `dv/formal/spec/spec_api.sv`
  - `dv/formal/spec/stub.sv`

## wb_stage

- Subject: `wb_stage`
  Confidence: low
  Reason: Documentation and code were grouped by shared subsystem keywords or path proximity.
  Likely related code:
  - `rtl/ibex_wb_stage.sv`

## Extra / Additional data

These files were preserved but did not have enough evidence to connect to a specific subsystem.
- `docs`: 98 files
- `images`: 10 files
- `code/verilog`: 452 files
- `code/other`: 22 files
