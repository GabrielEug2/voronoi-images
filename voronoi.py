import cv2
from random import randint
import numpy as np
import math
from collections import defaultdict

class Point(object):
    def __init__(self, x, y, color=None):
        self.x = x
        self.y = y
        self.color = color

    def __str__(self):
        return "Point(%s, %s)"%(self.x,self.y)

    def __lt__(self, other):
        return self.y < other.y

    # Euclidean distance
    def dist(self, p):
        dx = self.x - p.x
        dy = self.y - p.y
        return math.hypot(dx, dy)


class Edge(object):
    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2

    def __str__(self):
        return "Edge(%s, %s)"%(self.p1,self.p2)

    # Verifica se nenhum outro triangulo tem essa aresta
    def is_unique(self, current, triangles):
        for triangle in triangles:
            if current is not triangle:
                for edge in triangle:
                    # Aresta AB e a mesma que BA
                    if (edge.p1 == self.p1 and edge.p2 == self.p2) or (edge.p1 == self.p2 and edge.p2 == self.p1):
                        return False
        return True

class Triangle(object):
    def __init__(self, p1, p2, p3):
        self.p1 = p1
        self.p2 = p2
        self.p3 = p3
        self.cx, self.cy, self.cr = self.circumcenter()
        self.center = Point(self.cx, self.cy)
        self.edges = [Edge(p1, p2), Edge(p2, p3), Edge(p3, p1)]
        self.neighboors = []

    def __iter__(self):
        return iter(self.edges)

    def __str__(self):
        return "Points:(%s, %s, %s)"%(self.p1,self.p2,self.p3)

    # Calcula o circuncentro
    # Retirado de: http://www.ics.uci.edu/~eppstein/junkyard/circumcenter.html (segundo comentário)
    # Pode dar problema (d = 0), especialmente com NUM_POINTS grande
    # Tem que ver como resolver isso... ou como implementar o fortune...
    def circumcenter(self):
        p1 = self.p1
        p2 = self.p2
        p3 = self.p3
        d = (p1.x - p3.x) * (p2.y - p3.y) - (p2.x - p3.x) * (p1.y - p3.y)
        if d == 0:
            print("deu ruim")
        cx = (((p1.x - p3.x) * (p1.x + p3.x) + (p1.y - p3.y) * (p1.y + p3.y)) / 2 * (p2.y - p3.y) \
        -((p2.x - p3.x) * (p2.x + p3.x) + (p2.y - p3.y) * (p2.y + p3.y)) / 2 * (p1.y - p3.y)) \
        / d

        cy = (((p2.x - p3.x) * (p2.x + p3.x) + (p2.y - p3.y) * (p2.y + p3.y)) / 2 * (p1.x - p3.x) \
        -((p1.x - p3.x) * (p1.x + p3.x) + (p1.y - p3.y) * (p1.y + p3.y)) / 2 * (p2.x - p3.x)) \
        / d

        cr = np.hypot((p3.x - cx), (p3.y - cy))

        return cx, cy, cr

    # Se a distancia do circuncentro ate o ponto e menor que o raio esta dentro
    def is_in_circle(self, point):
        return self.cr >= point.dist(self.center)

    # Verifica se algum ponto do super triangulo esta sendo usado
    def contains_super(self, super_tri):
        # Set guarda valores unicos
        s = set([self.p1, self.p2, self.p3, super_tri.p1, super_tri.p2, super_tri.p3])
        # Entao se nao tiver 6 tem algum igual
        return len(s) != 6

    # Procura os vizinhos de cada triangulo
    def find_neighboors(self, triangulation):
        for edge in self.edges:
            flag = False
            for triangle in triangulation:
                if triangle is not self:
                    for e in triangle:
                        if (edge.p1 == e.p1 and edge.p2 == e.p2) or (edge.p1 == e.p2 and edge.p2 == e.p1):
                            self.neighboors.append(triangle)
                            # se achou o vizinho de um lado da break até o prox lado
                            flag = True
                            break
                    if flag:
                        break
                if flag:
                    break


image = cv2.imread('img/7.jpg', 1)
h = image.shape[0]
w = image.shape[1]
canais = 3
#h = 700
#w = 700
NUM_POINTS = 1000

black = (0, 0, 0)
white = (255, 255, 255)
red = (0, 0, 255)
blue = (255, 0, 0)
green = (0, 255, 0)

def main():
    img = np.zeros((h,w,3), np.uint8)
    img2 = np.zeros((h,w,3), np.uint8)
    # Bowyer-Watson
    # https://en.wikipedia.org/wiki/Bowyer%E2%80%93Watson_algorithm
    # Ainda e lento...
    # Pontos que criam um "super-triangulo" que contem o plano inteiro
    sp1 = Point(w//2, math.ceil(1.5*h))
    sp2 = Point(-math.ceil(w*1.5), -1)
    sp3 = Point(math.ceil(w*2.5), -1)

    # Cria pontos e desenha
    points = []
    for i in range(NUM_POINTS):
        y = randint(1, h - 2)
        x = randint(1, w - 2)

        points.append(Point(x, y))
        #cv2.circle(img,(x,y), 1, red, -1)


    # Super-triangulo
    super_tri = Triangle(sp2, sp3, sp1)

    triangulation = []

    triangulation.append(super_tri)

    for point in points:
        bad_tri = set()
        for triangle in triangulation:
            if triangle.is_in_circle(point):
                bad_tri.add(triangle)
        polygon = set()
        for triangle in bad_tri:
            for edge in triangle:
                if edge.is_unique(triangle, bad_tri):
                    polygon.add(edge)
        for triangle in bad_tri:
            triangulation.remove(triangle)
        for edge in polygon:
            new_tri = Triangle(edge.p1, edge.p2, point)
            triangulation.append(new_tri)

    # Nao precisa disso pro voronoi:
    # Remove os triangulos que contem vertices do super triangulo
    # Resultado e a triangulação de delaunay
    #result = [tri for tri in triangulation if not tri.contains_super(super_tri)]

    #for triangle in result:
        #for edge in triangle:
            #p1 = (edge.p1.x, edge.p1.y)
            #p2 = (edge.p2.x, edge.p2.y)
            #cv2.line(img, p1, p2, white, 1)

    # Acha os vizinhos de cada triangulo
    for triangle in triangulation:
        triangle.find_neighboors(triangulation)

    # Liga os circuncentros de cada triangulo vizinho,
    # gerando o diagrama de voronoi
    for triangle in triangulation:
        for neighboor in triangle.neighboors:
            c1 = (math.floor(triangle.cx), math.floor(triangle.cy))
            c2 = (math.floor(neighboor.cx), math.floor(neighboor.cy))
            cv2.line(img, c1, c2, white, 1)
            cv2.line(img2, c1, c2, white, 1)

    # Inicializa as cores
    colors = [0, 0, 0]
    # Flood fill
    for y in range(h):
        for x in range(w):
            color = tuple(img[y][x])
            if color == black:
                colors[0] += 1
                cv2.floodFill(img, None, (x, y), tuple(colors))
                if colors[0] >= 255:
                    colors[0] = -1
                    colors[1] += 1

    #showImg(img)
    # Dict de cells de lista de pontos
    cells = defaultdict(list)
    for y in range(h):
        for x in range(w):
            if tuple(img[y][x]) != white:
                cells[tuple(img[y][x])].append(Point(x, y, tuple(image[y][x])))

    best = defaultdict(tuple)
    for key, value in cells.items():
        colors = defaultdict(int)
        for point in value:
            colors[point.color] += 1
        # cor com maior frequencia p/ cada cell
        best[key] = max(colors, key=colors.get)


    for y in range(h):
        for x in range(w):
            if tuple(img[y][x]) != white:
                img2[y][x] = best[tuple(img[y][x])]


    showImg(img2)


    '''
    #bruteforce

    points = []

    for i in range(NUM_POINTS):
        y = randint(0, h - 1)
        x = randint(0, w - 1)

        b = int(image[y][x][0])
        g = int(image[y][x][1])
        r = int(image[y][x][2])
        points.append(Point(x, y, (b, g, r)))

    showImg(bruteforce(points))
    '''

def bruteforce(points):
    out = np.zeros((h, w, 3), np.uint8)
    for y in range(h):
        for x in range(w):
            closest = h * w
            pixel = Point(x, y)
            for point in points:
                dist = point.dist(pixel)
                if closest > dist:
                    cv2.circle(out, (x, y), 1, point.color, -1)
                    closest = dist
    return out

def showImg(img):
    cv2.imshow('image', img)
    cv2.waitKey(0)

if __name__ == "__main__":
    main()
