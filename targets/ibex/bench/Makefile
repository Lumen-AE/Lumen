BENCH_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
RTL_DIR := $(abspath $(BENCH_DIR)/../rtl)
IBEX_WRAPPER ?= lumen_top.sv
LUMEN_RTL_FCOV ?= 0
# Copyright lowRISC contributors.
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0
# Makefile

# defaults
SIM ?= verilator
TOPLEVEL_LANG ?= verilog

VERILOG_SOURCES += $(RTL_DIR)/lowrisc_lint_common_0.1/tools/verilator/common.vlt \
	$(RTL_DIR)/lowrisc_prim_assert_0.1/lint/prim_assert.vlt \
	$(RTL_DIR)/lowrisc_prim_generic_clock_gating_0/lint/prim_generic_clock_gating.vlt \
	$(RTL_DIR)/lowrisc_prim_xilinx_clock_gating_0/lint/prim_xilinx_clock_gating.vlt \
	$(RTL_DIR)/lowrisc_prim_xilinx_clock_mux2_0/lint/prim_xilinx_clock_mux2.vlt \
	$(RTL_DIR)/lowrisc_prim_cipher_0/lint/prim_cipher.vlt \
	$(RTL_DIR)/lowrisc_prim_generic_clock_mux2_0/lint/prim_generic_clock_mux2.vlt \
	$(RTL_DIR)/lowrisc_prim_generic_ram_1p_0/lint/prim_generic_ram_1p.vlt \
	$(RTL_DIR)/lowrisc_prim_onehot_check_0/lint/prim_onehot_check.vlt \
	$(RTL_DIR)/lowrisc_ibex_ibex_core_0.1/lint/verilator_waiver.vlt \
	$(RTL_DIR)/lowrisc_prim_ram_1p_scr_0.1/lint/prim_ram_1p_scr.vlt \
	$(RTL_DIR)/lowrisc_ibex_ibex_top_0.1/lint/verilator_waiver.vlt \
	$(RTL_DIR)/lowrisc_ibex_ibex_pkg_0.1/rtl/ibex_pkg.sv \
	$(RTL_DIR)/lowrisc_prim_abstract_prim_pkg_0.1/prim_pkg.sv \
	$(RTL_DIR)/lowrisc_prim_ram_1p_pkg_0/rtl/prim_ram_1p_pkg.sv \
	$(RTL_DIR)/lowrisc_prim_cipher_pkg_0.1/rtl/prim_cipher_pkg.sv \
	$(RTL_DIR)/lowrisc_prim_generic_buf_0/rtl/prim_generic_buf.sv \
	$(RTL_DIR)/lowrisc_prim_generic_clock_gating_0/rtl/prim_generic_clock_gating.sv \
	$(RTL_DIR)/lowrisc_prim_generic_flop_0/rtl/prim_generic_flop.sv \
	$(RTL_DIR)/lowrisc_prim_secded_0.1/rtl/prim_secded_pkg.sv \
	$(RTL_DIR)/lowrisc_prim_secded_0.1/rtl/prim_secded_22_16_dec.sv \
	$(RTL_DIR)/lowrisc_prim_secded_0.1/rtl/prim_secded_22_16_enc.sv \
	$(RTL_DIR)/lowrisc_prim_secded_0.1/rtl/prim_secded_28_22_dec.sv \
	$(RTL_DIR)/lowrisc_prim_secded_0.1/rtl/prim_secded_28_22_enc.sv \
	$(RTL_DIR)/lowrisc_prim_secded_0.1/rtl/prim_secded_39_32_dec.sv \
	$(RTL_DIR)/lowrisc_prim_secded_0.1/rtl/prim_secded_39_32_enc.sv \
	$(RTL_DIR)/lowrisc_prim_secded_0.1/rtl/prim_secded_64_57_dec.sv \
	$(RTL_DIR)/lowrisc_prim_secded_0.1/rtl/prim_secded_64_57_enc.sv \
	$(RTL_DIR)/lowrisc_prim_secded_0.1/rtl/prim_secded_72_64_dec.sv \
	$(RTL_DIR)/lowrisc_prim_secded_0.1/rtl/prim_secded_72_64_enc.sv \
	$(RTL_DIR)/lowrisc_prim_secded_0.1/rtl/prim_secded_hamming_22_16_dec.sv \
	$(RTL_DIR)/lowrisc_prim_secded_0.1/rtl/prim_secded_hamming_22_16_enc.sv \
	$(RTL_DIR)/lowrisc_prim_secded_0.1/rtl/prim_secded_hamming_39_32_dec.sv \
	$(RTL_DIR)/lowrisc_prim_secded_0.1/rtl/prim_secded_hamming_39_32_enc.sv \
	$(RTL_DIR)/lowrisc_prim_secded_0.1/rtl/prim_secded_hamming_72_64_dec.sv \
	$(RTL_DIR)/lowrisc_prim_secded_0.1/rtl/prim_secded_hamming_72_64_enc.sv \
	$(RTL_DIR)/lowrisc_prim_secded_0.1/rtl/prim_secded_hamming_76_68_dec.sv \
	$(RTL_DIR)/lowrisc_prim_secded_0.1/rtl/prim_secded_hamming_76_68_enc.sv \
	$(RTL_DIR)/lowrisc_prim_secded_0.1/rtl/prim_secded_inv_22_16_dec.sv \
	$(RTL_DIR)/lowrisc_prim_secded_0.1/rtl/prim_secded_inv_22_16_enc.sv \
	$(RTL_DIR)/lowrisc_prim_secded_0.1/rtl/prim_secded_inv_28_22_dec.sv \
	$(RTL_DIR)/lowrisc_prim_secded_0.1/rtl/prim_secded_inv_28_22_enc.sv \
	$(RTL_DIR)/lowrisc_prim_secded_0.1/rtl/prim_secded_inv_39_32_dec.sv \
	$(RTL_DIR)/lowrisc_prim_secded_0.1/rtl/prim_secded_inv_39_32_enc.sv \
	$(RTL_DIR)/lowrisc_prim_secded_0.1/rtl/prim_secded_inv_64_57_dec.sv \
	$(RTL_DIR)/lowrisc_prim_secded_0.1/rtl/prim_secded_inv_64_57_enc.sv \
	$(RTL_DIR)/lowrisc_prim_secded_0.1/rtl/prim_secded_inv_72_64_dec.sv \
	$(RTL_DIR)/lowrisc_prim_secded_0.1/rtl/prim_secded_inv_72_64_enc.sv \
	$(RTL_DIR)/lowrisc_prim_secded_0.1/rtl/prim_secded_inv_hamming_22_16_dec.sv \
	$(RTL_DIR)/lowrisc_prim_secded_0.1/rtl/prim_secded_inv_hamming_22_16_enc.sv \
	$(RTL_DIR)/lowrisc_prim_secded_0.1/rtl/prim_secded_inv_hamming_39_32_dec.sv \
	$(RTL_DIR)/lowrisc_prim_secded_0.1/rtl/prim_secded_inv_hamming_39_32_enc.sv \
	$(RTL_DIR)/lowrisc_prim_secded_0.1/rtl/prim_secded_inv_hamming_72_64_dec.sv \
	$(RTL_DIR)/lowrisc_prim_secded_0.1/rtl/prim_secded_inv_hamming_72_64_enc.sv \
	$(RTL_DIR)/lowrisc_prim_secded_0.1/rtl/prim_secded_inv_hamming_76_68_dec.sv \
	$(RTL_DIR)/lowrisc_prim_secded_0.1/rtl/prim_secded_inv_hamming_76_68_enc.sv \
	$(RTL_DIR)/lowrisc_prim_xilinx_buf_0/rtl/prim_xilinx_buf.sv \
	$(RTL_DIR)/lowrisc_prim_xilinx_clock_gating_0/rtl/prim_xilinx_clock_gating.sv \
	$(RTL_DIR)/lowrisc_prim_xilinx_clock_mux2_0/rtl/prim_xilinx_clock_mux2.sv \
	$(RTL_DIR)/lowrisc_prim_xilinx_flop_0/rtl/prim_xilinx_flop.sv \
	$(RTL_DIR)/lowrisc_ibex_ibex_icache_0.1/rtl/ibex_icache.sv \
  $(RTL_DIR)/lowrisc_ibex_ibex_tracer_0.1/rtl/ibex_tracer_pkg.sv \
  $(RTL_DIR)/lowrisc_ibex_ibex_tracer_0.1/rtl/ibex_tracer.sv \
	$(RTL_DIR)/lowrisc_prim_abstract_buf_0/prim_buf.sv \
	$(RTL_DIR)/lowrisc_prim_abstract_clock_gating_0/prim_clock_gating.sv \
	$(RTL_DIR)/lowrisc_prim_abstract_flop_0/prim_flop.sv \
	$(RTL_DIR)/lowrisc_prim_cipher_0/rtl/prim_subst_perm.sv \
	$(RTL_DIR)/lowrisc_prim_cipher_0/rtl/prim_present.sv \
	$(RTL_DIR)/lowrisc_prim_cipher_0/rtl/prim_prince.sv \
	$(RTL_DIR)/lowrisc_prim_generic_clock_mux2_0/rtl/prim_generic_clock_mux2.sv \
	$(RTL_DIR)/lowrisc_prim_generic_ram_1p_0/rtl/prim_generic_ram_1p.sv \
	$(RTL_DIR)/lowrisc_prim_lfsr_0.1/rtl/prim_lfsr.sv \
	$(RTL_DIR)/lowrisc_prim_util_0.1/rtl/prim_util_pkg.sv \
	$(RTL_DIR)/lowrisc_prim_abstract_clock_mux2_0/prim_clock_mux2.sv \
	$(RTL_DIR)/lowrisc_prim_badbit_ram_1p_0/prim_badbit_ram_1p.sv \
	$(RTL_DIR)/lowrisc_prim_onehot_check_0/rtl/prim_onehot_check.sv \
	$(RTL_DIR)/lowrisc_ibex_ibex_core_0.1/rtl/ibex_alu.sv \
	$(RTL_DIR)/lowrisc_ibex_ibex_core_0.1/rtl/ibex_branch_predict.sv \
	$(RTL_DIR)/lowrisc_ibex_ibex_core_0.1/rtl/ibex_compressed_decoder.sv \
	$(RTL_DIR)/lowrisc_ibex_ibex_core_0.1/rtl/ibex_controller.sv \
	$(RTL_DIR)/lowrisc_ibex_ibex_core_0.1/rtl/ibex_cs_registers.sv \
	$(RTL_DIR)/lowrisc_ibex_ibex_core_0.1/rtl/ibex_csr.sv \
	$(RTL_DIR)/lowrisc_ibex_ibex_core_0.1/rtl/ibex_counter.sv \
	$(RTL_DIR)/lowrisc_ibex_ibex_core_0.1/rtl/ibex_decoder.sv \
	$(RTL_DIR)/lowrisc_ibex_ibex_core_0.1/rtl/ibex_ex_block.sv \
	$(RTL_DIR)/lowrisc_ibex_ibex_core_0.1/rtl/ibex_fetch_fifo.sv \
	$(RTL_DIR)/lowrisc_ibex_ibex_core_0.1/rtl/ibex_id_stage.sv \
	$(RTL_DIR)/lowrisc_ibex_ibex_core_0.1/rtl/ibex_if_stage.sv \
	$(RTL_DIR)/lowrisc_ibex_ibex_core_0.1/rtl/ibex_load_store_unit.sv \
	$(RTL_DIR)/lowrisc_ibex_ibex_core_0.1/rtl/ibex_multdiv_fast.sv \
	$(RTL_DIR)/lowrisc_ibex_ibex_core_0.1/rtl/ibex_multdiv_slow.sv \
	$(RTL_DIR)/lowrisc_ibex_ibex_core_0.1/rtl/ibex_prefetch_buffer.sv \
	$(RTL_DIR)/lowrisc_ibex_ibex_core_0.1/rtl/ibex_pmp.sv \
	$(RTL_DIR)/lowrisc_ibex_ibex_core_0.1/rtl/ibex_wb_stage.sv \
	$(RTL_DIR)/lowrisc_ibex_ibex_core_0.1/rtl/ibex_dummy_instr.sv \
	$(RTL_DIR)/lowrisc_ibex_ibex_core_0.1/rtl/ibex_core.sv \
	$(RTL_DIR)/lowrisc_prim_abstract_ram_1p_0/prim_ram_1p.sv \
	$(RTL_DIR)/lowrisc_prim_ram_1p_adv_0.1/rtl/prim_ram_1p_adv.sv \
	$(RTL_DIR)/lowrisc_prim_ram_1p_scr_0.1/rtl/prim_ram_1p_scr.sv \
	$(RTL_DIR)/lowrisc_ibex_ibex_top_0.1/rtl/ibex_register_file_ff.sv \
	$(RTL_DIR)/lowrisc_ibex_ibex_top_0.1/rtl/ibex_register_file_fpga.sv \
	$(RTL_DIR)/lowrisc_ibex_ibex_top_0.1/rtl/ibex_register_file_latch.sv \
	$(RTL_DIR)/lowrisc_ibex_ibex_top_0.1/rtl/ibex_lockstep.sv \
	$(RTL_DIR)/lowrisc_ibex_ibex_top_0.1/rtl/ibex_top.sv \
  $(RTL_DIR)/lowrisc_ibex_ibex_top_tracing_0.1/rtl/ibex_top_tracing.sv \
  $(BENCH_DIR)/lumen_mem_monitor.sv \
	$(BENCH_DIR)/$(IBEX_WRAPPER)
# use VHDL_SOURCES for VHDL files

# TOPLEVEL is the name of the toplevel module in your Verilog or VHDL file
TOPLEVEL = lumen_ibex

# MODULE is the basename of the Python test file
MODULE = cocotb_session

#--trace-fst --trace-structs \

EXTRA_ARGS += $(LUMEN_PARAM_ARGS) \
	+incdir+$(RTL_DIR)/lowrisc_dv_crypto_prince_ref_0.1 \
	-CFLAGS -I$(RTL_DIR)/lowrisc_dv_crypto_prince_ref_0.1 \
	+incdir+$(RTL_DIR)/lowrisc_dv_dv_fcov_macros_0 \
	-CFLAGS -I$(RTL_DIR)/lowrisc_dv_dv_fcov_macros_0 \
	+incdir+$(RTL_DIR)/lowrisc_dv_secded_enc_0 \
	-CFLAGS -I$(RTL_DIR)/lowrisc_dv_secded_enc_0 \
	+incdir+$(RTL_DIR)/lowrisc_prim_util_get_scramble_params_0/rtl \
	-CFLAGS -I$(RTL_DIR)/lowrisc_prim_util_get_scramble_params_0/rtl \
	+incdir+$(RTL_DIR)/lowrisc_prim_util_memload_0/rtl \
	-CFLAGS -I$(RTL_DIR)/lowrisc_prim_util_memload_0/rtl \
	+incdir+$(RTL_DIR)/lowrisc_dv_scramble_model_0 \
	-CFLAGS -I$(RTL_DIR)/lowrisc_dv_scramble_model_0 \
	+incdir+$(RTL_DIR)/lowrisc_dv_verilator_memutil_dpi_0/cpp \
	-CFLAGS -I$(RTL_DIR)/lowrisc_dv_verilator_memutil_dpi_0/cpp \
	+incdir+$(RTL_DIR)/lowrisc_dv_verilator_memutil_dpi_scrambled_0/cpp \
	-CFLAGS -I$(RTL_DIR)/lowrisc_dv_verilator_memutil_dpi_scrambled_0/cpp \
	+incdir+$(RTL_DIR)/lowrisc_prim_assert_0.1/rtl \
	-CFLAGS -I$(RTL_DIR)/lowrisc_prim_assert_0.1/rtl \
	+incdir+$(RTL_DIR)/lowrisc_ibex_ibex_core_0.1/rtl \
	-CFLAGS -I$(RTL_DIR)/lowrisc_ibex_ibex_core_0.1/rtl \
  $(if $(filter 1,$(LUMEN_RTL_FCOV)),,-DSYNTHESIS=1) \
  -DRVFI=1 \
	--trace-fst \
  --trace-structs \
	-Wno-fatal \
  -CFLAGS "-std=c++14 -Wall -O3"


# include cocotb's make rules to take care of the simulator setup
include $(shell cocotb-config --makefiles)/Makefile.sim
