import cv2
import numpy as np
from random import randint
from voronoi import Point
from collections import defaultdict

# Quando escolher um pixel, já marca a vizinhança-8 como
# escolhidos, para não pegar 2 pontos um ao lado do outro
def set_neighboors_as_chosen(already_chosen, x, y, height, width):
    # +2 porque queremos ir de x-1 até x+1,
    # e range(A,B) vai de A até B-1
    for j in range(max(0, y-1), min(height-1, y+2)):
        for i in range(max(0, x-1), min(width-1, x+2)):
            if not (i == x and j == y):
                already_chosen[(i,j)] = 1

# Gera N pontos aleatórios, retorna um vetor
# com as coordenadas (x,y) de cada ponto
def random_points(img, n):
    height = img.shape[0]
    width = img.shape[1]

    points = []
    already_chosen = defaultdict(int) #começa com tudo setado em 0

    #Gera N pontos aleatórios
    for i in range(n):
        # Escolhe (x,y) aleatório
        x = randint(0, width-1)
        y = randint(0, height-1)
        # Se cair em um já escolhido, gera outro até ser único
        while already_chosen[(x,y)] == 1:
            x = randint(0, width-1)
            y = randint(0, height-1)
        already_chosen[(x,y)] = 1
        set_neighboors_as_chosen(already_chosen, x, y, height, width)
        points.append(Point(x, y))

    return points

# Gera N pontos aleatórios. Se está perto de uma borda, tem uma chance
# maior de ser escolhido. Retorna um vetor com as coordenadas (x,y) de cada ponto
def weighted_random(img, n):
    height = img.shape[0]
    width = img.shape[1]

    # Borra um pouco para tirar ruído
    img = cv2.GaussianBlur(img, (5,5), 0)

    # Detecta as bordas para cada canal separadamente e usando
    # diferentes limiares para a histerese, une tudo
    edges = np.zeros((height, width, 1), np.uint8)
    for channel in cv2.split(img):
        channel_edges = np.zeros((height, width, 1), np.uint8)
        higher_t = 255
        lower_t = higher_t//3
        for i in range(10):
            aux = cv2.Canny(channel, lower_t, higher_t)
            channel_edges = cv2.add(channel_edges, aux)
            higher_t -= 25
            lower_t = higher_t//3
        edges = cv2.add(edges, channel_edges)

    #cv2.imshow('image', edges)
    #cv2.waitKey(0)

    # Dilata as bordas
    kernel = np.ones((21,21), np.uint8)
    dilated_edges = cv2.dilate(edges, kernel, iterations = 1)

    # Perto das bordas = bordas dilatadas - bordas
    close_to_edges = cv2.subtract(dilated_edges, edges)

    #cv2.imshow('image', close_to_edges)
    #cv2.waitKey(0)

    points = []
    already_chosen = defaultdict(int) #começa com tudo setado em 0

    # Enquanto não selecionar N pontos
    while len(points) != n:
        # Escolhe (x,y) aleatório para testar
        x = randint(0, width-1)
        y = randint(0, height-1)
        # Se cair em um já escolhido, gera outro até ser único
        while already_chosen[(x,y)] == 1:
            x = randint(0, width-1)
            y = randint(0, height-1)

        # Rola um dado
        value = randint(1, 6)

        # Se estiver perto de alguma borda, tem grandes chances
        if close_to_edges[y][x] == 255:
            if value >= 3:
                already_chosen[(x,y)] = 1
                set_neighboors_as_chosen(already_chosen, x, y, height, width)
                points.append(Point(x,y))
        # Se não estiver perto, tem pouquíssimas chances
        else:
            if value >= 6:
                already_chosen[(x,y)] = 1
                set_neighboors_as_chosen(already_chosen, x, y, height, width)
                points.append(Point(x,y))

    return points
