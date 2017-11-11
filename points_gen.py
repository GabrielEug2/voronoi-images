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

def random_plus_edges(img, n):
    altura = img.shape[0]
    largura = img.shape[1]

    # Detecta e dilata as bordas
    edges = cv2.Canny(img, 50, 200)
    cv2.imshow('image', edges)
    cv2.waitKey(0)
    kernel = np.ones((21,21),np.uint8)
    close_to_edges = cv2.dilate(edges, kernel, iterations = 1)
    cv2.imshow('image', close_to_edges)
    cv2.waitKey(0)

    # Adiciona todos os candidatos a pontos em um vetor.
    # Se o pixel está perto de alguma borda, ele é inserido
    # mais de uma vez
    candidates = []
    for y in range(0, altura):
        for x in range(0, largura):
            if close_to_edges[y][x] == 255:
                candidates.append(Point(x, y))
                candidates.append(Point(x, y))
            else: #se estiver longe
                candidates.append(Point(x, y))

    # Seleciona N pontos aleatórios
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
