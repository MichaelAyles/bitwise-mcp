/**
 * @file mcp2515.h
 * @brief MCP2515 CAN Controller Driver for S32K144 MCU
 *
 * Driver for Microchip MCP2515 stand-alone CAN controller with SPI interface.
 * Supports 125kbps to 1Mbps CAN bus speeds with standard and extended IDs.
 */

#ifndef MCP2515_H
#define MCP2515_H

#include <stdint.h>
#include <stdbool.h>

/* MCP2515 SPI Instructions */
#define MCP2515_RESET           0xC0
#define MCP2515_READ            0x03
#define MCP2515_WRITE           0x02
#define MCP2515_RTS             0x80  /* Request to Send */
#define MCP2515_READ_STATUS     0xA0
#define MCP2515_RX_STATUS       0xB0
#define MCP2515_BIT_MODIFY      0x05

/* MCP2515 Register Addresses */
#define MCP2515_BFPCTRL         0x0C
#define MCP2515_TXRTSCTRL       0x0D
#define MCP2515_CANSTAT         0x0E
#define MCP2515_CANCTRL         0x0F
#define MCP2515_TEC             0x1C
#define MCP2515_REC             0x1D
#define MCP2515_CNF3            0x28
#define MCP2515_CNF2            0x29
#define MCP2515_CNF1            0x2A
#define MCP2515_CANINTE         0x2B
#define MCP2515_CANINTF         0x2C
#define MCP2515_EFLG            0x2D
#define MCP2515_TXB0CTRL        0x30
#define MCP2515_TXB0SIDH        0x31
#define MCP2515_TXB1CTRL        0x40
#define MCP2515_TXB1SIDH        0x41
#define MCP2515_TXB2CTRL        0x50
#define MCP2515_TXB2SIDH        0x51
#define MCP2515_RXB0CTRL        0x60
#define MCP2515_RXB0SIDH        0x61
#define MCP2515_RXB1CTRL        0x70
#define MCP2515_RXB1SIDH        0x71

/* CANCTRL Register Bits */
#define CANCTRL_REQOP_MASK      0xE0
#define CANCTRL_REQOP_NORMAL    0x00
#define CANCTRL_REQOP_SLEEP     0x20
#define CANCTRL_REQOP_LOOPBACK  0x40
#define CANCTRL_REQOP_LISTENONLY 0x60
#define CANCTRL_REQOP_CONFIG    0x80
#define CANCTRL_ABAT            0x10
#define CANCTRL_OSM             0x08  /* One-Shot Mode */
#define CANCTRL_CLKEN           0x04
#define CANCTRL_CLKPRE_MASK     0x03

/* CANSTAT Register Bits */
#define CANSTAT_OPMOD_MASK      0xE0

/* CANINTE Register Bits */
#define CANINTE_MERRE           0x80  /* Message Error Interrupt Enable */
#define CANINTE_WAKIE           0x40  /* Wakeup Interrupt Enable */
#define CANINTE_ERRIE           0x20  /* Error Interrupt Enable */
#define CANINTE_TX2IE           0x10  /* TX Buffer 2 Empty Interrupt Enable */
#define CANINTE_TX1IE           0x08  /* TX Buffer 1 Empty Interrupt Enable */
#define CANINTE_TX0IE           0x04  /* TX Buffer 0 Empty Interrupt Enable */
#define CANINTE_RX1IE           0x02  /* RX Buffer 1 Full Interrupt Enable */
#define CANINTE_RX0IE           0x01  /* RX Buffer 0 Full Interrupt Enable */

/* CANINTF Register Bits */
#define CANINTF_MERRF           0x80  /* Message Error Flag */
#define CANINTF_WAKIF           0x40  /* Wakeup Interrupt Flag */
#define CANINTF_ERRIF           0x20  /* Error Interrupt Flag */
#define CANINTF_TX2IF           0x10  /* TX Buffer 2 Empty Flag */
#define CANINTF_TX1IF           0x08  /* TX Buffer 1 Empty Flag */
#define CANINTF_TX0IF           0x04  /* TX Buffer 0 Empty Flag */
#define CANINTF_RX1IF           0x02  /* RX Buffer 1 Full Flag */
#define CANINTF_RX0IF           0x01  /* RX Buffer 0 Full Flag */

/* EFLG Register Bits */
#define EFLG_RX1OVR             0x80  /* RX Buffer 1 Overflow */
#define EFLG_RX0OVR             0x40  /* RX Buffer 0 Overflow */
#define EFLG_TXBO               0x20  /* Bus-Off Error */
#define EFLG_TXEP               0x10  /* Transmit Error-Passive */
#define EFLG_RXEP               0x08  /* Receive Error-Passive */
#define EFLG_TXWAR              0x04  /* Transmit Error Warning */
#define EFLG_RXWAR              0x02  /* Receive Error Warning */
#define EFLG_EWARN              0x01  /* Error Warning */

/* TXBnCTRL Register Bits */
#define TXBCTRL_ABTF            0x40  /* Message Aborted Flag */
#define TXBCTRL_MLOA            0x20  /* Message Lost Arbitration */
#define TXBCTRL_TXERR           0x10  /* Transmission Error Detected */
#define TXBCTRL_TXREQ           0x08  /* Message Transmit Request */
#define TXBCTRL_TXP_MASK        0x03  /* Transmit Priority */

/* RXBnCTRL Register Bits */
#define RXBCTRL_RXM_MASK        0x60  /* Receive Buffer Operating Mode */
#define RXBCTRL_RXM_STD_EXT     0x00  /* Receive all valid messages */
#define RXBCTRL_RXM_STDONLY     0x20  /* Receive standard IDs only */
#define RXBCTRL_RXM_EXTONLY     0x40  /* Receive extended IDs only */
#define RXBCTRL_BUKT            0x04  /* Rollover Enable */

/* CAN ID Type */
typedef enum {
    MCP2515_ID_STANDARD = 0,  /* 11-bit ID */
    MCP2515_ID_EXTENDED = 1   /* 29-bit ID */
} mcp2515_id_type_t;

/* MCP2515 Operating Mode */
typedef enum {
    MCP2515_MODE_NORMAL = 0,
    MCP2515_MODE_SLEEP = 1,
    MCP2515_MODE_LOOPBACK = 2,
    MCP2515_MODE_LISTEN_ONLY = 3,
    MCP2515_MODE_CONFIG = 4
} mcp2515_mode_t;

/* CAN Baud Rate */
typedef enum {
    MCP2515_BAUD_125KBPS = 0,
    MCP2515_BAUD_250KBPS = 1,
    MCP2515_BAUD_500KBPS = 2,
    MCP2515_BAUD_1MBPS = 3
} mcp2515_baud_t;

/* CAN Message Structure */
typedef struct {
    uint32_t id;                /* CAN identifier (11 or 29 bits) */
    mcp2515_id_type_t id_type;  /* Standard or Extended */
    bool rtr;                   /* Remote Transmission Request */
    uint8_t dlc;                /* Data length code (0-8) */
    uint8_t data[8];            /* Message data */
} mcp2515_message_t;

/* MCP2515 Configuration */
typedef struct {
    mcp2515_baud_t baud_rate;   /* CAN bus baud rate */
    mcp2515_mode_t mode;        /* Operating mode */
    bool enable_interrupts;     /* Enable interrupt output */
    uint8_t rx_mask_0;          /* RX buffer 0 mask (0 = don't care) */
    uint8_t rx_mask_1;          /* RX buffer 1 mask */
} mcp2515_config_t;

/* SPI Pin Configuration for S32K144 */
typedef struct {
    uint8_t spi_instance;       /* LPSPI instance (0, 1, or 2) */
    uint16_t cs_port;           /* Chip select GPIO port */
    uint16_t cs_pin;            /* Chip select GPIO pin */
} mcp2515_spi_config_t;

/* Status Codes */
typedef enum {
    MCP2515_OK = 0,
    MCP2515_ERROR = -1,
    MCP2515_BUSY = -2,
    MCP2515_TIMEOUT = -3,
    MCP2515_NO_MESSAGE = -4,
    MCP2515_INVALID_PARAM = -5
} mcp2515_status_t;

/**
 * @brief Initialize MCP2515 controller
 *
 * @param spi_config SPI interface configuration
 * @param config MCP2515 operating configuration
 * @return mcp2515_status_t Status of initialization
 */
mcp2515_status_t mcp2515_init(const mcp2515_spi_config_t *spi_config,
                               const mcp2515_config_t *config);

/**
 * @brief Reset MCP2515 controller
 *
 * @return mcp2515_status_t Status of reset operation
 */
mcp2515_status_t mcp2515_reset(void);

/**
 * @brief Set MCP2515 operating mode
 *
 * @param mode Desired operating mode
 * @return mcp2515_status_t Status of mode change
 */
mcp2515_status_t mcp2515_set_mode(mcp2515_mode_t mode);

/**
 * @brief Transmit CAN message (non-blocking)
 *
 * Uses first available TX buffer (priority: TXB0 > TXB1 > TXB2)
 *
 * @param msg Pointer to message to transmit
 * @return mcp2515_status_t MCP2515_OK if queued, MCP2515_BUSY if all buffers full
 */
mcp2515_status_t mcp2515_transmit(const mcp2515_message_t *msg);

/**
 * @brief Receive CAN message (non-blocking)
 *
 * Checks both RX buffers (priority: RXB0 > RXB1)
 *
 * @param msg Pointer to store received message
 * @return mcp2515_status_t MCP2515_OK if message received, MCP2515_NO_MESSAGE if no message
 */
mcp2515_status_t mcp2515_receive(mcp2515_message_t *msg);

/**
 * @brief Check for received messages
 *
 * @return true if message available in RX buffers
 */
bool mcp2515_message_available(void);

/**
 * @brief Read MCP2515 interrupt flags
 *
 * @return uint8_t CANINTF register value
 */
uint8_t mcp2515_read_interrupts(void);

/**
 * @brief Clear specific interrupt flags
 *
 * @param flags Interrupt flags to clear (CANINTF bits)
 * @return mcp2515_status_t Status of operation
 */
mcp2515_status_t mcp2515_clear_interrupts(uint8_t flags);

/**
 * @brief Read error flags
 *
 * @return uint8_t EFLG register value
 */
uint8_t mcp2515_read_error_flags(void);

/**
 * @brief Read transmit error counter
 *
 * @return uint8_t TEC register value
 */
uint8_t mcp2515_read_tec(void);

/**
 * @brief Read receive error counter
 *
 * @return uint8_t REC register value
 */
uint8_t mcp2515_read_rec(void);

#endif /* MCP2515_H */
