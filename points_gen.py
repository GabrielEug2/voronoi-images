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

    # Converte para escala de cinza e borra um pouco para tirar ruído
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5,5), 0)

    # Detalhes = imagem - imagem borrada
    blur = cv2.GaussianBlur(gray, (15,15), 0)
    details = cv2.subtract(gray, blur)

    # Filtro máximo para "vazar" os detalhes
    details = cv2.dilate(details, np.ones((31, 31), np.uint8), iterations = 1)

    # Normaliza para 0..255
    details = cv2.normalize(details, None, 0, 255, cv2.NORM_MINMAX)
    cv2.imshow('image', details)
    cv2.waitKey(0)

    # Adiciona os candidatos a ponto em 2 vetores:
    # Detalhes acima de um treshold são bons candidatos,
    # o resto são candidatos ok
    good_candidates = []
    ok_candidates = []
    for y in range(0, altura):
        for x in range(0, largura):
            point = Point(x,y)
            if details[y][x] > 75:
                good_candidates.append(point)
            else:
                ok_candidates.append(point)

    # Seleciona N pontos aleatórios do vetor
    points = []
    already_chosen = defaultdict(int) #começa com tudo setado em 0

    # A maior parte será dos detalhes
    for i in range(0, int(n*0.7)):
        selected = choice(good_candidates)
        # garante que nenhum ponto vai ser igual: se cair
        # em um já escolhido, seleciona outro até ser único
        while already_chosen[selected] == 1:
            selected = choice(good_candidates)
        already_chosen[selected] = 1
        points.append(selected)

    # O resto é do fundo
    for i in range(0, int(n*0.3)):
        selected = choice(ok_candidates)
        # garante que nenhum ponto vai ser igual: se cair
        # em um já escolhido, seleciona outro até ser único
        while already_chosen[selected] == 1:
            selected = choice(ok_candidates)
        already_chosen[selected] = 1
        points.append(selected)

    return points
