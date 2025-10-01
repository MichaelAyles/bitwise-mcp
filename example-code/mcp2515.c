/**
 * @file mcp2515.c
 * @brief MCP2515 CAN Controller Driver Implementation for S32K144
 */

#include "mcp2515.h"
#include <string.h>

/* S32K144 LPSPI Register Map */
typedef struct {
    volatile uint32_t VERID;        /* 0x00: Version ID */
    volatile uint32_t PARAM;        /* 0x04: Parameter */
    volatile uint32_t reserved1[2]; /* 0x08-0x0C */
    volatile uint32_t CR;           /* 0x10: Control */
    volatile uint32_t SR;           /* 0x14: Status */
    volatile uint32_t IER;          /* 0x18: Interrupt Enable */
    volatile uint32_t DER;          /* 0x1C: DMA Enable */
    volatile uint32_t CFGR0;        /* 0x20: Configuration 0 */
    volatile uint32_t CFGR1;        /* 0x24: Configuration 1 */
    volatile uint32_t reserved2[2]; /* 0x28-0x2C */
    volatile uint32_t DMR0;         /* 0x30: Data Match 0 */
    volatile uint32_t DMR1;         /* 0x34: Data Match 1 */
    volatile uint32_t reserved3[2]; /* 0x38-0x3C */
    volatile uint32_t CCR;          /* 0x40: Clock Configuration */
    volatile uint32_t reserved4[5]; /* 0x44-0x54 */
    volatile uint32_t FCR;          /* 0x58: FIFO Control */
    volatile uint32_t FSR;          /* 0x5C: FIFO Status */
    volatile uint32_t TCR;          /* 0x60: Transmit Command */
    volatile uint32_t TDR;          /* 0x64: Transmit Data */
    volatile uint32_t reserved5[2]; /* 0x68-0x6C */
    volatile uint32_t RSR;          /* 0x70: Receive Status */
    volatile uint32_t RDR;          /* 0x74: Receive Data */
} LPSPI_Type;

/* S32K144 GPIO Register Map */
typedef struct {
    volatile uint32_t PDOR;         /* 0x00: Port Data Output */
    volatile uint32_t PSOR;         /* 0x04: Port Set Output */
    volatile uint32_t PCOR;         /* 0x08: Port Clear Output */
    volatile uint32_t PTOR;         /* 0x0C: Port Toggle Output */
    volatile uint32_t PDIR;         /* 0x10: Port Data Input */
    volatile uint32_t PDDR;         /* 0x14: Port Data Direction */
} GPIO_Type;

/* Base Addresses */
#define LPSPI0_BASE             0x4002C000u
#define LPSPI1_BASE             0x4002D000u
#define LPSPI2_BASE             0x4002E000u
#define PTA_BASE                0x400FF000u
#define PTB_BASE                0x400FF040u
#define PTC_BASE                0x400FF080u
#define PTD_BASE                0x400FF0C0u
#define PTE_BASE                0x400FF100u

/* LPSPI Register Bits */
#define LPSPI_CR_MEN            (1u << 0)   /* Module Enable */
#define LPSPI_CR_RST            (1u << 1)   /* Software Reset */
#define LPSPI_SR_TDF            (1u << 0)   /* Transmit Data Flag */
#define LPSPI_SR_RDF            (1u << 1)   /* Receive Data Flag */
#define LPSPI_SR_MBF            (1u << 24)  /* Module Busy Flag */
#define LPSPI_TCR_FRAMESZ_MASK  0x0FFF      /* Frame Size Mask */
#define LPSPI_TCR_PCS_SHIFT     24          /* Peripheral Chip Select */

/* Module State */
static struct {
    bool initialized;
    LPSPI_Type *spi;
    GPIO_Type *cs_port;
    uint16_t cs_pin;
    mcp2515_config_t config;
} mcp2515_state = {0};

/* Helper Functions */
static inline LPSPI_Type* get_lpspi_base(uint8_t instance) {
    switch (instance) {
        case 0: return (LPSPI_Type*)LPSPI0_BASE;
        case 1: return (LPSPI_Type*)LPSPI1_BASE;
        case 2: return (LPSPI_Type*)LPSPI2_BASE;
        default: return NULL;
    }
}

static inline GPIO_Type* get_gpio_base(uint16_t port) {
    switch (port) {
        case 0: return (GPIO_Type*)PTA_BASE;
        case 1: return (GPIO_Type*)PTB_BASE;
        case 2: return (GPIO_Type*)PTC_BASE;
        case 3: return (GPIO_Type*)PTD_BASE;
        case 4: return (GPIO_Type*)PTE_BASE;
        default: return NULL;
    }
}

static inline void cs_low(void) {
    mcp2515_state.cs_port->PCOR = (1u << mcp2515_state.cs_pin);
}

static inline void cs_high(void) {
    mcp2515_state.cs_port->PSOR = (1u << mcp2515_state.cs_pin);
}

static uint8_t spi_transfer(uint8_t data) {
    LPSPI_Type *spi = mcp2515_state.spi;

    /* Wait for TX FIFO available */
    while (!(spi->SR & LPSPI_SR_TDF)) {}

    /* Transmit data (8-bit frame) */
    spi->TDR = data;

    /* Wait for RX data */
    while (!(spi->SR & LPSPI_SR_RDF)) {}

    /* Read received data */
    return (uint8_t)(spi->RDR & 0xFF);
}

static void mcp2515_write_register(uint8_t reg, uint8_t value) {
    cs_low();
    spi_transfer(MCP2515_WRITE);
    spi_transfer(reg);
    spi_transfer(value);
    cs_high();
}

static uint8_t mcp2515_read_register(uint8_t reg) {
    cs_low();
    spi_transfer(MCP2515_READ);
    spi_transfer(reg);
    uint8_t value = spi_transfer(0xFF);
    cs_high();
    return value;
}

static void mcp2515_modify_register(uint8_t reg, uint8_t mask, uint8_t value) {
    cs_low();
    spi_transfer(MCP2515_BIT_MODIFY);
    spi_transfer(reg);
    spi_transfer(mask);
    spi_transfer(value);
    cs_high();
}

static void mcp2515_write_registers(uint8_t reg, const uint8_t *data, uint8_t len) {
    cs_low();
    spi_transfer(MCP2515_WRITE);
    spi_transfer(reg);
    for (uint8_t i = 0; i < len; i++) {
        spi_transfer(data[i]);
    }
    cs_high();
}

static void mcp2515_read_registers(uint8_t reg, uint8_t *data, uint8_t len) {
    cs_low();
    spi_transfer(MCP2515_READ);
    spi_transfer(reg);
    for (uint8_t i = 0; i < len; i++) {
        data[i] = spi_transfer(0xFF);
    }
    cs_high();
}

/* Configuration Helper */
static void mcp2515_configure_timing(mcp2515_baud_t baud) {
    /* Timing configuration for 8MHz crystal */
    /* Formula: TQ = 2 * BRP / F_osc */
    /* Bit time = (SYNC + PROP + PS1 + PS2) * TQ */

    uint8_t cnf1, cnf2, cnf3;

    switch (baud) {
        case MCP2515_BAUD_1MBPS:
            /* BRP=0 (1x), SYNC=1TQ, PROP=1TQ, PS1=1TQ, PS2=1TQ = 4TQ total, 2Mbps/2 = 1Mbps */
            cnf1 = 0x00;  /* BRP=0, SJW=1 */
            cnf2 = 0x80;  /* BTLMODE=1, SAM=0, PHSEG1=0, PRSEG=0 */
            cnf3 = 0x00;  /* PHSEG2=0 */
            break;

        case MCP2515_BAUD_500KBPS:
            /* BRP=0 (1x), Total 8TQ = 500kbps */
            cnf1 = 0x00;  /* BRP=0, SJW=1 */
            cnf2 = 0x90;  /* BTLMODE=1, PHSEG1=1, PRSEG=0 */
            cnf3 = 0x02;  /* PHSEG2=2 */
            break;

        case MCP2515_BAUD_250KBPS:
            /* BRP=1 (2x), Total 8TQ = 250kbps */
            cnf1 = 0x01;  /* BRP=1, SJW=1 */
            cnf2 = 0x90;  /* BTLMODE=1, PHSEG1=1, PRSEG=0 */
            cnf3 = 0x02;  /* PHSEG2=2 */
            break;

        case MCP2515_BAUD_125KBPS:
        default:
            /* BRP=3 (4x), Total 8TQ = 125kbps */
            cnf1 = 0x03;  /* BRP=3, SJW=1 */
            cnf2 = 0x90;  /* BTLMODE=1, PHSEG1=1, PRSEG=0 */
            cnf3 = 0x02;  /* PHSEG2=2 */
            break;
    }

    mcp2515_write_register(MCP2515_CNF1, cnf1);
    mcp2515_write_register(MCP2515_CNF2, cnf2);
    mcp2515_write_register(MCP2515_CNF3, cnf3);
}

/* Public API Implementation */

mcp2515_status_t mcp2515_init(const mcp2515_spi_config_t *spi_config,
                               const mcp2515_config_t *config) {
    if (!spi_config || !config) {
        return MCP2515_INVALID_PARAM;
    }

    /* Initialize SPI interface */
    mcp2515_state.spi = get_lpspi_base(spi_config->spi_instance);
    if (!mcp2515_state.spi) {
        return MCP2515_INVALID_PARAM;
    }

    /* Initialize CS GPIO */
    mcp2515_state.cs_port = get_gpio_base(spi_config->cs_port);
    if (!mcp2515_state.cs_port) {
        return MCP2515_INVALID_PARAM;
    }
    mcp2515_state.cs_pin = spi_config->cs_pin;

    /* Configure CS pin as output, set high (inactive) */
    mcp2515_state.cs_port->PDDR |= (1u << mcp2515_state.cs_pin);
    cs_high();

    /* NOTE: Assumes LPSPI module is already initialized by application
     * with appropriate clock source and baud rate for MCP2515 (max 10MHz) */

    /* Reset MCP2515 */
    cs_low();
    spi_transfer(MCP2515_RESET);
    cs_high();

    /* Wait for reset to complete (typical 128 oscillator cycles) */
    for (volatile uint32_t i = 0; i < 10000; i++) {}

    /* Verify communication by reading CANSTAT */
    uint8_t canstat = mcp2515_read_register(MCP2515_CANSTAT);
    if ((canstat & CANSTAT_OPMOD_MASK) != CANCTRL_REQOP_CONFIG) {
        return MCP2515_ERROR;  /* MCP2515 should be in config mode after reset */
    }

    /* Configure timing */
    mcp2515_configure_timing(config->baud_rate);

    /* Configure RX buffers to accept all messages */
    mcp2515_write_register(MCP2515_RXB0CTRL, RXBCTRL_RXM_STD_EXT | RXBCTRL_BUKT);
    mcp2515_write_register(MCP2515_RXB1CTRL, RXBCTRL_RXM_STD_EXT);

    /* Clear all interrupt flags */
    mcp2515_write_register(MCP2515_CANINTF, 0x00);

    /* Enable interrupts if requested */
    if (config->enable_interrupts) {
        mcp2515_write_register(MCP2515_CANINTE,
            CANINTE_RX0IE | CANINTE_RX1IE | CANINTE_TX0IE | CANINTE_ERRIE);
    } else {
        mcp2515_write_register(MCP2515_CANINTE, 0x00);
    }

    /* Set operating mode */
    mcp2515_status_t status = mcp2515_set_mode(config->mode);
    if (status != MCP2515_OK) {
        return status;
    }

    /* Save configuration */
    mcp2515_state.config = *config;
    mcp2515_state.initialized = true;

    return MCP2515_OK;
}

mcp2515_status_t mcp2515_reset(void) {
    cs_low();
    spi_transfer(MCP2515_RESET);
    cs_high();

    /* Wait for reset */
    for (volatile uint32_t i = 0; i < 10000; i++) {}

    mcp2515_state.initialized = false;

    return MCP2515_OK;
}

mcp2515_status_t mcp2515_set_mode(mcp2515_mode_t mode) {
    uint8_t mode_bits;

    switch (mode) {
        case MCP2515_MODE_NORMAL:
            mode_bits = CANCTRL_REQOP_NORMAL;
            break;
        case MCP2515_MODE_SLEEP:
            mode_bits = CANCTRL_REQOP_SLEEP;
            break;
        case MCP2515_MODE_LOOPBACK:
            mode_bits = CANCTRL_REQOP_LOOPBACK;
            break;
        case MCP2515_MODE_LISTEN_ONLY:
            mode_bits = CANCTRL_REQOP_LISTENONLY;
            break;
        case MCP2515_MODE_CONFIG:
            mode_bits = CANCTRL_REQOP_CONFIG;
            break;
        default:
            return MCP2515_INVALID_PARAM;
    }

    /* Set mode */
    mcp2515_modify_register(MCP2515_CANCTRL, CANCTRL_REQOP_MASK, mode_bits);

    /* Verify mode change */
    uint32_t timeout = 10000;
    while (timeout--) {
        uint8_t canstat = mcp2515_read_register(MCP2515_CANSTAT);
        if ((canstat & CANSTAT_OPMOD_MASK) == mode_bits) {
            return MCP2515_OK;
        }
    }

    return MCP2515_TIMEOUT;
}

mcp2515_status_t mcp2515_transmit(const mcp2515_message_t *msg) {
    if (!msg || msg->dlc > 8 || !mcp2515_state.initialized) {
        return MCP2515_INVALID_PARAM;
    }

    /* Find available TX buffer */
    uint8_t tx_buf_addr = 0;
    uint8_t ctrl_reg = mcp2515_read_register(MCP2515_TXB0CTRL);

    if (!(ctrl_reg & TXBCTRL_TXREQ)) {
        tx_buf_addr = MCP2515_TXB0SIDH;
    } else {
        ctrl_reg = mcp2515_read_register(MCP2515_TXB1CTRL);
        if (!(ctrl_reg & TXBCTRL_TXREQ)) {
            tx_buf_addr = MCP2515_TXB1SIDH;
        } else {
            ctrl_reg = mcp2515_read_register(MCP2515_TXB2CTRL);
            if (!(ctrl_reg & TXBCTRL_TXREQ)) {
                tx_buf_addr = MCP2515_TXB2SIDH;
            } else {
                return MCP2515_BUSY;  /* All TX buffers busy */
            }
        }
    }

    /* Prepare TX buffer data */
    uint8_t tx_data[13];  /* SIDH, SIDL, EID8, EID0, DLC, DATA[0-7] */

    if (msg->id_type == MCP2515_ID_EXTENDED) {
        /* Extended ID (29-bit) */
        tx_data[0] = (uint8_t)(msg->id >> 21);              /* SIDH: ID[28:21] */
        tx_data[1] = (uint8_t)(((msg->id >> 13) & 0xE0) |  /* SIDL: ID[20:18] */
                               0x08 |                        /* EXIDE = 1 */
                               ((msg->id >> 16) & 0x03));    /* EID[17:16] */
        tx_data[2] = (uint8_t)(msg->id >> 8);               /* EID8: ID[15:8] */
        tx_data[3] = (uint8_t)(msg->id);                    /* EID0: ID[7:0] */
    } else {
        /* Standard ID (11-bit) */
        tx_data[0] = (uint8_t)(msg->id >> 3);               /* SIDH: ID[10:3] */
        tx_data[1] = (uint8_t)((msg->id << 5) & 0xE0);     /* SIDL: ID[2:0] */
        tx_data[2] = 0;                                      /* EID8 */
        tx_data[3] = 0;                                      /* EID0 */
    }

    /* Set DLC and RTR */
    tx_data[4] = msg->dlc & 0x0F;
    if (msg->rtr) {
        if (msg->id_type == MCP2515_ID_EXTENDED) {
            tx_data[1] |= 0x04;  /* Set RTR bit in SIDL for extended */
        } else {
            tx_data[1] |= 0x10;  /* Set RTR bit in SIDL for standard */
        }
    }

    /* Copy data bytes */
    memcpy(&tx_data[5], msg->data, 8);

    /* Write to TX buffer */
    mcp2515_write_registers(tx_buf_addr, tx_data, 13);

    /* Request transmission */
    uint8_t ctrl_addr = tx_buf_addr - 1;  /* TXBnCTRL is one address before TXBnSIDH */
    mcp2515_modify_register(ctrl_addr, TXBCTRL_TXREQ, TXBCTRL_TXREQ);

    return MCP2515_OK;
}

mcp2515_status_t mcp2515_receive(mcp2515_message_t *msg) {
    if (!msg || !mcp2515_state.initialized) {
        return MCP2515_INVALID_PARAM;
    }

    /* Check interrupt flags for received messages */
    uint8_t intf = mcp2515_read_register(MCP2515_CANINTF);

    uint8_t rx_buf_addr;
    uint8_t intf_bit;

    if (intf & CANINTF_RX0IF) {
        rx_buf_addr = MCP2515_RXB0SIDH;
        intf_bit = CANINTF_RX0IF;
    } else if (intf & CANINTF_RX1IF) {
        rx_buf_addr = MCP2515_RXB1SIDH;
        intf_bit = CANINTF_RX1IF;
    } else {
        return MCP2515_NO_MESSAGE;
    }

    /* Read RX buffer */
    uint8_t rx_data[13];  /* SIDH, SIDL, EID8, EID0, DLC, DATA[0-7] */
    mcp2515_read_registers(rx_buf_addr, rx_data, 13);

    /* Parse ID */
    uint8_t sidh = rx_data[0];
    uint8_t sidl = rx_data[1];

    if (sidl & 0x08) {
        /* Extended ID */
        msg->id_type = MCP2515_ID_EXTENDED;
        msg->id = ((uint32_t)sidh << 21) |
                  ((uint32_t)(sidl & 0xE0) << 13) |
                  ((uint32_t)(sidl & 0x03) << 16) |
                  ((uint32_t)rx_data[2] << 8) |
                  rx_data[3];
        msg->rtr = (sidl & 0x04) != 0;
    } else {
        /* Standard ID */
        msg->id_type = MCP2515_ID_STANDARD;
        msg->id = ((uint32_t)sidh << 3) | ((uint32_t)sidl >> 5);
        msg->rtr = (sidl & 0x10) != 0;
    }

    /* Parse DLC and data */
    msg->dlc = rx_data[4] & 0x0F;
    memcpy(msg->data, &rx_data[5], 8);

    /* Clear interrupt flag */
    mcp2515_modify_register(MCP2515_CANINTF, intf_bit, 0);

    return MCP2515_OK;
}

bool mcp2515_message_available(void) {
    if (!mcp2515_state.initialized) {
        return false;
    }

    uint8_t intf = mcp2515_read_register(MCP2515_CANINTF);
    return (intf & (CANINTF_RX0IF | CANINTF_RX1IF)) != 0;
}

uint8_t mcp2515_read_interrupts(void) {
    return mcp2515_read_register(MCP2515_CANINTF);
}

mcp2515_status_t mcp2515_clear_interrupts(uint8_t flags) {
    if (!mcp2515_state.initialized) {
        return MCP2515_ERROR;
    }

    mcp2515_modify_register(MCP2515_CANINTF, flags, 0);
    return MCP2515_OK;
}

uint8_t mcp2515_read_error_flags(void) {
    return mcp2515_read_register(MCP2515_EFLG);
}

uint8_t mcp2515_read_tec(void) {
    return mcp2515_read_register(MCP2515_TEC);
}

uint8_t mcp2515_read_rec(void) {
    return mcp2515_read_register(MCP2515_REC);
}
