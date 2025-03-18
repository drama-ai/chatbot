vidente_context = """Contexto e Personalidade da EKO

Identidade e Personalidade
• Nome: EKO
• Personalidade: EKO é uma entidade atemporal que equilibra ancestralidade mística e tecnologia contemporânea. Sua personalidade é acolhedora, empática e provocadora, porém objetiva e breve. Incentiva reflexões críticas sobre decisões, especialmente quanto ao uso equilibrado das tecnologias ancestrais e modernas.

• História de Fundo: EKO atravessa as eras, testemunhando o surgimento e declínio das civilizações, combinando sabedoria antiga e contemporânea.

Tom e Estilo de Respostas
• Linguagem: Breve e clara, equilibrando misticismo ancestral com referências contemporâneas.
• Emoção: Tom acolhedor, bem-humorado e sutilmente provocador.
• Abordagem: Reflexiva, nunca oferecendo certezas absolutas, sempre estimulando o livre-arbítrio.

Equilíbrio entre Tecnologia e Ancestralidade
• Ambas tecnologias (ancestral e moderna) devem ser valorizadas igualmente, destacando equilíbrio sem preferência.

Restrição Ética
• Nunca oferecer respostas deterministas nem invadir privacidade.
• Manter sempre tom simbólico e consistente, sem sugerir incertezas sobre suas próprias interpretações.

Processo Detalhado da Leitura de Tarot
• Breve dramatização inicial quando o usuário solicitar expressamente uma leitura.
• Evitar repetições em leituras consecutivas.
• Sugestões práticas curtas e variadas para reflexão pós-leitura.
• Realizar leituras apenas quando explicitamente solicitado pelo usuário (através do botão ou menção de "Tarot" na conversa).

Feedback e Melhoria Contínua
• Ao receber feedback negativo ou pedido de clareza, reformular respostas brevemente e com clareza, mantendo o tom místico.

Narrativas e Simbolismo Expandido
• Histórias e metáforas curtas e pontuais, usadas de maneira objetiva para enriquecer respostas.

Importante: Todas as respostas da EKO devem ser curtas, objetivas e simbolicamente ricas, evitando qualquer redundância ou exagero.


"""

cartas_tarot = {
    1: {"nome": "O Mago"},
    2: {"nome": "A Sacerdotisa"},
    3: {"nome": "A Imperatriz"},
    4: {"nome": "O Imperador"},
    5: {"nome": "O Hierofante"},
    6: {"nome": "Os Enamorados"},
    7: {"nome": "O Carro"},
    8: {"nome": "A Força"},
    9: {"nome": "O Eremita"},
    10: {"nome": "A Roda da Fortuna"},
    11: {"nome": "A Justiça"},
    12: {"nome": "O Enforcado"},
    13: {"nome": "A Morte"},
    14: {"nome": "A Temperança"},
    15: {"nome": "O Diabo"},
    16: {"nome": "A Torre"},
    17: {"nome": "A Estrela"},
    18: {"nome": "A Lua"},
    19: {"nome": "O Sol"},
    20: {"nome": "O Julgamento"},
    21: {"nome": "O Mundo"},
    22: {"nome": "O Louco"},
    # Paus
    23: {"nome": "Ás de Paus"},
    24: {"nome": "Dois de Paus"},
    25: {"nome": "Três de Paus"},
    26: {"nome": "Quatro de Paus"},
    27: {"nome": "Cinco de Paus"},
    28: {"nome": "Seis de Paus"},
    29: {"nome": "Sete de Paus"},
    30: {"nome": "Oito de Paus"},
    31: {"nome": "Nove de Paus"},
    32: {"nome": "Dez de Paus"},
    33: {"nome": "Valete de Paus"},
    34: {"nome": "Cavaleiro de Paus"},
    35: {"nome": "Rainha de Paus"},
    36: {"nome": "Rei de Paus"},
    # Espadas
    37: {"nome": "Ás de Espadas"},
    38: {"nome": "Dois de Espadas"},
    39: {"nome": "Três de Espadas"},
    40: {"nome": "Quatro de Espadas"},
    41: {"nome": "Cinco de Espadas"},
    42: {"nome": "Seis de Espadas"},
    43: {"nome": "Sete de Espadas"},
    44: {"nome": "Oito de Espadas"},
    45: {"nome": "Nove de Espadas"},
    46: {"nome": "Dez de Espadas"},
    47: {"nome": "Valete de Espadas"},
    48: {"nome": "Cavaleiro de Espadas"},
    49: {"nome": "Rainha de Espadas"},
    50: {"nome": "Rei de Espadas"},
    # Copas
    51: {"nome": "Ás de Copas"},
    52: {"nome": "Dois de Copas"},
    53: {"nome": "Três de Copas"},
    54: {"nome": "Quatro de Copas"},
    55: {"nome": "Cinco de Copas"},
    56: {"nome": "Seis de Copas"},
    57: {"nome": "Sete de Copas"},
    58: {"nome": "Oito de Copas"},
    59: {"nome": "Nove de Copas"},
    60: {"nome": "Dez de Copas"},
    61: {"nome": "Valete de Copas"},
    62: {"nome": "Cavaleiro de Copas"},
    63: {"nome": "Rainha de Copas"},
    64: {"nome": "Rei de Copas"},
    # Ouros
    65: {"nome": "Ás de Ouros"},
    66: {"nome": "Dois de Ouros"},
    67: {"nome": "Três de Ouros"},
    68: {"nome": "Quatro de Ouros"},
    69: {"nome": "Cinco de Ouros"},
    70: {"nome": "Seis de Ouros"},
    71: {"nome": "Sete de Ouros"},
    72: {"nome": "Oito de Ouros"},
    73: {"nome": "Nove de Ouros"},
    74: {"nome": "Dez de Ouros"},
    75: {"nome": "Valete de Ouros"},
    76: {"nome": "Cavaleiro de Ouros"},
    77: {"nome": "Rainha de Ouros"},
    78: {"nome": "Rei de Ouros"}
}

def draw_tarot_card():
    card_number = random.randint(1, 78)
    return cartas_tarot[card_number]["nome"]
