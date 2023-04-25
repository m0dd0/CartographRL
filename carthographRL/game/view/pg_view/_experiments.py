import pygame


def main():
    pygame.init()
    display = pygame.display.set_mode((500, 500))
    display.fill((255, 255, 255))

    font = pygame.font.SysFont("Arial", 50)
    text = font.render("g", True, (0, 0, 0))

    display.blit(text, (0, 0))

    pygame.draw.rect(display, (0, 0, 0), (0, 0, 50, 50), 1)

    pygame.display.flip()

    while True:
        pass


if __name__ == "__main__":
    main()
