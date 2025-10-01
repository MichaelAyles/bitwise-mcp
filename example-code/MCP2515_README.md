# MCP2515 CAN Controller Driver for S32K144

Complete driver implementation for the Microchip MCP2515 stand-alone CAN controller with SPI interface, designed for the NXP S32K144 microcontroller.

## Features

- **Full CAN 2.0B Support**: Standard (11-bit) and Extended (29-bit) identifiers
- **Flexible Baud Rates**: 125 kbps, 250 kbps, 500 kbps, and 1 Mbps
- **Multiple Operating Modes**: Normal, Listen-Only, Loopback, Sleep
- **Non-blocking TX/RX**: Three TX buffers, two RX buffers with rollover
- **Error Monitoring**: Read error counters, flags, and bus status
- **Interrupt Support**: Optional interrupt-driven operation
- **Remote Frames**: Full RTR support

## Hardware Setup

### Required Components
- NXP S32K144 microcontroller
- Microchip MCP2515 CAN controller with 8 MHz crystal
- CAN transceiver (e.g., TJA1050, MCP2551)
- Pull-up resistors on MISO (10kΩ recommended)

### Pin Connections

| S32K144 Pin | MCP2515 Pin | Function |
|-------------|-------------|----------|
| PTB0        | CS          | Chip Select (GPIO) |
| PTB2        | SCK         | SPI Clock (LPSPI0_SCK) |
| PTB3        | SI          | SPI MOSI (LPSPI0_MOSI) |
| PTB4        | SO          | SPI MISO (LPSPI0_MISO) |
| -           | INT         | Interrupt (optional) |

**CAN Bus:**
- Connect MCP2515 CANH/CANL to CAN transceiver
- Add 120Ω termination resistors at both ends of CAN bus
- Recommended twisted pair cable for CAN_H and CAN_L

## File Structure

```
mcp2515.h              - Driver API and register definitions
mcp2515.c              - Driver implementation
mcp2515_example.c      - Example application demonstrating usage
```

## Usage Example

### 1. Initialize Hardware

```c
#include "mcp2515.h"

/* Configure SPI pins */
mcp2515_spi_config_t spi_config = {
    .spi_instance = 0,      /* LPSPI0 */
    .cs_port = 1,           /* PORTB */
    .cs_pin = 0             /* PTB0 */
};

/* Configure CAN parameters */
mcp2515_config_t can_config = {
    .baud_rate = MCP2515_BAUD_500KBPS,
    .mode = MCP2515_MODE_NORMAL,
    .enable_interrupts = false,
    .rx_mask_0 = 0x00,      /* Accept all messages */
    .rx_mask_1 = 0x00
};

/* Initialize MCP2515 */
mcp2515_status_t status = mcp2515_init(&spi_config, &can_config);
if (status != MCP2515_OK) {
    /* Handle error */
}
```

### 2. Transmit Messages

**Standard ID Message:**
```c
mcp2515_message_t msg = {
    .id = 0x123,
    .id_type = MCP2515_ID_STANDARD,
    .rtr = false,
    .dlc = 8,
    .data = {0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08}
};

status = mcp2515_transmit(&msg);
if (status == MCP2515_OK) {
    /* Message queued successfully */
} else if (status == MCP2515_BUSY) {
    /* All TX buffers full, retry later */
}
```

**Extended ID Message:**
```c
msg.id = 0x18FEF100;
msg.id_type = MCP2515_ID_EXTENDED;
msg.dlc = 4;
msg.data[0] = 0xAA;

status = mcp2515_transmit(&msg);
```

**Remote Frame Request:**
```c
msg.id = 0x200;
msg.id_type = MCP2515_ID_STANDARD;
msg.rtr = true;
msg.dlc = 0;

status = mcp2515_transmit(&msg);
```

### 3. Receive Messages

**Polling Mode:**
```c
while (1) {
    if (mcp2515_message_available()) {
        mcp2515_message_t rx_msg;
        status = mcp2515_receive(&rx_msg);

        if (status == MCP2515_OK) {
            /* Process received message */
            printf("Received ID: 0x%X, DLC: %u\n", rx_msg.id, rx_msg.dlc);
        }
    }
}
```

**Interrupt Mode:**
```c
/* Configure with interrupts enabled */
can_config.enable_interrupts = true;

/* In interrupt handler: */
void CAN_IRQHandler(void) {
    uint8_t interrupts = mcp2515_read_interrupts();

    if (interrupts & CANINTF_RX0IF) {
        /* Message in RX buffer 0 */
        mcp2515_message_t msg;
        mcp2515_receive(&msg);
    }

    mcp2515_clear_interrupts(interrupts);
}
```

### 4. Error Monitoring

```c
/* Read error flags */
uint8_t eflg = mcp2515_read_error_flags();

if (eflg & EFLG_TXBO) {
    printf("Bus-off error!\n");
}

if (eflg & EFLG_RX0OVR) {
    printf("RX buffer overflow!\n");
}

/* Read error counters */
uint8_t tec = mcp2515_read_tec();  /* Transmit Error Counter */
uint8_t rec = mcp2515_read_rec();  /* Receive Error Counter */

printf("TEC: %u, REC: %u\n", tec, rec);
```

## API Reference

### Initialization

- `mcp2515_init()` - Initialize MCP2515 with SPI and CAN configuration
- `mcp2515_reset()` - Software reset of MCP2515
- `mcp2515_set_mode()` - Change operating mode

### Message Transfer

- `mcp2515_transmit()` - Queue message for transmission (non-blocking)
- `mcp2515_receive()` - Read received message (non-blocking)
- `mcp2515_message_available()` - Check if messages are pending

### Status & Diagnostics

- `mcp2515_read_interrupts()` - Read interrupt flags (CANINTF register)
- `mcp2515_clear_interrupts()` - Clear specific interrupt flags
- `mcp2515_read_error_flags()` - Read error flags (EFLG register)
- `mcp2515_read_tec()` - Read transmit error counter
- `mcp2515_read_rec()` - Read receive error counter

## Configuration Notes

### Baud Rate Calculation

The driver assumes an 8 MHz crystal on the MCP2515. Baud rates are configured as:

| Baud Rate | BRP | TQ per bit | Sample Point |
|-----------|-----|------------|--------------|
| 1 Mbps    | 1   | 4          | 75%          |
| 500 kbps  | 1   | 8          | 75%          |
| 250 kbps  | 2   | 8          | 75%          |
| 125 kbps  | 4   | 8          | 75%          |

### SPI Clock Speed

- Maximum MCP2515 SPI clock: 10 MHz
- Recommended: 1-5 MHz for reliable operation
- Configure LPSPI prescaler accordingly

### Operating Modes

- **Normal**: Standard CAN communication, transmit and receive
- **Listen-Only**: Monitor bus without acknowledgment (no transmission)
- **Loopback**: Internal loopback for testing (no bus activity)
- **Sleep**: Low power mode
- **Configuration**: Required for changing timing parameters

## Troubleshooting

### No Communication
1. Verify SPI connections (especially CS, SCK, MOSI, MISO)
2. Check crystal oscillator on MCP2515 (should be 8 MHz)
3. Verify CAN transceiver power and connections
4. Check CAN bus termination (120Ω at both ends)
5. Use oscilloscope to verify SPI signals

### Messages Not Received
1. Ensure MCP2515 is in Normal or Listen-Only mode
2. Check RX buffer masks (set to 0x00 to accept all)
3. Verify bus termination
4. Check error counters (TEC/REC)
5. Monitor error flags for overflow

### Bus-Off Errors
1. Check physical layer (termination, cable quality)
2. Verify baud rate matches other nodes
3. Reduce bus speed if experiencing interference
4. Check error counters to identify transmit vs receive issues

### TX Busy
- All three TX buffers are full
- Reduce transmission rate
- Verify messages are being transmitted (check with CAN analyzer)
- Check for bus-off condition

## Example Application

The included `mcp2515_example.c` demonstrates:
- Hardware initialization
- Sending standard and extended ID messages
- Remote frame requests
- Receiving and echoing messages
- Continuous error monitoring

Build and run:
```bash
# Add to your S32K144 project
# Configure clock sources for LPSPI0
# Compile and flash to target
```

## License

This driver is provided as example code for educational and commercial use.

## References

- [MCP2515 Datasheet](https://ww1.microchip.com/downloads/en/DeviceDoc/MCP2515-Stand-Alone-CAN-Controller-with-SPI-20001801J.pdf)
- [S32K144 Reference Manual](https://www.nxp.com/docs/en/reference-manual/S32K1XXRM.pdf)
- CAN 2.0B Specification
