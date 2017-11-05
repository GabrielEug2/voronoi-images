import cv2
import numpy as np
import random
from random import randint
from voronoi import Point

def random_points(img, n):
    altura = img.shape[0]
    largura = img.shape[1]

    #points_img = np.zeros((altura, largura, 1), np.uint8)
    points = []

    #Gera N pontos aleatórios
    for i in range(0, n):
        x = randint(0, largura-1)
        y = randint(0, altura-1)
        points.append(Point(x, y))
        #points_img[y, x] = 255

    #cv2.imshow('image', points_img)
    #cv2.waitKey(0)
    return points

def random_plus_edges(img, n):
    altura = img.shape[0]
    largura = img.shape[1]

    # Detecta as bordas
    edges = cv2.Canny(img, 50, 200)
    #cv2.imshow('image', edges)
    #cv2.waitKey(0)

    # Salva os pixels brancos como possíveis sementes/pontos
    edges_coord = []
    for y in range(altura):
        for x in range(largura):
            if edges[y,x] == 255:
                edges_coord.append(Point(x, y))
    # Embaralha
    random.shuffle(edges_coord)

    # Seleciona uma porcentagem dos pixels das bordas,
    # e o restante aleatorios
    points = []
    n_from_edges = int(n*0.3)
    n_from_random = n - n_from_edges
    for i in range(0, n_from_edges):
        selected = edges_coord.pop()
        points.append(selected)

    for i in range(0, n_from_random):
        x = randint(0, largura-1)
        y = randint(0, altura-1)
        points.append(Point(x, y))

    return points
