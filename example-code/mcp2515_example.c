/**
 * @file mcp2515_example.c
 * @brief Example application using MCP2515 CAN controller with S32K144
 *
 * This example demonstrates:
 * - Initializing MCP2515 via SPI
 * - Sending CAN messages with standard and extended IDs
 * - Receiving and processing CAN messages
 * - Error monitoring
 *
 * Hardware Setup:
 * - MCP2515 connected to S32K144 via LPSPI0
 * - CS: PTB0 (GPIO)
 * - SCK: PTB2 (LPSPI0_SCK)
 * - MOSI: PTB3 (LPSPI0_MOSI)
 * - MISO: PTB4 (LPSPI0_MISO)
 * - 8MHz crystal on MCP2515
 * - CAN transceiver (e.g., TJA1050) connected to MCP2515 CANH/CANL
 */

#include "mcp2515.h"
#include <stdio.h>
#include <string.h>

/* S32K144 PCC Register for clock gating */
#define PCC_BASE                0x40065000u
#define PCC_LPSPI0_OFFSET       0xB0
#define PCC_PORTB_OFFSET        0x128
#define PCC_CGC                 (1u << 30)

/* S32K144 PORT Mux Configuration */
#define PORT_BASE               0x4004A000u
#define PORTB_PCR2_OFFSET       0x1008  /* LPSPI0_SCK */
#define PORTB_PCR3_OFFSET       0x100C  /* LPSPI0_MOSI */
#define PORTB_PCR4_OFFSET       0x1010  /* LPSPI0_MISO */
#define PORT_MUX_ALT3           0x300   /* ALT3 function */
#define PORT_MUX_GPIO           0x100   /* GPIO function */

/* Simple delay function */
static void delay_ms(uint32_t ms) {
    /* Assuming 80MHz core clock */
    for (volatile uint32_t i = 0; i < ms * 10000; i++) {}
}

/* Initialize S32K144 peripherals for MCP2515 */
static void hardware_init(void) {
    volatile uint32_t *pcc = (volatile uint32_t*)PCC_BASE;
    volatile uint32_t *portb = (volatile uint32_t*)PORT_BASE;

    /* Enable clocks for LPSPI0 and PORTB */
    pcc[PCC_LPSPI0_OFFSET / 4] = PCC_CGC;
    pcc[PCC_PORTB_OFFSET / 4] = PCC_CGC;

    /* Configure PORTB pins for LPSPI0 */
    portb[PORTB_PCR2_OFFSET / 4] = PORT_MUX_ALT3;  /* SCK */
    portb[PORTB_PCR3_OFFSET / 4] = PORT_MUX_ALT3;  /* MOSI */
    portb[PORTB_PCR4_OFFSET / 4] = PORT_MUX_ALT3;  /* MISO */

    /* Configure PTB0 as GPIO for CS */
    portb[0x1000 / 4] = PORT_MUX_GPIO;

    /* Initialize LPSPI0 */
    typedef struct {
        volatile uint32_t VERID;
        volatile uint32_t PARAM;
        uint32_t reserved1[2];
        volatile uint32_t CR;
        volatile uint32_t SR;
        volatile uint32_t IER;
        volatile uint32_t DER;
        volatile uint32_t CFGR0;
        volatile uint32_t CFGR1;
        uint32_t reserved2[2];
        volatile uint32_t DMR0;
        volatile uint32_t DMR1;
        uint32_t reserved3[2];
        volatile uint32_t CCR;
    } LPSPI_Init_Type;

    LPSPI_Init_Type *lpspi0 = (LPSPI_Init_Type*)0x4002C000u;

    /* Reset and disable module */
    lpspi0->CR = 0x02;  /* Software reset */
    lpspi0->CR = 0x00;  /* Clear reset */

    /* Configure LPSPI0:
     * - Master mode
     * - 8-bit frames
     * - CPOL=0, CPHA=0 (MCP2515 SPI mode 0,0)
     * - 1 MHz SPI clock (safe for 8MHz MCP2515)
     */
    lpspi0->CFGR1 = 0x00000001;  /* Master mode */
    lpspi0->CCR = 0x0F0F0F0F;    /* Prescaler for ~1MHz from 40MHz functional clock */

    /* Enable module */
    lpspi0->CR = 0x01;
}

/* Print CAN message to console */
static void print_message(const mcp2515_message_t *msg, const char *direction) {
    printf("%s CAN Message:\n", direction);
    printf("  ID: 0x%08X (%s)\n", (unsigned int)msg->id,
           msg->id_type == MCP2515_ID_STANDARD ? "STD" : "EXT");
    printf("  DLC: %u\n", msg->dlc);
    printf("  Data: ");
    for (uint8_t i = 0; i < msg->dlc; i++) {
        printf("%02X ", msg->data[i]);
    }
    printf("\n");
    if (msg->rtr) {
        printf("  [Remote Frame]\n");
    }
    printf("\n");
}

int main(void) {
    printf("=== MCP2515 CAN Controller Example ===\n\n");

    /* Initialize hardware */
    printf("Initializing hardware...\n");
    hardware_init();
    delay_ms(100);

    /* Configure MCP2515 SPI interface */
    mcp2515_spi_config_t spi_config = {
        .spi_instance = 0,      /* LPSPI0 */
        .cs_port = 1,           /* PORTB */
        .cs_pin = 0             /* Pin 0 */
    };

    /* Configure MCP2515 CAN parameters */
    mcp2515_config_t can_config = {
        .baud_rate = MCP2515_BAUD_500KBPS,
        .mode = MCP2515_MODE_NORMAL,
        .enable_interrupts = false,  /* Using polling for this example */
        .rx_mask_0 = 0x00,           /* Accept all messages */
        .rx_mask_1 = 0x00
    };

    /* Initialize MCP2515 */
    printf("Initializing MCP2515...\n");
    mcp2515_status_t status = mcp2515_init(&spi_config, &can_config);

    if (status != MCP2515_OK) {
        printf("ERROR: MCP2515 initialization failed (status=%d)\n", status);
        while (1) {}
    }

    printf("MCP2515 initialized successfully!\n");
    printf("CAN bus speed: 500 kbps\n");
    printf("Mode: Normal\n\n");

    /* Example 1: Send standard ID message */
    printf("Example 1: Sending standard ID message...\n");
    mcp2515_message_t tx_msg = {
        .id = 0x123,
        .id_type = MCP2515_ID_STANDARD,
        .rtr = false,
        .dlc = 8,
        .data = {0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08}
    };

    status = mcp2515_transmit(&tx_msg);
    if (status == MCP2515_OK) {
        print_message(&tx_msg, "TX");
    } else {
        printf("ERROR: Transmission failed (status=%d)\n\n", status);
    }

    delay_ms(100);

    /* Example 2: Send extended ID message */
    printf("Example 2: Sending extended ID message...\n");
    tx_msg.id = 0x18FEF100;
    tx_msg.id_type = MCP2515_ID_EXTENDED;
    tx_msg.dlc = 4;
    tx_msg.data[0] = 0xAA;
    tx_msg.data[1] = 0xBB;
    tx_msg.data[2] = 0xCC;
    tx_msg.data[3] = 0xDD;

    status = mcp2515_transmit(&tx_msg);
    if (status == MCP2515_OK) {
        print_message(&tx_msg, "TX");
    } else {
        printf("ERROR: Transmission failed (status=%d)\n\n", status);
    }

    delay_ms(100);

    /* Example 3: Send remote frame request */
    printf("Example 3: Sending remote frame request...\n");
    tx_msg.id = 0x200;
    tx_msg.id_type = MCP2515_ID_STANDARD;
    tx_msg.rtr = true;
    tx_msg.dlc = 0;

    status = mcp2515_transmit(&tx_msg);
    if (status == MCP2515_OK) {
        print_message(&tx_msg, "TX");
    } else {
        printf("ERROR: Transmission failed (status=%d)\n\n", status);
    }

    /* Main loop: Monitor CAN bus and receive messages */
    printf("=== Entering receive loop ===\n");
    printf("Waiting for CAN messages...\n\n");

    uint32_t msg_count = 0;
    uint32_t error_count = 0;

    while (1) {
        /* Check for received messages */
        if (mcp2515_message_available()) {
            mcp2515_message_t rx_msg;
            status = mcp2515_receive(&rx_msg);

            if (status == MCP2515_OK) {
                msg_count++;
                printf("--- Message #%u ---\n", (unsigned int)msg_count);
                print_message(&rx_msg, "RX");

                /* Example: Echo back received message with ID+1 */
                if (rx_msg.id < 0x7FF && !rx_msg.rtr) {
                    tx_msg = rx_msg;
                    tx_msg.id++;
                    printf("Echoing message back with ID 0x%03X...\n", (unsigned int)tx_msg.id);
                    mcp2515_transmit(&tx_msg);
                }
            }
        }

        /* Monitor errors every 1 second */
        static uint32_t error_check_counter = 0;
        if (++error_check_counter >= 100000) {
            error_check_counter = 0;

            uint8_t eflg = mcp2515_read_error_flags();
            uint8_t tec = mcp2515_read_tec();
            uint8_t rec = mcp2515_read_rec();

            if (eflg != 0 || tec > 0 || rec > 0) {
                error_count++;
                printf("\n[Error Status - Check #%u]\n", (unsigned int)error_count);
                printf("  EFLG: 0x%02X (", eflg);

                if (eflg & 0x80) printf("RX1OVR ");
                if (eflg & 0x40) printf("RX0OVR ");
                if (eflg & 0x20) printf("TXBO ");
                if (eflg & 0x10) printf("TXEP ");
                if (eflg & 0x08) printf("RXEP ");
                if (eflg & 0x04) printf("TXWAR ");
                if (eflg & 0x02) printf("RXWAR ");
                if (eflg & 0x01) printf("EWARN");

                printf(")\n");
                printf("  TEC: %u\n", tec);
                printf("  REC: %u\n", rec);
                printf("\n");

                /* Clear overflow flags if present */
                if (eflg & 0xC0) {
                    mcp2515_clear_interrupts(CANINTF_RX0IF | CANINTF_RX1IF);
                }
            }
        }

        delay_ms(10);
    }

    return 0;
}
