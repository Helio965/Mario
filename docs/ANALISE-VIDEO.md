# Análise da referência em vídeo

Arquivo analisado: `Screen_Recording_20261006_143029_Instagram.mp4`.

## Método e cobertura

O vídeo tem **19,618 segundos**, resolução **1080 × 2340**, orientação vertical e fluxo H.264 declarado a 120 quadros/s. Há um fluxo de áudio AAC estéreo, 48 kHz; a existência desse fluxo foi verificada, mas o conteúdo sonoro não foi interpretado. A inspeção visual cobriu o começo, o meio e o final: uma folha de contato da tela completa a 1 quadro/s e duas folhas da região de jogo a 2 quadros/s, com horários, além de um quadro ampliado. Isso identifica os segmentos e o comportamento visível, sem presumir acesso ao código ou à entrada do jogador.

Artefatos de inspeção: `video-frames/contact.png`, `video-frames/time-01.png`, `video-frames/time-02.png` e `video-frames/detail.png`, todos nesta pasta `scratch`.

## Conteúdo confirmado

- Trata-se de uma gravação da interface de Reels do Instagram. O vídeo exibido apresenta o título “Super Mario CSS”, uma janela de cenário na parte superior e dois painéis decorativos de código abaixo. Não é uma captura em tela cheia de um jogo. Ícones, comentários, nome de conta e botões da rede social são externos ao cenário.
- A janela de jogo é retangular, de aproximadamente **982 × 610 pixels dentro da gravação** (recorte usado: x=49, y=446). Uma borda clara delimita a cena.
- O cenário é lateral, de plataforma 2D, com estética simples de pixels/formas planas: céu azul vivo, nuvens brancas arredondadas, colinas verdes em semicírculo, chão alaranjado com divisões de tijolo e canos verdes de alturas diferentes.
- Há plataformas suspensas de tijolos alaranjados, blocos dourados com interrogação, moedas douradas suspensas e pequenos inimigos marrons com olhos claros sobre o chão.
- O protagonista é pequeno em relação ao cenário, com boné vermelho e roupa azul, representado por poucos blocos de cor. O desenho de pernas/braços muda entre corrida e salto.
- O deslocamento principal é da esquerda para a direita. Saltos sobem e descem em arco. O personagem aterrissa no chão e no topo de canos. A cena rola horizontalmente; depois do trecho inicial, o protagonista costuma permanecer perto do terço esquerdo enquanto obstáculos e fundo atravessam a janela para a esquerda.
- Blocos dourados atingidos por baixo passam a cinza. A colisão é acompanhada por pequenos elementos dourados/partículas subindo. Também aparece uma curta dispersão de fragmentos marrons perto de uma plataforma, compatível com quebra de tijolo.
- Próximo de 5 s o protagonista desce sobre um inimigo; no quadro seguinte há uma forma baixa no chão onde o inimigo estava. A imagem é compatível com esmagamento por pisão, embora o vídeo não permita reconstruir toda a regra de colisão.
- Há um fosso no chão. Ao chegar a esse trecho, o protagonista aparece abaixo da altura do piso e depois inclinado/rodando no ar; a cena retorna à posição inicial. A mesma sequência geral ocorre uma segunda vez.

## Segmentos visuais

Tempos aproximados, obtidos dos quadros amostrados:

| Intervalo | O que aparece |
| --- | --- |
| 0–1 s | Corrida no chão; aproximação do primeiro cano e primeiro salto. |
| 1–2 s | Salto perto de bloco dourado, transição do bloco para cinza e emissão de partículas; retorno ao chão. |
| 2–4 s | Avanço com câmera lateral, saltos entre canos e plataformas; fragmentos marrons perto de tijolos. |
| 4–5,5 s | Salto alto, descida junto/sobre inimigo e retorno ao chão. |
| 5,5–6,5 s | Novo salto sob bloco, bloco cinza e partículas; aproximação da interrupção no piso. |
| 6,5–8 s | Queda no fosso, personagem inclinado e retorno ao início. |
| 8–10 s | Personagem próximo do início; breve espera antes de novo avanço. |
| 10–18,5 s | Nova passagem pelo mesmo conjunto de obstáculos, com pequenos deslocamentos de tempo; nova queda e reinício. |
| 18,5–19,618 s | Cena novamente no início. Não surge tela de vitória ou outro cenário. |

## Características úteis para uma implementação original

A referência sustenta uma fase lateral clara, saltos com arco legível, personagem compacto, obstáculos verticais, plataformas em alturas diferentes, objetos dourados, câmera horizontal e resposta visual curta a impactos. O contraste entre céu, chão, protagonista e obstáculos facilita a leitura. O ambiente novo pode reproduzir essas funções com um personagem, paleta, formas, mapa, interface e nomes próprios. A interface do Instagram e os painéis de código não fazem parte do jogo a implementar. **Não extrair sprites, logos, música ou outros assets da gravação.**

## Limites da evidência

Não há demonstração de teclado, controle ou botões táteis; portanto, a gravação **não comprova que a cena é jogável**, em vez de uma animação programada. Também não comprova aceleração, desaceleração, alcance variável de salto, colisão lateral com inimigos, contador de moedas, pontos, vidas, pausa, menu, progressão, checkpoint, salvamento, vitória, bandeira final, múltiplas fases, powers-ups ou funcionamento offline. Essas funções devem vir do pedido escrito, e não ser atribuídas ao vídeo.

O reaparecimento no início é visível, mas não permite distinguir morte/reinício de jogo de uma repetição da animação. As moedas giram ou variam de largura visualmente; não se pode confirmar a regra completa de coleta. Há rolagem de fundo, mas não evidência suficiente para quantificar paralaxe independente, velocidade de câmera ou parâmetros físicos. Os painéis de código são pequenos e servem como composição do Reel; não foram transcritos nem tratados como instruções do usuário.
