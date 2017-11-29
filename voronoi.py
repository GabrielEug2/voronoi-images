from collections import defaultdict
import sys
import math
import time
import cv2
import numpy as np
import points_gen


BLACK = (0, 0, 0)
WHITE = (255, 255, 255)


class Point(object):
    """ Classe que define pontos (pixels) a partir de coordenadas x, y e sua cor """
    def __init__(self, x, y, color=None):
        self.x = x
        self.y = y
        self.color = color

    def __str__(self):
        return "Point({}, {})".format(self.x, self.y)

    def dist(self, p):
        """ Euclidean distance """
        dx = self.x - p.x
        dy = self.y - p.y
        return math.hypot(dx, dy)

    def is_in_circuncircle(self, triangle):
        """ Se a distância do circuncentro do triângulo até o ponto
        é menor que o raio, está dentro do circuncirculo
        """
        return self.dist(triangle.center) <= triangle.cr


class Edge(object):
    """ Classe que define arestas a partir de 2 pontos """
    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2

    def __str__(self):
        return "Edge({}, {})".format(self.p1, self.p2)

    def is_equal(self, other):
        """ Verifica se duas arestas são iguais """
        return self.p1 == other.p1 and self.p2 == other.p2

    def is_unique(self, triangles):
        """ Verifica se nenhum outro triângulo tem essa aresta """
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
    """ Classe que define triângulos a partir de 3 pontos """
    def __init__(self, p1, p2, p3):
        self.p1 = p1
        self.p2 = p2
        self.p3 = p3
        self.e1 = Edge(p1, p2)
        self.e2 = Edge(p2, p3)
        self.e3 = Edge(p1, p3)
        self.edges = [self.e1, self.e2, self.e3]
        self.cx, self.cy, self.cr = self.circumcenter()
        self.center = Point(self.cx, self.cy)

    def __iter__(self):
        return iter(self.edges)

    def __str__(self):
        return "Points:({}, {}, {})".format(self.p1, self.p2, self.p3)

    def circumcenter(self):
        """ Calcula o circuncentro (retorna as coordenadas x, y e o raio)
        Retirado de: http://www.ics.uci.edu/~eppstein/junkyard/circumcenter.html (segundo comentário)
        Pode dar problema (pontos colineares que resultam em d = 0)
        mas é raro de acontecer
        """
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

    def contains_super(self, super_tri):
        """ Verifica se algum ponto do super triangulo esta sendo usado """
        # Um set guarda valores únicos
        pontos = set([self.p1, self.p2, self.p3, super_tri.p1, super_tri.p2, super_tri.p3])
        # Então se não tiver 6, tem algum igual
        return len(pontos) != 6


def bowyer_watson(image, height, width, points):
    """ Bowyer Watson, algoritmo incremental para geração de
    triangulações de delaunay e diagramas de voronoi
    https://en.wikipedia.org/wiki/Bowyer%E2%80%93Watson_algorithm
    """

    # Pontos que criam um "super-triangulo" que contem o plano inteiro
    sp1 = Point(-math.ceil(width*1.5), -1) # a esquerda, encima
    sp2 = Point(math.ceil(width*2.5), -1) # a direita, encima
    sp3 = Point(width//2, math.ceil(height*2.5)) # centralizado, embaixo
    super_tri = Triangle(sp1, sp2, sp3)

    triangulation = []
    triangulation.append(super_tri)

    '''
    Guarda os 2 triângulos vizinhos de cada aresta.
    Foram usados 2 Points no lugar de um Edge, pois os objetos
    de cada aresta são diferentes (mesmo com pontos iguais),
    então eram criadas 2 keys diferentes no dict.
    '''
    neighbors = defaultdict(list)
    neighbors[(super_tri.e1.p1, super_tri.e1.p2)].append(super_tri)
    neighbors[(super_tri.e2.p1, super_tri.e2.p2)].append(super_tri)
    neighbors[(super_tri.e3.p1, super_tri.e3.p2)].append(super_tri)

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
            neighbors[(triangle.e1.p1, triangle.e1.p2)].remove(triangle)
            neighbors[(triangle.e2.p1, triangle.e2.p2)].remove(triangle)
            neighbors[(triangle.e3.p1, triangle.e3.p2)].remove(triangle)

        # Insere os novos triângulos (formados pelas extremidades de
        # cada aresta do polígono ligadas ao ponto) na triangulação
        for edge in polygon:
            new_tri = Triangle(edge.p1, edge.p2, point)
            triangulation.append(new_tri)
            neighbors[(new_tri.e1.p1, new_tri.e1.p2)].append(new_tri)
            neighbors[(new_tri.e2.p1, new_tri.e2.p2)].append(new_tri)
            neighbors[(new_tri.e3.p1, new_tri.e3.p2)].append(new_tri)

    # Remove os triangulos que contem vertices do super triangulo.
    # O resultado é a triangulação de delaunay
    delaunay_triangles = [tri for tri in triangulation if not tri.contains_super(super_tri)]
    delaunay = np.zeros((height, width, 1), np.uint8)
    for triangle in delaunay_triangles:
        for edge in triangle:
            p1 = (edge.p1.x, edge.p1.y)
            p2 = (edge.p2.x, edge.p2.y)
            cv2.line(delaunay, p1, p2, WHITE, 1)

    voronoi = voronoi_diagram(triangulation, neighbors, height, width)
    out = voronoi_painting(voronoi, image, height, width)

    return out, delaunay, voronoi


def voronoi_diagram(triangulation, neighbors, height, width):
    """ Cria uma imagem do diagrama de voronoi (somente as arestas)
    a partir da triangulação de delaunay
    """
    print("Gerando o diagrama de Voronoi...")
    # Liga os circuncentros dos triângulos vizinhos.
    # O resultado é o diagrama de voronoi
    voronoi = np.zeros((height, width, 3), np.uint8)
    for triangle in triangulation:
        for edge in triangle:
            for neighbor in neighbors[(edge.p1, edge.p2)]:
                if neighbor is not triangle:
                    c1 = (math.ceil(triangle.cx), math.ceil(triangle.cy))
                    c2 = (math.ceil(neighbor.cx), math.ceil(neighbor.cy))
                    cv2.line(voronoi, c1, c2, WHITE, 1)

    return voronoi


def voronoi_painting(voronoi, image, height, width):
    """ Pinta o diagrama de voronoi com as cores mais
    comuns de cada célula e remove ou disfarça as arestas
    """
    print("Colorindo células na imagem final...")
    # Acha as células (componentes conexos)
    voronoi_inv = cv2.cvtColor(voronoi, cv2.COLOR_BGR2GRAY)
    voronoi_inv = cv2.bitwise_not(voronoi_inv)
    _, labels = cv2.connectedComponents(voronoi_inv, None, 4)
    out = voronoi.copy()

    '''
    # Faz a mesma coisa que todo o resto dessa função
    # (tirando a parte de tirar/pintar as arestas) mas é mais lento
    
    
    for label in np.unique(labels):
        mask = (labels == label).astype(np.uint8)
        y,x = np.asarray(np.where(labels == label)).T[0]
        mean = cv2.mean(image, mask)
        cv2.floodFill(out, None, (x, y), mean)
    '''

    # Borra a imagem original para diminuir a diferença entre as cores
    #blurred = cv2.medianBlur(image, 5)

    # Dict de cells, onde cada célula (identificada pelo label),
    # tem uma lista de pixels que pertencem a ela
    cells = defaultdict(list)
    # Adiciona cada ponto a sua respectiva célula no dict
    for y in range(height):
        for x in range(width):
            if labels[y][x] != 0:
                cells[labels[y][x]].append(Point(x, y, tuple(map(int, image[y][x]))))

    # para cada célula, vê a cor média na imagem original
    for key, points in cells.items():
        bavg = gavg = ravg = area = 0
        for point in points:
            bavg += point.color[0]
            gavg += point.color[1]
            ravg += point.color[2]
            area += 1
            x = point.x
            y = point.y
        avg = (bavg//area, gavg//area, ravg//area)
        cv2.floodFill(out, None, (x, y), avg)
    '''
    # para cada célula, vê a cor que mais aparece na imagem original
    for key, points in cells.items():
        hist = defaultdict(int)
        # para isso, cria um histograma só com os pixels daquela célula
        for point in points:
            hist[point.color] += 1
            x = point.x
            y = point.y
        color = tuple(map(int, max(hist, key=hist.get)))
        cv2.floodFill(out, None, (x, y), color)
    '''
    # Faz algo com as fronteiras entre as células (linhas brancas)

    # 1) Muda a cor das linhas de acordo com as
    # intensidades da imagem original -->
    #   fronteiras ainda aparecem, mas ficam de
    #   uma cor que combina melhor com a imagem
    #   Imagem preta/cinza-escuro --> linhas claras
    #   Imagem branca/cinza-claro --> linhas pretas
    '''
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    hist = cv2.calcHist([gray],[0],None,[256],[0,256])
    intens = np.argmax(hist) #indice (intensidade) da posição com o maior valor
    intens = 255-intens
    out[np.where((voronoi == [255,255,255]).all(axis = 2))] = [intens,intens,intens]
    '''
    # 2) Remove as linhas -->
    #   faz um filtro da mediana, e só substitui o valor
    #   nos pixels das fronteiras (para não deformar as
    #   células)
    blurred = cv2.medianBlur(out, 11)

    edges = np.asarray(np.where(voronoi == WHITE)).T
    for y, x, _ in edges:
        out[y][x] = blurred[y][x]

    return out


def bruteforce(img, height, width, points):
    """ Para cada pixel da imagem, calcula a distância até todos os pontos e
    escolhe a cor do mais próximo
    """
    out = np.zeros((height, width, 1), np.uint8)
    for y in range(0, height):
        for x in range(0, width):
            min_dist = 10000000
            for point in points:
                dist = np.hypot((x - point.x), (y - point.y))
                if dist < min_dist:
                    min_dist = dist
                    x_min_dist = point.x
                    y_min_dist = point.y
            out[y, x] = img[y_min_dist, x_min_dist]
    return out


def show_img(img):
    """ Mostra img e espera por um keypress para continuar a execução """
    cv2.imshow('image', img)
    cv2.waitKey(0)


def main():
    if len(sys.argv) != 3:
        print("\nPara executar (Python 3):")
        print("\tpython voronoi.py image_path N\n")
        print("image_path -> caminho da imagem\nN -> quantidade de pontos\n")
        exit()

    # sys.argv[0] é o arquivo .py
    image_name = sys.argv[1]
    num_points = int(sys.argv[2])

    image = cv2.imread(image_name, 1)
    height = image.shape[0]
    width = image.shape[1]

    # Separa nome do arquivo e extensão para salvar as
    # imagens de saída com o nome parecido
    if "/" in image_name:
        image_name = image_name.split('/')[-1]
    image_name, extension = image_name.split('.')

    # Borra para tirar ruído
    image = cv2.GaussianBlur(image, (7, 7), 0)

    #points = points_gen.random_points(image, num_points)
    points = points_gen.weighted_random(image, num_points)

    #se quiser salvar ou mostrar uma imagem com os pontos
    points_img = np.zeros((height, width, 1), np.uint8)
    for point in points:
        points_img[point.y][point.x] = 255

    start_time = time.time()
    #out = brute_force(image, height, width, points)
    out, delaunay, voronoi = bowyer_watson(image, height, width, points)
    print("--- {:.2f} s ---".format(time.time() - start_time))

    for point in points:
        x = point.x
        y = point.y
        cv2.circle(voronoi, (x, y), 1, (0, 255, 0), -1)

    #show_img(points_img)
    #show_img(delaunay)
    #show_img(voronoi)
    show_img(out)

    cv2.imwrite(image_name + '-1points.' + extension, points_img)
    cv2.imwrite(image_name + '-2delaunay.' + extension, delaunay)
    cv2.imwrite(image_name + '-3voronoi.' + extension, voronoi)
    cv2.imwrite(image_name + '-4out.' + extension, out)


if __name__ == "__main__":
    main()
