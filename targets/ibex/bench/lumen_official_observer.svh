// Frozen observer generated from pinned lowRISC sources; hashes in ../coverage/probes.json.
import ibex_pkg::*;
wire lumen_core_clock = lumen_core_clk_o;
begin : g_official_uarch
  typedef enum {
    InstrCategoryALU,
    InstrCategoryMul,
    InstrCategoryDiv,
    InstrCategoryBranch,
    InstrCategoryJump,
    InstrCategoryLoad,
    InstrCategoryStore,
    InstrCategoryCSRAccess,
    InstrCategoryEBreakDbg,
    InstrCategoryEBreakExc,
    InstrCategoryECall,
    InstrCategoryMRet,
    InstrCategoryDRet,
    InstrCategoryWFI,
    InstrCategoryFence,
    InstrCategoryFenceI,
    InstrCategoryNone,
    InstrCategoryFetchError,
    InstrCategoryCompressedIllegal,
    InstrCategoryUncompressedIllegal,
    InstrCategoryCSRIllegal,
    InstrCategoryPrivIllegal,
    InstrCategoryOtherIllegal,
                                                                                             
                                                                                                  
                              
    InstrCategoryOther
  } instr_category_e;

  typedef enum {
    IdStallTypeNone,
    IdStallTypeInstr,
    IdStallTypeLdHz,
    IdStallTypeMem
  } id_stall_type_e;

  instr_category_e id_instr_category;
                                                                                                
                                                                                                
                                                                                                 
                          
  always_comb begin
    id_instr_category = InstrCategoryOther;

    case (u_top.u_ibex_top.u_ibex_core.id_stage_i.instr_rdata_i[6:0])
      ibex_pkg::OPCODE_LUI:    id_instr_category = InstrCategoryALU;
      ibex_pkg::OPCODE_AUIPC:  id_instr_category = InstrCategoryALU;
      ibex_pkg::OPCODE_JAL:    id_instr_category = InstrCategoryJump;
      ibex_pkg::OPCODE_JALR:   id_instr_category = InstrCategoryJump;
      ibex_pkg::OPCODE_BRANCH: id_instr_category = InstrCategoryBranch;
      ibex_pkg::OPCODE_LOAD:   id_instr_category = InstrCategoryLoad;
      ibex_pkg::OPCODE_STORE:  id_instr_category = InstrCategoryStore;
      ibex_pkg::OPCODE_OP_IMM: id_instr_category = InstrCategoryALU;
      ibex_pkg::OPCODE_OP: begin
        if ({u_top.u_ibex_top.u_ibex_core.id_stage_i.instr_rdata_i[26], u_top.u_ibex_top.u_ibex_core.id_stage_i.instr_rdata_i[13:12]} == {1'b1, 2'b01}) begin
          id_instr_category = InstrCategoryALU;                       
        end else if (u_top.u_ibex_top.u_ibex_core.id_stage_i.instr_rdata_i[31:25] inside {7'b000_0000, 7'b010_0000, 7'b011_0000,
              7'b011_0100, 7'b001_0100, 7'b001_0000, 7'b000_0101, 7'b000_0100, 7'b010_0100}) begin
          id_instr_category = InstrCategoryALU;                                       
        end else if (u_top.u_ibex_top.u_ibex_core.id_stage_i.instr_rdata_i[31:25] == 7'b000_0001) begin
          if (u_top.u_ibex_top.u_ibex_core.id_stage_i.instr_rdata_i[14]) begin
            id_instr_category = InstrCategoryDiv;        
          end else begin
            id_instr_category = InstrCategoryMul;        
          end
        end
      end
      ibex_pkg::OPCODE_SYSTEM: begin
        if (u_top.u_ibex_top.u_ibex_core.id_stage_i.instr_rdata_i[14:12] == 3'b000) begin
          case (u_top.u_ibex_top.u_ibex_core.id_stage_i.instr_rdata_i[31:20])
            12'h000: id_instr_category = InstrCategoryECall;
            12'h001: begin
              if (u_top.u_ibex_top.u_ibex_core.id_stage_i.debug_ebreakm_i && u_top.u_ibex_top.u_ibex_core.priv_mode_id == PRIV_LVL_M) begin
                id_instr_category = InstrCategoryEBreakDbg;
              end else if (u_top.u_ibex_top.u_ibex_core.id_stage_i.debug_ebreaku_i && u_top.u_ibex_top.u_ibex_core.priv_mode_id == PRIV_LVL_U) begin
                id_instr_category = InstrCategoryEBreakDbg;
              end else begin
                id_instr_category = InstrCategoryEBreakExc;
              end
            end
            12'h302: id_instr_category = InstrCategoryMRet;
            12'h7b2: id_instr_category = InstrCategoryDRet;
            12'h105: id_instr_category = InstrCategoryWFI;
          endcase
        end else begin
          id_instr_category = InstrCategoryCSRAccess;
        end
      end
      ibex_pkg::OPCODE_MISC_MEM: begin
        case (u_top.u_ibex_top.u_ibex_core.id_stage_i.instr_rdata_i[14:12])
          3'b000: id_instr_category = InstrCategoryFence;
          3'b001: id_instr_category = InstrCategoryFenceI;
        endcase
      end
      default: id_instr_category = InstrCategoryOther;
    endcase

    if (u_top.u_ibex_top.u_ibex_core.id_stage_i.instr_valid_i) begin
      if (u_top.u_ibex_top.u_ibex_core.id_stage_i.instr_fetch_err_i) begin
        id_instr_category = InstrCategoryFetchError;
      end else if (u_top.u_ibex_top.u_ibex_core.id_stage_i.illegal_c_insn_i) begin
        id_instr_category = InstrCategoryCompressedIllegal;
      end else if (u_top.u_ibex_top.u_ibex_core.id_stage_i.illegal_insn_dec) begin
        id_instr_category = InstrCategoryUncompressedIllegal;
      end else if (u_top.u_ibex_top.u_ibex_core.id_stage_i.illegal_csr_insn_i) begin
        if (u_top.u_ibex_top.u_ibex_core.cs_registers_i.illegal_csr_priv || u_top.u_ibex_top.u_ibex_core.cs_registers_i.illegal_csr_dbg) begin
          id_instr_category = InstrCategoryPrivIllegal;
        end else begin
          id_instr_category = InstrCategoryCSRIllegal;
        end
      end else if (u_top.u_ibex_top.u_ibex_core.id_stage_i.illegal_insn_o) begin
        if (u_top.u_ibex_top.u_ibex_core.id_stage_i.illegal_dret_insn || u_top.u_ibex_top.u_ibex_core.id_stage_i.illegal_umode_insn) begin
          id_instr_category = InstrCategoryPrivIllegal;
        end else begin
          id_instr_category = InstrCategoryOtherIllegal;
        end
      end
    end else begin
      id_instr_category = InstrCategoryNone;
    end
  end

                                                                                                   

                                                                                                    
                                                                                                   
                                                                                               
                                                               
  

  

  

  

                                                                           
                                                         
  

  

  

  
  

  

  

  

  

  

  



  id_stall_type_e id_stall_type;

                                                                                    
  always_comb begin
    id_stall_type = IdStallTypeNone;

    if (u_top.u_ibex_top.u_ibex_core.id_stage_i.instr_valid_i) begin
      if (u_top.u_ibex_top.u_ibex_core.id_stage_i.stall_mem) begin
        id_stall_type = IdStallTypeMem;
      end

      if (u_top.u_ibex_top.u_ibex_core.id_stage_i.stall_ld_hz) begin
        id_stall_type = IdStallTypeLdHz;
      end

      if (u_top.u_ibex_top.u_ibex_core.id_stage_i.stall_multdiv || u_top.u_ibex_top.u_ibex_core.id_stage_i.stall_branch ||
          u_top.u_ibex_top.u_ibex_core.id_stage_i.stall_jump) begin
        id_stall_type = IdStallTypeInstr;
      end
    end
  end

                           
  typedef enum {
    IFStageFullAndFetching,
    IFStageFullAndIdle,
    IFStageEmptyAndFetching,
    IFStageEmptyAndIdle
  } if_stage_state_e;

                                          
  typedef enum {
    PipeStageFullAndStalled,
    PipeStageFullAndUnstalled,
    PipeStageEmpty
  } pipe_stage_state_e;

  if_stage_state_e   if_stage_state;
  pipe_stage_state_e id_stage_state;
  pipe_stage_state_e wb_stage_state;

  always_comb begin
    if_stage_state = IFStageEmptyAndIdle;

    if (u_top.u_ibex_top.u_ibex_core.if_stage_i.if_instr_valid) begin
      if (u_top.u_ibex_top.u_ibex_core.if_stage_i.req_i) begin
        if_stage_state = IFStageFullAndFetching;
      end else begin
        if_stage_state = IFStageFullAndIdle;
      end
    end else if(u_top.u_ibex_top.u_ibex_core.if_stage_i.req_i) begin
      if_stage_state = IFStageEmptyAndFetching;
    end
  end

  always_comb begin
    id_stage_state = PipeStageEmpty;

    if (u_top.u_ibex_top.u_ibex_core.id_stage_i.instr_valid_i) begin
      if (u_top.u_ibex_top.u_ibex_core.id_stage_i.id_in_ready_o) begin
        id_stage_state = PipeStageFullAndUnstalled;
      end else begin
        id_stage_state = PipeStageFullAndStalled;
      end
    end
  end

  always_comb begin
    wb_stage_state = PipeStageEmpty;

    if (u_top.u_ibex_top.u_ibex_core.wb_stage_i.fcov_wb_valid) begin
      if (u_top.u_ibex_top.u_ibex_core.wb_stage_i.ready_wb_o) begin
        wb_stage_state = PipeStageFullAndUnstalled;
      end else begin
        wb_stage_state = PipeStageFullAndStalled;
      end
    end
  end

                                                                                 
                                                                                      
                                                                                         
                                                                  
  logic kept_wfi_with_irq;

  always_latch begin
    if (u_top.u_ibex_top.u_ibex_core.id_stage_i.controller_i.ctrl_fsm_cs == DECODE) begin
      kept_wfi_with_irq = 1'b0;
    end else if (u_top.u_ibex_top.u_ibex_core.id_stage_i.controller_i.ctrl_fsm_cs == SLEEP &&
                 u_top.u_ibex_top.u_ibex_core.id_stage_i.controller_i.ctrl_fsm_ns == SLEEP &&
                 (|u_top.u_ibex_top.u_ibex_core.cs_registers_i.mip)) begin
      kept_wfi_with_irq = 1'b1;
    end
  end

  logic instr_id_matches_trigger_d, instr_id_matches_trigger_q;

  assign instr_id_matches_trigger_d = u_top.u_ibex_top.u_ibex_core.id_stage_i.controller_i.trigger_match_i &&
                                      u_top.u_ibex_top.u_ibex_core.id_stage_i.controller_i.fcov_debug_entry_if;

                                                                             
                                                                                         
                                               
  always @(posedge lumen_core_clock or negedge rst_ni) begin
    if (!rst_ni) begin
      instr_id_matches_trigger_q <= 1'b0;
    end else begin
      instr_id_matches_trigger_q <= instr_id_matches_trigger_d;
    end
  end

                                                                                        
  logic [31:0]     prev_store_addr;
  logic [31:0]     data_addr_incr;
  logic [31:0]     curr_data_addr;
  logic            raw_hz;

  always @(posedge lumen_core_clock or negedge rst_ni) begin
    if (!rst_ni) begin
      prev_store_addr <= 1'b0;
    end else if (u_top.u_ibex_top.u_ibex_core.load_store_unit_i.data_we_o) begin
                                                                                              
                                                                                             
                                    
      prev_store_addr <= u_top.u_ibex_top.u_ibex_core.load_store_unit_i.data_addr_o;
    end
  end

                                                                                                 
                  
  always_comb begin
    if (u_top.u_ibex_top.u_ibex_core.load_store_unit_i.split_misaligned_access) begin
      data_addr_incr = u_top.u_ibex_top.u_ibex_core.load_store_unit_i.data_addr + 4;
      curr_data_addr = {data_addr_incr[2+:30],2'b00};
    end else begin
      curr_data_addr = u_top.u_ibex_top.u_ibex_core.load_store_unit_i.data_addr;
    end
  end

                                                                                                  
                                                                                
  assign raw_hz = u_top.u_ibex_top.u_ibex_core.wb_stage_i.outstanding_store_wb_o &&
                  id_instr_category == InstrCategoryLoad &&
                  prev_store_addr == curr_data_addr;

                                                                      
  logic [5:0] fcov_irqs;

  assign fcov_irqs = {u_top.u_ibex_top.u_ibex_core.id_stage_i.controller_i.irq_nm_ext_i,
                      u_top.u_ibex_top.u_ibex_core.id_stage_i.controller_i.irq_nm_int,
                      (|u_top.u_ibex_top.u_ibex_core.id_stage_i.controller_i.irqs_i.irq_fast),
                      u_top.u_ibex_top.u_ibex_core.id_stage_i.controller_i.irqs_i.irq_external,
                      u_top.u_ibex_top.u_ibex_core.id_stage_i.controller_i.irqs_i.irq_software,
                      u_top.u_ibex_top.u_ibex_core.id_stage_i.controller_i.irqs_i.irq_timer};

  logic            instr_unstalled;
  logic            instr_unstalled_last;
  logic            id_stall_type_last_valid;
  id_stall_type_e  id_stall_type_last;
  instr_category_e id_instr_category_last;

                                                                                                    
                                                                                                 
                                                                                                  
                                                       
  always @(posedge lumen_core_clock or negedge rst_ni) begin
    if (!rst_ni) begin
                                                                                              
      id_stall_type_last_valid <= 1'b0;
      id_stall_type_last       <= IdStallTypeNone;
      instr_unstalled_last     <= 1'b0;
      id_instr_category_last   <= InstrCategoryNone;
    end else begin
      id_stall_type_last_valid <= 1'b1;
      id_stall_type_last       <= id_stall_type;
      instr_unstalled_last     <= instr_unstalled;
      id_instr_category_last   <= id_instr_category;
    end
  end

  assign instr_unstalled =
    (id_stall_type == IdStallTypeNone) && (id_stall_type_last != IdStallTypeNone) &&
    id_stall_type_last_valid;

                                     
  logic rf_glitch_err;
  logic lockstep_glitch_err;

  logic imem_single_cycle_response, dmem_single_cycle_response;

  lumen_mem_monitor_if iside_mem_monitor(
    .clk_i(lumen_core_clock),
    .rst_ni,
    .req_i(instr_req_o),
    .gnt_i(instr_gnt_i),
    .rvalid_i(instr_rvalid_i),
    .outstanding_requests_o(),
    .single_cycle_response_o(imem_single_cycle_response)
  );

  lumen_mem_monitor_if dside_mem_monitor(
    .clk_i(lumen_core_clock),
    .rst_ni,
    .req_i(data_req_o),
    .gnt_i(data_gnt_i),
    .rvalid_i(data_rvalid_i),
    .outstanding_requests_o(),
    .single_cycle_response_o(dmem_single_cycle_response)
  );


assign rf_glitch_err = 1'b0;
assign lockstep_glitch_err = 1'b0;
assign lumen_official_bus_o[0+:32] = 32'(id_instr_category);
assign lumen_official_bus_o[32+:32] = 32'(id_instr_category_last);
assign lumen_official_bus_o[64+:32] = 32'(id_stall_type);
assign lumen_official_bus_o[96+:32] = 32'(u_top.u_ibex_top.u_ibex_core.id_stage_i.fcov_rf_rd_wb_hz &&
                                     !u_top.u_ibex_top.u_ibex_core.wb_stage_i.outstanding_load_wb_o);
assign lumen_official_bus_o[128+:32] = 32'(raw_hz);
assign lumen_official_bus_o[160+:32] = 32'(u_top.u_ibex_top.u_ibex_core.cs_registers_i.mstatus_q.mprv);
assign lumen_official_bus_o[192+:32] = 32'(u_top.u_ibex_top.u_ibex_core.load_store_unit_i.fcov_ls_error_exception);
assign lumen_official_bus_o[224+:32] = 32'(u_top.u_ibex_top.u_ibex_core.load_store_unit_i.fcov_ls_pmp_exception);
assign lumen_official_bus_o[256+:32] = 32'(u_top.u_ibex_top.u_ibex_core.id_stage_i.fcov_branch_taken);
assign lumen_official_bus_o[288+:32] = 32'(u_top.u_ibex_top.u_ibex_core.id_stage_i.fcov_branch_not_taken);
assign lumen_official_bus_o[320+:32] = 32'(u_top.u_ibex_top.u_ibex_core.priv_mode_id);
assign lumen_official_bus_o[352+:32] = 32'(u_top.u_ibex_top.u_ibex_core.priv_mode_lsu);
assign lumen_official_bus_o[384+:32] = 32'(if_stage_state);
assign lumen_official_bus_o[416+:32] = 32'(id_stage_state);
assign lumen_official_bus_o[448+:32] = 32'(wb_stage_state);
assign lumen_official_bus_o[480+:32] = 32'(u_top.u_ibex_top.u_ibex_core.cs_registers_i.data_ind_timing_o);
assign lumen_official_bus_o[512+:32] = 32'(id_instr_category);
assign lumen_official_bus_o[544+:32] = 32'(u_top.u_ibex_top.u_ibex_core.cs_registers_i.data_ind_timing_o);
assign lumen_official_bus_o[576+:32] = 32'(u_top.u_ibex_top.u_ibex_core.cs_registers_i.dummy_instr_en_o);
assign lumen_official_bus_o[608+:32] = 32'(u_top.u_ibex_top.u_ibex_core.cs_registers_i.dummy_instr_mask_o);
assign lumen_official_bus_o[640+:32] = 32'(u_top.u_ibex_top.u_ibex_core.if_stage_i.fcov_dummy_instr_type);
assign lumen_official_bus_o[672+:32] = 32'(id_instr_category);
assign lumen_official_bus_o[704+:32] = 32'(u_top.u_ibex_top.u_ibex_core.cs_registers_i.dummy_instr_en_o);
assign lumen_official_bus_o[736+:32] = 32'(u_top.u_ibex_top.u_ibex_core.if_stage_i.fcov_insert_dummy_instr);
assign lumen_official_bus_o[768+:32] = 32'(u_top.u_ibex_top.u_ibex_core.if_stage_i.dummy_instr_id_o);
assign lumen_official_bus_o[800+:32] = 32'(u_top.u_ibex_top.u_ibex_core.wb_stage_i.dummy_instr_wb_o);
assign lumen_official_bus_o[832+:32] = 32'(u_top.u_ibex_top.u_ibex_core.fcov_rf_ecc_err_a_id);
assign lumen_official_bus_o[864+:32] = 32'(u_top.u_ibex_top.u_ibex_core.fcov_rf_ecc_err_b_id);
assign lumen_official_bus_o[896+:32] = 32'(u_top.u_ibex_top.u_ibex_core.if_stage_i.icache_ecc_error_o);
assign lumen_official_bus_o[928+:32] = 32'(u_top.u_ibex_top.u_ibex_core.load_store_unit_i.load_resp_intg_err_o);
assign lumen_official_bus_o[960+:32] = 32'(u_top.u_ibex_top.u_ibex_core.load_store_unit_i.store_resp_intg_err_o);
assign lumen_official_bus_o[992+:32] = 32'(lockstep_glitch_err);
assign lumen_official_bus_o[1024+:32] = 32'(rf_glitch_err);
assign lumen_official_bus_o[1056+:32] = 32'(u_top.u_ibex_top.u_ibex_core.if_stage_i.pc_mismatch_alert_o);
assign lumen_official_bus_o[1088+:32] = 32'(u_top.u_ibex_top.u_ibex_core.fetch_enable_i);
assign lumen_official_bus_o[1120+:32] = 32'(u_top.u_ibex_top.u_ibex_core.id_stage_i.mret_insn_dec && u_top.u_ibex_top.u_ibex_core.priv_mode_id == PRIV_LVL_U);
assign lumen_official_bus_o[1152+:32] = 32'(u_top.u_ibex_top.u_ibex_core.id_stage_i.wfi_insn_dec && u_top.u_ibex_top.u_ibex_core.priv_mode_id == PRIV_LVL_U);
assign lumen_official_bus_o[1184+:32] = 32'(u_top.u_ibex_top.u_ibex_core.fcov_csr_write &&
                       (u_top.u_ibex_top.u_ibex_core.cs_registers_i.u_mstatus_csr.wr_data_i !=
                       u_top.u_ibex_top.u_ibex_core.cs_registers_i.csr_wdata_int));
assign lumen_official_bus_o[1216+:32] = 32'(u_top.u_ibex_top.u_ibex_core.fcov_csr_write &&
                       (u_top.u_ibex_top.u_ibex_core.cs_registers_i.u_mie_csr.wr_data_i !=
                       u_top.u_ibex_top.u_ibex_core.cs_registers_i.csr_wdata_int));
assign lumen_official_bus_o[1248+:32] = 32'(u_top.u_ibex_top.u_ibex_core.fcov_csr_write &&
                       (u_top.u_ibex_top.u_ibex_core.cs_registers_i.u_mtvec_csr.wr_data_i !=
                       u_top.u_ibex_top.u_ibex_core.cs_registers_i.csr_wdata_int));
assign lumen_official_bus_o[1280+:32] = 32'(u_top.u_ibex_top.u_ibex_core.fcov_csr_write &&
                       (u_top.u_ibex_top.u_ibex_core.cs_registers_i.u_mepc_csr.wr_data_i !=
                       u_top.u_ibex_top.u_ibex_core.cs_registers_i.csr_wdata_int));
assign lumen_official_bus_o[1312+:32] = 32'(u_top.u_ibex_top.u_ibex_core.fcov_csr_write &&
                       (u_top.u_ibex_top.u_ibex_core.cs_registers_i.u_mtval_csr.wr_data_i !=
                       u_top.u_ibex_top.u_ibex_core.cs_registers_i.csr_wdata_int));
assign lumen_official_bus_o[1344+:32] = 32'(u_top.u_ibex_top.u_ibex_core.fcov_csr_write &&
                       (u_top.u_ibex_top.u_ibex_core.cs_registers_i.u_dcsr_csr.wr_data_i !=
                       u_top.u_ibex_top.u_ibex_core.cs_registers_i.csr_wdata_int));
assign lumen_official_bus_o[1376+:32] = 32'(u_top.u_ibex_top.u_ibex_core.fcov_csr_write &&
                       (u_top.u_ibex_top.u_ibex_core.cs_registers_i.u_cpuctrlsts_part_csr.wr_data_i !=
                       u_top.u_ibex_top.u_ibex_core.cs_registers_i.csr_wdata_int));
assign lumen_official_bus_o[1408+:32] = 32'(u_top.u_ibex_top.u_ibex_core.cs_registers_i.cpuctrlsts_part_d.double_fault_seen);
assign lumen_official_bus_o[1440+:32] = 32'(u_top.u_ibex_top.u_ibex_core.cs_registers_i.cpuctrlsts_part_d.icache_enable);
assign lumen_official_bus_o[1472+:32] = 32'(u_top.u_ibex_top.u_ibex_core.id_stage_i.irq_pending_i | u_top.u_ibex_top.u_ibex_core.id_stage_i.irq_nm_i);
assign lumen_official_bus_o[1504+:32] = 32'(u_top.u_ibex_top.u_ibex_core.id_stage_i.controller_i.fcov_debug_req);
assign lumen_official_bus_o[1536+:32] = 32'(u_top.u_ibex_top.u_ibex_core.cs_registers_i.csr_addr_i);
assign lumen_official_bus_o[1568+:32] = 32'(u_top.u_ibex_top.u_ibex_core.fcov_csr_read_only);
assign lumen_official_bus_o[1600+:32] = 32'(u_top.u_ibex_top.u_ibex_core.cs_registers_i.csr_addr_i);
assign lumen_official_bus_o[1632+:32] = 32'(u_top.u_ibex_top.u_ibex_core.fcov_csr_write);
assign lumen_official_bus_o[1664+:32] = 32'(u_top.u_ibex_top.u_ibex_core.fcov_csr_read_only && u_top.u_ibex_top.u_ibex_core.cs_registers_i.illegal_csr);
assign lumen_official_bus_o[1696+:32] = 32'(u_top.u_ibex_top.u_ibex_core.fcov_csr_write && u_top.u_ibex_top.u_ibex_core.cs_registers_i.illegal_csr);
assign lumen_official_bus_o[1728+:32] = 32'(u_top.u_ibex_top.u_ibex_core.debug_mode);
assign lumen_official_bus_o[1760+:32] = 32'(u_top.u_ibex_top.u_ibex_core.id_stage_i.controller_i.fcov_debug_wakeup);
assign lumen_official_bus_o[1792+:32] = 32'(u_top.u_ibex_top.u_ibex_core.id_stage_i.controller_i.fcov_all_debug_req);
assign lumen_official_bus_o[1824+:32] = 32'(u_top.u_ibex_top.u_ibex_core.id_stage_i.controller_i.fcov_debug_entry_if);
assign lumen_official_bus_o[1856+:32] = 32'(u_top.u_ibex_top.u_ibex_core.id_stage_i.controller_i.fcov_debug_entry_id);
assign lumen_official_bus_o[1888+:32] = 32'(u_top.u_ibex_top.u_ibex_core.id_stage_i.controller_i.fcov_pipe_flush);
assign lumen_official_bus_o[1920+:32] = 32'(u_top.u_ibex_top.u_ibex_core.id_stage_i.controller_i.fcov_debug_single_step_taken);
assign lumen_official_bus_o[1952+:32] = 32'(u_top.u_ibex_top.u_ibex_core.id_stage_i.controller_i.do_single_step_d &&
                                              u_top.u_ibex_top.u_ibex_core.id_stage_i.controller_i.fcov_pipe_flush);
assign lumen_official_bus_o[1984+:32] = 32'(instr_id_matches_trigger_q);
assign lumen_official_bus_o[2016+:32] = 32'(((fcov_irqs[5] || fcov_irqs[4])));
assign lumen_official_bus_o[2048+:32] = 32'(u_top.u_ibex_top.u_ibex_core.id_stage_i.controller_i.fcov_interrupt_taken);
assign lumen_official_bus_o[2080+:32] = 32'(fcov_irqs);
assign lumen_official_bus_o[2112+:32] = 32'(u_top.u_ibex_top.u_ibex_core.id_stage_i.controller_i.fcov_interrupt_taken);
assign lumen_official_bus_o[2144+:32] = 32'(u_top.u_ibex_top.u_ibex_core.id_stage_i.controller_i.ctrl_fsm_cs);
assign lumen_official_bus_o[2176+:32] = 32'(u_top.u_ibex_top.u_ibex_core.id_stage_i.controller_i.ctrl_fsm_cs);
assign lumen_official_bus_o[2208+:32] = 32'(kept_wfi_with_irq);
assign lumen_official_bus_o[2240+:32] = 32'(id_instr_category);
assign lumen_official_bus_o[2272+:32] = 32'(u_top.u_ibex_top.u_ibex_core.id_stage_i.controller_i.fcov_debug_single_step_taken);
assign lumen_official_bus_o[2304+:32] = 32'(u_top.u_ibex_top.u_ibex_core.load_store_unit_i.fcov_mis_bus_err_1_q);
assign lumen_official_bus_o[2336+:32] = 32'(u_top.u_ibex_top.u_ibex_core.load_store_unit_i.fcov_mis_rvalid_2);
assign lumen_official_bus_o[2368+:32] = 32'(u_top.u_ibex_top.u_ibex_core.load_store_unit_i.data_bus_err_i);
assign lumen_official_bus_o[2400+:32] = 32'(u_top.u_ibex_top.u_ibex_core.load_store_unit_i.fcov_mis_rvalid_2);
assign lumen_official_bus_o[2432+:32] = 32'(imem_single_cycle_response);
assign lumen_official_bus_o[2464+:32] = 32'(instr_rvalid_i);
assign lumen_official_bus_o[2496+:32] = 32'(instr_rvalid_i & instr_req_o & instr_gnt_i);
assign lumen_official_bus_o[2528+:32] = 32'(dmem_single_cycle_response);
assign lumen_official_bus_o[2560+:32] = 32'(data_rvalid_i);
assign lumen_official_bus_o[2592+:32] = 32'(data_rvalid_i & data_req_o & data_gnt_i);
assign lumen_official_bus_o[2624+:32] = 32'(u_top.u_ibex_top.u_ibex_core.id_stage_i.instr_fetch_err_i);
assign lumen_official_bus_o[2656+:32] = 32'(u_top.u_ibex_top.u_ibex_core.id_stage_i.instr_fetch_err_plus2_i);
assign lumen_official_bus_o[2688+:32] = 32'(u_top.u_ibex_top.u_ibex_core.cs_registers_i.mstatus_q.mie);
assign lumen_official_bus_o[2720+:32] = 32'(u_top.u_ibex_top.u_ibex_core.id_stage_i.irq_pending_i | u_top.u_ibex_top.u_ibex_core.id_stage_i.irq_nm_i);
assign lumen_official_bus_o[2752+:32] = 32'(u_top.u_ibex_top.u_ibex_core.id_stage_i.controller_i.fcov_all_debug_req);
assign lumen_official_bus_o[2784+:32] = 32'(wb_stage_state);
assign lumen_official_bus_o[2816+:32] = 32'(instr_unstalled_last);
assign lumen_official_bus_o[2848+:32] = 32'(u_top.u_ibex_top.u_ibex_core.id_stage_i.controller_i.fcov_interrupt_taken);
assign lumen_official_bus_o[2880+:32] = 32'(instr_unstalled);
assign lumen_official_bus_o[2912+:32] = 32'(u_top.u_ibex_top.u_ibex_core.cs_registers_i.dummy_instr_en_o);
assign lumen_official_bus_o[2944+:32] = 32'(u_top.u_ibex_top.u_ibex_core.fcov_rf_ecc_err_a_id);
assign lumen_official_bus_o[2976+:32] = 32'(u_top.u_ibex_top.u_ibex_core.fcov_rf_ecc_err_b_id);
assign lumen_official_bus_o[3008+:32] = 32'(u_top.u_ibex_top.u_ibex_core.id_stage_i.instr_valid_i);
end
if (PMPEnable) begin : g_official_pmp
localparam logic [31:0] DmBaseAddr = 32'h1A110000;
localparam logic [31:0] DmAddrMask = 32'h00000FFF;
  localparam int unsigned PMPNumChan = 3;

  `include "dv_fcov_macros.svh"

                                                                                                   
                                                                                                  
           
  typedef enum logic [4:0] {
    NONE        = 5'b00000,
    R           = 5'b00001,
    W           = 5'b00010,
    WR          = 5'b00011,
    X           = 5'b00100,
    XR          = 5'b00101,
    XW          = 5'b00110,
    XWR         = 5'b00111,
    L           = 5'b01000,
    LR          = 5'b01001,
    LW          = 5'b01010,
    LWR         = 5'b01011,
    LX          = 5'b01100,
    LXR         = 5'b01101,
    LXW         = 5'b01110,
    LXWR        = 5'b01111,
    MML_NONE    = 5'b10000,
    MML_RU      = 5'b10001,
    MML_WRM_RU  = 5'b10010,
    MML_WRU     = 5'b10011,
    MML_XU      = 5'b10100,
    MML_XRU     = 5'b10101,
    MML_WRM_WRU = 5'b10110,
    MML_XWRU    = 5'b10111,
    MML_L       = 5'b11000,
    MML_RM      = 5'b11001,
    MML_XM_XU   = 5'b11010,
    MML_WRM     = 5'b11011,
    MML_XM      = 5'b11100,
    MML_XRM     = 5'b11101,
    MML_XRM_XU  = 5'b11110,
    MML_RM_RU   = 5'b11111
  } pmp_priv_bits_e;

                                                                                                 
                                                          
  logic pmp_iside_req_err;
  logic pmp_iside2_req_err;
  logic pmp_dside_req_err;

  assign pmp_iside_req_err  = u_top.u_ibex_top.u_ibex_core.pmp_req_err[PMP_I];
  assign pmp_iside2_req_err = u_top.u_ibex_top.u_ibex_core.pmp_req_err[PMP_I2];
  assign pmp_dside_req_err  = u_top.u_ibex_top.u_ibex_core.pmp_req_err[PMP_D];

  logic [PMPNumRegions-1:0] current_priv_perm_check;
  bit en_pmp_fcov;

  logic csr_wdata_mseccfg_rlb;
  logic csr_wdata_mseccfg_mmwp;
  logic csr_wdata_mseccfg_mml;

  assign csr_wdata_mseccfg_rlb = u_top.u_ibex_top.u_ibex_core.cs_registers_i.csr_wdata_int[CSR_MSECCFG_RLB_BIT];
  assign csr_wdata_mseccfg_mmwp = u_top.u_ibex_top.u_ibex_core.cs_registers_i.csr_wdata_int[CSR_MSECCFG_MMWP_BIT];
  assign csr_wdata_mseccfg_mml = u_top.u_ibex_top.u_ibex_core.cs_registers_i.csr_wdata_int[CSR_MSECCFG_MML_BIT];

  initial begin
    if (PMPEnable) begin
      void'($value$plusargs("enable_ibex_fcov=%d", en_pmp_fcov));
    end else begin
      en_pmp_fcov = 1'b0;
    end
  end

  if (PMPEnable) begin : g_pmp_cgs
    logic [PMPNumChan-1:0] fcov_access_attempted_into_dm;

    logic [PMPNumRegions-1:0] pmp_iside_match;
    logic [PMPNumRegions-1:0] pmp_iside2_match;
    logic [PMPNumRegions-1:0] pmp_dside_match;
    logic [PMPNumRegions-1:0] pmp_dside_match_last;

    logic pmp_iside_nomatch;
    logic pmp_iside2_nomatch;
    logic pmp_dside_nomatch;

    logic pmp_iside_boundary_cross;
    logic pmp_dside_boundary_cross;

    logic misaligned_pmp_err_last;

    logic [31:0] pmp_addr_napot_valid [PMPNumRegions];

    assign pmp_iside_match      = u_top.u_ibex_top.u_ibex_core.g_pmp.pmp_i.region_match_all[PMP_I];
    assign pmp_iside2_match     = u_top.u_ibex_top.u_ibex_core.g_pmp.pmp_i.region_match_all[PMP_I2];
    assign pmp_dside_match      = u_top.u_ibex_top.u_ibex_core.g_pmp.pmp_i.region_match_all[PMP_D];

    assign pmp_iside_nomatch  = ~|pmp_iside_match;
    assign pmp_iside2_nomatch = ~|pmp_iside2_match;
    assign pmp_dside_nomatch  = ~|pmp_dside_match;

                                                                                               
    always @(posedge lumen_core_clock or negedge rst_ni) begin
      if (!rst_ni) begin
        pmp_dside_match_last    <= '0;
        misaligned_pmp_err_last <= 1'b0;
      end else if (u_top.u_ibex_top.u_ibex_core.load_store_unit_i.fcov_ls_first_req) begin
        pmp_dside_match_last    <= pmp_dside_match;
        misaligned_pmp_err_last <= u_top.u_ibex_top.u_ibex_core.load_store_unit_i.data_pmp_err_i;
      end
    end

    assign pmp_iside_boundary_cross = |(pmp_iside_match ^ pmp_iside2_match);
    assign pmp_dside_boundary_cross = |(pmp_dside_match ^ pmp_dside_match_last) &
                                      u_top.u_ibex_top.u_ibex_core.load_store_unit_i.fcov_ls_second_req;

    logic pmp_iside_access_fault_check;
    logic pmp_iside2_access_fault_check;
    logic pmp_dside_access_fault_check;

    assign pmp_iside_access_fault_check  = u_top.u_ibex_top.u_ibex_core.g_pmp.pmp_i.pmp_req_err_o[PMP_I];
    assign pmp_iside2_access_fault_check = u_top.u_ibex_top.u_ibex_core.g_pmp.pmp_i.pmp_req_err_o[PMP_I2];
    assign pmp_dside_access_fault_check  = u_top.u_ibex_top.u_ibex_core.g_pmp.pmp_i.pmp_req_err_o[PMP_D];

    for (genvar i_region = 0; i_region < PMPNumRegions; i_region += 1) begin : g_pmp_region_fcov
      pmp_priv_bits_e pmp_region_priv_bits;
      pmp_priv_bits_e pmp_region_priv_bits_wr;

      assign pmp_region_priv_bits = pmp_priv_bits_e'({u_top.u_ibex_top.u_ibex_core.csr_pmp_mseccfg.mml,
                                                      u_top.u_ibex_top.u_ibex_core.csr_pmp_cfg[i_region].lock,
                                                      u_top.u_ibex_top.u_ibex_core.csr_pmp_cfg[i_region].exec,
                                                      u_top.u_ibex_top.u_ibex_core.csr_pmp_cfg[i_region].write,
                                                      u_top.u_ibex_top.u_ibex_core.csr_pmp_cfg[i_region].read});
      assign pmp_region_priv_bits_wr =
          pmp_priv_bits_e'({u_top.u_ibex_top.u_ibex_core.csr_pmp_mseccfg.mml,
                            u_top.u_ibex_top.u_ibex_core.cs_registers_i.g_pmp_registers.pmp_cfg_wdata[i_region].lock,
                            u_top.u_ibex_top.u_ibex_core.cs_registers_i.g_pmp_registers.pmp_cfg_wdata[i_region].exec,
                            u_top.u_ibex_top.u_ibex_core.cs_registers_i.g_pmp_registers.pmp_cfg_wdata[i_region].write,
                            u_top.u_ibex_top.u_ibex_core.cs_registers_i.g_pmp_registers.pmp_cfg_wdata[i_region].read});

                                                                                                     
                                                                                                   
                    
      assign current_priv_perm_check[i_region] =
        u_top.u_ibex_top.u_ibex_core.g_pmp.pmp_i.perm_check_wrapper(u_top.u_ibex_top.u_ibex_core.csr_pmp_mseccfg.mml,
                                       u_top.u_ibex_top.u_ibex_core.csr_pmp_cfg[i_region],
                                       u_top.u_ibex_top.u_ibex_core.g_pmp.pmp_i.pmp_req_type_i[PMP_D],
                                       u_top.u_ibex_top.u_ibex_core.cs_registers_i.priv_mode_id_o,
                                       u_top.u_ibex_top.u_ibex_core.g_pmp.pmp_i.region_basic_perm_check[PMP_D][i_region]);

                                                                                                   
                                                                                                
                                                                                          
                                                                                             
      for (genvar i = 0; i < 32; i += 1) begin : g_pmp_napot_region_fcov
        assign pmp_addr_napot_valid[i_region][i] = u_top.u_ibex_top.u_ibex_core.csr_pmp_cfg[i_region].mode == PMP_MODE_NAPOT &&
          (u_top.u_ibex_top.u_ibex_core.csr_pmp_addr[i_region][i+2:2] == {1'b0, {i{1'b1}}});
      end

      if (i_region == 0) begin
assign lumen_official_bus_o[3040+:32] = 32'($clog2(pmp_addr_napot_valid[i_region]));
assign lumen_official_bus_o[3072+:32] = 32'($onehot(pmp_addr_napot_valid[i_region]));
assign lumen_official_bus_o[3104+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp_fcov_signals.g_pmp_region_fcov[i_region].fcov_warl_check_pmpcfg);
assign lumen_official_bus_o[3136+:32] = 32'(u_top.u_ibex_top.u_ibex_core.csr_pmp_cfg[i_region].mode);
assign lumen_official_bus_o[3168+:32] = 32'(pmp_region_priv_bits);
assign lumen_official_bus_o[3200+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp.pmp_priv_lvl[PMP_I]);
assign lumen_official_bus_o[3232+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp.pmp_req_type[PMP_I]);
assign lumen_official_bus_o[3264+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp.pmp_priv_lvl[PMP_I2]);
assign lumen_official_bus_o[3296+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp.pmp_req_type[PMP_I2]);
assign lumen_official_bus_o[3328+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp.pmp_priv_lvl[PMP_D]);
assign lumen_official_bus_o[3360+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp.pmp_req_type[PMP_D]);
assign lumen_official_bus_o[3392+:32] = 32'(u_top.u_ibex_top.u_ibex_core.fcov_csr_write &&
          u_top.u_ibex_top.u_ibex_core.csr_pmp_cfg[i_region].lock &&
          u_top.u_ibex_top.u_ibex_core.cs_registers_i.g_pmp_registers.g_pmp_csrs[i_region].u_pmp_cfg_csr.wr_en_i &&
          u_top.u_ibex_top.u_ibex_core.csr_pmp_mseccfg.rlb);
assign lumen_official_bus_o[3424+:32] = 32'(u_top.u_ibex_top.u_ibex_core.fcov_csr_write &&
          u_top.u_ibex_top.u_ibex_core.csr_pmp_cfg[i_region].lock &&
          u_top.u_ibex_top.u_ibex_core.cs_registers_i.g_pmp_registers.g_pmp_csrs[i_region].u_pmp_addr_csr.wr_en_i &&
          u_top.u_ibex_top.u_ibex_core.csr_pmp_mseccfg.rlb);
assign lumen_official_bus_o[3456+:32] = 32'(pmp_iside_req_err);
assign lumen_official_bus_o[3488+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp_fcov_signals.g_pmp_region_fcov[i_region].fcov_pmp_region_ichan_access);
assign lumen_official_bus_o[3520+:32] = 32'(pmp_iside2_req_err);
assign lumen_official_bus_o[3552+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp_fcov_signals.g_pmp_region_fcov[i_region].fcov_pmp_region_ichan2_access);
assign lumen_official_bus_o[3584+:32] = 32'(pmp_dside_req_err);
assign lumen_official_bus_o[3616+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp_fcov_signals.g_pmp_region_fcov[i_region].fcov_pmp_region_dchan_access);
assign lumen_official_bus_o[3648+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp_fcov_signals.g_pmp_region_fcov[i_region].fcov_pmp_region_ichan_access &&
                 u_top.u_ibex_top.u_ibex_core.g_pmp_fcov_signals.fcov_pmp_region_ichan_priority[i_region]                 &&
                 u_top.u_ibex_top.u_ibex_core.csr_pmp_cfg[i_region].mode != PMP_MODE_OFF                                  &&
                 !(fcov_access_attempted_into_dm[PMP_I]));
assign lumen_official_bus_o[3680+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp_fcov_signals.g_pmp_region_fcov[i_region].fcov_pmp_region_ichan2_access &&
                 u_top.u_ibex_top.u_ibex_core.g_pmp_fcov_signals.fcov_pmp_region_ichan2_priority[i_region]                 &&
                 u_top.u_ibex_top.u_ibex_core.csr_pmp_cfg[i_region].mode != PMP_MODE_OFF                                   &&
                   !(fcov_access_attempted_into_dm[PMP_I2]));
assign lumen_official_bus_o[3712+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp_fcov_signals.g_pmp_region_fcov[i_region].fcov_pmp_region_dchan_access &&
                 u_top.u_ibex_top.u_ibex_core.g_pmp_fcov_signals.fcov_pmp_region_dchan_priority[i_region]                 &&
                 u_top.u_ibex_top.u_ibex_core.csr_pmp_cfg[i_region].mode != PMP_MODE_OFF                                  &&
                 !(fcov_access_attempted_into_dm[PMP_D]));
assign lumen_official_bus_o[3744+:32] = 32'(pmp_region_priv_bits);
assign lumen_official_bus_o[3776+:32] = 32'(pmp_region_priv_bits_wr);
assign lumen_official_bus_o[3808+:32] = 32'(u_top.u_ibex_top.u_ibex_core.csr_pmp_mseccfg.rlb);
assign lumen_official_bus_o[3840+:32] = 32'(u_top.u_ibex_top.u_ibex_core.fcov_csr_write &&
             u_top.u_ibex_top.u_ibex_core.csr_pmp_mseccfg.mml &&
             u_top.u_ibex_top.u_ibex_core.cs_registers_i.csr_we_int &&
             u_top.u_ibex_top.u_ibex_core.cs_registers_i.csr_addr == (CSR_OFF_PMP_CFG + (i_region[11:0] >> 2)) &&
             ((!pmp_region_priv_bits[2] && pmp_region_priv_bits != MML_XM_XU) ||
              pmp_region_priv_bits inside {MML_WRM_WRU, MML_RM_RU}));
end
if (i_region == 1) begin
assign lumen_official_bus_o[3872+:32] = 32'($clog2(pmp_addr_napot_valid[i_region]));
assign lumen_official_bus_o[3904+:32] = 32'($onehot(pmp_addr_napot_valid[i_region]));
assign lumen_official_bus_o[3936+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp_fcov_signals.g_pmp_region_fcov[i_region].fcov_warl_check_pmpcfg);
assign lumen_official_bus_o[3968+:32] = 32'(u_top.u_ibex_top.u_ibex_core.csr_pmp_cfg[i_region].mode);
assign lumen_official_bus_o[4000+:32] = 32'(pmp_region_priv_bits);
assign lumen_official_bus_o[4032+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp.pmp_priv_lvl[PMP_I]);
assign lumen_official_bus_o[4064+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp.pmp_req_type[PMP_I]);
assign lumen_official_bus_o[4096+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp.pmp_priv_lvl[PMP_I2]);
assign lumen_official_bus_o[4128+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp.pmp_req_type[PMP_I2]);
assign lumen_official_bus_o[4160+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp.pmp_priv_lvl[PMP_D]);
assign lumen_official_bus_o[4192+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp.pmp_req_type[PMP_D]);
assign lumen_official_bus_o[4224+:32] = 32'(u_top.u_ibex_top.u_ibex_core.fcov_csr_write &&
          u_top.u_ibex_top.u_ibex_core.csr_pmp_cfg[i_region].lock &&
          u_top.u_ibex_top.u_ibex_core.cs_registers_i.g_pmp_registers.g_pmp_csrs[i_region].u_pmp_cfg_csr.wr_en_i &&
          u_top.u_ibex_top.u_ibex_core.csr_pmp_mseccfg.rlb);
assign lumen_official_bus_o[4256+:32] = 32'(u_top.u_ibex_top.u_ibex_core.fcov_csr_write &&
          u_top.u_ibex_top.u_ibex_core.csr_pmp_cfg[i_region].lock &&
          u_top.u_ibex_top.u_ibex_core.cs_registers_i.g_pmp_registers.g_pmp_csrs[i_region].u_pmp_addr_csr.wr_en_i &&
          u_top.u_ibex_top.u_ibex_core.csr_pmp_mseccfg.rlb);
assign lumen_official_bus_o[4288+:32] = 32'(pmp_iside_req_err);
assign lumen_official_bus_o[4320+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp_fcov_signals.g_pmp_region_fcov[i_region].fcov_pmp_region_ichan_access);
assign lumen_official_bus_o[4352+:32] = 32'(pmp_iside2_req_err);
assign lumen_official_bus_o[4384+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp_fcov_signals.g_pmp_region_fcov[i_region].fcov_pmp_region_ichan2_access);
assign lumen_official_bus_o[4416+:32] = 32'(pmp_dside_req_err);
assign lumen_official_bus_o[4448+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp_fcov_signals.g_pmp_region_fcov[i_region].fcov_pmp_region_dchan_access);
assign lumen_official_bus_o[4480+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp_fcov_signals.g_pmp_region_fcov[i_region].fcov_pmp_region_ichan_access &&
                 u_top.u_ibex_top.u_ibex_core.g_pmp_fcov_signals.fcov_pmp_region_ichan_priority[i_region]                 &&
                 u_top.u_ibex_top.u_ibex_core.csr_pmp_cfg[i_region].mode != PMP_MODE_OFF                                  &&
                 !(fcov_access_attempted_into_dm[PMP_I]));
assign lumen_official_bus_o[4512+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp_fcov_signals.g_pmp_region_fcov[i_region].fcov_pmp_region_ichan2_access &&
                 u_top.u_ibex_top.u_ibex_core.g_pmp_fcov_signals.fcov_pmp_region_ichan2_priority[i_region]                 &&
                 u_top.u_ibex_top.u_ibex_core.csr_pmp_cfg[i_region].mode != PMP_MODE_OFF                                   &&
                   !(fcov_access_attempted_into_dm[PMP_I2]));
assign lumen_official_bus_o[4544+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp_fcov_signals.g_pmp_region_fcov[i_region].fcov_pmp_region_dchan_access &&
                 u_top.u_ibex_top.u_ibex_core.g_pmp_fcov_signals.fcov_pmp_region_dchan_priority[i_region]                 &&
                 u_top.u_ibex_top.u_ibex_core.csr_pmp_cfg[i_region].mode != PMP_MODE_OFF                                  &&
                 !(fcov_access_attempted_into_dm[PMP_D]));
assign lumen_official_bus_o[4576+:32] = 32'(pmp_region_priv_bits);
assign lumen_official_bus_o[4608+:32] = 32'(pmp_region_priv_bits_wr);
assign lumen_official_bus_o[4640+:32] = 32'(u_top.u_ibex_top.u_ibex_core.csr_pmp_mseccfg.rlb);
assign lumen_official_bus_o[4672+:32] = 32'(u_top.u_ibex_top.u_ibex_core.fcov_csr_write &&
             u_top.u_ibex_top.u_ibex_core.csr_pmp_mseccfg.mml &&
             u_top.u_ibex_top.u_ibex_core.cs_registers_i.csr_we_int &&
             u_top.u_ibex_top.u_ibex_core.cs_registers_i.csr_addr == (CSR_OFF_PMP_CFG + (i_region[11:0] >> 2)) &&
             ((!pmp_region_priv_bits[2] && pmp_region_priv_bits != MML_XM_XU) ||
              pmp_region_priv_bits inside {MML_WRM_WRU, MML_RM_RU}));
end
if (i_region == 2) begin
assign lumen_official_bus_o[4704+:32] = 32'($clog2(pmp_addr_napot_valid[i_region]));
assign lumen_official_bus_o[4736+:32] = 32'($onehot(pmp_addr_napot_valid[i_region]));
assign lumen_official_bus_o[4768+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp_fcov_signals.g_pmp_region_fcov[i_region].fcov_warl_check_pmpcfg);
assign lumen_official_bus_o[4800+:32] = 32'(u_top.u_ibex_top.u_ibex_core.csr_pmp_cfg[i_region].mode);
assign lumen_official_bus_o[4832+:32] = 32'(pmp_region_priv_bits);
assign lumen_official_bus_o[4864+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp.pmp_priv_lvl[PMP_I]);
assign lumen_official_bus_o[4896+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp.pmp_req_type[PMP_I]);
assign lumen_official_bus_o[4928+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp.pmp_priv_lvl[PMP_I2]);
assign lumen_official_bus_o[4960+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp.pmp_req_type[PMP_I2]);
assign lumen_official_bus_o[4992+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp.pmp_priv_lvl[PMP_D]);
assign lumen_official_bus_o[5024+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp.pmp_req_type[PMP_D]);
assign lumen_official_bus_o[5056+:32] = 32'(u_top.u_ibex_top.u_ibex_core.fcov_csr_write &&
          u_top.u_ibex_top.u_ibex_core.csr_pmp_cfg[i_region].lock &&
          u_top.u_ibex_top.u_ibex_core.cs_registers_i.g_pmp_registers.g_pmp_csrs[i_region].u_pmp_cfg_csr.wr_en_i &&
          u_top.u_ibex_top.u_ibex_core.csr_pmp_mseccfg.rlb);
assign lumen_official_bus_o[5088+:32] = 32'(u_top.u_ibex_top.u_ibex_core.fcov_csr_write &&
          u_top.u_ibex_top.u_ibex_core.csr_pmp_cfg[i_region].lock &&
          u_top.u_ibex_top.u_ibex_core.cs_registers_i.g_pmp_registers.g_pmp_csrs[i_region].u_pmp_addr_csr.wr_en_i &&
          u_top.u_ibex_top.u_ibex_core.csr_pmp_mseccfg.rlb);
assign lumen_official_bus_o[5120+:32] = 32'(pmp_iside_req_err);
assign lumen_official_bus_o[5152+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp_fcov_signals.g_pmp_region_fcov[i_region].fcov_pmp_region_ichan_access);
assign lumen_official_bus_o[5184+:32] = 32'(pmp_iside2_req_err);
assign lumen_official_bus_o[5216+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp_fcov_signals.g_pmp_region_fcov[i_region].fcov_pmp_region_ichan2_access);
assign lumen_official_bus_o[5248+:32] = 32'(pmp_dside_req_err);
assign lumen_official_bus_o[5280+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp_fcov_signals.g_pmp_region_fcov[i_region].fcov_pmp_region_dchan_access);
assign lumen_official_bus_o[5312+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp_fcov_signals.g_pmp_region_fcov[i_region].fcov_pmp_region_ichan_access &&
                 u_top.u_ibex_top.u_ibex_core.g_pmp_fcov_signals.fcov_pmp_region_ichan_priority[i_region]                 &&
                 u_top.u_ibex_top.u_ibex_core.csr_pmp_cfg[i_region].mode != PMP_MODE_OFF                                  &&
                 !(fcov_access_attempted_into_dm[PMP_I]));
assign lumen_official_bus_o[5344+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp_fcov_signals.g_pmp_region_fcov[i_region].fcov_pmp_region_ichan2_access &&
                 u_top.u_ibex_top.u_ibex_core.g_pmp_fcov_signals.fcov_pmp_region_ichan2_priority[i_region]                 &&
                 u_top.u_ibex_top.u_ibex_core.csr_pmp_cfg[i_region].mode != PMP_MODE_OFF                                   &&
                   !(fcov_access_attempted_into_dm[PMP_I2]));
assign lumen_official_bus_o[5376+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp_fcov_signals.g_pmp_region_fcov[i_region].fcov_pmp_region_dchan_access &&
                 u_top.u_ibex_top.u_ibex_core.g_pmp_fcov_signals.fcov_pmp_region_dchan_priority[i_region]                 &&
                 u_top.u_ibex_top.u_ibex_core.csr_pmp_cfg[i_region].mode != PMP_MODE_OFF                                  &&
                 !(fcov_access_attempted_into_dm[PMP_D]));
assign lumen_official_bus_o[5408+:32] = 32'(pmp_region_priv_bits);
assign lumen_official_bus_o[5440+:32] = 32'(pmp_region_priv_bits_wr);
assign lumen_official_bus_o[5472+:32] = 32'(u_top.u_ibex_top.u_ibex_core.csr_pmp_mseccfg.rlb);
assign lumen_official_bus_o[5504+:32] = 32'(u_top.u_ibex_top.u_ibex_core.fcov_csr_write &&
             u_top.u_ibex_top.u_ibex_core.csr_pmp_mseccfg.mml &&
             u_top.u_ibex_top.u_ibex_core.cs_registers_i.csr_we_int &&
             u_top.u_ibex_top.u_ibex_core.cs_registers_i.csr_addr == (CSR_OFF_PMP_CFG + (i_region[11:0] >> 2)) &&
             ((!pmp_region_priv_bits[2] && pmp_region_priv_bits != MML_XM_XU) ||
              pmp_region_priv_bits inside {MML_WRM_WRU, MML_RM_RU}));
end
if (i_region == 3) begin
assign lumen_official_bus_o[5536+:32] = 32'($clog2(pmp_addr_napot_valid[i_region]));
assign lumen_official_bus_o[5568+:32] = 32'($onehot(pmp_addr_napot_valid[i_region]));
assign lumen_official_bus_o[5600+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp_fcov_signals.g_pmp_region_fcov[i_region].fcov_warl_check_pmpcfg);
assign lumen_official_bus_o[5632+:32] = 32'(u_top.u_ibex_top.u_ibex_core.csr_pmp_cfg[i_region].mode);
assign lumen_official_bus_o[5664+:32] = 32'(pmp_region_priv_bits);
assign lumen_official_bus_o[5696+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp.pmp_priv_lvl[PMP_I]);
assign lumen_official_bus_o[5728+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp.pmp_req_type[PMP_I]);
assign lumen_official_bus_o[5760+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp.pmp_priv_lvl[PMP_I2]);
assign lumen_official_bus_o[5792+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp.pmp_req_type[PMP_I2]);
assign lumen_official_bus_o[5824+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp.pmp_priv_lvl[PMP_D]);
assign lumen_official_bus_o[5856+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp.pmp_req_type[PMP_D]);
assign lumen_official_bus_o[5888+:32] = 32'(u_top.u_ibex_top.u_ibex_core.fcov_csr_write &&
          u_top.u_ibex_top.u_ibex_core.csr_pmp_cfg[i_region].lock &&
          u_top.u_ibex_top.u_ibex_core.cs_registers_i.g_pmp_registers.g_pmp_csrs[i_region].u_pmp_cfg_csr.wr_en_i &&
          u_top.u_ibex_top.u_ibex_core.csr_pmp_mseccfg.rlb);
assign lumen_official_bus_o[5920+:32] = 32'(u_top.u_ibex_top.u_ibex_core.fcov_csr_write &&
          u_top.u_ibex_top.u_ibex_core.csr_pmp_cfg[i_region].lock &&
          u_top.u_ibex_top.u_ibex_core.cs_registers_i.g_pmp_registers.g_pmp_csrs[i_region].u_pmp_addr_csr.wr_en_i &&
          u_top.u_ibex_top.u_ibex_core.csr_pmp_mseccfg.rlb);
assign lumen_official_bus_o[5952+:32] = 32'(pmp_iside_req_err);
assign lumen_official_bus_o[5984+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp_fcov_signals.g_pmp_region_fcov[i_region].fcov_pmp_region_ichan_access);
assign lumen_official_bus_o[6016+:32] = 32'(pmp_iside2_req_err);
assign lumen_official_bus_o[6048+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp_fcov_signals.g_pmp_region_fcov[i_region].fcov_pmp_region_ichan2_access);
assign lumen_official_bus_o[6080+:32] = 32'(pmp_dside_req_err);
assign lumen_official_bus_o[6112+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp_fcov_signals.g_pmp_region_fcov[i_region].fcov_pmp_region_dchan_access);
assign lumen_official_bus_o[6144+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp_fcov_signals.g_pmp_region_fcov[i_region].fcov_pmp_region_ichan_access &&
                 u_top.u_ibex_top.u_ibex_core.g_pmp_fcov_signals.fcov_pmp_region_ichan_priority[i_region]                 &&
                 u_top.u_ibex_top.u_ibex_core.csr_pmp_cfg[i_region].mode != PMP_MODE_OFF                                  &&
                 !(fcov_access_attempted_into_dm[PMP_I]));
assign lumen_official_bus_o[6176+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp_fcov_signals.g_pmp_region_fcov[i_region].fcov_pmp_region_ichan2_access &&
                 u_top.u_ibex_top.u_ibex_core.g_pmp_fcov_signals.fcov_pmp_region_ichan2_priority[i_region]                 &&
                 u_top.u_ibex_top.u_ibex_core.csr_pmp_cfg[i_region].mode != PMP_MODE_OFF                                   &&
                   !(fcov_access_attempted_into_dm[PMP_I2]));
assign lumen_official_bus_o[6208+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp_fcov_signals.g_pmp_region_fcov[i_region].fcov_pmp_region_dchan_access &&
                 u_top.u_ibex_top.u_ibex_core.g_pmp_fcov_signals.fcov_pmp_region_dchan_priority[i_region]                 &&
                 u_top.u_ibex_top.u_ibex_core.csr_pmp_cfg[i_region].mode != PMP_MODE_OFF                                  &&
                 !(fcov_access_attempted_into_dm[PMP_D]));
assign lumen_official_bus_o[6240+:32] = 32'(pmp_region_priv_bits);
assign lumen_official_bus_o[6272+:32] = 32'(pmp_region_priv_bits_wr);
assign lumen_official_bus_o[6304+:32] = 32'(u_top.u_ibex_top.u_ibex_core.csr_pmp_mseccfg.rlb);
assign lumen_official_bus_o[6336+:32] = 32'(u_top.u_ibex_top.u_ibex_core.fcov_csr_write &&
             u_top.u_ibex_top.u_ibex_core.csr_pmp_mseccfg.mml &&
             u_top.u_ibex_top.u_ibex_core.cs_registers_i.csr_we_int &&
             u_top.u_ibex_top.u_ibex_core.cs_registers_i.csr_addr == (CSR_OFF_PMP_CFG + (i_region[11:0] >> 2)) &&
             ((!pmp_region_priv_bits[2] && pmp_region_priv_bits != MML_XM_XU) ||
              pmp_region_priv_bits inside {MML_WRM_WRU, MML_RM_RU}));
end

      
    end

                                                                                                    
                                                                                                          
                       
    logic pmp_current_priv_req_err;
    assign pmp_current_priv_req_err =
      u_top.u_ibex_top.u_ibex_core.g_pmp.pmp_i.access_fault_check(u_top.u_ibex_top.u_ibex_core.csr_pmp_mseccfg.mmwp,
                                     u_top.u_ibex_top.u_ibex_core.csr_pmp_mseccfg.mml,
                                     u_top.u_ibex_top.u_ibex_core.g_pmp.pmp_i.pmp_req_type_i[PMP_D],
                                     u_top.u_ibex_top.u_ibex_core.g_pmp.pmp_i.region_match_all[PMP_D],
                                     u_top.u_ibex_top.u_ibex_core.cs_registers_i.priv_mode_id_o,
                                     current_priv_perm_check);

                                                                                                  
                                                                                             
                                                                                              
                                                                                                
                                                                                  
    logic [PMPNumChan-1:0] access_check_into_dm;
    for (genvar c = 0; c < PMPNumChan; c++) begin : g_pmp_channel_access_check
      assign access_check_into_dm[c] = (u_top.u_ibex_top.u_ibex_core.g_pmp.pmp_req_addr[c][31:0] & ~DmAddrMask) == DmBaseAddr;
    end
    assign fcov_access_attempted_into_dm[PMP_I] =
      access_check_into_dm[PMP_D] & u_top.u_ibex_top.u_ibex_core.data_req_out;
    assign fcov_access_attempted_into_dm[PMP_I2] =
      access_check_into_dm[PMP_I2] & u_top.u_ibex_top.u_ibex_core.if_stage_i.if_id_pipe_reg_we;
    assign fcov_access_attempted_into_dm[PMP_D] =
      access_check_into_dm[PMP_I] & u_top.u_ibex_top.u_ibex_core.if_stage_i.if_id_pipe_reg_we;

    assign lumen_official_bus_o[6368+:32] = 32'(u_top.u_ibex_top.u_ibex_core.csr_pmp_mseccfg.rlb);
assign lumen_official_bus_o[6400+:32] = 32'(u_top.u_ibex_top.u_ibex_core.csr_pmp_mseccfg.mmwp);
assign lumen_official_bus_o[6432+:32] = 32'(u_top.u_ibex_top.u_ibex_core.csr_pmp_mseccfg.mml);
assign lumen_official_bus_o[6464+:32] = 32'(csr_wdata_mseccfg_rlb);
assign lumen_official_bus_o[6496+:32] = 32'(csr_wdata_mseccfg_mmwp);
assign lumen_official_bus_o[6528+:32] = 32'(csr_wdata_mseccfg_mml);
assign lumen_official_bus_o[6560+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp.pmp_priv_lvl[PMP_I]);
assign lumen_official_bus_o[6592+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp.pmp_req_type[PMP_I]);
assign lumen_official_bus_o[6624+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp.pmp_priv_lvl[PMP_I2]);
assign lumen_official_bus_o[6656+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp.pmp_req_type[PMP_I2]);
assign lumen_official_bus_o[6688+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp.pmp_priv_lvl[PMP_D]);
assign lumen_official_bus_o[6720+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp.pmp_req_type[PMP_D]);
assign lumen_official_bus_o[6752+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp.pmp_i.g_access_check[PMP_I].fcov_pmp_region_override);
assign lumen_official_bus_o[6784+:32] = 32'(u_top.u_ibex_top.u_ibex_core.if_stage_i.if_id_pipe_reg_we);
assign lumen_official_bus_o[6816+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp.pmp_i.g_access_check[PMP_I2].fcov_pmp_region_override);
assign lumen_official_bus_o[6848+:32] = 32'(u_top.u_ibex_top.u_ibex_core.if_stage_i.if_id_pipe_reg_we);
assign lumen_official_bus_o[6880+:32] = 32'(u_top.u_ibex_top.u_ibex_core.g_pmp.pmp_i.g_access_check[PMP_D].fcov_pmp_region_override);
assign lumen_official_bus_o[6912+:32] = 32'(u_top.u_ibex_top.u_ibex_core.data_req_out);
assign lumen_official_bus_o[6944+:32] = 32'(u_top.u_ibex_top.u_ibex_core.cs_registers_i.mstatus_q.mprv);
assign lumen_official_bus_o[6976+:32] = 32'(u_top.u_ibex_top.u_ibex_core.debug_mode);
assign lumen_official_bus_o[7008+:32] = 32'(fcov_access_attempted_into_dm[PMP_I]);
assign lumen_official_bus_o[7040+:32] = 32'(u_top.u_ibex_top.u_ibex_core.debug_mode);
assign lumen_official_bus_o[7072+:32] = 32'(fcov_access_attempted_into_dm[PMP_I2]);
assign lumen_official_bus_o[7104+:32] = 32'(u_top.u_ibex_top.u_ibex_core.debug_mode);
assign lumen_official_bus_o[7136+:32] = 32'(fcov_access_attempted_into_dm[PMP_D]);
assign lumen_official_bus_o[7168+:32] = 32'(u_top.u_ibex_top.u_ibex_core.load_store_unit_i.fcov_ls_pmp_exception);
assign lumen_official_bus_o[7200+:32] = 32'(u_top.u_ibex_top.u_ibex_core.fcov_csr_write && u_top.u_ibex_top.u_ibex_core.cs_registers_i.csr_addr_i == CSR_MSECCFG);
assign lumen_official_bus_o[7232+:32] = 32'(u_top.u_ibex_top.u_ibex_core.cs_registers_i.g_pmp_registers.any_pmp_entry_locked);
assign lumen_official_bus_o[7264+:32] = 32'(u_top.u_ibex_top.u_ibex_core.fcov_csr_write && u_top.u_ibex_top.u_ibex_core.cs_registers_i.csr_addr_i == CSR_MSECCFG);
assign lumen_official_bus_o[7296+:32] = 32'(u_top.u_ibex_top.u_ibex_core.fcov_csr_write && u_top.u_ibex_top.u_ibex_core.cs_registers_i.csr_addr_i == CSR_MSECCFG);
assign lumen_official_bus_o[7328+:32] = 32'(pmp_iside_req_err);
assign lumen_official_bus_o[7360+:32] = 32'(pmp_iside_nomatch);
assign lumen_official_bus_o[7392+:32] = 32'(pmp_iside2_req_err);
assign lumen_official_bus_o[7424+:32] = 32'(pmp_iside2_nomatch);
assign lumen_official_bus_o[7456+:32] = 32'(pmp_dside_req_err);
assign lumen_official_bus_o[7488+:32] = 32'(pmp_dside_nomatch);
assign lumen_official_bus_o[7520+:32] = 32'(u_top.u_ibex_top.u_ibex_core.cs_registers_i.mstatus_q.mpp);
assign lumen_official_bus_o[7552+:32] = 32'(u_top.u_ibex_top.u_ibex_core.cs_registers_i.priv_mode_id_o);
assign lumen_official_bus_o[7584+:32] = 32'(pmp_current_priv_req_err);
assign lumen_official_bus_o[7616+:32] = 32'(u_top.u_ibex_top.u_ibex_core.id_stage_i.instr_rdata_i[6:0] inside
                                    {ibex_pkg::OPCODE_LOAD, ibex_pkg::OPCODE_STORE} &&
                                  u_top.u_ibex_top.u_ibex_core.cs_registers_i.mstatus_q.mprv);
assign lumen_official_bus_o[7648+:32] = 32'(u_top.u_ibex_top.u_ibex_core.if_stage_i.instr_is_compressed_out);
assign lumen_official_bus_o[7680+:32] = 32'(pmp_iside_boundary_cross);
assign lumen_official_bus_o[7712+:32] = 32'(misaligned_pmp_err_last);
assign lumen_official_bus_o[7744+:32] = 32'(u_top.u_ibex_top.u_ibex_core.load_store_unit_i.fcov_ls_mis_pmp_err_2);
assign lumen_official_bus_o[7776+:32] = 32'(pmp_dside_boundary_cross);
assign lumen_official_bus_o[7808+:32] = 32'(pmp_iside_access_fault_check);
assign lumen_official_bus_o[7840+:32] = 32'(pmp_iside2_access_fault_check);
assign lumen_official_bus_o[7872+:32] = 32'(pmp_dside_access_fault_check);

    
  end


end else begin : g_official_no_pmp
assign lumen_official_bus_o[3040+:32] = '0;
assign lumen_official_bus_o[3072+:32] = '0;
assign lumen_official_bus_o[3104+:32] = '0;
assign lumen_official_bus_o[3136+:32] = '0;
assign lumen_official_bus_o[3168+:32] = '0;
assign lumen_official_bus_o[3200+:32] = '0;
assign lumen_official_bus_o[3232+:32] = '0;
assign lumen_official_bus_o[3264+:32] = '0;
assign lumen_official_bus_o[3296+:32] = '0;
assign lumen_official_bus_o[3328+:32] = '0;
assign lumen_official_bus_o[3360+:32] = '0;
assign lumen_official_bus_o[3392+:32] = '0;
assign lumen_official_bus_o[3424+:32] = '0;
assign lumen_official_bus_o[3456+:32] = '0;
assign lumen_official_bus_o[3488+:32] = '0;
assign lumen_official_bus_o[3520+:32] = '0;
assign lumen_official_bus_o[3552+:32] = '0;
assign lumen_official_bus_o[3584+:32] = '0;
assign lumen_official_bus_o[3616+:32] = '0;
assign lumen_official_bus_o[3648+:32] = '0;
assign lumen_official_bus_o[3680+:32] = '0;
assign lumen_official_bus_o[3712+:32] = '0;
assign lumen_official_bus_o[3744+:32] = '0;
assign lumen_official_bus_o[3776+:32] = '0;
assign lumen_official_bus_o[3808+:32] = '0;
assign lumen_official_bus_o[3840+:32] = '0;
assign lumen_official_bus_o[3872+:32] = '0;
assign lumen_official_bus_o[3904+:32] = '0;
assign lumen_official_bus_o[3936+:32] = '0;
assign lumen_official_bus_o[3968+:32] = '0;
assign lumen_official_bus_o[4000+:32] = '0;
assign lumen_official_bus_o[4032+:32] = '0;
assign lumen_official_bus_o[4064+:32] = '0;
assign lumen_official_bus_o[4096+:32] = '0;
assign lumen_official_bus_o[4128+:32] = '0;
assign lumen_official_bus_o[4160+:32] = '0;
assign lumen_official_bus_o[4192+:32] = '0;
assign lumen_official_bus_o[4224+:32] = '0;
assign lumen_official_bus_o[4256+:32] = '0;
assign lumen_official_bus_o[4288+:32] = '0;
assign lumen_official_bus_o[4320+:32] = '0;
assign lumen_official_bus_o[4352+:32] = '0;
assign lumen_official_bus_o[4384+:32] = '0;
assign lumen_official_bus_o[4416+:32] = '0;
assign lumen_official_bus_o[4448+:32] = '0;
assign lumen_official_bus_o[4480+:32] = '0;
assign lumen_official_bus_o[4512+:32] = '0;
assign lumen_official_bus_o[4544+:32] = '0;
assign lumen_official_bus_o[4576+:32] = '0;
assign lumen_official_bus_o[4608+:32] = '0;
assign lumen_official_bus_o[4640+:32] = '0;
assign lumen_official_bus_o[4672+:32] = '0;
assign lumen_official_bus_o[4704+:32] = '0;
assign lumen_official_bus_o[4736+:32] = '0;
assign lumen_official_bus_o[4768+:32] = '0;
assign lumen_official_bus_o[4800+:32] = '0;
assign lumen_official_bus_o[4832+:32] = '0;
assign lumen_official_bus_o[4864+:32] = '0;
assign lumen_official_bus_o[4896+:32] = '0;
assign lumen_official_bus_o[4928+:32] = '0;
assign lumen_official_bus_o[4960+:32] = '0;
assign lumen_official_bus_o[4992+:32] = '0;
assign lumen_official_bus_o[5024+:32] = '0;
assign lumen_official_bus_o[5056+:32] = '0;
assign lumen_official_bus_o[5088+:32] = '0;
assign lumen_official_bus_o[5120+:32] = '0;
assign lumen_official_bus_o[5152+:32] = '0;
assign lumen_official_bus_o[5184+:32] = '0;
assign lumen_official_bus_o[5216+:32] = '0;
assign lumen_official_bus_o[5248+:32] = '0;
assign lumen_official_bus_o[5280+:32] = '0;
assign lumen_official_bus_o[5312+:32] = '0;
assign lumen_official_bus_o[5344+:32] = '0;
assign lumen_official_bus_o[5376+:32] = '0;
assign lumen_official_bus_o[5408+:32] = '0;
assign lumen_official_bus_o[5440+:32] = '0;
assign lumen_official_bus_o[5472+:32] = '0;
assign lumen_official_bus_o[5504+:32] = '0;
assign lumen_official_bus_o[5536+:32] = '0;
assign lumen_official_bus_o[5568+:32] = '0;
assign lumen_official_bus_o[5600+:32] = '0;
assign lumen_official_bus_o[5632+:32] = '0;
assign lumen_official_bus_o[5664+:32] = '0;
assign lumen_official_bus_o[5696+:32] = '0;
assign lumen_official_bus_o[5728+:32] = '0;
assign lumen_official_bus_o[5760+:32] = '0;
assign lumen_official_bus_o[5792+:32] = '0;
assign lumen_official_bus_o[5824+:32] = '0;
assign lumen_official_bus_o[5856+:32] = '0;
assign lumen_official_bus_o[5888+:32] = '0;
assign lumen_official_bus_o[5920+:32] = '0;
assign lumen_official_bus_o[5952+:32] = '0;
assign lumen_official_bus_o[5984+:32] = '0;
assign lumen_official_bus_o[6016+:32] = '0;
assign lumen_official_bus_o[6048+:32] = '0;
assign lumen_official_bus_o[6080+:32] = '0;
assign lumen_official_bus_o[6112+:32] = '0;
assign lumen_official_bus_o[6144+:32] = '0;
assign lumen_official_bus_o[6176+:32] = '0;
assign lumen_official_bus_o[6208+:32] = '0;
assign lumen_official_bus_o[6240+:32] = '0;
assign lumen_official_bus_o[6272+:32] = '0;
assign lumen_official_bus_o[6304+:32] = '0;
assign lumen_official_bus_o[6336+:32] = '0;
assign lumen_official_bus_o[6368+:32] = '0;
assign lumen_official_bus_o[6400+:32] = '0;
assign lumen_official_bus_o[6432+:32] = '0;
assign lumen_official_bus_o[6464+:32] = '0;
assign lumen_official_bus_o[6496+:32] = '0;
assign lumen_official_bus_o[6528+:32] = '0;
assign lumen_official_bus_o[6560+:32] = '0;
assign lumen_official_bus_o[6592+:32] = '0;
assign lumen_official_bus_o[6624+:32] = '0;
assign lumen_official_bus_o[6656+:32] = '0;
assign lumen_official_bus_o[6688+:32] = '0;
assign lumen_official_bus_o[6720+:32] = '0;
assign lumen_official_bus_o[6752+:32] = '0;
assign lumen_official_bus_o[6784+:32] = '0;
assign lumen_official_bus_o[6816+:32] = '0;
assign lumen_official_bus_o[6848+:32] = '0;
assign lumen_official_bus_o[6880+:32] = '0;
assign lumen_official_bus_o[6912+:32] = '0;
assign lumen_official_bus_o[6944+:32] = '0;
assign lumen_official_bus_o[6976+:32] = '0;
assign lumen_official_bus_o[7008+:32] = '0;
assign lumen_official_bus_o[7040+:32] = '0;
assign lumen_official_bus_o[7072+:32] = '0;
assign lumen_official_bus_o[7104+:32] = '0;
assign lumen_official_bus_o[7136+:32] = '0;
assign lumen_official_bus_o[7168+:32] = '0;
assign lumen_official_bus_o[7200+:32] = '0;
assign lumen_official_bus_o[7232+:32] = '0;
assign lumen_official_bus_o[7264+:32] = '0;
assign lumen_official_bus_o[7296+:32] = '0;
assign lumen_official_bus_o[7328+:32] = '0;
assign lumen_official_bus_o[7360+:32] = '0;
assign lumen_official_bus_o[7392+:32] = '0;
assign lumen_official_bus_o[7424+:32] = '0;
assign lumen_official_bus_o[7456+:32] = '0;
assign lumen_official_bus_o[7488+:32] = '0;
assign lumen_official_bus_o[7520+:32] = '0;
assign lumen_official_bus_o[7552+:32] = '0;
assign lumen_official_bus_o[7584+:32] = '0;
assign lumen_official_bus_o[7616+:32] = '0;
assign lumen_official_bus_o[7648+:32] = '0;
assign lumen_official_bus_o[7680+:32] = '0;
assign lumen_official_bus_o[7712+:32] = '0;
assign lumen_official_bus_o[7744+:32] = '0;
assign lumen_official_bus_o[7776+:32] = '0;
assign lumen_official_bus_o[7808+:32] = '0;
assign lumen_official_bus_o[7840+:32] = '0;
assign lumen_official_bus_o[7872+:32] = '0;
end
