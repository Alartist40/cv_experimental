idf_component_register(SRCS "main.c"
                       INCLUDE_DIRS "."
                       REQUIRES esp_netif nvs_flash esp_event esp_tinyusb esp_http_server esp32-camera)
