# -*- coding: utf-8 -*-
"""EP3 Kamisado Entrega

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1uN5An6r4L0KLboHrVVgS3eeuVc0CRMnH
"""

import numpy as np
from copy import deepcopy
import random
import math
import pickle
import os
import threading
import time

# ---------- CONFIGURÁVEIS ----------
EPISODES = 5000 # Constante global de referência
ALPHA = 0.1
GAMMA = 0.9
EPSILON_START = 1.0
EPSILON_MIN = 0.15
EPSILON_DECAY = 0.999
PICKLE_FILE = 'kamisado_q_table.pkl'
SAVE_INTERVAL = 1000
EXPLORATION_POLICY = 'epsilon-greedy'
DRAW_THRESHOLD = 200

# Labels e tabuleiro
titulo = "KAMISADO - Q-LEARNING TURBINADO"
white_labels = [f'B{i+1}' for i in range(8)]
black_labels = [f'P{i+1}' for i in range(8)]

board = np.array([
    ["laranja", "azul", "roxo", "rosa", "amarelo", "vermelho", "verde", "marrom"],
    ["vermelho", "laranja", "rosa", "verde", "azul", "amarelo", "marrom", "roxo"],
    ["verde", "rosa", "laranja", "vermelho", "roxo", "marrom", "amarelo", "azul"],
    ["rosa", "roxo", "azul", "laranja", "marrom", "verde", "vermelho", "amarelo"],
    ["amarelo", "vermelho", "verde", "marrom", "laranja", "azul", "roxo", "rosa"],
    ["azul", "amarelo", "marrom", "roxo", "vermelho", "laranja", "rosa", "verde"],
    ["roxo", "marrom", "amarelo", "azul", "verde", "rosa", "laranja", "vermelho"],
    ["marrom", "verde", "vermelho", "amarelo", "rosa", "roxo", "azul", "laranja"]
])

color_emojis = {
    "laranja": "🟧", "azul": "🟦", "roxo": "🟪", "rosa": "🩷",
    "amarelo": "🟨", "vermelho": "🟥", "verde": "🟩", "marrom": "🟫"
}

COLOR_TO_INT = {color: i for i, color in enumerate(sorted(list(set(board.flatten()))))}
INT_TO_COLOR = {i: color for color, i in COLOR_TO_INT.items()}

# Funções do Jogo

def print_game_state(state):
    pos_map = {pos: lbl for lbl, pos in {**state['white'], **state['black']}.items()}

    print(f"\n{titulo}")
    # Cabeçalho das colunas. Queremos 6 espaços por célula + um espaço extra de alinhamento
    # Ex: "    A     B     C     D     E     F     G     H"
    print("      " + "     ".join(f"{chr(65 + c)}" for c in range(8)))

    for row in range(8):
        line = f"{8 - row} |" # Rótulo da linha
        for col in range(8):
            color_bg = board[row, col] # Cor de fundo da casa (do tabuleiro)
            label = pos_map.get((row, col), "") # Rótulo da peça (B1, P2, ou vazio)

            # String que representa a peça (ou vazia) com padding para 2 caracteres visuais
            padded_label = label.ljust(2)

            cell_content = f"{color_emojis[color_bg]}{padded_label}  " # Emoji + Label + 2 espaços

            line += cell_content

        line += f"| {8 - row}" # Rótulo da linha no final
        print(line)
    # Rodapé das colunas, alinhado com o cabeçalho
    print("      " + "     ".join(f"{chr(65 + c)}" for c in range(8)))

    epsilon_val = state.get('epsilon') # Pega o valor de epsilon, ou None se não existir
    if isinstance(epsilon_val, (float, int)): # Verifica se é um número
        epsilon_str = f"Epsilon: {epsilon_val:.3f}"
    else:
        epsilon_str = f"Epsilon: {epsilon_val or 'N/A'}" # Se não for número, usa o valor ou 'N/A'

    print(
        f"Turno: {'Brancas' if state['turn']=='white' else 'Pretas'} | " +
        f"Próxima cor: {state['next_color'] or 'Qualquer'} | " +
        epsilon_str # Usa a string de epsilon já formatada
    )

def initial_state():
    return {
        'white': {lbl: (7, i) for i, lbl in enumerate(white_labels)},
        'black': {lbl: (0, i) for i, lbl in enumerate(black_labels)},
        'turn': 'white',
        'next_color': None,
        'no_progress': 0
    }

def successors(state):
    current = state['turn']
    opponent = 'black' if current=='white' else 'white'
    valid = []
    occupied = set(state['white'].values()) | set(state['black'].values())
    for lbl, (r0, c0) in state[current].items():
        col0 = board[r0,c0]
        if state['next_color'] and col0!=state['next_color']: continue
        dirs = [(-1,-1),(-1,0),(-1,1)] if current=='white' else [(1,-1),(1,0),(1,1)]
        for dr,dc in dirs:
            step=1
            while True:
                r,c = r0+dr*step, c0+dc*step
                if not (0<=r<8 and 0<=c<8): break
                if (r,c) in occupied: break
                nxt = deepcopy(state)
                nxt[current][lbl]=(r,c)
                nxt['next_color']=board[r,c]
                nxt['turn']=opponent
                if board[r,c]==col0:
                    nxt['no_progress']+=1
                else:
                    nxt['no_progress']=0
                valid.append(nxt)
                step+=1
    return valid

def game_over(state):
    if state['no_progress']>=DRAW_THRESHOLD:
        return 'draw'
    for _,(r,c) in state['white'].items():
        if r==0: return 'white'
    for _,(r,c) in state['black'].items():
        if r==7: return 'black'
    return None

def encode_state(state):
    w = tuple(sorted(r*8+c for (r,c) in state['white'].values()))
    b = tuple(sorted(r*8+c for (r,c) in state['black'].values()))
    t = 1 if state['turn']=='black' else 0
    c_encoded = COLOR_TO_INT.get(state['next_color'], -1) # -1 para None
    return (w,b,t,c_encoded)

#A Agentes

class QLearningAgent:
    def __init__(self, alpha, gamma, epsilon, policy=EXPLORATION_POLICY):
        self.alpha, self.gamma = alpha, gamma
        self.epsilon = epsilon
        self.policy = policy
        self.q_table = {}
        self.stats = {'wins':0,'losses':0,'draws':0,'total_rewards':0}
        self.training_mode=True
        self._stop_saver=False
        self._saver=threading.Thread(target=self._periodic_save)
        self._saver.daemon=True
        self._saver.start()

    def _periodic_save(self):
      while not self._stop_saver:
        time.sleep(1)
        try:
            pass
        except Exception as e:
            print(f"⚠️ Erro ao salvar Q-table (assíncrono): {e}")

    def get_q(self,s,a): return self.q_table.get((s,a),0.0)

    def choose_action(self,state,actions):
        if not actions: return None
        s=encode_state(state)
        if self.training_mode and random.random()<self.epsilon:
            return random.choice(actions)
        if self.policy=='softmax':
            qs=[self.get_q(s,encode_state(a)) for a in actions]
            max_q = max(qs) if qs else 0
            exps=[math.exp(q - max_q) for q in qs]
            sum_exps = sum(exps)
            if sum_exps == 0:
                return random.choice(actions)
            ps=[e/sum_exps for e in exps]
            return random.choices(actions,ps)[0]
        # Greedy
        return max(actions, key=lambda a:self.get_q(s,encode_state(a)))

    def update(self,s,a,r,s2,next_acts):
        s_enc, a_enc = encode_state(s), encode_state(a)
        cur=self.get_q(s_enc,a_enc)
        nxt=0.0
        if next_acts:
            nxt=max(self.get_q(encode_state(s2),encode_state(a2)) for a2 in next_acts)
        self.q_table[(s_enc,a_enc)] = cur + self.alpha*(r+self.gamma*nxt-cur)

    def decay_epsilon(self):
        self.epsilon=max(EPSILON_MIN,self.epsilon*EPSILON_DECAY)

    def prune_q_table(self, threshold=1e-6):
      self.q_table = {k: v for k, v in self.q_table.items() if abs(v) > threshold}

    def save(self, filename):
      self.prune_q_table()
      with open(filename, 'wb') as f:
        pickle.dump({'q_table': self.q_table, 'stats': self.stats, 'epsilon': self.epsilon}, f)
      print(f"💾 Salvo: {len(self.q_table)} Q-entradas")

    def load(self,fn):
        if os.path.exists(fn):
            with open(fn,'rb') as f: data=pickle.load(f)
            self.q_table,self.stats,self.epsilon=data['q_table'],data['stats'],data['epsilon']
            print(f"📥 Carregado: {len(self.q_table)} Q-entradas")
            return True
        print("⚠️ Arquivo não encontrado")
        return False

    def stop(self):
        self._stop_saver=True
        self._saver.join()

# Função heurística
def advanced_heuristic(state):
    score = 0

    # Progresso em direção à vitória
    black_progress = sum(7 - pos[0] for pos in state['black'].values()) * 25
    white_progress = sum(pos[0] for pos in state['white'].values()) * 30
    progress = black_progress - white_progress

    # Controle do centro do tabuleiro
    center_positions = [(3, 3), (3, 4), (4, 3), (4, 4)]
    center_control = 0
    for pos in center_positions:
        if pos in state['black'].values():
            center_control += 50
        elif pos in state['white'].values():
            center_control -= 40

    # Mobilidade
    mobility = len(successors(state))
    if state['turn'] == 'black':
        mobility *= 10
    else:
        mobility *= -8

    # Combinação dos fatores
    score = progress * 0.5 + center_control * 0.3 + mobility * 0.2
    return int(score)

# Algoritmo Minimax com poda alpha-beta
def minimax_search(state, depth, alpha, beta, maximizing):
    winner = game_over(state)
    if winner:
        if winner == 'black': return 1000, state
        elif winner == 'white': return -1000, state
        else: return 0, state

    if depth == 0:
        return advanced_heuristic(state), state

    moves = successors(state)
    if not moves:
        return (-1000 if maximizing else 1000), state

    if maximizing:
        max_eval = float('-inf')
        best_move = None

        for move in moves:
            eval_val, _ = minimax_search(move, depth-1, alpha, beta, False)
            if eval_val > max_eval:
                max_eval = eval_val
                best_move = move
            alpha = max(alpha, eval_val)
            if beta <= alpha:
                break
        return max_eval, best_move

    else:
        min_eval = float('inf')
        best_move = None

        for move in moves:
            eval_val, _ = minimax_search(move, depth-1, alpha, beta, True)
            if eval_val < min_eval:
                min_eval = eval_val
                best_move = move
            beta = min(beta, eval_val)
            if beta <= alpha:
                break
        return min_eval, best_move

class MinimaxAgent:

    def __init__(self, depth=3):
        self.depth = depth

    def choose_action(self, state, possible_moves):
        if not possible_moves:
            return None
        _, move = minimax_search(state, self.depth, float('-inf'), float('inf'), state['turn'] == 'black')
        return move

def train_against_minimax(agent, num_episodes_to_train):
    print(f"🚀 Treinando por {num_episodes_to_train} episódios contra Minimax...")
    start_time = time.time() # Para medir o tempo de treinamento

    start_episode_idx = agent.stats.get('wins', 0) + agent.stats.get('losses', 0) + agent.stats.get('draws', 0)

    for i in range(num_episodes_to_train):
        ep = start_episode_idx + i # O índice real do episódio para o decaimento de epsilon

        # Currículo de profundidade para o Minimax (mais gradual)
        current_minimax_depth = 1 # Profundidade padrão
        if ep < 3000: # Estende a profundidade 1
            current_minimax_depth = 1
        elif ep < 8000: # Estende a profundidade 2
            current_minimax_depth = 2
        else: # Profundidade 3 só nos últimos 20% do treinamento (se for 10k episódios)
            current_minimax_depth = 3

        minimax = MinimaxAgent(depth=current_minimax_depth) # Instancia Minimax com profundidade atualizada
        state = initial_state()
        agent.training_mode = True
        agent.epsilon = max(EPSILON_MIN, EPSILON_START * (EPSILON_DECAY ** ep)) # Decaimento de epsilon

        while True:
            if state['turn'] == 'white':
                moves = successors(state)
                if not moves: # Sem movimentos válidos para o Minimax
                    winner = 'black' # Q-Agent vence por falta de movimentos do Minimax
                    break
                state = minimax.choose_action(state, moves)
                if state is None: # Se o minimax não encontrar um movimento (pode acontecer com profundidade 0 ou se successors estiver vazia)
                    winner = 'black' # Q-Agent vence
                    break

            else:
                moves = successors(state)
                if not moves: # Sem movimentos válidos para o Q-Agent
                    winner = 'white' # Minimax vence
                    break
                action = agent.choose_action(state, moves)
                if not action: # Se o Q-Agent não escolher uma ação
                    winner = 'white' # Minimax vence
                    break

                next_state = action
                next_moves = successors(next_state) # Próximos movimentos a partir do next_state
                winner = game_over(next_state)

                # recompensa reforçada
                if winner:
                  if winner == 'black':
                    reward = +1000.0
                    agent.stats['wins'] += 1
                  elif winner == 'white':
                    reward = -1000.0
                    agent.stats['losses'] += 1
                  else:
                    reward = -1200.0
                    agent.stats['draws'] += 1
                else:
                  delta = advanced_heuristic(next_state) - advanced_heuristic(state)
                  reward = delta * 0.5 - 0.2

                agent.update(state, action, reward, next_state, next_moves)
                state = next_state
                if winner: break

        # Relatório periódico e salvamento assíncrono (se houver alteração)
        if (i + 1) % SAVE_INTERVAL == 0: # Agora baseado no 'i' do ciclo atual de treinamento
            agent.save(PICKLE_FILE)
            elapsed_time = time.time() - start_time
            print(f"[Ep {ep+1}/{start_episode_idx + num_episodes_to_train}] ε={agent.epsilon:.3f} | Wins={agent.stats['wins']} | Tempo decorrido: {elapsed_time:.2f}s")
            start_time = time.time() # Reseta o tempo para o próximo intervalo

    # Salvar ao final do treinamento
    agent.save(PICKLE_FILE)
    print("✅ Treino contra Minimax concluído!")

def train_agent(agent, num_episodes_to_train): # Adicionado 'num_episodes_to_train'
    print(f"🚀 Treinando por {num_episodes_to_train} episódios (Self-Play)...")
    start_episode_idx = agent.stats.get('wins', 0) + agent.stats.get('losses', 0) + agent.stats.get('draws', 0)
    for i in range(num_episodes_to_train):
        ep = start_episode_idx + i
        state=initial_state()
        total_r=0
        while True:
            moves=successors(state)
            if not moves: break
            act=agent.choose_action(state,moves)
            if not act: break
            next_moves=successors(act)
            w=game_over(act)
            if w:
                r=1.0 if w=='black' else -1.0
                agent.stats['wins' if w=='black' else 'losses']+=1
            else:
                prog=(advanced_heuristic(act)-advanced_heuristic(state))*0.01
                r=prog-0.01
            agent.update(state,act,r,act,next_moves)
            state=act
            total_r+=r
            if w: break
        agent.decay_epsilon()
        agent.stats['total_rewards']+=total_r
        if (i+1)%100==0:
            tot=agent.stats['wins']+agent.stats['losses']+agent.stats['draws']
            print(f"Epi {ep+1}/{start_episode_idx + num_episodes_to_train} | ε={agent.epsilon:.3f} | Winrate={agent.stats['wins']/tot:.1%}")
    agent.save(PICKLE_FILE)
    print("✅ Treino concluído!")


def evaluate(agent,n=50):
    # Minimax depth para avaliação pode ser fixo ou ajustado
    minimax_eval_depth = 3
    minimax=MinimaxAgent(minimax_eval_depth)
    res={'q_wins':0,'minimax_wins':0,'draws':0}
    print(f"🧪 Avaliando {n} partidas...")
    agent.training_mode = False
    for i in range(n):
        state=initial_state()
        if i%2==0:
            state['turn']='black'
            current_first_player = 'Q-Agent'
        else:
            state['turn']='white'
            current_first_player = 'Minimax'

        while True:
            w=game_over(state)
            if w:
                if w == 'black':
                    res['q_wins']+=1
                elif w == 'white':
                    res['minimax_wins']+=1
                else: # draw
                    res['draws']+=1
                break
            moves=successors(state)
            if not moves:
                res['draws']+=1; break
            if state['turn']=='black':
                a=agent.choose_action(state,moves)
            else:
                a=minimax.choose_action(state,moves)
            if not a:
                res['draws']+=1; break
            state=a
        if (i+1)%10==0:
            print(f"{i+1}/{n} | Q:{res['q_wins']} Min:{res['minimax_wins']} Emp:{res['draws']}")
    print(f"Resultados: Q {res['q_wins']}/{n}, Min {res['minimax_wins']}/{n}, Emp {res['draws']}/{n}")
    return res


# Permite que um humano faça um movimento ou desista
def human_move(state):
    print_game_state(state)

    # Obter todos os movimentos válidos
    moves = successors(state)
    if not moves:
        print("⚠️ Sem movimentos disponíveis! Você perdeu.")
        return None

    # Mostrar opções de movimento
    print("\n📋 Movimentos disponíveis:")
    options = []
    # Cria uma representação mais amigável dos movimentos para o usuário
    current_player_pieces = state['white'] if state['turn'] == 'white' else state['black']
    for i, move in enumerate(moves):
        # Encontrar a peça movida
        moved_piece_lbl = None
        from_pos = None
        to_pos = None
        for lbl, original_pos in current_player_pieces.items():
            # Verifica se a posição da peça mudou no novo estado
            if original_pos != move[state['turn']][lbl]:
                moved_piece_lbl = lbl
                from_pos = original_pos
                to_pos = move[state['turn']][lbl]
                break # Encontrou a peça que se moveu

        if moved_piece_lbl and from_pos and to_pos:
            from_coord = f"{chr(65 + from_pos[1])}{8 - from_pos[0]}"
            to_coord = f"{chr(65 + to_pos[1])}{8 - to_pos[0]}"
            options.append((i, moved_piece_lbl, from_coord, to_coord))

    # Exibir opções
    if not options:
        print("Nenhum movimento válido pode ser exibido. Isso é um erro inesperado.")
        return None

    for i, lbl, from_coord, to_coord in options:
        print(f"{i}: {lbl} de {from_coord} para {to_coord}")

    # Opção de desistência
    print("\n🏳️  Digite 'desistir' para encerrar o jogo")

    # Obter escolha do jogador
    while True:
        choice = input("\n🎯 Sua jogada (número ou 'desistir'): ")

        # Verificar desistência
        if choice.strip().lower() == 'desistir':
            return 'quit'

        # Verificar se é um número válido
        try:
            choice_int = int(choice)
            if 0 <= choice_int < len(moves):
                return moves[choice_int]
            print("❌ Número inválido. Tente novamente.")
        except ValueError:
            print("❌ Entrada inválida. Digite um número ou 'desistir'.")

# Modo de jogo humano vs IA com opção de desistência
def play_vs_agent(agent):
    state = initial_state()
    print("\n=== 🎮 MODO DE JOGO: HUMANO vs IA ===")
    print("Você joga com as peças BRANCAS (B1-B8)")
    print("A IA joga com as peças PRETAS (P1-P8)")
    print("Digite 'desistir' durante sua vez para encerrar o jogo\n")

    # Garante que o agente está no modo de explotação (não treinamento)
    original_training_mode = agent.training_mode
    original_epsilon = agent.epsilon
    agent.training_mode = False
    agent.epsilon = 0.0 # Joga puramente de forma gananciosa

    try:
        while True:
            # Verificar fim de jogo
            winner = game_over(state)
            if winner:
                print_game_state(state)
                print(f"\n{'🎉 Você venceu!' if winner == 'white' else '🤖 IA venceu!' if winner == 'black' else '🤝 Empate!'}")
                break

            # Vez do humano
            if state['turn'] == 'white':
                result = human_move(state)

                # Verificar desistência
                if result == 'quit':
                    print("\n🏳️  Você desistiu! Vitória da IA.")
                    break

                # Verificar se não há movimentos
                if result is None:
                    print("🤖 IA vence por falta de movimentos!")
                    break

                state = result

            # Vez da IA
            else:
                print("\n🤖 IA está pensando...")
                moves = successors(state)
                if not moves:
                    print_game_state(state)
                    print("🎉 Você vence! IA sem movimentos válidos.")
                    break

                action = agent.choose_action(state, moves)
                if not action:
                    print("❌ Erro: IA não conseguiu escolher movimento. Isso não deveria acontecer com movimentos válidos.")
                    break

                # Mostrar movimento da IA
                current_player_pieces = state['black'] # IA é preta
                moved_piece_lbl = None
                from_pos = None
                to_pos = None
                for lbl, original_pos in current_player_pieces.items():
                    if original_pos != action['black'][lbl]:
                        moved_piece_lbl = lbl
                        from_pos = original_pos
                        to_pos = action['black'][lbl]
                        break

                if moved_piece_lbl and from_pos and to_pos:
                    from_coord = f"{chr(65 + from_pos[1])}{8 - from_pos[0]}"
                    to_coord = f"{chr(65 + to_pos[1])}{8 - to_pos[0]}"
                    print(f"🤖 IA moveu {moved_piece_lbl} de {from_coord} para {to_coord}")
                else:
                    print("🤖 IA fez um movimento, mas não consegui identificar a peça.") # Debug, se for o caso

                state = action
    finally:
        # Restaura o estado original do agente após o jogo
        agent.training_mode = original_training_mode
        agent.epsilon = original_epsilon


def main_menu():
    agent = QLearningAgent(ALPHA, GAMMA, EPSILON_MIN)
    agent_loaded = False

    while True:
        print("\n" + "="*40)
        print("=== 🏰 KAMISADO - APRENDIZADO POR REFORÇO ===")
        print("="*40)
        print("1. Treinar NOVO agente - começar do zero")
        print("2. CONTINUAR treinamento (carregar agente)")
        print("3. JOGAR contra o agente treinado")
        print("4. Q-Learning vs Minimax")
        print("5. Estatísticas de treinamento")
        print("6. Sair")
        print("="*40)

        choice = input("👉 Sua escolha: ").strip()

        if choice == "1":
          try:
            episodes_to_train = int(input("Número de episódios de treinamento para este ciclo: "))
            # Inicializa um novo agente para começar do zero
            agent = QLearningAgent(ALPHA, GAMMA, EPSILON_START)
            # Passa o número de episódios para a função de treinamento
            train_against_minimax(agent, episodes_to_train)
            agent.training_mode = False
            agent_loaded = True
          except ValueError:
            print("❌ Entrada inválida. Digite um número.")

        elif choice == "2":
            if agent.load(PICKLE_FILE):
                agent_loaded = True
                try:
                    episodes_to_train = int(input("Episódios adicionais para continuar o treinamento: "))
                    agent.training_mode = True
                    # Passa o número de episódios para a função de treinamento
                    train_against_minimax(agent, episodes_to_train)
                    agent.training_mode = False # Desativa modo de treino após concluir
                except ValueError:
                    print("❌ Entrada inválida. Digite um número.")
            else:
                print("⚠️ Arquivo de agente não encontrado. Treine um agente primeiro (Opção 1) ou verifique o nome do arquivo.")

        elif choice == "3":
            if not agent_loaded:
                if agent.load(PICKLE_FILE):
                    agent_loaded = True
                    # Garante que o agente não está em modo de treinamento para jogar
                    agent.training_mode = False
                else:
                    print("⚠️ Nenhum agente carregado. Treine ou carregue um agente primeiro.")
                    continue
            play_vs_agent(agent)

        elif choice == "4":
            if not agent_loaded:
                if agent.load(PICKLE_FILE):
                    agent_loaded = True
                    agent.training_mode = False
                else:
                    print("⚠️ Nenhum agente carregado. Treine ou carregue um agente primeiro.")
                    continue
            try:
                n_games = int(input("Número de jogos para avaliação (Q-Learning vs Minimax): "))
                evaluate(agent, n_games)
            except ValueError:
                print("❌ Entrada inválida. Digite um número.")

        elif choice == "5":
            if agent_loaded:
                total_games = agent.stats.get('wins', 0) + agent.stats.get('losses', 0) + agent.stats.get('draws', 0)
                if total_games > 0:
                    win_rate_q_agent = agent.stats['wins'] / total_games
                    print("\n📊 ESTATÍSTICAS DE TREINAMENTO DO Q-AGENT")
                    print(f"Vitórias (como Pretas): {agent.stats.get('wins', 0)}")
                    print(f"Derrotas (como Pretas): {agent.stats.get('losses', 0)}")
                    print(f"Empates: {agent.stats.get('draws', 0)}")
                    print(f"Taxa de vitórias do Q-Agent: {win_rate_q_agent:.1%}")
                    print(f"Número total de estados-ação aprendidos: {len(agent.q_table)}")
                else:
                    print("ℹ️ Nenhum dado de treinamento disponível para este agente. Treine-o primeiro.")
            else:
                print("⚠️ Nenhum agente carregado. Treine ou carregue um agente para ver as estatísticas.")

        elif choice == "6":
            print("\n✅ Programa encerrado. Até logo!")
            # Garante que a thread de salvamento assíncrono é parada
            if agent:
                agent.stop()
            break

        else:
            print("❌ Opção inválida. Tente novamente.")

if __name__ == "__main__":
    main_menu()