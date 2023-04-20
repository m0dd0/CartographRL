import pygame


def draw_edges(coords, surf):
    s = 30
    d = 3
    edges = []
    for x, y in coords:
        if (x - 1, y) not in coords:  # left edge
            left_edge = [x * s, y * s, d, s]
            edges.append(left_edge)
        if (x + 1, y) not in coords:  # right edge
            right_edge = [(x + 1) * s - d, y * s, d, s]
            edges.append(right_edge)
        if (x, y - 1) not in coords:  # top edge
            top_edge = [x * s, y * s, s, d]
            edges.append(top_edge)
        if (x, y + 1) not in coords:  # bottom edge
            bottom_edge = [x * s, (y + 1) * s - d, s, d]
            edges.append(bottom_edge)

    for edge in edges:
        print(edge)
        pygame.draw.rect(surf, (0, 0, 0), edge)


def main():
    pygame.init()
    display = pygame.display.set_mode((500, 500))

    background = pygame.Surface((500, 500))
    background.fill((255, 255, 255))
    display.blit(background, (0, 0))

    surf = pygame.Surface((30, 30), pygame.SRCALPHA)
    surf.fill((255, 0, 0, 100))
    pygame.draw.ö(surf, (0, 0, 0), [(0, 0), (29, 0), (29, 29), (0, 29)], 1)

    # draw_edges([[0, 0]], surf)

    display.blit(surf, (200, 200))

    pygame.display.flip()

    while True:
        pass


if __name__ == "__main__":
    main()
