import cv2
import numpy as np
import points_gen
import sys #pra pegar o N e o nome do arquivo por argumento
import math
import time
from collections import defaultdict

black = (0, 0, 0)
white = (255, 255, 255)

class Point(object):
    def __init__(self, x, y, color=None):
        self.x = x
        self.y = y
        self.color = color

    def __str__(self):
        return "Point({}, {})".format(self.x,self.y)

    # Euclidean distance
    def dist(self, p):
        dx = self.x - p.x
        dy = self.y - p.y
        return math.hypot(dx, dy)

    # Se a distância do circuncentro do triângulo até o ponto
    # é menor que o raio, está dentro do circuncirculo
    def is_in_circuncircle(self, triangle):
        return self.dist(triangle.center) <= triangle.cr

class Edge(object):
    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2

    def __str__(self):
        return "Edge({}, {})".format(self.p1,self.p2)

    def is_equal(self, other):
        # Lembrando que AB = BA, temos que testar os dois casos
        # para ver se uma aresta é igual a outra
        if (self.p1 == other.p1 and self.p2 == other.p2) or (self.p1 == other.p2 and self.p2 == other.p1):
            return True
        return False

    # Verifica se nenhum outro triângulo tem essa aresta
    def is_unique(self, triangles):
        count = 0
        for triangle in triangles:
            for edge in triangle:
                if self.is_equal(edge):
                    # Quando for igual, conta 1
                    count += 1
                    # Se encontrou 2 vezes pode parar, não é única
                    if count == 2:
                        return False
        return True

class Triangle(object):
    def __init__(self, p1, p2, p3):
        self.p1 = p1
        self.p2 = p2
        self.p3 = p3
        self.edges = [Edge(p1, p2), Edge(p2, p3), Edge(p3, p1)]
        self.cx, self.cy, self.cr = self.circumcenter()
        self.center = Point(self.cx, self.cy)
        self.neighboors = []

    def __iter__(self):
        return iter(self.edges)

    def __str__(self):
        return "Points:(%s, %s, %s)"%(self.p1,self.p2,self.p3)

    # Calcula o circuncentro (retorna as coordenadas x,y e o raio)
    # Retirado de: http://www.ics.uci.edu/~eppstein/junkyard/circumcenter.html (segundo comentário)
    # Pode dar problema (pontos colineares que resultam em d = 0)
    # mas é bem raro usando pontos random
    def circumcenter(self):
        p1 = self.p1
        p2 = self.p2
        p3 = self.p3
        d = (p1.x - p3.x) * (p2.y - p3.y) - (p2.x - p3.x) * (p1.y - p3.y)

        if d == 0:
            print("Erro, pontos colineares")
            d = 1

        cx = (((p1.x - p3.x) * (p1.x + p3.x) + (p1.y - p3.y) * (p1.y + p3.y)) / 2 * (p2.y - p3.y) \
        -((p2.x - p3.x) * (p2.x + p3.x) + (p2.y - p3.y) * (p2.y + p3.y)) / 2 * (p1.y - p3.y)) \
        / d

        cy = (((p2.x - p3.x) * (p2.x + p3.x) + (p2.y - p3.y) * (p2.y + p3.y)) / 2 * (p1.x - p3.x) \
        -((p1.x - p3.x) * (p1.x + p3.x) + (p1.y - p3.y) * (p1.y + p3.y)) / 2 * (p2.x - p3.x)) \
        / d

        cr = np.hypot((p3.x - cx), (p3.y - cy))

        return cx, cy, cr


    # Verifica se algum ponto do super triangulo esta sendo usado
    def contains_super(self, super_tri):
        # Set guarda valores unicos
        s = set([self.p1, self.p2, self.p3, super_tri.p1, super_tri.p2, super_tri.p3])
        # Entao se nao tiver 6 tem algum igual
        return len(s) != 6

    # Procura os vizinhos de cada triangulo
    def find_neighboors(self, triangulation):
        # Para cada aresta do triângulo, procura por uma
        # igual no resto da triangulação
        for edge in self.edges:
            shared = False
            for triangle in triangulation:
                if triangle is not self:
                    for e in triangle:
                        if e.is_equal(edge):
                            self.neighboors.append(triangle)
                            # se achou o vizinho daquele lado, vai para o próximo
                            shared = True
                            break
                if shared:
                    break

#####################################################################
### Bowyer Watson, vai inserindo um ponto de cada vez
### https://en.wikipedia.org/wiki/Bowyer%E2%80%93Watson_algorithm
#####################################################################

def bowyer_watson(image, points):
    height = image.shape[0]
    width = image.shape[1]

    # Pontos que criam um "super-triangulo" que contem o plano inteiro
    sp1 = Point(-math.ceil(width*1.5), -1) # a esquerda, encima
    sp2 = Point(math.ceil(width*2.5), -1) # a direita, encima
    sp3 = Point(width//2, math.ceil(height*2.5)) # centralizado, embaixo
    super_tri = Triangle(sp1, sp2, sp3)

    triangulation = []
    triangulation.append(super_tri)

    print("Fazendo a triangulação de Delaunay...")
    # Vai inserindo um ponto de cada vez
    for point in points:
        # Remove da triangulação os triângulos nos quais o ponto
        # está dentro do circuncírculo. Eles são triângulos inválidos
        bad_tri = set()
        for triangle in triangulation:
            if point.is_in_circuncircle(triangle):
                bad_tri.add(triangle)
        # Encontra as arestas do poligono que será
        # usado na próxima triangulação
        polygon = set()
        for triangle in bad_tri:
            for edge in triangle:
                if edge.is_unique(bad_tri):
                    polygon.add(edge)
        for triangle in bad_tri:
            triangulation.remove(triangle)
        # Insere os novos triângulos (formados pelas extremidades de
        # cada aresta do polígono ligadas ao ponto) na triangulação
        for edge in polygon:
            new_tri = Triangle(edge.p1, edge.p2, point)
            triangulation.append(new_tri)

    # Remove os triangulos que contem vertices do super triangulo.
    # O resultado é a triangulação de delaunay
    delaunay_triangles = [tri for tri in triangulation if not tri.contains_super(super_tri)]
    delaunay = np.zeros((height, width, 1), np.uint8)
    for triangle in delaunay_triangles:
        for edge in triangle:
            p1 = (edge.p1.x, edge.p1.y)
            p2 = (edge.p2.x, edge.p2.y)
            cv2.line(delaunay, p1, p2, white, 1)

    print("Gerando o diagrama de Voronoi...")
    # Acha os vizinhos de cada triangulo
    for triangle in triangulation:
        triangle.find_neighboors(triangulation)

    # Liga os circuncentros dos triângulos vizinhos.
    # O resultado é o diagrama de voronoi
    voronoi = np.zeros((height, width, 3), np.uint8)
    for triangle in triangulation:
        for neighboor in triangle.neighboors:
            c1 = (math.ceil(triangle.cx), math.ceil(triangle.cy))
            c2 = (math.ceil(neighboor.cx), math.ceil(neighboor.cy))
            cv2.line(voronoi, c1, c2, white, 1)

    print("Colorindo células na imagem final...")
    # Acha as células (componentes conexos)
    voronoi_inv = cv2.cvtColor(voronoi, cv2.COLOR_BGR2GRAY)
    voronoi_inv = cv2.bitwise_not(voronoi_inv)
    _, labels = cv2.connectedComponents(voronoi_inv, None, 4)

    # Borra a imagem original para diminuir a diferença entre as cores
    blurred = cv2.medianBlur(image, 21)

    # Dict de cells, onde cada célula (identificada pelo label),
    # tem uma lista de pixels que pertencem a ela
    cells = defaultdict(list)
    # Adiciona cada ponto a sua respectiva célula no dict
    for y in range(height):
        for x in range(width):
            if labels[y][x] != 0:
                cells[labels[y][x]].append(Point(x, y, tuple(blurred[y][x])))

    # para cada célula, vê a cor que mais aparece na imagem original
    best = defaultdict(tuple)
    for key, points in cells.items():
        hist = defaultdict(int)
        # para isso, cria um histograma só com os pixels daquela célula
        for point in points:
            hist[point.color] += 1
        best[key] = max(hist, key=hist.get)

    #preenche a imagem final com as cores selecionadas
    out = voronoi.copy()
    for key, points in cells.items():
        x = points[0].x
        y = points[0].y
        color = best[key]
        b = int(color[0])
        g = int(color[1])
        r = int(color[2])
        cv2.floodFill(out, None, (x, y), (b, g, r))

    # Faz algo com as fronteiras entre as células (linhas brancas)

    # Tornar as linhas da cor que mais aparece nas células e
    # fazer anti-aliasing para reduzir serrilhamento -->
    #   fronteiras ainda aparecem, mas ficam de
    #   uma cor que combina mais com a imagem
    '''
    hist = defaultdict(int)
    for label, color in best.items():
        hist[color] += 1
    new_color = max(hist, key=hist.get)
    b = int(new_color[0])
    g = int(new_color[1])
    r = int(new_color[2])
    for y in range(height):
        for x in range(width):
            if tuple(voronoi[y][x]) == white:
                out[y][x] = [b, g, r]
    '''
    # Como as células tem cores "maciças", o resultado
    # é o mesmo que borrar a imagem inteira
    #out = cv2.GaussianBlur(out, (3,3), 0)

    # Pegar a cor do primeiro vizinho não-branco -->
    #   remove as fronteiras, mas é lento e não fica tão bonito
    '''
    aux = out.copy()
    for y in range(height):
        for x in range(width):
            if tuple(voronoi[y][x]) == white:
                colored = False
                for j in range(max(0, y-1), min(height-1, y+2)):
                    for i in range(max(0, x-1), min(width-1, x+2)):
                        if tuple(aux[j][i]) != white:
                            out[y][x] = aux[j][i]
                            colored = True
                            break
                    if colored:
                        break
    '''

    # Se for pra remover usa filtro da mediana (tem um bom resultado e é rápido)
    out = cv2.medianBlur(out, 11)

    return out, delaunay, voronoi

#####################################################################
### Bruteforce, lento pra caramba
#####################################################################

def bruteforce(img, points):
    height = image.shape[0]
    width = image.shape[1]
    channels = image.shape[2]

    # para cada pixel, calcula a distância até todos os pontos, e
    # fica com a cor do que for mais perto
    out = np.zeros((height, width, channels), np.uint8)
    for y in range(0, height):
        for x in range(0, width):
            min_dist = 10000000
            for point in points:
                dist = sqrt( (x-point.x)**2 + (y-point.y)**2 )
                if dist < min_dist:
                    min_dist = dist
                    x_min_dist = point.x
                    y_min_dist = point.y
            out[y,x] = img[y_min_dist, x_min_dist]
    return out

#####################################################################

def showImg(img):
    cv2.imshow('image', img)
    cv2.waitKey(0)

def saveImg(img, name):
    #img = cv2.convertScaleAbs(img, alpha=(255.0))
    cv2.imwrite(name, img)

def main():
    if len(sys.argv) != 3:
        print("\nMelhor assim, não tem que ficar mudando parâmetros no código:")
        print("\tpython voronoi.py image_name N")
        print("image_name é o nome da imagem e N o numero de pontos\n")
        exit()

    # sys.argv[0] é o arquivo .py
    image_name = sys.argv[1]
    NUM_POINTS = int(sys.argv[2])

    image = cv2.imread(image_name, 1)
    height = image.shape[0]
    width = image.shape[1]

    # Separa nome do arquivo e extensão para salvar as
    # imagens de saída (delaunay, voronoi) com o mesmo nome
    if "/" in image_name:
        image_name = image_name.split('/')[-1]
    image_name, extension = image_name.split('.')

    # Borra para tirar ruído
    image = cv2.GaussianBlur(image, (7,7), 0)

    #points = points_gen.random_points(image, NUM_POINTS)
    points = points_gen.weighted_random(image, NUM_POINTS)

    #se quiser salvar ou mostrar uma imagem com os pontos
    points_img = np.zeros((height, width, 1), np.uint8)
    for point in points:
        points_img[point.y][point.x] = 255

    start_time = time.time()
    #out = brute_force(image, points)
    out, delaunay, voronoi = bowyer_watson(image, points)
    print("--- {:.2f} s ---".format(time.time() - start_time))

    for point in points:
        x = point.x
        y = point.y
        cv2.circle(voronoi, (x,y), 1, (0,255,0), -1)

    #showImg(points_img)
    #showImg(delaunay)
    #showImg(voronoi)
    #showImg(out)

    saveImg(points_img, image_name + '-1points.' + extension)
    saveImg(delaunay, image_name + '-2delaunay.' + extension)
    saveImg(voronoi, image_name + '-3voronoi.' + extension)
    saveImg(out, image_name + '-4out.' + extension)

if __name__ == "__main__":
    main()
