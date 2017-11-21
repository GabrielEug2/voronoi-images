# voronoi
### Voronoi Images

Implementação do Algoritmo de Bowyer-Watson

TODO:
* Otimizar a busca por vizinhos
* O que é mais rápido na hora de mudar a cor das linhas?
    for y in range(height):
        for x in range(width):
            if tuple(voronoi[y][x]) == white:
                out[y][x] = new_color
    ...ou...
    for triangle in triangulation:
        for neighboor in triangle.neighboors:
            c1 = (math.ceil(triangle.cx), math.ceil(triangle.cy))
            c2 = (math.ceil(neighboor.cx), math.ceil(neighboor.cy))
            cv2.line(voronoi, c1, c2, new_color, 1)
