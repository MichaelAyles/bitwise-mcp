# LPI2C (Low Power Inter-Integrated Circuit) Registers

## Overview

The LPI2C module provides a low-power I2C interface supporting standard-mode, fast-mode, fast-mode plus, and ultra-fast modes. The module includes separate master and slave logic operating independently.

**Base Address:** LPI2C0 - 0x40066000

**Configuration:**
- TX FIFO: 4 words
- RX FIFO: 4 words
- SMBus: Supported
- Slave Mode: Enabled

---

## Register Memory Map

| Offset | Register | Width | Access | Reset | Description |
|--------|----------|-------|--------|-------|-------------|
| 0x00 | VERID | 32 | RO | 0x0100_0003 | Version ID Register |
| 0x04 | PARAM | 32 | RO | 0x0000_0202 | Parameter Register |
| 0x10 | MCR | 32 | RW | 0x0000_0000 | Master Control Register |
| 0x14 | MSR | 32 | W1C | 0x0000_0001 | Master Status Register |
| 0x18 | MIER | 32 | RW | 0x0000_0000 | Master Interrupt Enable Register |
| 0x1C | MDER | 32 | RW | 0x0000_0000 | Master DMA Enable Register |
| 0x20 | MCFGR0 | 32 | RW | 0x0000_0000 | Master Configuration Register 0 |
| 0x24 | MCFGR1 | 32 | RW | 0x0000_0000 | Master Configuration Register 1 |
| 0x28 | MCFGR2 | 32 | RW | 0x0000_0000 | Master Configuration Register 2 |
| 0x2C | MCFGR3 | 32 | RW | 0x0000_0000 | Master Configuration Register 3 |
| 0x40 | MDMR | 32 | RW | 0x0000_0000 | Master Data Match Register |
| 0x48 | MCCR0 | 32 | RW | 0x0000_0000 | Master Clock Configuration Register 0 |
| 0x4C | MCCR1 | 32 | RW | 0x0000_0000 | Master Clock Configuration Register 1 |
| 0x50 | MFCR | 32 | RW | 0x0000_0000 | Master FIFO Control Register |
| 0x54 | MFSR | 32 | RO | 0x0000_0000 | Master FIFO Status Register |
| 0x58 | MTDR | 32 | WO | 0x0000_0000 | Master Transmit Data Register |
| 0x5C | MRDR | 32 | RO | 0x0000_0000 | Master Receive Data Register |
| 0x110 | SCR | 32 | RW | 0x0000_0000 | Slave Control Register |
| 0x114 | SSR | 32 | W1C | 0x0000_0000 | Slave Status Register |
| 0x118 | SIER | 32 | RW | 0x0000_0000 | Slave Interrupt Enable Register |
| 0x11C | SDER | 32 | RW | 0x0000_0000 | Slave DMA Enable Register |
| 0x120 | SCFGR0 | 32 | RW | 0x0000_0000 | Slave Configuration Register 0 |
| 0x124 | SCFGR1 | 32 | RW | 0x0000_0000 | Slave Configuration Register 1 |
| 0x140 | SAMR | 32 | RW | 0x0000_0000 | Slave Address Match Register |
| 0x150 | SASR | 32 | RO | 0x0000_0000 | Slave Address Status Register |
| 0x154 | STAR | 32 | WO | 0x0000_0000 | Slave Transmit ACK Register |
| 0x160 | STDR | 32 | WO | 0x0000_0000 | Slave Transmit Data Register |
| 0x170 | SRDR | 32 | RO | 0x0000_0001 | Slave Receive Data Register |

---

## Master Mode Registers

### MCR - Master Control Register (Offset: 0x10)

**Function:** Controls master operation including enable, reset, and debug mode.

**Key Fields:**
- **RST** - Software reset (resets all master logic except MCR)
- **MEN** - Master Enable
- **DBG** - Debug Enable (allows operation during debug)
- **RTF** - Reset Transmit FIFO
- **RRF** - Reset Receive FIFO

**Notes:**
- MCR[RST] resets all master logic and registers to default state, except MCR itself
- Must disable master before changing most configuration registers

---

### MSR - Master Status Register (Offset: 0x14)

**Function:** Contains status flags for master operation.

**Key Status Flags (W1C):**
- **TDF** [0] - Transmit Data Flag (FIFO has space)
- **RDF** [1] - Receive Data Flag (FIFO has data)
- **EPF** [8] - End Packet Flag
- **SDF** [9] - STOP Detect Flag
- **NDF** [10] - NACK Detect Flag
- **ALF** [11] - Arbitration Lost Flag
- **FEF** [12] - FIFO Error Flag
- **PLTF** [13] - Pin Low Timeout Flag
- **DMF** [14] - Data Match Flag
- **MBF** [25] - Master Busy Flag (read-only)
- **BBF** [24] - Bus Busy Flag (read-only)

**Error Conditions:**
- **NDF** sets when:
  - Master expected NACK but detected ACK (address byte)
  - Master detected NACK during transmit
  - ACK detected when expecting NACK, and MCFGR1[IGNACK] is clear
- **FEF** sets when transmit FIFO requests data without START condition
- **PLTF** sets when SCL/SDA is low for more than MCFGR3[PINLOW] cycles

---

### MIER - Master Interrupt Enable Register (Offset: 0x18)

**Function:** Enables master interrupts.

**Interrupt Enable Bits:**
- **TDIE** [0] - Transmit Data Interrupt Enable
- **RDIE** [1] - Receive Data Interrupt Enable
- **EPIE** [8] - End Packet Interrupt Enable
- **SDIE** [9] - STOP Detect Interrupt Enable
- **NDIE** [10] - NACK Detect Interrupt Enable
- **ALIE** [11] - Arbitration Lost Interrupt Enable
- **FEIE** [12] - FIFO Error Interrupt Enable
- **PLTIE** [13] - Pin Low Timeout Interrupt Enable
- **DMIE** [14] - Data Match Interrupt Enable

---

### MDER - Master DMA Enable Register (Offset: 0x1C)

**Function:** Enables master DMA requests.

**DMA Enable Bits:**
- **TDDE** [0] - Transmit Data DMA Enable
- **RDDE** [1] - Receive Data DMA Enable

---

### MCFGR0 - Master Configuration Register 0 (Offset: 0x20)

**Function:** Clock configuration for standard/fast mode. Only writable when master disabled.

**Key Fields:**
- **HREN** - Host Request Enable
- **HRPOL** - Host Request Polarity
- **HRSEL** - Host Request Select
- **CIRFIFO** - Circular FIFO Enable
- **RDMO** - Receive Data Match Only

---

### MCFGR1 - Master Configuration Register 1 (Offset: 0x24)

**Function:** Pin and protocol configuration. Only writable when master disabled.

**Key Fields:**
- **PRESCALE** [26:24] - Prescaler value (divides functional clock)
- **AUTOSTOP** [23] - Automatic STOP generation
- **IGNACK** [22] - Ignore NACK
- **TIMECFG** [21] - Timeout configuration
- **MATCFG** [18:16] - Match configuration
- **PINCFG** [10:8] - Pin configuration (2-wire, 4-wire, open-drain, push-pull modes)

**Pin Configuration Options:**
- 000b - 2-pin open drain mode
- 001b - 2-pin output only (ultra-fast mode)
- 010b - 2-pin push-pull mode
- 011b - 4-pin push-pull mode
- 100b - 2-pin open drain with separate slave
- 101b - 2-pin output only with separate slave
- 110b - 2-pin push-pull with separate slave
- 111b - 4-pin push-pull (inverted outputs)

---

### MCFGR2 - Master Configuration Register 2 (Offset: 0x28)

**Function:** Glitch filter and timeout configuration. Only writable when master disabled.

**Key Fields:**
- **BUSIDLE** [27:16] - Bus Idle Timeout (in prescaler cycles)
- **FILTSCL** [11:8] - SCL glitch filter (cycles to ignore)
- **FILTSDA** [3:0] - SDA glitch filter (cycles to ignore)

**Notes:**
- Glitch filter disabled when set to 0
- Glitches ≤ FILTSDA/FILTSCL cycles are filtered
- Latency = filter value + 3 cycles
- Must be less than minimum SCL low/high period
- Not affected by PRESCALE configuration

---

### MCFGR3 - Master Configuration Register 3 (Offset: 0x2C)

**Function:** Pin low timeout configuration.

**Key Fields:**
- **PINLOW** [19:8] - Pin Low Timeout (in 256 × prescaler cycles)

---

### MDMR - Master Data Match Register (Offset: 0x40)

**Function:** Configures data match values for receive filtering.

**Key Fields:**
- **MATCH1** [23:16] - Match 1 Value
- **MATCH0** [7:0] - Match 0 Value

**Notes:**
- Compared against received data when receive data match is enabled
- Can be used to filter or trigger on specific data patterns

---

### MCCR0 - Master Clock Configuration Register 0 (Offset: 0x48)

**Function:** Timing for standard/fast mode. Cannot be changed when master enabled.

**Key Fields:**
- **DATAVD** [30:24] - Data Valid Delay
- **SETHOLD** [21:16] - Setup Hold Delay
- **CLKHI** [13:8] - Clock High Period
- **CLKLO** [5:0] - Clock Low Period

**Notes:**
- Used for standard, fast, and fast-mode plus
- Values in prescaler cycles

---

### MCCR1 - Master Clock Configuration Register 1 (Offset: 0x4C)

**Function:** Timing for ultra-fast mode. Cannot be changed when master enabled.

**Key Fields:**
- **DATAVD** [30:24] - Data Valid Delay
- **SETHOLD** [21:16] - Setup Hold Delay
- **CLKHI** [13:8] - Clock High Period
- **CLKLO** [5:0] - Clock Low Period

---

### MFCR - Master FIFO Control Register (Offset: 0x50)

**Function:** Controls FIFO watermarks.

**Key Fields:**
- **RXWATER** [17:16] - Receive FIFO Watermark (RDF sets when words > RXWATER)
- **TXWATER** [1:0] - Transmit FIFO Watermark (TDF sets when words ≤ TXWATER)

**Notes:**
- Values ≥ FIFO size are truncated
- FIFO size = 4 words

---

### MFSR - Master FIFO Status Register (Offset: 0x54)

**Function:** Reports current FIFO status (read-only).

**Key Fields:**
- **RXCOUNT** [17:16] - Receive FIFO Count (number of words in RX FIFO)
- **TXCOUNT** [1:0] - Transmit FIFO Count (number of words in TX FIFO)

---

### MTDR - Master Transmit Data Register (Offset: 0x58)

**Function:** Write-only register for transmit commands and data.

**Key Fields:**
- **CMD** [10:8] - Command (START, STOP, transmit, receive, etc.)
- **DATA** [7:0] - Transmit Data

**Command Values:**
- 000b - Transmit DATA
- 001b - Receive (DATA+1) bytes
- 010b - Generate STOP
- 011b - Receive and discard (DATA+1) bytes
- 100b - Generate (repeated) START + transmit address in DATA[7:0]
- 101b - Generate (repeated) START + transmit address in DATA[7:0] (expect NACK)
- 110b - Generate (repeated) START + high-speed mode master code
- 111b - Generate (repeated) START + high-speed mode master code (expect NACK)

---

### MRDR - Master Receive Data Register (Offset: 0x5C)

**Function:** Read-only register containing received data.

**Key Fields:**
- **RXEMPTY** [14] - Receive FIFO Empty flag
- **DATA** [7:0] - Receive Data

---

## Slave Mode Registers

### SCR - Slave Control Register (Offset: 0x110)

**Function:** Controls slave operation including enable, reset, and filtering.

**Key Fields:**
- **RST** - Software reset (resets all slave logic except SCR)
- **SEN** - Slave Enable
- **FILTDZ** - Filter Doze Enable
- **FILTEN** - Filter Enable
- **RTF** - Reset Transmit FIFO
- **RRF** - Reset Receive FIFO

**Notes:**
- SCR[RST] resets all slave logic and registers to default state, except SCR itself

---

### SSR - Slave Status Register (Offset: 0x114)

**Function:** Contains status flags for slave operation.

**Key Status Flags (W1C):**
- **TDF** [0] - Transmit Data Flag
- **RDF** [1] - Receive Data Flag
- **AVF** [2] - Address Valid Flag
- **TAF** [3] - Transmit ACK Flag
- **RSF** [8] - Repeated START Flag
- **SDF** [9] - STOP Detect Flag
- **BEF** [10] - Bit Error Flag
- **FEF** [11] - FIFO Error Flag
- **AM0F** [12] - Address Match 0 Flag
- **AM1F** [13] - Address Match 1 Flag
- **GCF** [14] - General Call Flag
- **SARF** [15] - SMBus Alert Response Flag
- **SBF** [24] - Slave Busy Flag (read-only)
- **BBF** [25] - Bus Busy Flag (read-only)

**Error Conditions:**
- **BEF** sets when slave drives SDA but samples different value
- **FEF** sets due to:
  - Transmit data underrun
  - Receive data overrun
  - Address overrun (when RXCFG is set)
- Clock stretching eliminates underrun/overrun

---

### SIER - Slave Interrupt Enable Register (Offset: 0x118)

**Function:** Enables slave interrupts.

**Interrupt Enable Bits:**
- **TDIE** [0] - Transmit Data Interrupt Enable
- **RDIE** [1] - Receive Data Interrupt Enable
- **AVIE** [2] - Address Valid Interrupt Enable
- **TAIE** [3] - Transmit ACK Interrupt Enable
- **RSIE** [8] - Repeated START Interrupt Enable
- **SDIE** [9] - STOP Detect Interrupt Enable
- **BEIE** [10] - Bit Error Interrupt Enable
- **FEIE** [11] - FIFO Error Interrupt Enable
- **AM0IE** [12] - Address Match 0 Interrupt Enable
- **AM1IE** [13] - Address Match 1 Interrupt Enable
- **GCIE** [14] - General Call Interrupt Enable
- **SARIE** [15] - SMBus Alert Response Interrupt Enable

---

### SDER - Slave DMA Enable Register (Offset: 0x11C)

**Function:** Enables slave DMA requests.

**DMA Enable Bits:**
- **TDDE** [0] - Transmit Data DMA Enable
- **RDDE** [1] - Receive Data DMA Enable

---

### SCFGR0 - Slave Configuration Register 0 (Offset: 0x120)

**Function:** Address and clock stretching configuration.

**Key Fields:**
- **FILTSCL** [11:8] - SCL glitch filter
- **FILTSDA** [3:0] - SDA glitch filter

---

### SCFGR1 - Slave Configuration Register 1 (Offset: 0x124)

**Function:** Slave protocol configuration. Only writable when slave disabled.

**Key Fields:**
- **ADDRCFG** [18:16] - Address Configuration (7-bit, 10-bit, or range)
- **HSMEN** [13] - High-Speed Mode Enable
- **IGNACK** [12] - Ignore NACK
- **RXCFG** [11] - Receive Data Configuration
- **TXCFG** [10] - Transmit Data Configuration
- **SAEN** [9] - SMBus Alert Enable
- **GCEN** [8] - General Call Enable
- **ACKSTALL** [3] - ACK Stall (clock stretching during ACK)
- **TXDSTALL** [2] - Transmit Data Stall
- **RXSTALL** [1] - Receive Data Stall
- **ADRSTALL** [0] - Address Stall

**Address Configuration:**
- 000b - Address disabled
- 001b - 7-bit address
- 010b - 10-bit address
- 011b - 7-bit range (ADDR0 to ADDR1)
- 100b - 10-bit range (ADDR0 to ADDR1)
- 101b - 7-bit or 10-bit address
- 110b - 7-bit range or 10-bit address

---

### SAMR - Slave Address Match Register (Offset: 0x140)

**Function:** Configures slave addresses for matching.

**Key Fields:**
- **ADDR1** [26:17] - Address 1 Value (10-bit: bits [9:0], 7-bit: bits [6:0])
- **ADDR0** [10:1] - Address 0 Value (10-bit: bits [9:0], 7-bit: bits [6:0])

**Address Matching:**
- In 7-bit mode: compared directly to received address
- In 10-bit mode:
  - First byte: {11110, ADDR[9:8]}
  - Second byte: ADDR[7:0]
- Range mode: matches if received address is between ADDR0 and ADDR1

---

### SASR - Slave Address Status Register (Offset: 0x150)

**Function:** Read-only register indicating which address was matched.

**Key Fields:**
- **ANV** [14] - Address Not Valid (set during general call or SMBus alert)
- **RADDR** [10:0] - Received Address

---

### STAR - Slave Transmit ACK Register (Offset: 0x154)

**Function:** Write-only register to control ACK/NACK transmission.

**Key Fields:**
- **TXNACK** [0] - Transmit NACK (1 = send NACK, 0 = send ACK)

---

### STDR - Slave Transmit Data Register (Offset: 0x160)

**Function:** Write-only register for transmit data.

**Key Fields:**
- **DATA** [7:0] - Transmit Data

---

### SRDR - Slave Receive Data Register (Offset: 0x170)

**Function:** Read-only register containing received data.

**Key Fields:**
- **SOF** [15] - Start Of Frame (set for first data word after address)
- **RXEMPTY** [14] - Receive FIFO Empty flag
- **DATA** [7:0] - Receive Data

---

## Operating Modes

### Chip Mode Support

| Chip Mode | LPI2C Operation |
|-----------|-----------------|
| Run | Normal operation (master and slave) |
| VLPR | Reduced power, uses slow internal clock |
| STOP | All clocks gated, retains register state |
| Debug | Operation controlled by DOZE bit in MCR/SCR |

### Master vs Slave Operation

- **Independent Logic:** Master and slave operate independently but cannot connect to separate I2C buses
- **Simultaneous Operation:** Can be used together on same bus
- **Reset:** Separate software reset bits in MCR and SCR

---

## Addressing Modes

### Master Mode
- Supports 7-bit and 10-bit addressing
- 10-bit addressing: (repeated) START + address byte 1 + address byte 2

### Slave Mode
- Configurable for 7-bit or 10-bit addressing
- Can match one or two addresses
- Can match address ranges
- General call support (address 0x00)
- SMBus alert response

---

## FIFO Configuration

**TX FIFO:** 4 words (master and slave)
**RX FIFO:** 4 words (master and slave)

**Watermark Control:**
- TX watermark: TDF sets when words ≤ TXWATER
- RX watermark: RDF sets when words > RXWATER
- Configurable via MFCR (master) or SFCR (slave)

**FIFO Reset:**
- Master: MCR[RTF], MCR[RRF]
- Slave: SCR[RTF], SCR[RRF]

---

## Clock Configuration

### Clock Modes
1. **Standard mode:** 100 kHz (MCCR0)
2. **Fast mode:** 400 kHz (MCCR0)
3. **Fast-mode plus:** 1 MHz (MCCR0)
4. **Ultra-fast mode:** 5 MHz (MCCR1)

### Clock Prescaler
- Configured via MCFGR1[PRESCALE] (bits 26:24)
- Divides functional clock before timing registers

### Timing Parameters (MCCR0/MCCR1)
- **CLKLO** - Clock Low Period
- **CLKHI** - Clock High Period
- **SETHOLD** - Setup/Hold Delay
- **DATAVD** - Data Valid Delay

---

## Glitch Filtering

**Purpose:** Filter noise on SCL and SDA lines

**Configuration:**
- Master: MCFGR2[FILTSCL], MCFGR2[FILTSDA]
- Slave: SCFGR0[FILTSCL], SCFGR0[FILTSDA]

**Behavior:**
- 0 = disabled
- N = filters glitches ≤ N cycles
- Latency = N + 3 cycles
- Not affected by prescaler
- Must be less than minimum SCL period

---

## Clock Stretching

**Slave Clock Stretching:**
- Enabled via SCFGR1 stall bits:
  - ADRSTALL - During address byte
  - RXSTALL - During receive
  - TXDSTALL - During transmit
  - ACKSTALL - During ACK

**Benefits:**
- Prevents FIFO underrun/overrun
- Allows slave to process data at its own pace

---

## Interrupts and DMA

### Master Interrupts (MIER)
All master status flags can generate interrupts when enabled

### Slave Interrupts (SIER)
All slave status flags can generate interrupts when enabled

### DMA Support
- **Master:** TX DMA (MDER[TDDE]), RX DMA (MDER[RDDE])
- **Slave:** TX DMA (SDER[TDDE]), RX DMA (SDER[RDDE])

### Low Power Wakeup
Most interrupts can generate asynchronous wakeup from low power modes

---

## Reset Behavior

### Chip Reset
All LPI2C master and slave logic/registers reset to default state

### Software Reset
- **Master:** MCR[RST] - Resets all master logic except MCR
- **Slave:** SCR[RST] - Resets all slave logic except SCR

---

## Pin Configuration (MCFGR1[PINCFG])

### 2-Wire Modes
- **Open drain:** Standard I2C with external pull-ups
- **Output only:** Ultra-fast mode, unidirectional
- **Push-pull:** Faster edges, requires special bus configuration

### 4-Wire Modes
- **Separate input/output pins:** SCLS/SDAS outputs, SCL/SDA inputs
- **Push-pull operation:** No external pull-ups required

---

## SMBus Support

**Features:**
- SMBus packet error checking (PEC)
- SMBus alert response
- SMBus timeout detection
- General call address support

**Configuration:**
- Slave: SCFGR1[SAEN] enables SMBus alert
- SARF flag set on SMBus alert response

---

## Host Request (HREQ)

**Function:** External signal to initiate master transfer when bus idle

**Configuration:**
- MCFGR0[HREN] - Enable host request
- MCFGR0[HRPOL] - Polarity (active high/low)
- MCFGR0[HRSEL] - Source selection

**Note:** Not supported on 32-pin QFN and 48-pin LQFP packages

---

## Pin Low Timeout

**Purpose:** Detect stuck bus condition (SCL or SDA held low too long)

**Configuration:**
- MCFGR3[PINLOW] - Timeout value (in 256 × prescaler cycles)

**Behavior:**
- MSR[PLTF] sets when timeout occurs
- Works even when master is idle
- Software must resolve condition
- Flag cannot be cleared until pin returns high

---

## Data Matching

**Purpose:** Filter or trigger on specific received data patterns

**Configuration:**
- MDMR[MATCH0], MDMR[MATCH1] - Match values
- MCFGR1[MATCFG] - Match configuration

**Behavior:**
- MSR[DMF] sets when match occurs
- Can be used with MCFGR0[RDMO] to discard non-matching data
- Useful for packet filtering in master-receiver mode

---

## Register Access Notes

1. **Configuration Registers:** Most MCFGR and SCFGR registers can only be written when module is disabled (MEN=0 or SEN=0)

2. **Status Flags:** Most status flags are W1C (Write-1-to-Clear). Write 1 to clear the flag.

3. **FIFO Access:**
   - MTDR is write-only
   - MRDR and SRDR are read-only
   - Reading/writing automatically updates FIFO pointers

4. **Simultaneous Master/Slave:** Can enable both but they share the same physical pins (cannot operate on separate buses)

5. **Debug Mode:** Set MCR[DBGEN] or SCR[FILTDZ] to allow operation during debug halt

---

## Reference

**Source:** S32K144 Reference Manual, Chapter 52 (Low Power Inter-Integrated Circuit)
**Pages:** 1634-1690