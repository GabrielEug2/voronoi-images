# voronoi
### Voronoi Images

Implementação do Algoritmo de Bowyer-Watson

TODO:
* Testar método alternativo para gerar pontos:
    quanto mais perto da borda, maior a chance de ser escolhido
    (seria tipo um random com "pesos")
* Otimizar a busca por vizinhos
* Otimizar a identificação da cor mais comum das células
    * Implementar tolerância quando for ver qual é a cor mais frequente na célula
    * Após saber a cor ideal, pintar com flood fill, não pixel por pixel
* Melhorar o algoritmo (implementar o fortune?)
* Refatorar o código
