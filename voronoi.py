import cv2
import numpy as np
import points_gen
import sys #pra pegar o N e o nome do arquivo por argumento
import math
from collections import defaultdict

black = (0, 0, 0)
white = (255, 255, 255)

class Point(object):
    def __init__(self, x, y, color=None):
        self.x = x
        self.y = y
        self.color = color

    def __str__(self):
        return "Point(%s, %s)"%(self.x,self.y)

#    def __lt__(self, other):
#        return self.y < other.y

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
        return "Edge(%s, %s)"%(self.p1,self.p2)

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
        # Para cada aresta do triângulo, procura por uma igual nos
        # outros triãngulos da triangulação
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
    for point in points:
        bad_tri = set()
        # remove da triangulação os triângulos nos quais o ponto
        # está fora do circuncentro. Eles são triângulos inválidos
        for triangle in triangulation:
            if point.is_in_circuncircle(triangle):
                bad_tri.add(triangle)
        polygon = set()
        # encontra as arestas do poligono, que será
        # usado na próxima triangulação
        for triangle in bad_tri:
            for edge in triangle:
                if edge.is_unique(bad_tri):
                    polygon.add(edge)
        for triangle in bad_tri:
            triangulation.remove(triangle)
        # insere os novos triângulos (formados pelas extremidades de
        # cada aresta do polígono ligadas ao ponto) na triangulação
        for edge in polygon:
            new_tri = Triangle(edge.p1, edge.p2, point)
            triangulation.append(new_tri)

    ### Nao precisa disso pro voronoi, mas é interessante deixar
    ### a imagem da triangulação para mostrar como funciona
    # Remove os triangulos que contem vertices do super triangulo.
    # O resultado é a triangulação de delaunay
    delaunay_triangles = [tri for tri in triangulation if not tri.contains_super(super_tri)]
    delaunay = np.zeros((height, width, 1), np.uint8)
    for triangle in delaunay_triangles:
        for edge in triangle:
            p1 = (edge.p1.x, edge.p1.y)
            p2 = (edge.p2.x, edge.p2.y)
            cv2.line(delaunay, p1, p2, white, 1)
    showImg(delaunay)

    print("Gerando o diagrama de Voronoi...")
    # Acha os vizinhos de cada triangulo
    for triangle in triangulation:
        triangle.find_neighboors(triangulation)

    # Liga os circuncentros dos triângulos vizinhos,
    # gerando o diagrama de voronoi
    voronoi = np.zeros((height, width, 3), np.uint8)
    for triangle in triangulation:
        for neighboor in triangle.neighboors:
            c1 = (math.floor(triangle.cx), math.floor(triangle.cy))
            c2 = (math.floor(neighboor.cx), math.floor(neighboor.cy))
            cv2.line(voronoi, c1, c2, white, 1)
    showImg(voronoi)
    sys.exit()

    print("Colorindo células na imagem final...")
    voronoi_labels = voronoi.copy()
    # Flood fill: para cada célula (área preta, delimitada por
    # arestas brancas), dá uma cor BGR (label) diferente:
    #   Começa com (1, 0, 0) e vai até (255, 0, 0),
    #   então vai para (0, 1, 0) indo até (255, 1, 0)
    #   e assim sucessivamente até (255, 255, 0).
    # No total são (256*256)-1 = 65535 cores de células diferentes.
    # (o -1 é porque (0,0,0) não conta, ele significa célula não-preenchida)
    next_color = [1, 0, 0]
    for y in range(height):
        for x in range(width):
            color = tuple(voronoi_labels[y][x])
            if color == black:
                # Se achou uma célula não preenchida (preta),
                # inunda com a próxima cor/label
                cv2.floodFill(voronoi_labels, None, (x, y), tuple(next_color))
                next_color[0] += 1
                if next_color[0] == 255:
                    next_color[0] = -1
                    next_color[1] += 1

    # Dict de cells, onde cada célula (identificada pelo label),
    # tem uma lista de pontos que pertencem a ela e a cor desse
    # pixel na imagem original.
    cells = defaultdict(list)
    for y in range(height):
        for x in range(width):
            if tuple(voronoi_labels[y][x]) != white:
                cells[tuple(voronoi_labels[y][x])].append(Point(x, y, tuple(image[y][x])))

    # para cada célula, vê a cor que mais aparece na imagem original
    best = defaultdict(tuple)
    for key, value in cells.items():
        colors = defaultdict(int)
        # para isso, cria um histograma só com os pixels daquela célula
        for point in value:
            colors[point.color] += 1
        best[key] = max(colors, key=colors.get)

    #preenche a imagem final com as cores selecionadas
    out = np.zeros((height, width, 3), np.uint8)
    for y in range(height):
        for x in range(width):
            if tuple(voronoi_labels[y][x]) != white:
                out[y][x] = best[tuple(voronoi_labels[y][x])]
            else:
                out[y][x] = white

    # Tira as linhas brancas
    # OPCAO 1: borrar
    #   Cria um efeito de gradiente nas arestas. Se uma aresta
    #   é azul claro e outra azul escuro, a parte onde elas se
    #   encostam fica azul médio
    #out = cv2.blur(out,(5,5))
    # OPCAO 2: filtro mínimo (aka. erosão)
    #   Como os pixels da linha são brancos, pegar o mínimo sempre
    #   vai pegar o valor de alguma célula vizinha
    out = cv2.erode(out, np.ones((5,5),np.uint8), iterations = 1)
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

    # Bora para tirar ruído
    image = cv2.GaussianBlur(image,(7,7),0)

    #points = points_gen.random_points(image, NUM_POINTS)
    points = points_gen.weighted_random(image, NUM_POINTS)

    #se quiser salvar ou mostrar uma imagem com os pontos
    points_img = np.zeros((height, width, 1), np.uint8)
    for point in points:
        points_img[point.y][point.x] = 255
    saveImg(points_img, image_name + '-1points.' + extension)
    showImg(points_img)

    #out = brute_force(image, points)
    out, delaunay, voronoi = bowyer_watson(image, points)

    saveImg(delaunay, image_name + '-2delaunay.' + extension)
    for point in points:
        x = point.x
        y = point.y
        cv2.circle(voronoi, (x,y), 1, (0,255,0), -1)
    #showImg(voronoi)
    saveImg(voronoi, image_name + '-3voronoi.' + extension)
    saveImg(out, image_name + '-4out.' + extension)

if __name__ == "__main__":
    main()
