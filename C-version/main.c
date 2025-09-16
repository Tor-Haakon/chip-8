#define SDL_MAIN_USE_CALLBACKS 1  /* use the callbacks instead of main() */
#include <stdio.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>
#include <SDL3/SDL.h>
#include <SDL3/SDL_main.h>

#define SCR_WIDTH 64
#define SCR_HEIGHT 32
#define PIXEL_SIZE 15

bool pixels[SCR_WIDTH][SCR_HEIGHT];
unsigned char memory[4096];
unsigned short V[16];
unsigned short stack[64];
int I;
int PC = 0x200;
int delay_timer = 0;
int sound_timer = 0;

/* We will use this renderer to draw into this window every frame. */
static SDL_Window *window = NULL;
static SDL_Renderer *renderer = NULL;
static SDL_FPoint points[500];

/* This function runs once at startup. */
SDL_AppResult SDL_AppInit(void **appstate, int argc, char *argv[])
{

    // SDL_SetAppMetadata("Example Renderer Primitives", "1.0", "com.example.renderer-primitives");

    if (!SDL_Init(SDL_INIT_VIDEO)) {
        SDL_Log("Couldn't initialize SDL: %s", SDL_GetError());
        return SDL_APP_FAILURE;
    }

    if (!SDL_CreateWindowAndRenderer("chip-8", SCR_WIDTH*PIXEL_SIZE, SCR_HEIGHT*PIXEL_SIZE, 0, &window, &renderer)) {
        SDL_Log("Couldn't create window/renderer: %s", SDL_GetError());
        return SDL_APP_FAILURE;
    }

    for (int i = 0; i < SCR_HEIGHT; i++) {
        for (int j = 0; j < SCR_WIDTH; j++) {
            pixels[i][j] = false;
        }
    }

    FILE* rom_file = fopen("../ROMS/IBM Logo.ch8", "rb");
    if (rom_file == NULL) {
        printf("Could not locate file\n");
    }
    fseek(rom_file, 0, SEEK_END);
    int rom_length = ftell(rom_file);
    fseek(rom_file, 0, SEEK_SET);
    fread(&memory[0x200], 1, rom_length, rom_file);
    fclose(rom_file); 

    return SDL_APP_CONTINUE;  /* carry on with the program! */
}

/* This function runs when a new event (mouse input, keypresses, etc) occurs. */
SDL_AppResult SDL_AppEvent(void *appstate, SDL_Event *event)
{
    if (event->type == SDL_EVENT_QUIT) {
        return SDL_APP_SUCCESS;  /* end the program, reporting success to the OS. */
    }
    return SDL_APP_CONTINUE;  /* carry on with the program! */
}

/* This function runs once per frame, and is the heart of the program. */
SDL_AppResult SDL_AppIterate(void *appstate)
{
    SDL_FRect rect;
    rect.h = rect.w = PIXEL_SIZE;

    // Fetch
    char instruction[5];
    sprintf(instruction, "%02x%02x", memory[PC], memory[PC+1]);
    PC += 2;
    
    // Find values for X, Y, NN, and NNN
    char X_string[4];
    long X;
    snprintf(X_string, sizeof(X_string), "0x%c", instruction[1]);
    X = strtol(X_string, NULL, 16);

    char Y_string[4];
    long Y;
    snprintf(Y_string, sizeof(Y_string), "0x%c", instruction[2]);
    Y = strtol(Y_string, NULL, 16);

    char NNN_string[6];
    long NNN;
    snprintf(NNN_string, sizeof(NNN_string), "0x%c%c%c", instruction[1], instruction[2], instruction[3]);
    NNN = strtol(NNN_string, NULL, 16);

    char NN_string[5];
    long NN;
    snprintf(NN_string, sizeof(NN_string), "0x%c%c", instruction[2], instruction[3]);
    NN = strtol(NN_string, NULL, 16);

    char N_string[4];
    long N;
    snprintf(N_string, sizeof(N_string), "0x%c", instruction[3]);
    N = strtol(N_string, NULL, 16);

    // Decode
    switch (instruction[0]) {
    case ('0'):
        const char* e0 = "00e0";
        if (strcmp(instruction, e0) == 0) {
            for (int i = 0; i < SCR_WIDTH; i++) {
                for (int j = 0; j < SCR_HEIGHT; j++) {
                    pixels[i][j] = false;
                }
            }
        }
        break;

    case ('1'):
        PC = NNN;
        break;

    case ('6'):        
        V[X] = NN;
        break;

    case ('7'):
        V[X] = (V[X] + NN) % 256;
        break;

    case ('a'):
        I = NNN;
        break;

    case ('d'):
        int y = V[Y] % 32;
        V[0xf] = 0;
        for (int i = 0; i < N; i++) {
            int x = V[X] % 64;
            char sprite_data[3];
            sprintf(sprite_data, "%02x", memory[I+i]);
            char sprite_data0[2];
            snprintf(sprite_data0, sizeof(sprite_data0), "%c", sprite_data[0]);
            char sprite_data1[2];
            snprintf(sprite_data1, sizeof(sprite_data1), "%c", sprite_data[1]);
            char bin_sprite[9];
            for (int i = 0; i < 2; i++){
                long dec_value;
                if (i == 0) {
                    dec_value = strtol(sprite_data0, NULL, 16);
                } else if (i == 1) {
                    dec_value = strtol(sprite_data1, NULL, 16);
                }
                bin_sprite[4*i] = dec_value / 8;
                dec_value %= 8;
                bin_sprite[4*i+1] = dec_value / 4;
                dec_value %= 4;
                bin_sprite[4*i+2] = dec_value / 2;
                dec_value %= 2;
                bin_sprite[4*i+3] = dec_value / 1;        
            }
            // char bin_sprite[8] = hex_to_binary(sprite_data);
            for (int j = 0; j < 8; j++) {
                if (bin_sprite[j] == '\001' && pixels[x][y] == 1) {
                    pixels[x][y] = 0;
                    V[0xf] = 1;
                }
                else if (bin_sprite[j] == '\001' && pixels[x][y] == 0) {
                    pixels[x][y] = 1;
                }
                if (x > 63) {
                    x = V[X] % 64;
                    break;
                }
                x++;
            }
            y++;
            if (y > 31) {
                break;
            }
        }
        break;
    }
    
    SDL_SetRenderDrawColor(renderer, 165, 42, 42, SDL_ALPHA_OPAQUE);  /* dark gray, full alpha */
    SDL_RenderClear(renderer);  /* start with a blank canvas. */

    /* draw a filled rectangle in the middle of the canvas. */
    SDL_SetRenderDrawColor(renderer, 255, 255, 0, SDL_ALPHA_OPAQUE);  /* blue, full alpha */
    int i;
    int j;
    for (i = 0; i < SCR_WIDTH; i++) {
        for (j = 0; j < SCR_HEIGHT; j++) {
            if (pixels[i][j] == true) {
                rect.x = i * PIXEL_SIZE;
                rect.y = j * PIXEL_SIZE;
                SDL_RenderFillRect(renderer, &rect);
            }
        }
    }

    SDL_RenderPresent(renderer);  /* put it all on the screen! */

    return SDL_APP_CONTINUE;  /* carry on with the program! */
}

/* This function runs once at shutdown. */
void SDL_AppQuit(void *appstate, SDL_AppResult result)
{
    /* SDL will clean up the window/renderer for us. */
}