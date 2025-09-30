/**
 * @file can.c
 * @brief FlexCAN HAL Implementation for S32K144 MCU
 */

#include "can.h"
#include <string.h>

/* FlexCAN Register Map */
typedef struct {
    volatile uint32_t MCR;              /* 0x00: Module Configuration Register */
    volatile uint32_t CTRL1;            /* 0x04: Control 1 Register */
    volatile uint32_t TIMER;            /* 0x08: Free Running Timer */
    volatile uint32_t reserved1;        /* 0x0C */
    volatile uint32_t RXMGMASK;         /* 0x10: RX Mailboxes Global Mask */
    volatile uint32_t RX14MASK;         /* 0x14: RX Buffer 14 Mask */
    volatile uint32_t RX15MASK;         /* 0x18: RX Buffer 15 Mask */
    volatile uint32_t ECR;              /* 0x1C: Error Counter */
    volatile uint32_t ESR1;             /* 0x20: Error and Status 1 */
    volatile uint32_t IMASK2;           /* 0x24: Interrupt Masks 2 */
    volatile uint32_t IMASK1;           /* 0x28: Interrupt Masks 1 */
    volatile uint32_t IFLAG2;           /* 0x2C: Interrupt Flags 2 */
    volatile uint32_t IFLAG1;           /* 0x30: Interrupt Flags 1 */
    volatile uint32_t CTRL2;            /* 0x34: Control 2 */
    volatile uint32_t ESR2;             /* 0x38: Error and Status 2 */
    volatile uint32_t reserved2[2];     /* 0x3C-0x40 */
    volatile uint32_t CRCR;             /* 0x44: CRC Register */
    volatile uint32_t RXFGMASK;         /* 0x48: RX FIFO Global Mask */
    volatile uint32_t RXFIR;            /* 0x4C: RX FIFO Information */
    volatile uint32_t reserved3[12];    /* 0x50-0x7C */
    volatile uint32_t MB[128];          /* 0x80+: Message Buffers (32 MBs x 4 words each) */
} FlexCAN_Type;

/* Message Buffer Structure (4 words = 16 bytes per MB) */
typedef struct {
    volatile uint32_t CS;               /* Control/Status word */
    volatile uint32_t ID;               /* ID word */
    volatile uint32_t DATA[2];          /* Data words (8 bytes) */
} flexcan_mb_t;

/* MCR Register Bits */
#define CAN_MCR_MDIS        (1u << 31)  /* Module Disable */
#define CAN_MCR_FRZ         (1u << 30)  /* Freeze Enable */
#define CAN_MCR_RFEN        (1u << 29)  /* RX FIFO Enable */
#define CAN_MCR_HALT        (1u << 28)  /* Halt FlexCAN */
#define CAN_MCR_NOTRDY      (1u << 27)  /* FlexCAN Not Ready */
#define CAN_MCR_SOFTRST     (1u << 25)  /* Soft Reset */
#define CAN_MCR_FRZACK      (1u << 24)  /* Freeze Acknowledge */
#define CAN_MCR_SUPV        (1u << 23)  /* Supervisor Mode */
#define CAN_MCR_WRNEN       (1u << 21)  /* Warning Interrupt Enable */
#define CAN_MCR_LPMACK      (1u << 20)  /* Low Power Mode Acknowledge */
#define CAN_MCR_SRXDIS      (1u << 17)  /* Self Reception Disable */
#define CAN_MCR_IRMQ        (1u << 16)  /* Individual RX Masking */
#define CAN_MCR_MAXMB_MASK  (0x7Fu)     /* Number of last MB */

/* CTRL1 Register Bits */
#define CAN_CTRL1_PRESDIV_SHIFT (24u)
#define CAN_CTRL1_PRESDIV_MASK  (0xFFu << 24)
#define CAN_CTRL1_RJW_SHIFT     (22u)
#define CAN_CTRL1_RJW_MASK      (0x3u << 22)
#define CAN_CTRL1_PSEG1_SHIFT   (19u)
#define CAN_CTRL1_PSEG1_MASK    (0x7u << 19)
#define CAN_CTRL1_PSEG2_SHIFT   (16u)
#define CAN_CTRL1_PSEG2_MASK    (0x7u << 16)
#define CAN_CTRL1_BOFFMSK       (1u << 15)
#define CAN_CTRL1_ERRMSK        (1u << 14)
#define CAN_CTRL1_LPB           (1u << 12)  /* Loopback Mode */
#define CAN_CTRL1_LOM           (1u << 3)   /* Listen-Only Mode */
#define CAN_CTRL1_PROPSEG_SHIFT (0u)
#define CAN_CTRL1_PROPSEG_MASK  (0x7u)

/* Message Buffer CS Field Bits */
#define CAN_CS_CODE_SHIFT       (24u)
#define CAN_CS_CODE_MASK        (0xFu << 24)
#define CAN_CS_SRR              (1u << 22)  /* Substitute Remote Request */
#define CAN_CS_IDE              (1u << 21)  /* ID Extended */
#define CAN_CS_RTR              (1u << 20)  /* Remote Transmission Request */
#define CAN_CS_DLC_SHIFT        (16u)
#define CAN_CS_DLC_MASK         (0xFu << 16)
#define CAN_CS_TIMESTAMP_MASK   (0xFFFFu)

/* Message Buffer Code Values */
#define CAN_CODE_TX_INACTIVE    (0x8u)
#define CAN_CODE_TX_ABORT       (0x9u)
#define CAN_CODE_TX_DATA        (0xCu)
#define CAN_CODE_TX_TANSWER     (0xEu)
#define CAN_CODE_RX_INACTIVE    (0x0u)
#define CAN_CODE_RX_EMPTY       (0x4u)
#define CAN_CODE_RX_FULL        (0x2u)
#define CAN_CODE_RX_OVERRUN     (0x6u)
#define CAN_CODE_RX_BUSY        (0x1u)

/* ID Field Bits */
#define CAN_ID_STD_SHIFT        (18u)
#define CAN_ID_EXT_MASK         (0x1FFFFFFFu)

/* J1939 ID Format */
#define J1939_PRIORITY_SHIFT    (26u)
#define J1939_PGN_SHIFT         (8u)
#define J1939_SA_SHIFT          (0u)
#define J1939_PF_SHIFT          (16u)
#define J1939_PS_SHIFT          (8u)

/* Module State */
typedef struct {
    bool initialized;
    can_config_t config;
    uint8_t next_tx_mb;
} can_module_state_t;

static can_module_state_t can_state[3] = {0};

/* Helper Functions */
static inline FlexCAN_Type* can_get_base(can_instance_t instance) {
    switch (instance) {
        case CAN_INSTANCE_0: return (FlexCAN_Type*)CAN0_BASE;
        case CAN_INSTANCE_1: return (FlexCAN_Type*)CAN1_BASE;
        case CAN_INSTANCE_2: return (FlexCAN_Type*)CAN2_BASE;
        default: return NULL;
    }
}

static inline flexcan_mb_t* can_get_mb(FlexCAN_Type *base, uint8_t mb_idx) {
    return (flexcan_mb_t*)&base->MB[mb_idx * 4];
}

static can_status_t can_enter_freeze_mode(FlexCAN_Type *base) {
    uint32_t timeout = 10000;

    base->MCR |= CAN_MCR_FRZ | CAN_MCR_HALT;

    while (!(base->MCR & CAN_MCR_FRZACK) && timeout--) {
        /* Wait for freeze acknowledge */
    }

    return (timeout > 0) ? CAN_STATUS_SUCCESS : CAN_STATUS_TIMEOUT;
}

static can_status_t can_exit_freeze_mode(FlexCAN_Type *base) {
    uint32_t timeout = 10000;

    base->MCR &= ~(CAN_MCR_FRZ | CAN_MCR_HALT);

    while ((base->MCR & CAN_MCR_FRZACK) && timeout--) {
        /* Wait for freeze mode exit */
    }

    return (timeout > 0) ? CAN_STATUS_SUCCESS : CAN_STATUS_TIMEOUT;
}

can_status_t can_init(const can_config_t *config) {
    if (!config || config->instance > CAN_INSTANCE_2) {
        return CAN_STATUS_INVALID_PARAM;
    }

    FlexCAN_Type *base = can_get_base(config->instance);
    if (!base) {
        return CAN_STATUS_INVALID_PARAM;
    }

    /* Enable CAN module clock (assumes clock gating is handled externally) */

    /* Enable module */
    base->MCR &= ~CAN_MCR_MDIS;

    /* Wait for module ready */
    uint32_t timeout = 10000;
    while ((base->MCR & CAN_MCR_LPMACK) && timeout--) {}
    if (timeout == 0) return CAN_STATUS_TIMEOUT;

    /* Soft reset */
    base->MCR |= CAN_MCR_SOFTRST;
    timeout = 10000;
    while ((base->MCR & CAN_MCR_SOFTRST) && timeout--) {}
    if (timeout == 0) return CAN_STATUS_TIMEOUT;

    /* Enter freeze mode for configuration */
    if (can_enter_freeze_mode(base) != CAN_STATUS_SUCCESS) {
        return CAN_STATUS_TIMEOUT;
    }

    /* Configure MCR */
    uint32_t mcr = base->MCR;
    mcr &= ~CAN_MCR_MAXMB_MASK;
    mcr |= (config->num_tx_mb + config->num_rx_mb - 1) & CAN_MCR_MAXMB_MASK;
    mcr |= CAN_MCR_SRXDIS;  /* Disable self-reception */
    mcr |= CAN_MCR_IRMQ;    /* Enable individual RX masking */

    if (config->enable_fifo) {
        mcr |= CAN_MCR_RFEN;
    } else {
        mcr &= ~CAN_MCR_RFEN;
    }

    base->MCR = mcr;

    /* Configure timing (CTRL1) */
    uint32_t ctrl1 = 0;
    ctrl1 |= ((config->timing.presdiv - 1) << CAN_CTRL1_PRESDIV_SHIFT) & CAN_CTRL1_PRESDIV_MASK;
    ctrl1 |= (config->timing.rjw << CAN_CTRL1_RJW_SHIFT) & CAN_CTRL1_RJW_MASK;
    ctrl1 |= (config->timing.pseg1 << CAN_CTRL1_PSEG1_SHIFT) & CAN_CTRL1_PSEG1_MASK;
    ctrl1 |= (config->timing.pseg2 << CAN_CTRL1_PSEG2_SHIFT) & CAN_CTRL1_PSEG2_MASK;
    ctrl1 |= (config->timing.propseg << CAN_CTRL1_PROPSEG_SHIFT) & CAN_CTRL1_PROPSEG_MASK;

    /* Configure operating mode */
    if (config->mode == CAN_MODE_LISTEN_ONLY) {
        ctrl1 |= CAN_CTRL1_LOM;
    } else if (config->mode == CAN_MODE_LOOPBACK) {
        ctrl1 |= CAN_CTRL1_LPB;
    }

    base->CTRL1 = ctrl1;

    /* Initialize RX mask (accept all messages by default) */
    base->RXMGMASK = 0;
    base->RX14MASK = 0;
    base->RX15MASK = 0;
    base->RXFGMASK = 0;

    /* Initialize mailboxes - TX mailboxes first */
    for (uint8_t i = 0; i < config->num_tx_mb; i++) {
        flexcan_mb_t *mb = can_get_mb(base, i);
        mb->CS = (CAN_CODE_TX_INACTIVE << CAN_CS_CODE_SHIFT);
        mb->ID = 0;
        mb->DATA[0] = 0;
        mb->DATA[1] = 0;
    }

    /* Initialize RX mailboxes */
    for (uint8_t i = config->num_tx_mb; i < (config->num_tx_mb + config->num_rx_mb); i++) {
        flexcan_mb_t *mb = can_get_mb(base, i);
        mb->CS = (CAN_CODE_RX_EMPTY << CAN_CS_CODE_SHIFT);
        mb->ID = 0;
        mb->DATA[0] = 0;
        mb->DATA[1] = 0;
    }

    /* Exit freeze mode */
    if (can_exit_freeze_mode(base) != CAN_STATUS_SUCCESS) {
        return CAN_STATUS_TIMEOUT;
    }

    /* Save state */
    can_state[config->instance].initialized = true;
    can_state[config->instance].config = *config;
    can_state[config->instance].next_tx_mb = 0;

    return CAN_STATUS_SUCCESS;
}

can_status_t can_deinit(can_instance_t instance) {
    if (instance > CAN_INSTANCE_2) {
        return CAN_STATUS_INVALID_PARAM;
    }

    FlexCAN_Type *base = can_get_base(instance);
    if (!base) {
        return CAN_STATUS_INVALID_PARAM;
    }

    /* Disable module */
    base->MCR |= CAN_MCR_MDIS;

    can_state[instance].initialized = false;

    return CAN_STATUS_SUCCESS;
}

can_status_t can_update_baudrate(can_instance_t instance, const can_timing_config_t *timing) {
    if (instance > CAN_INSTANCE_2 || !timing) {
        return CAN_STATUS_INVALID_PARAM;
    }

    if (!can_state[instance].initialized) {
        return CAN_STATUS_ERROR;
    }

    FlexCAN_Type *base = can_get_base(instance);

    /* Enter freeze mode */
    if (can_enter_freeze_mode(base) != CAN_STATUS_SUCCESS) {
        return CAN_STATUS_TIMEOUT;
    }

    /* Update timing */
    uint32_t ctrl1 = base->CTRL1;
    ctrl1 &= ~(CAN_CTRL1_PRESDIV_MASK | CAN_CTRL1_RJW_MASK |
               CAN_CTRL1_PSEG1_MASK | CAN_CTRL1_PSEG2_MASK |
               CAN_CTRL1_PROPSEG_MASK);

    ctrl1 |= ((timing->presdiv - 1) << CAN_CTRL1_PRESDIV_SHIFT) & CAN_CTRL1_PRESDIV_MASK;
    ctrl1 |= (timing->rjw << CAN_CTRL1_RJW_SHIFT) & CAN_CTRL1_RJW_MASK;
    ctrl1 |= (timing->pseg1 << CAN_CTRL1_PSEG1_SHIFT) & CAN_CTRL1_PSEG1_MASK;
    ctrl1 |= (timing->pseg2 << CAN_CTRL1_PSEG2_SHIFT) & CAN_CTRL1_PSEG2_MASK;
    ctrl1 |= (timing->propseg << CAN_CTRL1_PROPSEG_SHIFT) & CAN_CTRL1_PROPSEG_MASK;

    base->CTRL1 = ctrl1;

    /* Exit freeze mode */
    if (can_exit_freeze_mode(base) != CAN_STATUS_SUCCESS) {
        return CAN_STATUS_TIMEOUT;
    }

    can_state[instance].config.timing = *timing;

    return CAN_STATUS_SUCCESS;
}

can_status_t can_set_mode(can_instance_t instance, can_mode_t mode) {
    if (instance > CAN_INSTANCE_2) {
        return CAN_STATUS_INVALID_PARAM;
    }

    if (!can_state[instance].initialized) {
        return CAN_STATUS_ERROR;
    }

    FlexCAN_Type *base = can_get_base(instance);

    /* Enter freeze mode */
    if (can_enter_freeze_mode(base) != CAN_STATUS_SUCCESS) {
        return CAN_STATUS_TIMEOUT;
    }

    /* Update mode */
    uint32_t ctrl1 = base->CTRL1;
    ctrl1 &= ~(CAN_CTRL1_LOM | CAN_CTRL1_LPB);

    if (mode == CAN_MODE_LISTEN_ONLY) {
        ctrl1 |= CAN_CTRL1_LOM;
    } else if (mode == CAN_MODE_LOOPBACK) {
        ctrl1 |= CAN_CTRL1_LPB;
    }

    base->CTRL1 = ctrl1;

    /* Exit freeze mode */
    if (can_exit_freeze_mode(base) != CAN_STATUS_SUCCESS) {
        return CAN_STATUS_TIMEOUT;
    }

    can_state[instance].config.mode = mode;

    return CAN_STATUS_SUCCESS;
}

can_status_t can_transmit(can_instance_t instance, const can_message_t *msg) {
    if (instance > CAN_INSTANCE_2 || !msg || msg->dlc > 8) {
        return CAN_STATUS_INVALID_PARAM;
    }

    if (!can_state[instance].initialized) {
        return CAN_STATUS_ERROR;
    }

    FlexCAN_Type *base = can_get_base(instance);
    can_module_state_t *state = &can_state[instance];

    /* Find available TX mailbox */
    uint8_t mb_idx = 0xFF;
    for (uint8_t i = 0; i < state->config.num_tx_mb; i++) {
        flexcan_mb_t *mb = can_get_mb(base, i);
        uint32_t code = (mb->CS >> CAN_CS_CODE_SHIFT) & 0xF;
        if (code == CAN_CODE_TX_INACTIVE) {
            mb_idx = i;
            break;
        }
    }

    if (mb_idx == 0xFF) {
        return CAN_STATUS_BUSY;  /* No TX mailbox available */
    }

    flexcan_mb_t *mb = can_get_mb(base, mb_idx);

    /* Prepare message buffer */
    uint32_t cs = (CAN_CODE_TX_DATA << CAN_CS_CODE_SHIFT);
    cs |= (msg->dlc << CAN_CS_DLC_SHIFT) & CAN_CS_DLC_MASK;

    uint32_t id;
    if (msg->id_type == CAN_ID_EXTENDED) {
        cs |= CAN_CS_IDE | CAN_CS_SRR;
        id = msg->id & CAN_ID_EXT_MASK;
    } else {
        id = (msg->id << CAN_ID_STD_SHIFT);
    }

    /* Write data */
    uint32_t data_h = ((uint32_t)msg->data[0] << 24) | ((uint32_t)msg->data[1] << 16) |
                      ((uint32_t)msg->data[2] << 8) | msg->data[3];
    uint32_t data_l = ((uint32_t)msg->data[4] << 24) | ((uint32_t)msg->data[5] << 16) |
                      ((uint32_t)msg->data[6] << 8) | msg->data[7];

    mb->DATA[0] = data_h;
    mb->DATA[1] = data_l;
    mb->ID = id;
    mb->CS = cs;  /* Triggers transmission */

    return CAN_STATUS_SUCCESS;
}

can_status_t can_receive(can_instance_t instance, can_message_t *msg) {
    if (instance > CAN_INSTANCE_2 || !msg) {
        return CAN_STATUS_INVALID_PARAM;
    }

    if (!can_state[instance].initialized) {
        return CAN_STATUS_ERROR;
    }

    FlexCAN_Type *base = can_get_base(instance);
    can_module_state_t *state = &can_state[instance];

    /* Search for RX mailbox with message */
    for (uint8_t i = state->config.num_tx_mb;
         i < (state->config.num_tx_mb + state->config.num_rx_mb); i++) {

        flexcan_mb_t *mb = can_get_mb(base, i);
        uint32_t cs = mb->CS;
        uint32_t code = (cs >> CAN_CS_CODE_SHIFT) & 0xF;

        if (code == CAN_CODE_RX_FULL || code == CAN_CODE_RX_OVERRUN) {
            /* Read message */
            uint32_t id = mb->ID;
            uint32_t data_h = mb->DATA[0];
            uint32_t data_l = mb->DATA[1];

            /* Lock mailbox by reading control word */
            uint32_t timer = base->TIMER;
            (void)timer;  /* Unlock mailbox */

            /* Parse message */
            msg->dlc = (cs >> CAN_CS_DLC_SHIFT) & 0xF;
            msg->timestamp = cs & CAN_CS_TIMESTAMP_MASK;

            if (cs & CAN_CS_IDE) {
                msg->id_type = CAN_ID_EXTENDED;
                msg->id = id & CAN_ID_EXT_MASK;
            } else {
                msg->id_type = CAN_ID_STANDARD;
                msg->id = (id >> CAN_ID_STD_SHIFT) & 0x7FF;
            }

            msg->data[0] = (data_h >> 24) & 0xFF;
            msg->data[1] = (data_h >> 16) & 0xFF;
            msg->data[2] = (data_h >> 8) & 0xFF;
            msg->data[3] = data_h & 0xFF;
            msg->data[4] = (data_l >> 24) & 0xFF;
            msg->data[5] = (data_l >> 16) & 0xFF;
            msg->data[6] = (data_l >> 8) & 0xFF;
            msg->data[7] = data_l & 0xFF;

            /* Clear mailbox */
            mb->CS = (CAN_CODE_RX_EMPTY << CAN_CS_CODE_SHIFT);

            return CAN_STATUS_SUCCESS;
        }
    }

    return CAN_STATUS_NO_MESSAGE;
}

can_tx_status_t can_get_tx_status(can_instance_t instance, uint8_t mailbox) {
    if (instance > CAN_INSTANCE_2 || !can_state[instance].initialized) {
        return CAN_TX_ERROR;
    }

    if (mailbox >= can_state[instance].config.num_tx_mb) {
        return CAN_TX_ERROR;
    }

    FlexCAN_Type *base = can_get_base(instance);
    flexcan_mb_t *mb = can_get_mb(base, mailbox);

    uint32_t code = (mb->CS >> CAN_CS_CODE_SHIFT) & 0xF;

    switch (code) {
        case CAN_CODE_TX_INACTIVE:
            return CAN_TX_IDLE;
        case CAN_CODE_TX_DATA:
        case CAN_CODE_TX_TANSWER:
            return CAN_TX_BUSY;
        default:
            return CAN_TX_COMPLETE;
    }
}

can_status_t can_abort_tx(can_instance_t instance, uint8_t mailbox) {
    if (instance > CAN_INSTANCE_2 || !can_state[instance].initialized) {
        return CAN_STATUS_ERROR;
    }

    if (mailbox >= can_state[instance].config.num_tx_mb) {
        return CAN_STATUS_INVALID_PARAM;
    }

    FlexCAN_Type *base = can_get_base(instance);
    flexcan_mb_t *mb = can_get_mb(base, mailbox);

    mb->CS = (CAN_CODE_TX_ABORT << CAN_CS_CODE_SHIFT);

    return CAN_STATUS_SUCCESS;
}

can_status_t can_j1939_transmit(can_instance_t instance, const can_j1939_message_t *msg) {
    if (!msg || msg->priority > 7 || msg->dlc > 8) {
        return CAN_STATUS_INVALID_PARAM;
    }

    /* Build J1939 extended ID: [Priority(3) | Reserved(1) | DP(1) | PF(8) | PS(8) | SA(8)] */
    uint32_t pf = (msg->pgn >> 8) & 0xFF;
    uint32_t ps = msg->pgn & 0xFF;
    uint32_t dp = (msg->pgn >> 16) & 0x1;

    uint32_t id = ((uint32_t)msg->priority << J1939_PRIORITY_SHIFT) |
                  (dp << 24) |
                  (pf << J1939_PF_SHIFT) |
                  (ps << J1939_PS_SHIFT) |
                  msg->source_addr;

    can_message_t can_msg = {
        .id = id,
        .id_type = CAN_ID_EXTENDED,
        .dlc = msg->dlc
    };

    memcpy(can_msg.data, msg->data, 8);

    return can_transmit(instance, &can_msg);
}

can_status_t can_j1939_receive(can_instance_t instance, can_j1939_message_t *msg) {
    if (!msg) {
        return CAN_STATUS_INVALID_PARAM;
    }

    can_message_t can_msg;
    can_status_t status = can_receive(instance, &can_msg);

    if (status != CAN_STATUS_SUCCESS) {
        return status;
    }

    if (can_msg.id_type != CAN_ID_EXTENDED) {
        return CAN_STATUS_ERROR;  /* J1939 requires extended ID */
    }

    /* Parse J1939 ID */
    msg->priority = (can_msg.id >> J1939_PRIORITY_SHIFT) & 0x7;
    msg->source_addr = can_msg.id & 0xFF;

    uint8_t pf = (can_msg.id >> J1939_PF_SHIFT) & 0xFF;
    uint8_t ps = (can_msg.id >> J1939_PS_SHIFT) & 0xFF;
    uint8_t dp = (can_msg.id >> 24) & 0x1;

    msg->pgn = (dp << 16) | (pf << 8);

    /* PDU1 format (PF < 240): PS is destination address */
    /* PDU2 format (PF >= 240): PS is group extension */
    if (pf < 240) {
        msg->dest_addr = ps;
    } else {
        msg->dest_addr = 0xFF;  /* Broadcast */
        msg->pgn |= ps;
    }

    msg->dlc = can_msg.dlc;
    msg->timestamp = can_msg.timestamp;
    memcpy(msg->data, can_msg.data, 8);

    return CAN_STATUS_SUCCESS;
}

can_status_t can_calculate_timing(uint32_t peripheral_clk_hz, uint32_t baudrate,
                                   can_timing_config_t *timing) {
    if (!timing || baudrate == 0 || peripheral_clk_hz == 0) {
        return CAN_STATUS_INVALID_PARAM;
    }

    /* Target: 80% sample point, 16 time quanta per bit */
    const uint32_t tq_per_bit = 16;
    uint32_t prescaler = peripheral_clk_hz / (baudrate * tq_per_bit);

    if (prescaler == 0 || prescaler > 256) {
        return CAN_STATUS_INVALID_PARAM;
    }

    /* Time quantum distribution: SYNC(1) + PROP + PSEG1 + PSEG2 = 16 */
    /* Sample point at 80%: SYNC(1) + PROP(3) + PSEG1(8) = 12, PSEG2 = 4 */
    timing->baudrate = baudrate;
    timing->presdiv = prescaler;
    timing->propseg = 2;  /* PROPSEG = 3 TQ (value + 1) */
    timing->pseg1 = 7;    /* PSEG1 = 8 TQ (value + 1) */
    timing->pseg2 = 3;    /* PSEG2 = 4 TQ (value + 1) */
    timing->rjw = 3;      /* RJW = 4 TQ (value + 1) */

    return CAN_STATUS_SUCCESS;
}