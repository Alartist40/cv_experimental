#include "esp_http_server.h"
#include "esp_log.h"

static esp_err_t test_handler(httpd_req_t *req)
{
    httpd_resp_send(req, "Vision Hub Ready\n", HTTPD_RESP_USE_STRLEN);
    return ESP_OK;
}

httpd_handle_t start_webserver(void)
{
    httpd_config_t config = HTTPD_DEFAULT_CONFIG();
    config.server_port = 80;
    httpd_handle_t server = NULL;
    if (httpd_start(&server, &config) == ESP_OK) {
        httpd_uri_t uri = {
            .uri = "/",
            .method = HTTP_GET,
            .handler = test_handler,
            .user_ctx = NULL
        };
        httpd_register_uri_handler(server, &uri);
    }
    return server;
}
