/**
 * @file can.h
 * @brief FlexCAN HAL for S32K144 MCU
 *
 * Non-blocking CAN driver supporting:
 * - Standard (11-bit) and Extended (29-bit) identifiers
 * - Runtime configuration updates (baud rate, listen-only mode)
 * - Optional J1939 support
 */

#ifndef CAN_H
#define CAN_H

#include <stdint.h>
#include <stdbool.h>

/* FlexCAN Base Addresses */
#define CAN0_BASE 0x40024000u
#define CAN1_BASE 0x40025000u
#define CAN2_BASE 0x4002B000u

/* CAN Instance Selection */
typedef enum {
    CAN_INSTANCE_0 = 0,
    CAN_INSTANCE_1 = 1,
    CAN_INSTANCE_2 = 2
} can_instance_t;

/* CAN ID Type */
typedef enum {
    CAN_ID_STANDARD = 0,  /* 11-bit ID */
    CAN_ID_EXTENDED = 1   /* 29-bit ID */
} can_id_type_t;

/* CAN Operating Mode */
typedef enum {
    CAN_MODE_NORMAL = 0,
    CAN_MODE_LISTEN_ONLY = 1,
    CAN_MODE_LOOPBACK = 2
} can_mode_t;

/* CAN Message Structure */
typedef struct {
    uint32_t id;                /* CAN identifier (11 or 29 bits) */
    can_id_type_t id_type;      /* Standard or Extended */
    uint8_t dlc;                /* Data length code (0-8) */
    uint8_t data[8];            /* Message data */
    uint32_t timestamp;         /* RX timestamp (optional) */
} can_message_t;

/* J1939 Message Structure */
typedef struct {
    uint8_t priority;           /* Priority (0-7) */
    uint32_t pgn;               /* Parameter Group Number (0-0x3FFFF) */
    uint8_t source_addr;        /* Source address (0-255) */
    uint8_t dest_addr;          /* Destination address (0-255, 0xFF=broadcast) */
    uint8_t dlc;                /* Data length code (0-8) */
    uint8_t data[8];            /* Message data */
    uint32_t timestamp;         /* RX timestamp (optional) */
} can_j1939_message_t;

/* CAN Timing Configuration */
typedef struct {
    uint32_t baudrate;          /* Desired baud rate (e.g., 500000 for 500kbps) */
    uint8_t presdiv;            /* Prescaler division factor (1-256) */
    uint8_t propseg;            /* Propagation segment (0-7) */
    uint8_t pseg1;              /* Phase segment 1 (0-7) */
    uint8_t pseg2;              /* Phase segment 2 (1-7) */
    uint8_t rjw;                /* Resync jump width (0-3) */
} can_timing_config_t;

/* CAN Configuration Structure */
typedef struct {
    can_instance_t instance;    /* CAN instance (0, 1, or 2) */
    can_timing_config_t timing; /* Timing parameters */
    can_mode_t mode;            /* Operating mode */
    uint8_t num_tx_mb;          /* Number of TX mailboxes (1-32) */
    uint8_t num_rx_mb;          /* Number of RX mailboxes (1-32) */
    bool enable_fifo;           /* Enable RX FIFO */
} can_config_t;

/* CAN Status */
typedef enum {
    CAN_STATUS_SUCCESS = 0,
    CAN_STATUS_ERROR = -1,
    CAN_STATUS_BUSY = -2,
    CAN_STATUS_TIMEOUT = -3,
    CAN_STATUS_NO_MESSAGE = -4,
    CAN_STATUS_INVALID_PARAM = -5
} can_status_t;

/* CAN TX Status */
typedef enum {
    CAN_TX_IDLE = 0,
    CAN_TX_BUSY = 1,
    CAN_TX_COMPLETE = 2,
    CAN_TX_ERROR = 3
} can_tx_status_t;

/**
 * @brief Initialize CAN module
 *
 * @param config Pointer to CAN configuration structure
 * @return can_status_t Status of initialization
 */
can_status_t can_init(const can_config_t *config);

/**
 * @brief Deinitialize CAN module
 *
 * @param instance CAN instance to deinitialize
 * @return can_status_t Status of deinitialization
 */
can_status_t can_deinit(can_instance_t instance);

/**
 * @brief Update CAN baud rate (runtime reconfiguration)
 *
 * @param instance CAN instance
 * @param timing New timing configuration
 * @return can_status_t Status of operation
 */
can_status_t can_update_baudrate(can_instance_t instance, const can_timing_config_t *timing);

/**
 * @brief Update CAN operating mode
 *
 * @param instance CAN instance
 * @param mode New operating mode
 * @return can_status_t Status of operation
 */
can_status_t can_set_mode(can_instance_t instance, can_mode_t mode);

/**
 * @brief Transmit CAN message (non-blocking)
 *
 * @param instance CAN instance
 * @param msg Pointer to message to transmit
 * @return can_status_t Status of transmission request
 *         CAN_STATUS_SUCCESS if message queued successfully
 *         CAN_STATUS_BUSY if no TX mailbox available
 */
can_status_t can_transmit(can_instance_t instance, const can_message_t *msg);

/**
 * @brief Receive CAN message (non-blocking)
 *
 * @param instance CAN instance
 * @param msg Pointer to store received message
 * @return can_status_t Status of reception
 *         CAN_STATUS_SUCCESS if message received
 *         CAN_STATUS_NO_MESSAGE if no message available
 */
can_status_t can_receive(can_instance_t instance, can_message_t *msg);

/**
 * @brief Check TX mailbox status
 *
 * @param instance CAN instance
 * @param mailbox Mailbox number
 * @return can_tx_status_t Current status of TX mailbox
 */
can_tx_status_t can_get_tx_status(can_instance_t instance, uint8_t mailbox);

/**
 * @brief Abort pending transmission
 *
 * @param instance CAN instance
 * @param mailbox Mailbox number
 * @return can_status_t Status of abort operation
 */
can_status_t can_abort_tx(can_instance_t instance, uint8_t mailbox);

/* J1939 Specific Functions */

/**
 * @brief Transmit J1939 message (non-blocking)
 *
 * Converts J1939 message to CAN extended ID format:
 * [Priority(3) | Reserved(1) | DP(1) | PF(8) | PS(8) | SA(8)]
 *
 * @param instance CAN instance
 * @param msg Pointer to J1939 message to transmit
 * @return can_status_t Status of transmission request
 */
can_status_t can_j1939_transmit(can_instance_t instance, const can_j1939_message_t *msg);

/**
 * @brief Receive J1939 message (non-blocking)
 *
 * Parses CAN extended ID into J1939 format
 *
 * @param instance CAN instance
 * @param msg Pointer to store received J1939 message
 * @return can_status_t Status of reception
 */
can_status_t can_j1939_receive(can_instance_t instance, can_j1939_message_t *msg);

/**
 * @brief Calculate CAN timing parameters for given baud rate
 *
 * Helper function to automatically calculate timing parameters
 * based on peripheral clock and desired baud rate
 *
 * @param peripheral_clk_hz Peripheral clock frequency in Hz
 * @param baudrate Desired baud rate in bps
 * @param timing Pointer to store calculated timing parameters
 * @return can_status_t Status of calculation
 */
can_status_t can_calculate_timing(uint32_t peripheral_clk_hz, uint32_t baudrate, can_timing_config_t *timing);

#endif /* CAN_H */