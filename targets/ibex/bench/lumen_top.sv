// Copyright lowRISC contributors.
// Licensed under the Apache License, Version 2.0, see LICENSE for details.
// SPDX-License-Identifier: Apache-2.0

module lumen_ibex(
  `include "lumen_official_ports.svh"
  input logic instr_err_i, data_err_i,
  input logic irq_software_i, irq_timer_i, irq_external_i, irq_nm_i,
  input logic [14:0] irq_fast_i,
  input logic debug_req_i,
  output logic [31:0] lumen_flags_o, lumen_instruction_o, lumen_pc_o,
  output logic [3:0] lumen_fsm_o, lumen_next_fsm_o,
  output logic [1:0] lumen_privilege_o,
  output logic lumen_mie_o, lumen_core_clk_o,
  output logic [5:0] lumen_irqs_o,
  output logic [2:0] lumen_lsu_state_o,
  output logic lumen_data_error_o, lumen_data_response_o,
  output logic [1:0] lumen_profile_o, lumen_mpp_o, lumen_priv_lsu_o,
  output logic lumen_mprv_o, lumen_nmi_o, lumen_irq_pending_o, lumen_debug_req_o,
  output logic lumen_ls_error_o, lumen_ls_pmp_o, lumen_ls_first_o, lumen_ls_second_o,
  output logic lumen_ls_mis_pmp_2_o, lumen_ls_data_pmp_o, lumen_if_compressed_o,
  output logic lumen_wb_valid_o, lumen_wb_load_o, lumen_wb_store_o,
  output logic [2:0] lumen_pmp_err_o,
  output logic [3:0] lumen_match_i_o, lumen_match_i2_o, lumen_match_d_o,
  output logic lumen_current_priv_err_o,
  output logic [31:0] lumen_mcause_o, lumen_mepc_o, lumen_mtval_o, lumen_pmp_cfg_o,
  
  input  logic                         clk_i,
  input  logic                         rst_ni,

  // Instruction memory interface
  output logic                         instr_req_o,
  input  logic                         instr_gnt_i,
  input  logic                         instr_rvalid_i,
  output logic [31:0]                  instr_addr_o,
  input  logic [31:0]                  instr_rdata_i,

  // Data memory interface
  output logic                         data_req_o,
  input  logic                         data_gnt_i,
  input  logic                         data_rvalid_i,
  output logic                         data_we_o,
  output logic [3:0]                   data_be_o,
  output logic [31:0]                  data_addr_o,
  output logic [31:0]                  data_wdata_o,
  input  logic [31:0]                  data_rdata_i
);
  parameter bit                 SecureIbex               = 1'b0;
  parameter bit                 ICacheScramble           = 1'b0;
  parameter bit                 PMPEnable                = 1'b0;
  parameter int unsigned        PMPGranularity           = 0;
  parameter int unsigned        PMPNumRegions            = 4;
  parameter int unsigned        MHPMCounterNum           = 0;
  parameter int unsigned        MHPMCounterWidth         = 40;
  parameter bit                 RV32E                    = 1'b0;
  parameter ibex_pkg::rv32m_e   RV32M                    = ibex_pkg::RV32MFast;
  parameter ibex_pkg::rv32b_e   RV32B                    = ibex_pkg::RV32BNone;
  parameter ibex_pkg::regfile_e RegFile                  = ibex_pkg::RegFileFF;
  parameter bit                 BranchTargetALU          = 1'b0;
  parameter bit                 WritebackStage           = 1'b0;
  parameter bit                 ICache                   = 1'b0;
  parameter bit                 DbgTriggerEn             = 1'b0;
  parameter bit                 ICacheECC                = 1'b0;
  parameter bit                 BranchPredictor          = 1'b0;

  ibex_top_tracing #(
      .SecureIbex      ( SecureIbex       ),
      .ICacheScramble  ( ICacheScramble   ),
      .PMPEnable       ( PMPEnable        ),
      .PMPGranularity  ( PMPGranularity   ),
      .PMPNumRegions   ( PMPNumRegions    ),
      .MHPMCounterNum  ( MHPMCounterNum   ),
      .MHPMCounterWidth( MHPMCounterWidth ),
      .RV32E           ( RV32E            ),
      .RV32M           ( RV32M            ),
      .RV32B           ( RV32B            ),
      .RegFile         ( RegFile          ),
      .BranchTargetALU ( BranchTargetALU  ),
      .ICache          ( ICache           ),
      .ICacheECC       ( ICacheECC        ),
      .WritebackStage  ( WritebackStage   ),
      .BranchPredictor ( BranchPredictor  ),
      .DbgTriggerEn    ( DbgTriggerEn     ),
      .DmHaltAddr      ( 32'h00100000     ),
      .DmExceptionAddr ( 32'h00100000     )
  ) u_top (
    .clk_i,
    .rst_ni,

    .test_en_i              ('b0),
    .scan_rst_ni            (1'b1),
    .ram_cfg_i              ('b0),

    .hart_id_i              (32'b0),
    // First instruction executed is at 0x0 + 0x80
    .boot_addr_i            (32'h00100000),

    .instr_req_o,
    .instr_gnt_i,
    .instr_rvalid_i,
    .instr_addr_o,
    .instr_rdata_i,
    .instr_rdata_intg_i     ('0),
    .instr_err_i(instr_err_i),

    .data_req_o,
    .data_gnt_i,
    .data_rvalid_i,
    .data_we_o,
    .data_be_o,
    .data_addr_o,
    .data_wdata_o,
    .data_wdata_intg_o      (),
    .data_rdata_i,
    .data_rdata_intg_i      ('0),
    .data_err_i(data_err_i),

    .irq_software_i(irq_software_i),
    .irq_timer_i(irq_timer_i),
    .irq_external_i(irq_external_i),
    .irq_fast_i(irq_fast_i),
    .irq_nm_i(irq_nm_i),

    .scramble_key_valid_i   ('0),
    .scramble_key_i         ('0),
    .scramble_nonce_i       ('0),
    .scramble_req_o         (),

    .debug_req_i(debug_req_i),
    .crash_dump_o           (),
    .double_fault_seen_o    (),

    .fetch_enable_i         (ibex_pkg::IbexMuBiOn),
    .alert_minor_o          (),
    .alert_major_internal_o (),
    .alert_major_bus_o      (),
    .core_sleep_o           ()
  );

  // Read-only observations. No hierarchical force or deposit is used.
  assign lumen_flags_o[0] = u_top.u_ibex_top.u_ibex_core.id_stage_i.instr_valid_i; // valid
  assign lumen_flags_o[1] = u_top.u_ibex_top.u_ibex_core.id_stage_i.instr_fetch_err_i; // fetch_error
  assign lumen_flags_o[2] = u_top.u_ibex_top.u_ibex_core.id_stage_i.illegal_c_insn_i; // illegal_c
  assign lumen_flags_o[3] = u_top.u_ibex_top.u_ibex_core.id_stage_i.illegal_insn_dec; // illegal_dec
  assign lumen_flags_o[4] = u_top.u_ibex_top.u_ibex_core.id_stage_i.illegal_csr_insn_i; // illegal_csr
  assign lumen_flags_o[5] = u_top.u_ibex_top.u_ibex_core.cs_registers_i.illegal_csr_priv; // illegal_csr_priv
  assign lumen_flags_o[6] = u_top.u_ibex_top.u_ibex_core.cs_registers_i.illegal_csr_dbg; // illegal_csr_dbg
  assign lumen_flags_o[7] = u_top.u_ibex_top.u_ibex_core.id_stage_i.illegal_insn_o; // illegal_out
  assign lumen_flags_o[8] = u_top.u_ibex_top.u_ibex_core.id_stage_i.illegal_dret_insn; // illegal_dret
  assign lumen_flags_o[9] = u_top.u_ibex_top.u_ibex_core.id_stage_i.illegal_umode_insn; // illegal_umode
  assign lumen_flags_o[10] = u_top.u_ibex_top.u_ibex_core.id_stage_i.debug_ebreakm_i; // ebreakm
  assign lumen_flags_o[11] = u_top.u_ibex_top.u_ibex_core.id_stage_i.debug_ebreaku_i; // ebreaku
  assign lumen_flags_o[12] = u_top.u_ibex_top.u_ibex_core.id_stage_i.stall_mem; // stall_mem
  assign lumen_flags_o[13] = u_top.u_ibex_top.u_ibex_core.id_stage_i.stall_ld_hz; // stall_ld
  assign lumen_flags_o[14] = u_top.u_ibex_top.u_ibex_core.id_stage_i.stall_multdiv; // stall_muldiv
  assign lumen_flags_o[15] = u_top.u_ibex_top.u_ibex_core.id_stage_i.stall_branch; // stall_branch
  assign lumen_flags_o[16] = u_top.u_ibex_top.u_ibex_core.id_stage_i.stall_jump; // stall_jump
  assign lumen_flags_o[17] = u_top.u_ibex_top.u_ibex_core.debug_mode; // debug_mode
  assign lumen_flags_o[18] = u_top.u_ibex_top.u_ibex_core.id_stage_i.irq_pending_i; // irq_pending
  assign lumen_flags_o[19] = (u_top.u_ibex_top.u_ibex_core.id_stage_i.controller_i.debug_req_i || u_top.u_ibex_top.u_ibex_core.id_stage_i.controller_i.debug_mode_q || u_top.u_ibex_top.u_ibex_core.id_stage_i.controller_i.debug_single_step_i); // all_debug_req
  assign lumen_flags_o[20] = (u_top.u_ibex_top.u_ibex_core.id_stage_i.controller_i.ctrl_fsm_cs == ibex_pkg::SLEEP && u_top.u_ibex_top.u_ibex_core.id_stage_i.controller_i.ctrl_fsm_ns == ibex_pkg::FIRST_FETCH && (u_top.u_ibex_top.u_ibex_core.id_stage_i.controller_i.debug_req_i || u_top.u_ibex_top.u_ibex_core.id_stage_i.controller_i.debug_mode_q || u_top.u_ibex_top.u_ibex_core.id_stage_i.controller_i.debug_single_step_i)); // debug_wakeup
  assign lumen_flags_o[21] = (u_top.u_ibex_top.u_ibex_core.id_stage_i.controller_i.ctrl_fsm_cs != ibex_pkg::IRQ_TAKEN && u_top.u_ibex_top.u_ibex_core.id_stage_i.controller_i.ctrl_fsm_ns == ibex_pkg::IRQ_TAKEN); // interrupt_taken
  assign lumen_flags_o[22] = (u_top.u_ibex_top.u_ibex_core.id_stage_i.controller_i.ctrl_fsm_cs != ibex_pkg::DBG_TAKEN_IF && u_top.u_ibex_top.u_ibex_core.id_stage_i.controller_i.ctrl_fsm_ns == ibex_pkg::DBG_TAKEN_IF); // debug_entry_if
  assign lumen_flags_o[23] = (u_top.u_ibex_top.u_ibex_core.id_stage_i.controller_i.ctrl_fsm_cs != ibex_pkg::DBG_TAKEN_ID && u_top.u_ibex_top.u_ibex_core.id_stage_i.controller_i.ctrl_fsm_ns == ibex_pkg::DBG_TAKEN_ID); // debug_entry_id
  assign lumen_flags_o[24] = (u_top.u_ibex_top.u_ibex_core.id_stage_i.controller_i.ctrl_fsm_cs != ibex_pkg::FLUSH && u_top.u_ibex_top.u_ibex_core.id_stage_i.controller_i.ctrl_fsm_ns == ibex_pkg::FLUSH); // pipe_flush
  assign lumen_flags_o[25] = (u_top.u_ibex_top.u_ibex_core.id_stage_i.controller_i.do_single_step_d && !u_top.u_ibex_top.u_ibex_core.id_stage_i.controller_i.do_single_step_q); // step_taken
  assign lumen_flags_o[26] = u_top.u_ibex_top.u_ibex_core.id_stage_i.controller_i.do_single_step_d; // do_step
  assign lumen_flags_o[27] = u_top.u_ibex_top.u_ibex_core.id_stage_i.mret_insn_dec; // mret_dec
  assign lumen_flags_o[28] = u_top.u_ibex_top.u_ibex_core.id_stage_i.wfi_insn_dec; // wfi_dec
  assign lumen_flags_o[29] = (u_top.u_ibex_top.u_ibex_core.csr_op == ibex_pkg::CSR_OP_READ && u_top.u_ibex_top.u_ibex_core.csr_access && (u_top.u_ibex_top.u_ibex_core.csr_op_en || u_top.u_ibex_top.u_ibex_core.illegal_insn_id)); // csr_read_only
  assign lumen_flags_o[30] = (u_top.u_ibex_top.u_ibex_core.cs_registers_i.csr_wr && u_top.u_ibex_top.u_ibex_core.csr_access && (u_top.u_ibex_top.u_ibex_core.csr_op_en || u_top.u_ibex_top.u_ibex_core.illegal_insn_id)); // csr_write
  assign lumen_flags_o[31] = u_top.u_ibex_top.u_ibex_core.cs_registers_i.illegal_csr; // csr_invalid
  assign lumen_instruction_o = u_top.u_ibex_top.u_ibex_core.id_stage_i.instr_rdata_i;
  assign lumen_pc_o = u_top.u_ibex_top.u_ibex_core.id_stage_i.pc_id_i;
  assign lumen_fsm_o = u_top.u_ibex_top.u_ibex_core.id_stage_i.controller_i.ctrl_fsm_cs;
  assign lumen_next_fsm_o = u_top.u_ibex_top.u_ibex_core.id_stage_i.controller_i.ctrl_fsm_ns;
  assign lumen_privilege_o = u_top.u_ibex_top.u_ibex_core.priv_mode_id;
  assign lumen_mie_o = u_top.u_ibex_top.u_ibex_core.csr_mstatus_mie;
  assign lumen_core_clk_o = u_top.u_ibex_top.u_ibex_core.clk_i;
  assign lumen_irqs_o = {u_top.u_ibex_top.u_ibex_core.id_stage_i.controller_i.irq_nm_ext_i, u_top.u_ibex_top.u_ibex_core.id_stage_i.controller_i.irq_nm_int, |u_top.u_ibex_top.u_ibex_core.id_stage_i.controller_i.irqs_i.irq_fast, u_top.u_ibex_top.u_ibex_core.id_stage_i.controller_i.irqs_i.irq_external, u_top.u_ibex_top.u_ibex_core.id_stage_i.controller_i.irqs_i.irq_software, u_top.u_ibex_top.u_ibex_core.id_stage_i.controller_i.irqs_i.irq_timer};
  assign lumen_lsu_state_o = u_top.u_ibex_top.u_ibex_core.load_store_unit_i.ls_fsm_cs;
  assign lumen_data_error_o = u_top.u_ibex_top.u_ibex_core.load_store_unit_i.data_bus_err_i;
  assign lumen_data_response_o = u_top.u_ibex_top.u_ibex_core.load_store_unit_i.data_rvalid_i;

  // LUMEN observers are read-only. The helper expressions mirror the pinned
  // official fcov sources; none of these signals drive the processor.
  `define TC u_top.u_ibex_top.u_ibex_core
  `define TL u_top.u_ibex_top.u_ibex_core.load_store_unit_i
  assign lumen_profile_o = {PMPEnable, WritebackStage};
  assign lumen_mpp_o = `TC.cs_registers_i.mstatus_q.mpp;
  assign lumen_mprv_o = `TC.cs_registers_i.mstatus_q.mprv;
  assign lumen_priv_lsu_o = `TC.priv_mode_lsu;
  assign lumen_nmi_o = lumen_irqs_o[5] | lumen_irqs_o[4];
  assign lumen_irq_pending_o = `TC.id_stage_i.irq_pending_i | `TC.id_stage_i.irq_nm_i;
  assign lumen_debug_req_o = `TC.id_stage_i.controller_i.debug_req_i &
                              ~`TC.id_stage_i.controller_i.debug_mode_q;
  assign lumen_ls_error_o = (`TL.load_err_o | `TL.store_err_o) & ~`TL.pmp_err_q;
  assign lumen_ls_pmp_o = (`TL.load_err_o | `TL.store_err_o) & `TL.pmp_err_q;
  assign lumen_ls_first_o = `TL.lsu_req_i & (`TL.ls_fsm_cs == 0);
  assign lumen_ls_second_o = (`TL.ls_fsm_cs == 2) & `TL.data_req_o & `TL.addr_incr_req_o;
  assign lumen_ls_mis_pmp_2_o = (`TL.ls_fsm_cs inside {2,4}) && `TL.data_pmp_err_i;
  assign lumen_ls_data_pmp_o = `TL.data_pmp_err_i;
  assign lumen_if_compressed_o = `TC.if_stage_i.instr_is_compressed_out;
  if (WritebackStage) begin : g_lumen_wb
    assign lumen_wb_valid_o = `TC.wb_stage_i.g_writeback_stage.wb_valid_q;
  end else begin : g_lumen_no_wb
    assign lumen_wb_valid_o = 1'b0;
  end
  assign lumen_wb_load_o = `TC.wb_stage_i.outstanding_load_wb_o;
  assign lumen_wb_store_o = `TC.wb_stage_i.outstanding_store_wb_o;
  assign lumen_mcause_o = {(`TC.cs_registers_i.mcause_q.irq_ext |
                           `TC.cs_registers_i.mcause_q.irq_int),
                          (`TC.cs_registers_i.mcause_q.irq_int ? {26{1'b1}} : 26'b0),
                          `TC.cs_registers_i.mcause_q.lower_cause[4:0]};
  assign lumen_mepc_o = `TC.cs_registers_i.mepc_q;
  assign lumen_mtval_o = `TC.cs_registers_i.mtval_q;
  assign lumen_pmp_err_o = {`TC.pmp_req_err[ibex_pkg::PMP_D],
                           `TC.pmp_req_err[ibex_pkg::PMP_I2],
                           `TC.pmp_req_err[ibex_pkg::PMP_I]};
  if (PMPEnable) begin : g_lumen_pmp
    logic [PMPNumRegions-1:0] current_priv_perm;
    assign lumen_match_i_o = 4'(`TC.g_pmp.pmp_i.region_match_all[ibex_pkg::PMP_I]);
    assign lumen_match_i2_o = 4'(`TC.g_pmp.pmp_i.region_match_all[ibex_pkg::PMP_I2]);
    assign lumen_match_d_o = 4'(`TC.g_pmp.pmp_i.region_match_all[ibex_pkg::PMP_D]);
    for (genvar r=0; r<PMPNumRegions; r++) begin : g_perm
      assign current_priv_perm[r] = `TC.g_pmp.pmp_i.perm_check_wrapper(
        `TC.csr_pmp_mseccfg.mml, `TC.csr_pmp_cfg[r],
        `TC.g_pmp.pmp_i.pmp_req_type_i[ibex_pkg::PMP_D], `TC.priv_mode_id,
        `TC.g_pmp.pmp_i.region_basic_perm_check[ibex_pkg::PMP_D][r]);
      assign lumen_pmp_cfg_o[8*r+:8] = {`TC.csr_pmp_cfg[r].lock, 2'b0,
        `TC.csr_pmp_cfg[r].mode, `TC.csr_pmp_cfg[r].exec,
        `TC.csr_pmp_cfg[r].write, `TC.csr_pmp_cfg[r].read};
    end
    assign lumen_current_priv_err_o = `TC.g_pmp.pmp_i.access_fault_check(
      `TC.csr_pmp_mseccfg.mmwp, `TC.csr_pmp_mseccfg.mml,
      `TC.g_pmp.pmp_i.pmp_req_type_i[ibex_pkg::PMP_D],
      `TC.g_pmp.pmp_i.region_match_all[ibex_pkg::PMP_D],
      `TC.priv_mode_id, current_priv_perm);
  end else begin : g_lumen_no_pmp
    assign lumen_match_i_o = '0;
    assign lumen_match_i2_o = '0;
    assign lumen_match_d_o = '0;
    assign lumen_current_priv_err_o = '0;
    assign lumen_pmp_cfg_o = '0;
  end
  `include "lumen_official_observer.svh"
  `undef TC
  `undef TL
endmodule
