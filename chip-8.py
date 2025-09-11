import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame
from random import randint
import time

SCR_WIDTH = 64
SCR_HEIGHT = 32
PIXEL_SIZE = 15
FPS = 60
PROGRAM = "Space Invaders.ch8"

memory = bytearray(4096)
V = [0] * 16                   # 16 8-bit registers, V0-VF
I = 0                          # 1 12-bit address register
PC = 0x200                     # program counter (program starts here)
stack = []
delay_timer = 0
sound_timer = 0

keys = [pygame.K_x, pygame.K_1, pygame.K_2, pygame.K_3,
        pygame.K_q, pygame.K_w, pygame.K_e, pygame.K_a,
        pygame.K_s, pygame.K_s, pygame.K_z, pygame.K_c,
        pygame.K_4, pygame.K_r, pygame.K_f, pygame.K_v]

with open(PROGRAM, mode="rb") as file:
    file_content = file.read()

file_size = os.path.getsize(PROGRAM)
memory[0x200:0x200+file_size] = file_content

with open("fonts.ch8", mode="rb") as file:
    font = file.read()

memory[0x50:0xa0] = font


pixels = [[0 for i in range(SCR_HEIGHT)] for j in range(SCR_WIDTH)]

pygame.init()
screen = pygame.display.set_mode((SCR_WIDTH * PIXEL_SIZE, SCR_HEIGHT * PIXEL_SIZE))
clock = pygame.time.Clock()
running = True

last_time = time.time()
time_accumulator = 0

while running:

    current_time = time.time()
    delta_time = current_time - last_time
    last_time = current_time
    time_accumulator += delta_time

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    instruction = memory[PC:PC+2].hex()
    PC += 2

    match instruction[0]:

        case '0':
            match instruction:

                case '00e0':
                    for i in range(SCR_WIDTH):
                        for j in range(SCR_HEIGHT):
                            pixels[i][j] = 0

                case '00ee':
                    PC = stack.pop()

        case '1':
            PC = int(instruction[1:4], base=16)

        case '2':
            stack.append(PC)
            PC = int(instruction[1:4], base=16)

        case '3':
            X = int(instruction[1], base=16)
            value = int(instruction[2:4], base=16)
            if V[X] == value:
                PC += 2

        case '4':
            X = int(instruction[1], base=16)
            value = int(instruction[2:4], base=16)
            if V[X] != value:
                PC += 2
        
        case '5':
            X = int(instruction[1], base=16)
            Y = int(instruction[2], base=16)
            if V[X] == V[Y]:
                PC += 2
        
        case '6':
            X = int(instruction[1], base=16)
            value = int(instruction[2:4], base=16)
            V[X] = value % 256

        case '7':
            X = int(instruction[1], base=16)
            value = int(instruction[2:4], base=16)
            V[X] = (V[X] + value) % 256

        case '8':
            X = int(instruction[1], base=16)
            Y = int(instruction[2], base=16)
            match instruction[3]:

                case '0':
                    V[X] = V[Y]

                case '1':
                    V[X] = V[X] | V[Y]

                case '2':
                    V[X] = V[X] & V[Y]

                case '3':
                    V[X] = V[X] ^ V[Y]

                case '4':
                    V[X] += V[Y]
                    if V[X] > 255:
                        V[0xf] = 1
                    else:
                        V[0xf] = 0
                    V[X] %= 256
                
                case '5':
                    vx = V[X]
                    V[X] = (V[X] - V[Y]) % 256
                    if vx >= V[Y]:
                        V[0xf] = 1
                    else:
                        V[0xf] = 0                    

                case '6':
                    vx = V[X]
                    V[X] = V[X] >> 1
                    if vx % 2 == 1:
                        V[0xf] = 1
                    else:
                        V[0xf] = 0
                    

                case '7':
                    vx = V[X]
                    V[X] = (V[Y] - V[X]) % 256
                    if vx <= V[Y]:
                        V[0xf] = 1
                    else:
                        V[0xF] = 0

                case 'e':
                    vx = V[X]
                    V[X] = (vx << 1) % 256
                    if vx // 128 == 1:
                        V[0xf] = 1
                    else:
                        V[0xf] = 0
                    

        case '9':
            X = int(instruction[1], base=16)
            Y = int(instruction[2], base=16)
            if V[X] != V[Y]:
                PC += 2

        case 'a':
            I = int(instruction[1:4], base=16)

        case 'b':
            PC = int(instruction[1:4], base=16) + V[0]

        case 'c':
            X = int(instruction[1], base=16)
            value = int(instruction[2:4], base=16)
            rand = randint(0, 0xff)
            V[X] = value & rand

        case 'd':
            x = V[int(instruction[1], base=16)] % 64
            y = V[int(instruction[2], base=16)] % 32
            N = int(instruction[3], base=16)
            V[0xf] = 0

            for i in range(N):
                sprite = bin(memory[I+i])[2:].rjust(8, '0')
                for j in range(8):
                    if pixels[x][y] == 1 and sprite[j] == '1':
                        pixels[x][y] = 0
                        V[0xf] = 1
                    elif pixels[x][y] == 0 and sprite[j] == '1':
                        pixels[x][y] = 1
                    x += 1
                    if x > 63:
                        break
                x = V[int(instruction[1], base=16)] % 64
                y += 1
                if y > 31:
                    break
        
        case 'e':
            X = int(instruction[1], base=16)
            key = keys[V[X]%16]
            if instruction[2:4] == '9e':          
                if pygame.key.get_pressed()[key] == True:
                    PC += 2
            elif instruction[2:4] == 'a1':
                if pygame.key.get_pressed()[key] != True:
                    PC += 2

        case 'f':
            X = int(instruction[1], base=16)
            match instruction[2:4]:

                case '07':
                    V[X] = delay_timer

                case '15':
                    delay_timer = V[X]

                case '18':
                    sound_timer = V[X]

                case '0a':
                    for i, key in enumerate(keys):
                        if pygame.key.get_pressed()[key] == True:
                            V[X] = i
                        else:
                            PC -= 2

                case '1e':
                    I += V[X]

                case '29':
                    I = 0x50 + (V[X] % 16) * 5

                case '33':
                    whole_num = V[X]
                    num_1 = whole_num % 10
                    whole_num //= 10
                    num_2 = whole_num % 10
                    num_3 = whole_num // 10
                    memory[I] = num_3
                    memory[I+1] = num_2
                    memory[I+2] = num_1

                case '55':
                    for i in range(X+1):
                        memory[I+i] = V[i]

                case '65':
                    for i in range(X+1):
                        V[i] = memory[I+i]       

    screen.fill("brown")

    for i in range(SCR_WIDTH):
        for j in range(SCR_HEIGHT):
            if pixels[i][j] == 1:
                rect = pygame.Rect(i * PIXEL_SIZE, j * PIXEL_SIZE, PIXEL_SIZE, PIXEL_SIZE)
                pygame.draw.rect(screen, "yellow", rect)

    if time_accumulator >= (1 / FPS):

        pygame.display.flip()

        if delay_timer > 0:
            delay_timer -= 1
        if sound_timer > 0:
            sound_timer -= 1

        time_accumulator = 0

        # print(delta_time, time_accumulator)


    # clock.tick(60)

pygame.quit()