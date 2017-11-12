import cv2
import numpy as np
from random import randint
from random import choice
from voronoi import Point
from collections import defaultdict

# Gera N pontos aleatórios, retorna um vetor
# com as coordenadas (x,y) de cada ponto
def random_points(img, n):
    altura = img.shape[0]
    largura = img.shape[1]

    points = []
    already_chosen = defaultdict(int) #começa com tudo setado em 0

    #Gera N pontos aleatórios
    for i in range(0, n):
        x = randint(0, largura-1)
        y = randint(0, altura-1)
        # garante que nenhum ponto vai ser igual: se cair
        # em um já escolhido, gera outro até ser único
        while already_chosen[(x,y)] == 1:
            x = randint(0, largura-1)
            y = randint(0, altura-1)
        already_chosen[(x,y)] = 1
        points.append(Point(x, y))

    return points

# Gera N pontos aleatórios. Se está perto de uma borda, tem uma chance
# maior de ser escolhido. Retorna um vetor com as coordenadas (x,y) de cada ponto
def weighted_random(img, n):
    altura = img.shape[0]
    largura = img.shape[1]

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Imagem - imagem borrada = detalhes
    blur = cv2.GaussianBlur(gray, (71,71), 0)
    details = cv2.subtract(gray, blur)

    # Filtro máximo para "vazar" os detalhes
    details = cv2.dilate(details, np.ones((7, 7), np.uint8), iterations = 1)

    # Normalize para 0..1
    details = cv2.normalize(details.astype('float32'), None, 0.0, 1.0, cv2.NORM_MINMAX)
    #cv2.imshow('image', details)
    #cv2.waitKey(0)

    # Adiciona todos os candidatos a pontos em um vetor. Quanto mais claro
    # o pixel for no mapa, maior as chances de ser escolhido
    #   perto das bordas = muitas chances
    #   ...
    #   longe das bordas = poucas chances
    candidates = []
    for y in range(0, altura):
        for x in range(0, largura):
            point = Point(x,y)
            chances = int(details[y][x] * 10)
            for i in (0, chances):
                candidates.append(point)

    # Seleciona N pontos aleatórios do vetor
    points = []
    already_chosen = defaultdict(int) #começa com tudo setado em 0

    for i in range(0, n):
        selected = choice(candidates)
        # garante que nenhum ponto vai ser igual: se cair
        # em um já escolhido, seleciona outro até ser único
        while already_chosen[selected] == 1:
            selected = choice(candidates)
        already_chosen[selected] = 1
        points.append(selected)

    return points
