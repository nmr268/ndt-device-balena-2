/* Copyright (C) 2020 Nordetect
 */

#include <stdint.h>
#include <stdlib.h>
#include <errno.h>

#include "ws2811.h"

// Config for specific LED strip
#define TARGET_FREQ             WS2811_TARGET_FREQ
#define GPIO_PIN                12
#define DMA                     10
#define STRIP_TYPE              WS2811_STRIP_GRB
#define LED_COUNT               12

ws2811_t ledstring =
{
    .freq = TARGET_FREQ,
    .dmanum = DMA,
    .channel =
    {
        [0] =
        {
            .gpionum = GPIO_PIN,
            .count = LED_COUNT,
            .invert = 0,
            .brightness = 255,
            .strip_type = STRIP_TYPE,
        },
        [1] =
        {
            .gpionum = 0,
            .count = 0,
            .invert = 0,
            .brightness = 0,
        },
    },
};

void set_color(ws2811_led_t color)
{
    int i;
    for (i = 0; i < LED_COUNT; i++)
    {
        ledstring.channel[0].leds[i] = color;
    }
}

int main(int argc, char *argv[])
{
    unsigned long arg;
    ws2811_return_t ret;
    
    if (argc != 2) {
        return 1;
    }
    arg = strtoul(argv[1], NULL, 16);
    if (arg == 0) {
        // Maybe an error occured, check it
        if (errno == EINVAL) return 2;
        if (errno == ERANGE) return 3;
    }
    if (arg > 0xffffffff) {
        return 3;
    }
    
    if ((ret = ws2811_init(&ledstring)) != WS2811_SUCCESS) return ret;
    set_color((ws2811_led_t)arg);
    ret = ws2811_render(&ledstring);
    ws2811_fini(&ledstring);
    
    return ret;
}
