# Projeto Integrador: Aplicações de Inteligência Artificial

## 📚 Visão Geral do Projeto

Este projeto implementa e treina um agente de Inteligência Artificial utilizando o algoritmo **Q-Learning** para jogar o jogo de tabuleiro **Kamisado**. Ele explora conceitos de aprendizado por reforço e compara o desempenho com um agente Minimax.

## 🎲 O Jogo Kamisado

Kamisado é um jogo de tabuleiro 8x8 para dois jogadores. O objetivo é mover suas peças até a linha de base do oponente. A regra principal é que a cor da casa onde uma peça para determina a cor da peça que o oponente deve mover no próximo turno. O jogo também possui uma condição de empate para evitar estagnação.

## 🤖 Agentes de Inteligência Artificial

Exploramos dois agentes:

1.  **Agente Minimax:** Usa busca em árvore e uma **heurística** para encontrar a melhor jogada.
2.  **Agente Q-Learning:** Aprende a jogar por **experiência e experimentação**, construindo uma **Tabela Q**.

## 💻 Estrutura do Código

O código é organizado em funções e classes para representar o jogo e os agentes:

* Representação do tabuleiro e estado (`encode_state`).
* Funções para movimentos (`successors`) e fim de jogo (`game_over`).
* Classes `QLearningAgent` e `MinimaxAgent`.
* Lógica de treinamento (`train_against_minimax`) com currículo.
* Menu interativo para execução.

## 🔗 Materiais da Apresentação

* **Slides da Apresentação:** [Kamisado Q-Learning Slides](https://www.canva.com/design/DAGqPu_Dvq8/JGwVtBlIk1j-1hismn5R4w/edit?utm_content=DAGqPu_Dvq8&utm_campaign=designshare&utm_medium=link2&utm_source=sharebutton)
* **Vídeo da Apresentação:** [Assista ao Vídeo no YouTube](https://youtu.be/K9RebnOcXds)
* **Notebook no Google Colab:** [Acesse o Projeto no Google Colab](https://colab.research.google.com/drive/1uN5An6r4L0KLboHrVVgS3eeuVc0CRMnH?usp=sharing)


## 📊 Resultados e Desafios

O agente Q-Learning foi treinado por um total de **10.000** episódios contra um Minimax de profundidade crescente.

* **Desempenho Final (Estatísticas de Treinamento - Primeiro Ciclo de 10.000 episódios):**
    * Vitórias (como Pretas): **31**
    * Derrotas (como Pretas): **51**
    * Empates (estatística interna): **0** (conforme registrado na ferramenta de stats, mas muitos jogos resultaram em estagnação).
    * Taxa de vitórias do Q-Agent: **37.8%** (com base apenas em vitórias e derrotas não-empate).
    * Número total de estados-ação aprendidos: **570** Q-entradas.

* **Avaliação de Desempenho (100 Partidas Q-Learning vs Minimax):**
    * Q-Agent (vitórias): **0/100**
    * Minimax (vitórias): **0/100**
    * Empates: **100/100**
    * **Análise:** A avaliação consistente em empates demonstra a dificuldade do agente em converter o aprendizado em vitórias diretas contra um Minimax, e a prevalência de estagnação no jogo.

* **Desafios Chave:**
    * **Exploração Limitada:** Atingir um número maior de estados-ação visitados mostrou-se um desafio, impactando o aprendizado global.
    * **Custo Computacional:** A complexidade da busca Minimax (especialmente em profundidade 3) resultou em tempos de treinamento prolongados (aproximadamente 20 minutos por 1000 episódios na fase final).
    * **Convergência:** A convergência para um desempenho superior em jogos complexos de alto espaço de estados, como o Kamisado, demanda um volume de treinamento excepcionalmente grande (centenas de milhares ou milhões de episódios), que excedeu o escopo e o tempo deste projeto.

* **Soluções Aplicadas:** Implementamos ajustes nos hiperparâmetros de exploração (aumentando `EPSILON_MIN` e diminuindo `EPSILON_DECAY`), na função de recompensa (penalidades mais agressivas por empate e por turno) e no currículo de treinamento (profundidade do Minimax gradual) para tentar otimizar o aprendizado e a exploração do ambiente.

## 💡 Considerações Finais

Este projeto demonstrou a implementação funcional de um agente de Inteligência Artificial baseado em **Q-Learning** para o jogo **Kamisado**, interagindo com um oponente **Minimax**.

A experiência prática permitiu uma compreensão aprofundada de conceitos como representação de estado, balanceamento entre exploração/explotação e calibração de recompensas e hiperparâmetros.

A principal conclusão do trabalho é que, apesar do aprendizado observado e dos ajustes realizados, a convergência para um desempenho de vitória consistente em jogos complexos como o Kamisado exige um **volume de treinamento excepcionalmente grande (centenas de milhares ou milhões de episódios)**. Isso ressalta os desafios de escala do Aprendizado por Reforço, demonstrando a necessidade de vastos recursos computacionais e tempo para otimizar agentes em ambientes complexos.

---
