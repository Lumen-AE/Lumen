// SPI Master state machine states
`ifndef SPI_DEFINES_VH
`define SPI_DEFINES_VH

`define SPI_IDLE      3'b000
`define SPI_LOAD      3'b001
`define SPI_SHIFT     3'b010
`define SPI_DONE      3'b011
`define SPI_CS_DEASSERT 3'b100

`endif
