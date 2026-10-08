#include <stdio.h>
#include <string.h>
#include "esp_log.h"
#include "esp_netif.h"
#include "esp_event.h"
#include "nvs_flash.h"
#include "tinyusb.h"
#include "tinyusb_default_config.h"
#include "tinyusb_net.h"
#include "dhcpserver/dhcpserver_options.h"
#include "lwip/esp_netif_net_stack.h"
#include "esp_http_server.h"
#include "test_pattern.h"

static const char *TAG = "vision_hub";
static esp_netif_t *s_netif = NULL;
static uint32_t s_frame_counter = 0;

#define PART_BOUNDARY "123456789000000000000987654321"
static const char* _STREAM_CONTENT_TYPE = "multipart/x-mixed-replace;boundary=" PART_BOUNDARY;
static const char* _STREAM_BOUNDARY = "\r\n--" PART_BOUNDARY "\r\n";
static const char* _STREAM_PART = "Content-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n";

static void l2_free(void *h, void *buffer) { free(buffer); }

static esp_err_t netif_transmit(void *h, void *buffer, size_t len)
{
    if (tinyusb_net_send_sync(buffer, len, NULL, pdMS_TO_TICKS(100)) != ESP_OK) {
        ESP_LOGE(TAG, "Failed to send packet to USB NCM");
    }
    return ESP_OK;
}

static esp_err_t netif_recv_callback(void *buffer, uint16_t len, void *ctx)
{
    if (s_netif) {
        void *buf_copy = malloc(len);
        if (!buf_copy) return ESP_ERR_NO_MEM;
        memcpy(buf_copy, buffer, len);
        return esp_netif_receive(s_netif, buf_copy, len, NULL);
    }
    return ESP_OK;
}

static esp_err_t init_ncm_netif(void)
{
    const tinyusb_config_t tusb_cfg = TINYUSB_DEFAULT_CONFIG();
    ESP_ERROR_CHECK(tinyusb_driver_install(&tusb_cfg));

    const tinyusb_net_config_t net_config = {
        .mac_addr = {0x02, 0x02, 0x11, 0x22, 0x33, 0x01},
        .on_recv_callback = netif_recv_callback,
    };
    ESP_ERROR_CHECK(tinyusb_net_init(&net_config));

    uint8_t lwip_addr[6] = {0x02, 0x02, 0x11, 0x22, 0x33, 0x02};

    esp_netif_inherent_config_t base_cfg = {
        .flags = ESP_NETIF_DHCP_SERVER | ESP_NETIF_FLAG_AUTOUP,
        .ip_info = &_g_esp_netif_soft_ap_ip,
        .if_key = "ncm",
        .if_desc = "usb ncm vision hub",
        .route_prio = 10,
    };

    esp_netif_driver_ifconfig_t driver_cfg = {
        .handle = (void *)1,
        .transmit = netif_transmit,
        .driver_free_rx_buffer = l2_free,
    };

    struct esp_netif_netstack_config lwip_netif_config = {
        .lwip = {
            .init_fn = ethernetif_init,
            .input_fn = ethernetif_input,
        }
    };

    esp_netif_config_t cfg = {
        .base = &base_cfg,
        .driver = &driver_cfg,
        .stack = &lwip_netif_config,
    };

    s_netif = esp_netif_new(&cfg);
    if (!s_netif) return ESP_FAIL;
    esp_netif_set_mac(s_netif, lwip_addr);

    uint32_t lease_opt = 1;
    esp_netif_dhcps_option(s_netif, ESP_NETIF_OP_SET, IP_ADDRESS_LEASE_TIME, &lease_opt, sizeof(lease_opt));
    esp_netif_action_start(s_netif, 0, 0, 0);

    ESP_LOGI(TAG, "USB NCM Netif running at 192.168.4.1");
    return ESP_OK;
}

static esp_err_t status_handler(httpd_req_t *req)
{
    char buf[128];
    snprintf(buf, sizeof(buf), "Vision Hub OK. Test Stream active: %lu frames streamed\n", s_frame_counter);
    httpd_resp_send(req, buf, HTTPD_RESP_USE_STRLEN);
    return ESP_OK;
}

static esp_err_t stream_handler(httpd_req_t *req)
{
    esp_err_t res = httpd_resp_set_type(req, _STREAM_CONTENT_TYPE);
    if (res != ESP_OK) return res;
    httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");

    char part_buf[64];
    size_t frame_len = sizeof(TEST_JPEG_FRAME);

    while (true) {
        res = httpd_resp_send_chunk(req, _STREAM_BOUNDARY, strlen(_STREAM_BOUNDARY));
        if (res == ESP_OK) {
            size_t hlen = snprintf(part_buf, 64, _STREAM_PART, frame_len);
            res = httpd_resp_send_chunk(req, part_buf, hlen);
        }
        if (res == ESP_OK) {
            res = httpd_resp_send_chunk(req, (const char *)TEST_JPEG_FRAME, frame_len);
        }

        if (res != ESP_OK) break;
        s_frame_counter++;
        vTaskDelay(pdMS_TO_TICKS(66)); // ~15 FPS
    }
    return res;
}

static void start_webservers(void)
{
    // Port 80 status
    httpd_config_t cfg80 = HTTPD_DEFAULT_CONFIG();
    cfg80.server_port = 80;
    httpd_handle_t server80 = NULL;
    if (httpd_start(&server80, &cfg80) == ESP_OK) {
        httpd_uri_t uri_status = { .uri = "/", .method = HTTP_GET, .handler = status_handler };
        httpd_register_uri_handler(server80, &uri_status);
    }

    // Port 81 MJPEG stream
    httpd_config_t cfg81 = HTTPD_DEFAULT_CONFIG();
    cfg81.server_port = 81;
    cfg81.ctrl_port = 32770;
    httpd_handle_t server81 = NULL;
    if (httpd_start(&server81, &cfg81) == ESP_OK) {
        httpd_uri_t uri_stream = { .uri = "/stream", .method = HTTP_GET, .handler = stream_handler };
        httpd_register_uri_handler(server81, &uri_stream);
        ESP_LOGI(TAG, "Test pattern MJPEG stream active on :81/stream");
    }
}

void app_main(void)
{
    ESP_LOGI(TAG, "Starting Vision Hub NCM Test Pattern Server...");
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());

    ESP_ERROR_CHECK(init_ncm_netif());
    start_webservers();
}
