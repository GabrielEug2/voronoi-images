import cv2
import numpy as np
import points_gen
import sys #pra pegar o N e o nome do arquivo por argumento
import math
from collections import defaultdict

black = (0, 0, 0)
white = (255, 255, 255)

#####################################################################
### Bowyer Watson, vai inserindo um ponto de cada vez
#####################################################################

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

    # Se a distancia do circuncentro do triangulo ate o ponto
    # e menor que o raio, esta dentro do circuncirculo
    def is_in_circuncircle(self, triangle):
        return self.dist(triangle.center) <= triangle.cr

class Edge(object):
    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2

    def __str__(self):
        return "Edge(%s, %s)"%(self.p1,self.p2)

    # Verifica se nenhum outro triangulo tem essa aresta
    def is_unique(self, triangles):
        count = 0
        for triangle in triangles:
            for edge in triangle:
                # Lembrando que AB = BA, a outra aresta pode ter os pontos invertidos
                if (edge.p1 == self.p1 and edge.p2 == self.p2) or (edge.p1 == self.p2 and edge.p2 == self.p1):
                    count += 1
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
    # Pode dar problema (d = 0), especialmente com NUM_POINTS grande
    # Tem que ver como resolver isso... ou como implementar o fortune...
    ### solução temporária: se d==0, d=1
    def circumcenter(self):
        p1 = self.p1
        p2 = self.p2
        p3 = self.p3
        d = (p1.x - p3.x) * (p2.y - p3.y) - (p2.x - p3.x) * (p1.y - p3.y)
        if d == 0:
            d=1
        cx = (((p1.x - p3.x) * (p1.x + p3.x) + (p1.y - p3.y) * (p1.y + p3.y)) / 2 * (p2.y - p3.y) \
        -((p2.x - p3.x) * (p2.x + p3.x) + (p2.y - p3.y) * (p2.y + p3.y)) / 2 * (p1.y - p3.y)) \
        / d

        cy = (((p2.x - p3.x) * (p2.x + p3.x) + (p2.y - p3.y) * (p2.y + p3.y)) / 2 * (p1.x - p3.x) \
        -((p1.x - p3.x) * (p1.x + p3.x) + (p1.y - p3.y) * (p1.y + p3.y)) / 2 * (p2.x - p3.x)) \
        / d

        cr = np.hypot((p3.x - cx), (p3.y - cy))

        return cx, cy, cr

### Nao usa para o Voronoi, mas vou deixar aqui por enquanto.
### Se achar que não vai usar mesmo pode tirar
#    # Verifica se algum ponto do super triangulo esta sendo usado
#    def contains_super(self, super_tri):
#        # Set guarda valores unicos
#        s = set([self.p1, self.p2, self.p3, super_tri.p1, super_tri.p2, super_tri.p3])
#        # Entao se nao tiver 6 tem algum igual
#        return len(s) != 6

    # Procura os vizinhos de cada triangulo
    def find_neighboors(self, triangulation):
        # Para cada uma das 3 arestas do triangulo, olha os outros
        # triângulos da triangulação para ver se tem a aresta igual
        for edge in self.edges:
            shared = False
            for triangle in triangulation:
                if triangle is not self:
                    for e in triangle:
                        # Lembrando que AB = BA, o outro triângulo pode ter os pontos invertidos
                        if (edge.p1 == e.p1 and edge.p2 == e.p2) or (edge.p1 == e.p2 and edge.p2 == e.p1):
                            self.neighboors.append(triangle)
                            # se achou o vizinho daquele lado, vai para o próximo
                            shared = True
                            break
                if shared:
                    break

def bowyer_watson(image, altura, largura, points):
    # Bowyer-Watson
    # https://en.wikipedia.org/wiki/Bowyer%E2%80%93Watson_algorithm
    # Ainda e lento...

    # Pontos que criam um "super-triangulo" que contem o plano inteiro
    sp1 = Point(-math.ceil(largura*1.5), -1) # a esquerda, encima
    sp2 = Point(math.ceil(largura*2.5), -1) # a direita, encima
    sp3 = Point(largura//2, math.ceil(altura*2.5)) # centralizado, embaixo
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

    # Nao precisa disso pro voronoi:
    # Remove os triangulos que contem vertices do super triangulo
    # Resultado e a triangulação de delaunay
    #result = [tri for tri in triangulation if not tri.contains_super(super_tri)]
    #for triangle in result:
        #for edge in triangle:
            #p1 = (edge.p1.x, edge.p1.y)
            #p2 = (edge.p2.x, edge.p2.y)
            #cv2.line(img, p1, p2, white, 1)

    print("Verificando vizinhos...")
    # Acha os vizinhos de cada triangulo
    for triangle in triangulation:
        triangle.find_neighboors(triangulation)

    print("Gerando o diagrama de Voronoi...")
    # Liga os circuncentros dos triângulos vizinhos,
    # gerando o diagrama de voronoi
    diag = np.zeros((altura, largura, 3), np.uint8)
    for triangle in triangulation:
        for neighboor in triangle.neighboors:
            c1 = (math.floor(triangle.cx), math.floor(triangle.cy))
            c2 = (math.floor(neighboor.cx), math.floor(neighboor.cy))
            cv2.line(diag, c1, c2, white, 1)
    #showImg(diag)
    salvaImagem(diag, 'voronoi.bmp')
    out = diag.copy()

    # Flood fill: para cada célula (blob preto, cercado por
    # arestas brancas), dá um label diferente
    next_color = [0, 0, 0]
    for y in range(altura):
        for x in range(largura):
            color = diag[y][x]
            if tuple(color) == black:
                next_color[0] += 1
                cv2.floodFill(diag, None, (x, y), tuple(next_color))
                # evita estourar
                if next_color[0] == 255:
                    next_color[0] = 0
                    next_color[1] += 1
                if next_color[1] == 255:
                    next_color[1] = 0
                    next_color[2] += 1

    # Dict de cells, onde cada célula (identificada pelo label),
    # tem uma lista de pontos que pertencem a ela e a cor desse
    # pixel na imagem original.
    cells = defaultdict(list)
    for y in range(altura):
        for x in range(largura):
            if tuple(diag[y][x]) != white:
                cells[tuple(diag[y][x])].append(Point(x, y, tuple(image[y][x])))

    # para cada célula, vê a cor que mais aparece na imagem original
    out = np.zeros((altura, largura, 3), np.uint8)
    best = defaultdict(tuple)
    for key, value in cells.items():
        colors = defaultdict(int)
        # para isso, cria um histograma só com os pixels daquela célula
        for point in value:
            colors[point.color] += 1
        best[key] = max(colors, key=colors.get)

    #preenche a imagem final com as cores selecionadas
    for y in range(altura):
        for x in range(largura):
            if tuple(diag[y][x]) != white:
                out[y][x] = best[tuple(diag[y][x])]
            else:
                out[y][x] = white

    # Tira as linhas brancas
    # OPCAO 1: borrar
    #   Cria um efeito de gradiente nas arestas. Se uma aresta
    #   é azul claro e outra azul escuro, a parte onde elas se
    #   encostam fica azul médio
    #out = cv2.blur(img,(5,5))
    # OPCAO 2: filtro mínimo (aka. erosão)
    #   Como os pixels da linha são brancos, pegar o mínimo sempre
    #   vai pegar o valor de alguma célula vizinha
    out = cv2.erode(out, np.ones((5,5),np.uint8), iterations = 1)
    return out

#####################################################################
### Bruteforce, lento pra caramba
#####################################################################

def bruteforce(img, altura, largura, points):
    # para cada pixel, calcula a distância até todos os pontos, e
    # fica com a cor do que for mais perto
    out = np.zeros((altura, largura, canais), np.uint8)
    for y in range(0, altura):
        for x in range(0, largura):
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

def salvaImagem(img, nome_arq):
    #img = cv2.convertScaleAbs(img, alpha=(255.0))
    cv2.imwrite(nome_arq, img)

def main():
    if len(sys.argv) != 3:
        print("Melhor assim, não tem que ficar mudando parâmetros no código:")
        print("\n\tpython voronoi.py image_name N\n")
        print("image_name é o nome da imagem e N o numero de pontos")
        exit()

    # sys.argv[0] é o arquivo .py
    image_name = sys.argv[1]
    NUM_POINTS = int(sys.argv[2])

    image = cv2.imread(image_name, 1)
    altura = image.shape[0]
    largura = image.shape[1]
    canais = 3

    #points = points_gen.random_points(image, NUM_POINTS)
    points = points_gen.random_plus_edges(image, NUM_POINTS)

    #out = brute_force(image, altura, largura, points)
    out = bowyer_watson(image, altura, largura, points)

    image_name = image_name.split('.')[0] #tira a extensão
    salvaImagem(out, image_name + '-voronoi.bmp')

if __name__ == "__main__":
    main()
