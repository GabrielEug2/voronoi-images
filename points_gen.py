import cv2
import numpy as np
import random
import sys
from random import randint
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
    sys.exit("Use pontos aleatórios, desse jeito (usando bordas) é mais lento e não melhora nada")
    ### TODO: Tentar dividir em várias áreas (3 ou 4) de pixels com
    ### chance diferente de serem escolhidos. Quanto mais perto da borda, maior a
    ### chance de tirar de lá. Como colocar "pesos" na hora de escolher um random?
