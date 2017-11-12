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

    # Detecta as bordas
    edges = cv2.Canny(img, 50, 200)
    #cv2.imshow('image', edges)
    #cv2.waitKey(0)

    # Dilata usando kernels diferentes
    kernel_small = np.ones((25,25), np.uint8)
    really_close_to_edges = cv2.dilate(edges, kernel_small, iterations = 1)

    kernel_big = np.ones((51,51),np.uint8)
    close_to_edges = cv2.dilate(edges, kernel_big, iterations = 1)

    # O que estiver muito perto da borda é desconsiderado,
    # diminuindo o número de "pontas" nas fronteiras das
    # células do Voronoi
    kernel_too_small = np.ones((5,5), np.uint8)
    edges = cv2.dilate(edges, kernel_too_small, iterations = 1)
    really_close_to_edges = cv2.subtract(really_close_to_edges, edges)
    close_to_edges = cv2.subtract(close_to_edges, edges)

    # Para melhor preservar as fronteiras dos objetos no Voronoi,
    # é melhor que muitos pixels perto da borda sejam escolhidos.

    # Para garantir isso, somamos as imagens dilatadas, criando
    # uma espécie de mapa.
    #   bem perto das bordas = 2
    #   meio perto das bordas = 1
    #   longe das bordas = 0
    really_close_to_edges = cv2.normalize(really_close_to_edges.astype('float32'), None, 0.0, 1.0, cv2.NORM_MINMAX)
    close_to_edges = cv2.normalize(close_to_edges.astype('float32'), None, 0.0, 1.0, cv2.NORM_MINMAX)
    odds_map = cv2.add(close_to_edges, really_close_to_edges)

    # Adiciona todos os candidatos a pontos em um vetor. Quanto mais claro
    # o pixel for no mapa, maior as chances de ser escolhido
    #   perto das bordas = muitas chances
    #   ...
    #   longe das bordas = poucas chances
    candidates = []
    for y in range(0, altura):
        for x in range(0, largura):
            point = Point(x,y)
            if odds_map[y][x] == 2:
                for i in range(0, 10):
                    candidates.append(point)
            if odds_map[y][x] == 1:
                for i in range(0, 5):
                    candidates.append(point)
            else: #se estiver longe
                candidates.append(point)
    odds_map = cv2.normalize(odds_map.astype('float32'), None, 0.0, 1.0, cv2.NORM_MINMAX)
    odds_map = cv2.convertScaleAbs(odds_map, alpha=(255.0))
    cv2.imshow('image', odds_map)
    cv2.waitKey(0)

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
