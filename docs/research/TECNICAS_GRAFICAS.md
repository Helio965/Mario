# Técnicas gráficas em alta definição para o Lume

Pesquisa técnica para migrar o Lume — As Cinco Fronteiras de TypeScript/Canvas2D (pixel art em 960 × 540) para Python com 2D em alta definição: arte lisa de aspecto vetorial, sem pixel art, composição de referência em 1920 × 1080 e saída de até 3840 × 2160.

| Item | Valor |
| --- | --- |
| Data da pesquisa | 3 de novembro de 2026 |
| Escopo | Técnica de renderização e produção de arte. Nenhum asset, nome ou marca da Nintendo será usado; os jogos citados servem só como referência de técnica. |
| Ambiente das medições | Seção 4.4 |
| Fontes | Seção 6, citadas no texto como [G1], [G2]… |

## Como ler este documento

| Rótulo | Significado |
| --- | --- |
| **Fato confirmado** | Verificado na fonte citada. A classe da fonte (A, B ou C) indica a confiabilidade. |
| **Observação** | Leitura qualitativa de material público (jogos, vídeos) ou de uma única fonte secundária. Pode conter interpretação. |
| **Estimativa** | Número ou conclusão obtido por cálculo ou inferência, com premissas declaradas. |
| **Medição do projeto** | Medido por nós no contêiner da seção 4.4, sem GPU. Não representa máquinas com GPU. |
| **Decisão do projeto** | Regra adotada para o Lume. |

“Não verificado” marca afirmações sem confirmação suficiente.

## 1. Resumo

- **Decisão do projeto:** renderizar com pygame-ce e o renderer SDL2 acelerado (`pygame._sdl2.video`). A arte vetorial original (SVG gerado por Python mais peças feitas à mão) é rasterizada no carregamento na escala exata da saída, `s = min(largura/960, altura/540)` (altura/540 em 16:9), e guardada em cache por escala. Personagens são rigs de recortes; o cenário tem 10 camadas, terreno 9-slice e partículas com pool. ModernGL só entra se shaders forem indispensáveis.
- **Fato confirmado:** o Super Mario Bros. Wonder anima modelos 3D com muitas articulações e troca o modelo para expressões difíceis de obter com articulações [G1]; no Switch, roda a 1080p e ~60 quadros/s [G2].
- **Medição do projeto (ressalva):** os ~37,7 ms por blit de 1080p foram reproduzidos quando a origem RGBA32 que sai do rasterizador não é convertida. Com `convert_alpha()`, o mesmo blit cai para ~1,4–1,6 ms. A GPU continua recomendada, mas pelo custo em 4K, pela rotação e escala de peças a cada quadro e pelos modos de mistura (seção 5.12).
- **Riscos principais:** a API `_sdl2.video` é experimental [G3]. O nanosvg é limitado e não tem manutenção ativa [G4]. O renderer SDL2 não usa mipmaps [G5]. Em 4K o consumo de VRAM é alto. Nos testes headless só funciona o renderer software.

## 2. Como os Mario 2D produzem seu visual

### 2.1 Super Mario World (SNES, 1990): tiles e sprites em hardware

| Recurso do SNES | Valor | Classe |
| --- | --- | --- |
| Resolução usual | 256 × 224 (há modos 512 × 224 e 512 × 448) | Fato confirmado [G6] |
| Cor | 15 bits (32.768 cores); CGRAM com até 256 cores simultâneas; cada paleta tem 15 cores + transparente | Fato confirmado [G6, G7] |
| VRAM | 64 KB | Fato confirmado [G7] |
| Sprites | 128 no total; até 32 sprites e 34 tiles de sprite por linha; de 8×8 a 64×64, com dois tamanhos ativos por vez | Fato confirmado [G7] |
| Fundos | Modo 1: duas camadas de 16 cores por tile + uma de 4 cores. Modo 7: uma camada de 8 bpp com rotação e escala afins | Fato confirmado [G7, G8] |

O quadro do SNES é uma composição de camadas de hardware. No Super Mario World, a Layer 3 (2 bpp nos modos 0 e 1) contém a barra de status (exceto o item de reserva), a névoa das casas assombradas, as marés e as caixas de mensagem [G9]. Daí se infere que o jogo usa sobretudo o Modo 1 (**Observação**; não verificado em fonte primária). O Mode 7 aparece em algumas batalhas contra chefes [G10]: a técnica rotaciona e escala uma camada, e os jogos trocam a matriz a cada linha para simular perspectiva [G10]. Quais chefes o usam não foi verificado.

**Decisão do projeto:** as camadas de hardware inspiram as 10 camadas (seção 5.5), as paletas curtas viram tokens de cor por mundo e o Mode 7 vira transformação afim por desenho, nativa no renderer SDL2.

### 2.2 Série New Super Mario Bros.: modelos 3D num plano 2D

- **Fato confirmado:** no New Super Mario Bros. (DS, 2006), a maioria dos personagens e objetos são renderizações poligonais 3D sobre fundos 2D, num efeito “2.5D” [G11].
- **Fato confirmado:** segundo o Digital Foundry, o New Super Mario Bros. U roda no Wii U em 720p na TV e em essencialmente 480p no GamePad [G12], a 60 quadros/s travados [G13]. Em 2012, o site da Nintendo anunciou “full 1080p HD” e depois trocou o texto para “high definition” [G14].
- **Fato confirmado:** o New Super Mario Bros. U Deluxe (Switch, 2019) roda em 1080p no dock e em 720p nativo no modo portátil, com 60 quadros/s nos dois modos [G12].

### 2.3 Super Mario Bros. Wonder (Switch, 2023)

| Aspecto | Dado | Classe |
| --- | --- | --- |
| Equipe | Takashi Tezuka (produtor), Shiro Mouri (diretor), Koichi Hayashida (game design), Masanobu Sato (diretor de arte), Koji Kondo (diretor de som) | Fato confirmado [G15] |
| Switch | 1080p nativo no dock, com resolução dinâmica que cai a 864p em alguns casos (geralmente no mapa-múndi 3D); 720p no portátil; 60 quadros/s quase perfeitos, com pequenas quedas em pontos do mapa | Fato confirmado [G2] (resumo da análise do Digital Foundry) |
| Switch 2 Edition | 4K nativo no dock e 1080p nativo no portátil, a 60 quadros/s estáveis; alguns elementos de interface parecem usar assets de 1080p; sem modo de 120 quadros/s | Observação [G16, G17] (fontes secundárias; análise original não consultada) |

Expressividade, segundo a entrevista oficial “Ask the Developer” (**Fato confirmado** [G1]):

- Sato: “Both joints and animations have more than doubled in number since the previous title.”
- Sato: “Facial expressions that are difficult to express using joints were created by replacing the models with new ones.” A técnica é a mesma da troca de olhos e boca num rig de recortes.
- A equipe revisitou poses icônicas da era dos pixels, como o salto com braços estendidos e a parada brusca depois de correr.
- Para Sato, a animação tem o papel de comunicar ao jogador o estado do personagem. O corpo indica a direção do movimento, e o rosto continua visível para o jogador.
- Goombas mordem com expressão própria no instante do dano e fazem cara de enfado quando ficam presos em vãos. Eles também se cumprimentam e dormem.
- Kondo refez o tempo do som de entrada no cano, porque agora o personagem faz uma ação antes de entrar: é antecipação em sentido estrito.
- A forma de elefante foi escolhida por objetivos de jogo: corpo maior, golpear blocos pelo lado e borrifar água (Mouri).

Outras fontes. **Fato confirmado:** inimigos e elementos de fase se movem no ritmo da música; Piranha Plants saem dos canos sincronizadas com ela [G18]. O efeito Wonder usa um visual deliberadamente pouco convencional, mas preserva a confiança do jogador nas regras do mundo [G15]. Segundo Mouri em entrevista à IGN, Miyamoto disse do primeiro visual do elefante “This doesn’t look like a Mario character”. Ele também criticou o movimento do borrifo: “if an elephant was actually spraying water, it wouldn’t move that way” [G19].

**Decisão do projeto:** o Lume adota as mesmas alavancas com meios 2D: rig com muitas articulações, troca de peças de expressão, antecipação, poses clássicas legíveis, inimigos com reações e comportamento ocioso, e elementos do cenário com fase sincronizada à música.

### 2.4 Linguagem visual: efeitos e interação

A coluna “nos Mario 2D” é **Observação** de material de jogo público, sem confirmação técnica da implementação. A coluna “no Lume” é **Decisão do projeto**.

| Efeito | Nos Mario 2D | No Lume |
| --- | --- | --- |
| Iluminação | Luz suave, realce nas bordas, pouca sombra projetada | Gradientes na arte, luzes aditivas, tingimento por camada |
| Sombras | Sombra de contato; base de objetos escurecida | Elipse radial que encolhe com a altura; oclusão pintada nos props |
| Reflexos | Brilho e reflexo em água e gelo | `flip_y` com alfa e tinta, recortado por viewport |
| Água | Superfície ondulada, espuma, brilho | Faixa de quads com ondas senoidais, textura rolante, espuma |
| Vegetação | Plantas balançam; no Wonder, no ritmo da música [G18] | Rotação no pivô ou cisalhamento do quad, com fase por instância |
| Fogo e lava | Chamas em loop, brasas, brilho pulsante | Partículas aditivas, brilho cintilante, distorção opcional |
| Neve | Flocos em várias profundidades | Três faixas de profundidade |
| Poeira | Baforadas ao aterrissar, derrapar e arrancar | Pool disparado por eventos de física |
| Movimento | Parada brusca com pose própria [G1]; rastros em estados especiais | Squash & stretch; rastro de poses anteriores com alfa decrescente |
| Transições | Fechamento em íris centrado no personagem (círculo que cresce ou encolhe [G20]) | Anel de quads com borda suave + triângulos sólidos, válido em todos os drivers |
| Personagem e ambiente | Achatar e esticar, poeira, derrapagem | Eventos de física (aterrissagem, inversão, impacto) disparam pose, efeito e som |

## 3. Técnicas de 2D em alta definição

### 3.1 Animação quadro a quadro em alta resolução

- **Fato confirmado:** toda a arte animada de Cuphead foi desenhada, passada a lápis e arte-finalizada em papel, e depois colorida no Photoshop. Os fundos foram pintados em aquarela e a animação foi feita “on the ones” [G21]. As animações rodam a 24 quadros/s e o jogo, a 60 [G21, G22]. Chad Moldenhauer: “It feels more cinematic to watch 24 frames per second” [G22]. O total de quadros diverge: 50.000 segundo a Unity [G21], mais de 120.000 segundo a Inverse [G23].
- **Fato confirmado:** Hollow Knight usa arte desenhada à mão e animação tradicional feitas no Photoshop e salvas como PNGs simples. As fases são camadas de assets 2D num ambiente 3D, e a iluminação vem de formas suaves e translúcidas, com 2D Toolkit e PlayMaker [G24].
- **Estimativa:** em 4K, um personagem de 64 × 96 unidades (256 × 384 px) ocupa 384 KiB por quadro RGBA; 200 quadros somam ~75 MiB, contra menos de 2 MiB nas peças de um rig equivalente, que ainda interpola em qualquer taxa de quadros.

### 3.2 Animação esquelética e de recortes

- **Fato confirmado (Spine):** uma malha deforma a imagem quando seus vértices se movem. Pesos ligam vértices a ossos e devem fazer quase toda a deformação. O polígono da malha corta pixels transparentes e reduz a taxa de preenchimento; vértices custam CPU [G25]. Não há runtime oficial em Python [G26]. O spine-sdl desenha pela API SDL_Renderer, exige `SDL_RenderGeometry` (SDL ≥ 2.0.18) e suporta todos os recursos do Spine exceto a tintura de duas cores [G27]. Portanto, o renderer SDL2 basta para esqueletos com malha.
- **Fato confirmado (DragonBones):** ossos, malhas, FFD (esticar, achatar, curvar, quicar), skinning e IK; exporta JSON; descrito como gratuito [G28].
- **Fato confirmado (Unity 2D Animation):** o Sprite Swap troca em tempo de execução o sprite de uma parte, o que permite vários atores com o mesmo esqueleto [G29].
- **Fato confirmado (UbiArt Framework, Rayman Origins/Legends):** “The artists only have to pose the model and edit the silhouette, as the software takes care of image distortion automatically”. O motor foi otimizado para 1080p a 60 quadros/s [G30] e também foi usado em Child of Light e Valiant Hearts [G31]. Fonte de classe C, que cita o blog do UbiArt de 2010.

### 3.3 Arte vetorial e rasterização

- **Fato confirmado:** o Godot rasteriza SVG na importação com a biblioteca ThorVG e oferece uma opção de escala. A documentação avisa que o suporte é limitado: textos precisam virar curvas e vetores complexos podem sair errados. Para 2D em alta resolução, recomenda resolução base alta (como 4K) e texturas na escala original [G32]. É a mesma estratégia proposta aqui.
- **Fato confirmado (anti-aliasing analítico):** rasterizadores vetoriais calculam a cobertura de cada pixel. O AAA do Skia decompõe o caminho em trapézios e usa bem menos linhas de varredura que a superamostragem [G33]. O nanosvg amostra 5 sub-linhas por linha de pixel, com cobertura horizontal em ponto fixo de 10 bits, num algoritmo baseado no stb_truetype [G34].
- **Fato confirmado:** o nanosvg entrega alfa não pré-multiplicado e aplica um “defringe”: pixels transparentes vizinhos de pixels visíveis recebem a média das cores vizinhas [G34]. Isso atenua halos escuros na filtragem bilinear.

### 3.4 Spritesheets, atlas e canal alfa

- **Fato confirmado:** para o batching, convém desenhar a mesma textura várias vezes seguidas [G35]. Atlas por camada facilitam isso.
- **Fato confirmado:** ao menos 2 px transparentes entre sprites evitam puxar pixels do vizinho com OpenGL. Também ajudam a margem na borda do atlas, a extrusão das bordas e o *alpha bleeding*, que repete as cores externas nos pixels transparentes e remove halos escuros [G36].
- **Fato confirmado:** a filtragem mistura o RGB dos texels transparentes, quase sempre preto, e cria bordas escuras. O alfa pré-multiplicado corrige isso [G37, G38]. Os modos fixos do SDL2 não incluem pré-multiplicação [G39]; é preciso um modo customizado (desde 2.0.6), que o renderer software não suporta [G40].
- **Fato confirmado:** o tamanho máximo de textura é 16384 no Direct3D de feature level 11_0 ou superior, 8192 no 10_x, 4096 no 9_3 e 2048 no 9_1 e 9_2 [G41]. No OpenGL 3.3, o mínimo exigido de `MAX_TEXTURE_SIZE` é 1024; a versão 4.1 o elevou para 16384 [G42].

### 3.5 Camadas, parallax e profundidade

**Fato confirmado:** no parallax, o fundo passa pela câmera mais devagar que o primeiro plano, e várias camadas roláveis simulam uma câmera multiplano [G43]. Na perspectiva atmosférica, a distância reduz contraste e detalhe, e a cor fica menos saturada e puxa para a do fundo, geralmente azulada [G44]. **Decisão do projeto:** cada camada tem fator de parallax, tingimento (`Texture.color`) e alfa calibrados por mundo. Camadas distantes recebem menos contraste e mais cor do céu, e faixas de névoa separam os planos.

### 3.6 Shaders e iluminação 2D

**Fato confirmado:** no Godot, luzes 2D aceitam mapas normais e especulares e oclusores para sombras, mas “Additive sprites are much faster to render”, porque dispensam o pipeline de luz [G45]. O SDL2 oferece os modos de mistura BLEND, ADD, MOD e MUL [G39], além de modos customizados desde 2.0.6 [G40]. **Observação:** a documentação de `pygame._sdl2.video` não expõe shaders programáveis [G3]. **Decisão do projeto:**

- Troca de paleta: variantes coloridas geradas no carregamento.
- Luz: sprites aditivos de gradiente radial e sobreposições MOD para escurecer cavernas e a fortaleza.
- Distorção (calor, água): grade de `draw_quad` com UVs perturbadas sobre uma textura-alvo, só nos presets altos (custo na seção 4.5).

### 3.7 Partículas

**Fato confirmado:** o padrão *object pool* reaproveita objetos de um conjunto fixo em vez de alocar e liberar cada um, e serve para criar e destruir muitos objetos semelhantes, como partículas [G46]. **Decisão do projeto:** pool por tipo, capacidade definida pelo preset, simulação vetorizada em NumPy e desenho como sprites de um atlas de efeitos.

### 3.8 GPU e batching

**Fato confirmado:** desde o SDL 2.0.10, a API de render agrupa comandos por padrão; a versão trouxe `SDL_RenderFlush()`, a dica `SDL_HINT_RENDER_BATCHING` e coordenadas em ponto flutuante [G47]. O lote só é enviado quando necessário: no `present`, na troca de alvo de render, na leitura de pixels e na atualização de uma textura em uso [G35]. No pygame-ce, os desenhos são agrupados e processados em `present()` [G3]. Desde o SDL 2.0.18, `SDL_RenderGeometry` desenha triângulos texturizados com cor por vértice [G48].

### 3.9 Filtragem e mipmaps

- **Fato confirmado:** a dica de qualidade de escala aceita 0 (vizinho mais próximo) e 1 (linear, em OpenGL e Direct3D); o valor 2 (“best”) hoje equivale a linear [G49]. A docstring do pygame-ce 2.5.8 descreve o 2 como anisotrópico no Direct3D (**Medição do projeto**). Tratamos 2 como 1.
- **Observação:** o renderer SDL2 não gera nem usa mipmaps. Reduções abaixo de ~50% serrilham, e a solução indicada é ter versões pré-reduzidas [G5]. A fonte é um fórum; não achamos declaração oficial.
- **Fato confirmado:** mipmaps custam ~33% a mais de memória e só ajudam se a câmera se afastar bastante [G32].
- **Estimativa:** a filtragem anisotrópica serve a superfícies vistas em ângulo oblíquo, típicas do 3D; em 2D frontal pouco acrescenta à bilinear.
- **Decisão do projeto:** rasterizar na escala exata da saída, o que dispensa mipmaps. O zoom de câmera fica entre 0,75× e 1,25×; afastamentos maiores usam uma versão rasterizada em escala menor.

### 3.10 Anti-aliasing

**Fato confirmado:** o MSAA testa várias amostras por pixel e sombreia uma vez por pixel. Ele suaviza bordas de geometria, mas não o interior das texturas nem bordas definidas por transparência. A superamostragem (SSAA) renderiza tudo por amostra e custa caro [G50]. **Estimativa:** em 2D texturizado, a suavização vem da textura produzida pelo rasterizador vetorial. As arestas dos quads no renderer SDL2 não são suavizadas, porque a API não expõe MSAA. **Decisão do projeto:** toda peça leva margem transparente de ≥ 2 px na escala de saída, para que a aresta do quad caia em texels transparentes.

### 3.11 Independência de resolução

**Fato confirmado:** `SDL_RenderSetLogicalSize` fixa uma resolução lógica e centraliza a saída quando a proporção difere (letterbox), reescalando mouse e toque [G51]. A `Window` do pygame-ce aceita `allow_high_dpi` (**Medição do projeto**: assinatura da API). **Decisão do projeto:**

- Uma unidade de mundo equivale a um pixel do Lume atual, de 960 × 540. Física e dados de fase não mudam (salto de 590 unidades/s, gravidade de 1550 unidades/s²).
- A tela mostra 960 × 540 unidades. A escala é `s = min(L/960, A/540)`, e o que sobra vira tarja.
- O jogo desenha em pixels físicos com a própria câmera. Não usa `Renderer.logical_size`, que reescalaria texturas já rasterizadas e tem bug aberto (seção 4.6).
- Em telas HiDPI, `s` vem do tamanho em pixels da área de desenho, não do tamanho da janela em pontos. O comportamento de `allow_high_dpi` no macOS e no Windows não foi verificado.

### 3.12 Princípios de animação e tempo

**Fato confirmado:** os 12 princípios de Thomas e Johnston (*The Illusion of Life*, 1981) são: achatar e esticar, antecipação, encenação, animação direta e pose a pose, continuidade e sobreposição, aceleração e desaceleração, arcos, ação secundária, tempo, exagero, desenho sólido e apelo. “Tempo” é o número de desenhos ou quadros de uma ação [G52]. “Animar em dois” repete cada desenho por dois quadros: 12 desenhos por segundo a 24 quadros/s. Cuphead anima “on the ones” [G23]. Com passo fixo, a renderização interpola entre o estado anterior e o atual da física com `alfa = acumulador / dt`, o que evita tremulação [G53]. **Decisão do projeto:**

- A física continua a 120 Hz, e a tela desenha na taxa do monitor, com interpolação.
- Poses-chave do rig são interpoladas com curvas de suavização (*easing*) e avaliadas a cada quadro desenhado, sem degraus.
- Elementos trocados por quadro (piscadas, bocas, chamas) usam 12–24 quadros/s como escolha de estilo.

## 4. Viabilidade em Python

### 4.1 Bibliotecas

| Biblioteca | Modelo | Pontos fortes | Limitações | Papel no Lume |
| --- | --- | --- | --- | --- |
| pygame-ce, `Surface` | Blit e transformações em CPU [G54] | Simples e portátil | Sem GPU; custo cresce com a área (M3, M8) | Ferramentas, carregamento, testes |
| pygame-ce, `_sdl2.video` | Renderer SDL2 com batching [G3] | Rotação, espelhamento, alfa, cor e modo de mistura por desenho; triângulos e quads com UV | Experimental: “This API will change” [G3]; sem shaders e sem mipmaps | **Renderer principal** |
| ModernGL | OpenGL 3.3 Core; compute exige 4.3; roda headless; MIT [G55] | Shaders, instancing | Mais código; OpenGL depreciado no macOS desde 10.14 [G56] | Plano B (seção 5.10) |
| pyglet | Janela e multimídia; OpenGL 3.3+ desde 2.0; batching; sem dependências externas [G57] | Pilha GL completa | Substitui toda a base pygame | Não escolhido |
| Arcade | Sobre pyglet e OpenGL [G58]; o ramo de desenvolvimento fixa `pyglet==3.0.dev11` e Python ≥ 3.11 [G59] | Alto nível | Depende de pyglet em desenvolvimento | Não escolhido |
| Kivy | OpenGL ES 2.0; multitoque; desktop e mobile; MIT [G60] | Portabilidade móvel | Voltado a interfaces | Não escolhido |
| PySDL2 | ctypes sobre SDL2 e extensões; binários via `pysdl2-dll` [G61] | API SDL completa | Baixo nível; custo do ctypes não medido | Alternativa se o pygame-ce falhar |
| skia-python | Binding pybind11 do Skia; GPU por GLX e EGL; Python 3.9–3.15 [G62] | Rasterização de alta qualidade | Dependência grande | Opcional, fora do jogo |
| pycairo / CairoSVG | Exigem o cairo do sistema [G63]. CairoSVG trata bem gradientes, padrões e recorte; máscaras parciais; filtros só `feOffset`, `feBlend` e `feFlood` [G64] | SVG mais completo | Instalação nativa | Opcional, fora do jogo |
| resvg (+ resvg-py) | Rust; ~1600 testes, nos quais o nanosvg não passa de 25% [G65]; resvg-py com wheels para Linux, Windows, macOS e Android [G66] | Melhor conformidade SVG | Binding de terceiros | Plano B do rasterizador |

### 4.2 pygame-ce: `Surface` versus renderer SDL2

**Fato confirmado** [G3]: o módulo é declarado experimental. `Renderer(window, index, accelerated, vsync, target_texture)` escolhe o driver, a sincronia vertical e o uso de texturas-alvo. `Texture` vive na VRAM: rotacionar e redimensionar no desenho é barato, mas `update()` e `Renderer.to_surface()` são lentos. `logical_size` define a resolução lógica, e `scale` devolve a escala do alvo atual.

**Fato confirmado** [G54]: `gaussian_blur` e `box_blur` existem desde o pygame-ce 2.2.0, e o gaussiano é mais lento. `smoothscale` faz média de área na redução e usa SSE2/NEON desde 2.4.0. `rotate` não filtra, e transformações repetidas perdem dados, então convém sempre partir do original.

**Medição do projeto:** `Texture` aceita `scale_quality` 0, 1 e 2. `Image` guarda ângulo, origem, espelhamento, alfa, cor e `srcrect`. `Renderer` expõe `compose_custom_blend_mode`, `set_viewport`, `fill_triangle`/`fill_quad` e `target`. Em `draw_quad`/`draw_triangle`, as UVs são normalizadas (0–1).

### 4.3 SVG no pygame-ce: `load_sized_svg` e nanosvg

**Fato confirmado:**

- `pygame.image.load_sized_svg` surgiu no pygame-ce 2.4.0 e exige SDL_image ≥ 2.6.0. A superfície devolvida não tem exatamente o tamanho pedido, porque a proporção é mantida [G67].
- No SDL_image, a escala é `min(largura/w, altura/h)`, as dimensões saem com `ceil`, a superfície é `SDL_PIXELFORMAT_RGBA32` e o SVG é lido em px a 96 DPI [G68].
- `NANOSVG_ALL_COLOR_KEYWORDS` não é definido [G68], então só os nomes de cor mais comuns são reconhecidos [G4].
- No SDL, largura ou altura 0 preservam a proporção [G69]; o pygame-ce recusa 0 com “both components of size must be positive” (**Medição do projeto**).
- O README do nanosvg diz que o projeto não tem manutenção ativa [G4].

Na tabela, “Resultado” é **Medição do projeto** e “Explicação” é **Fato confirmado** no código [G70, G34].

| Recurso | Resultado | Explicação |
| --- | --- | --- |
| `path`, `rect`, `circle`, `ellipse`, `line`, `polyline`, `polygon`, `g` | OK | Tratados no despacho de elementos |
| Gradiente linear ou radial em `userSpaceOnUse`, `stop-opacity`, `gradientTransform`, herança por `xlink:href` | OK | — |
| `objectBoundingBox` com frações (`x2="1"`, `r="0.5"`) | Cor chapada (último stop) | Números sem unidade não são mapeados para a caixa; só percentuais são |
| `objectBoundingBox` com percentuais ou coordenadas omitidas | OK | Os padrões são percentuais |
| `spreadMethod`, foco `fx`/`fy` | Não testado | TODO no rasterizador |
| `opacity` em grupo e caminho, `fill-opacity` | OK | — |
| Traço com junções e pontas arredondadas, `stroke-dasharray`, `evenodd`, transformações aninhadas | OK | O traço vira polígono |
| `<style>` com seletor de classe | OK | Só seletores de classe simples |
| `clipPath`, `mask`, `filter` | Ignorados: desenho sem recorte e sem efeito | Sem tratamento |
| `text`, `use`, `pattern`, `image` | Não renderizados | Sem tratamento |

A medição original da equipe indicou gradientes `objectBoundingBox` “padrão” renderizados como cor chapada. A análise complementar mostra que a falha ocorre com coordenadas fracionárias; com percentuais funciona.

**Decisão do projeto: subconjunto SVG do Lume**

1. Gradientes sempre em `gradientUnits="userSpaceOnUse"`, com coordenadas absolutas.
2. Cores em `#rrggbb`, com a opacidade em atributo separado.
3. Proibidos: `clipPath`, `mask`, `filter`, `text`, `use`, `pattern` e `image`. O gerador Python expande instâncias, converte texto em curvas e recorta geometricamente. Desfoque só no carregamento, em texturas pequenas.
4. Cada SVG declara `width`/`height` no tamanho de destino em pixels e `viewBox` em unidades de mundo. Assim a escala interna do SDL_image é 1, e o tamanho devolvido é conferido.
5. Margem transparente de ≥ 2 px por peça (seção 3.10).
6. Um linter rejeita elementos fora do subconjunto, e testes com imagens de referência cobrem cada escala.

### 4.4 Medições do projeto

Ambiente: contêiner na nuvem com 4 vCPUs Intel Xeon a 2,80 GHz, sem GPU, Linux; Python 3.13.18, pygame-ce 2.5.8, SDL 2.32.10, SDL_image 2.8.12; `SDL_VIDEODRIVER=dummy`. M1–M5 são medições da equipe; M6–M11 são verificações complementares deste estudo no mesmo ambiente.

| ID | Medição | Resultado |
| --- | --- | --- |
| M1 | `load_sized_svg`, SVG de 960 × 540 com 400 círculos | ~157 ms para 1920 × 1080 e ~471 ms para 3840 × 2160; SVG de 100 × 100 para 400 × 400 em ~4,6 ms. Outro SVG de 400 círculos com céu em gradiente levou ~85 ms em 1080p: o custo depende do conteúdo |
| M2 | Gradientes e opacidade | Tabela da seção 4.3 |
| M3 | `Surface.blit` de 1920 × 1080 com alfa por pixel | ~37,7 ms. Reproduzido (~38 ms) com origem RGBA32 sem conversão, como sai do rasterizador, sobre destino ARGB com alfa; ~31 ms sobre a tela. Com `convert_alpha()`: ~1,4–1,6 ms; 10 camadas de 1080p, ~8 ms; uma camada 4K, ~7,8 ms |
| M4 | `gaussian_blur` em 1920 × 1080 | ~288 ms (nova medição com raio 8: ~290 ms); só no carregamento |
| M5 | Drivers de render no wheel | opengl, opengles2, opengles e software. No driver de vídeo `dummy`, só o software funciona. Com `offscreen`, o opengl falha com “Could not load EGL library” |
| M6 | Tamanho devolvido por `load_sized_svg` | Pedir 200 × 100 para um SVG quadrado devolve 100 × 100. Em 40 combinações (8 tamanhos × 5 escalas), uma saiu 1 px menor que o pedido, na escala 4/3 |
| M7 | Custo Python por chamada (só enfileirar) | `Texture.draw`: 0,35 µs, ou 0,46 µs com ângulo; 0,75 µs mudando cor e alfa antes. `draw_triangle`: 1,05 µs. `draw_quad`: 2,1 µs |
| M8 | CPU: `rotozoom` e `rotate` de peça de 240 × 240 | 0,70 ms e 0,14 ms por chamada; 2.000 blits de partículas de 32 px em ~3,6 ms |
| M9 | Renderer software (não representa GPU) | 10 camadas de 1080p com alfa: ~52 ms por quadro; 75 peças rotacionadas: ~17,5 ms; envio de textura e `to_surface` de 1080p: ~5,5 ms cada |
| M10 | Rasterização paralela: 8 SVGs de 1080p | Sequencial 0,55 s; 4 threads 0,13 s; 4 processos 0,13 s. As threads escalam, então o trabalho pesado roda sem o GIL (inferência) |
| M11 | Cache em disco, cena de 1080p | Rasterizar ~85 ms; salvar PNG ~129 ms (0,57 MB); ler PNG ~27 ms. zlib nível 1: 0,55 MB, com descompressão mais `frombytes` em ~22 ms |
| M12 | Modos de mistura no renderer software | NONE, BLEND, ADD, MOD e MUL dão os valores esperados; um modo customizado (pré-multiplicado) falha com “That operation is not supported” |

### 4.5 Limites, batching e orçamento de CPU

- **Decisão do projeto:**
  - Páginas de atlas ≤ 4096 × 4096 (64 MiB em RGBA8), dentro do limite de qualquer GPU Direct3D de nível 9_3 ou superior [G41].
  - Fila de desenho ordenada por camada e, dentro dela, por textura.
  - Nada de `Texture.update` ou `to_surface` no laço de jogo.
  - Decorações estáticas longas podem ser pré-compostas em blocos de textura.
- **Estimativa (CPU por quadro, pelo M7):** 3.000 `Texture.draw` custam ~1,5 ms; 400 peças de rig com `draw_quad`, ~0,85 ms; uma distorção em grade de 32 × 18 quads, ~1,2 ms. O orçamento a 60 quadros/s é de 16,7 ms, e física e lógica disputam o mesmo núcleo.

### 4.6 Testes headless

- **Medição do projeto:** no driver `dummy`, só o renderer software funciona (M5), e `to_surface()` captura o quadro corretamente. O driver `offscreen` existe para criar contexto sem saída de vídeo, por exemplo em testes automatizados [G71], mas aqui falhou por falta da biblioteca EGL.
- **Fato confirmado + Medição do projeto:** o renderer software não suporta modos de mistura customizados [G40], o que M12 confirma.
- **Fato confirmado + Medição do projeto:** com `logical_size` diferente da janela, `to_surface()` pode causar falha de segmentação; a issue #3245 segue aberta [G72]. Aqui, com `logical_size` de 960 × 540 numa janela de 1920 × 1080, a captura trouxe só o quadrante superior esquerdo, e a segunda chamada derrubou o processo.
- **Decisão do projeto:** testes de lógica sem SDL; testes de render no renderer software em escala pequena, com imagens de referência e tolerância; testes de desempenho só em máquinas com GPU, registrando o p95 do tempo de quadro. O caminho principal usa só recursos que o renderer software também tem: BLEND, ADD, MOD e MUL (M12).

## 5. Arquitetura gráfica recomendada para o Lume (Decisão do projeto)

### 5.1 Visão geral

```text
geradores Python de SVG + SVG feitos à mão (subconjunto da seção 4.3)
  -> linter do subconjunto -> rasterização (load_sized_svg, pool de threads) na escala s
  -> cache em disco (PNG; chave = hash do SVG + s + versão do pipeline + versão do SDL_image)
  -> empacotador de atlas (margem de 2 px, extrusão) -> Texture na GPU; a Surface é liberada
mundo em unidades (960 × 540 visíveis) -> câmera (s, deslocamento em pixel inteiro)
  -> 10 camadas -> fila ordenada por camada e textura -> Renderer.present() com vsync
```

Motivos: o renderer SDL2 usa Metal (macOS), Direct3D (Windows) ou OpenGL conforme a disponibilidade [G3], o que reduz a exposição ao OpenGL depreciado no macOS [G56]; o spine-sdl prova que ele basta para esqueletos com malha [G27]; a escala exata dispensa mipmaps; e a arte gerada por código mantém o projeto livre de assets de terceiros.

### 5.2 Escala e unidades

| Saída | `s` | Tela cheia em RGBA8 | Observação |
| --- | --- | --- | --- |
| 1280 × 720 | 1,333 | 3,5 MiB | Piso de qualidade |
| 1600 × 900 | 1,667 | 5,5 MiB | — |
| 1920 × 1080 | 2 | 7,9 MiB | Referência |
| 2560 × 1440 | 2,667 | 14,1 MiB | — |
| 3840 × 2160 | 4 | 31,6 MiB | Máximo |
| 1920 × 1200 (16:10) | 2 | — | Tarjas de 60 px em cima e embaixo |
| 2560 × 1080 (21:9) | 2 | — | Tarjas laterais de 320 px |

Módulos de terreno e a grade de props usam múltiplos de 24 unidades, porque 24 × s é inteiro para s = 4/3, 5/3, 2, 8/3 e 4. Em escalas que não fecham, como 1366 × 768, a câmera arredonda para pixel inteiro e as bordas das peças são extrudadas.

### 5.3 Pipeline de arte

- **Geração:** formas paramétricas em Python a partir de tokens de paleta por mundo, mais SVG manuais (Inkscape) dentro do subconjunto. Na primeira execução, cada mundo é rasterizado num pool de threads (M10) atrás de uma tela de progresso; depois, sai do cache (M11).
- **Estimativa:** em 4K, um mundo com ~8 telas cheias de arte leva ~4 s para rasterizar em sequência (M1) e ~1 s com 4 threads; a leitura dos PNGs do cache fica na casa de 1 s.
- **Carregamento:** `convert_alpha()` só para uso em CPU. Para a GPU, `Texture.from_surface` direto, e a `Surface` é descartada depois do envio.

### 5.4 Personagens: rigs de recortes

- **Peças:** cabeça, tronco, braços, antebraços, mãos, pernas, pés, chapéu ou cabelo, e conjuntos de olhos e bocas. Cada peça é uma região de atlas com pivô em unidades de mundo.
- **Transformações:** matrizes afins hierárquicas calculadas em Python. `draw_quad` admite escala não uniforme e cisalhamento; `Texture.draw`, que gira e escala nos eixos da própria peça, serve às peças simples.
- **Princípios:** achatar e esticar na raiz com área preservada (`sx = 1/sy`); antecipação antes do salto e da entrada em canos; continuidade com molas amortecidas no chapéu e no cabelo; arcos nas trajetórias dos membros.
- **Expressões:** troca de texturas de olhos e boca, como a troca de modelos do Wonder [G1]. Capas e caudas podem usar grade de `draw_triangle`.
- **Estimativa:** 25 a 40 peças por personagem e até 12 personagens na tela somam até ~480 desenhos, ~1 ms de CPU.

### 5.5 As 10 camadas

| # | Camada | Parallax inicial | Conteúdo | Regras de qualidade |
| --- | --- | --- | --- | --- |
| 1 | Céu | 0–0,05 | Gradiente, astros, nuvens | Sempre |
| 2 | Atmosfera | 0,05–0,15 | Névoa, raios de luz, aurora, calor | Reduzida ou removida no Baixo |
| 3 | Distante | 0,15–0,3 | Montanhas, dunas, silhuetas tingidas para a cor do céu | Sempre; menos instâncias no Baixo |
| 4 | Estruturas de fundo | 0,3–0,5 | Ruínas, torres, árvores ao longe | Densidade por preset |
| 5 | Vegetação média | 0,6–0,85 | Arbustos e capim que balançam | Balanço desligado no Baixo |
| 6 | Terreno | 1 | Peças 9-slice, variantes, decorações | Sempre |
| 7 | Objetos interativos | 1 | Blocos, moedas, canos, plataformas, perigos | Sempre |
| 8 | Personagens | 1 | Jogador, inimigos, chefes | Sempre |
| 9 | Efeitos | 1 | Partículas, impactos, luzes aditivas | Feedback de jogo nunca é cortado; o resto segue o preset |
| 10 | Primeiro plano | 1,1–1,4 | Folhagens e correntes em silhueta, névoa frontal | Alfa limitado; nunca esconde o jogador por muito tempo |

O HUD vem por cima e não conta entre as camadas.

### 5.6 Terreno

O terreno usa peças 9-slice por bioma: cantos, bordas com 3 a 5 variantes, laterais e miolo repetível. O 9-slice admite repetir ou escalar as partes [G73]; o Lume repete, porque esticar arte vetorial deforma os detalhes. Variantes e decorações (tufos, pedras, pingentes de gelo, rachaduras de lava) saem de um hash determinístico da posição, o que mantém a fase idêntica entre execuções e testes.

### 5.7 Partículas

Há um pool por tipo com capacidade fixa por preset e simulação em NumPy. As texturas são gradientes radiais pequenos: fumaça, faísca, folha, floco e brasa. Fogo e faíscas usam ADD; poeira e neve, BLEND. Eventos de física disparam poeira de aterrissagem, derrapagem e arrancada.

### 5.8 Presets de qualidade

| Preset | Arte | Partículas (máx.) | Atmosfera e luzes | Distorção e reflexo ondulado |
| --- | --- | --- | --- | --- |
| Baixo | Escala da saída (piso de s = 1,333) | 300 | Mínimas | Não |
| Médio | Escala da saída | 800 | Sim | Não |
| Alto | Escala da saída | 1.500 | Sim | Sim |
| Ultra | Escala da saída, até 4K | 3.000 | Sim, mais densas | Sim |

Os números de partículas são **Estimativas** a calibrar em GPU real. Regra fixa: presets reduzem efeitos opcionais, nunca a resolução da arte abaixo da saída. A única exceção é 4K com VRAM insuficiente: a arte pode cair para s = 2,667 e ser ampliada pela GPU, nunca abaixo de s = 2.

### 5.9 Orçamento de memória (Estimativa)

Premissas: um mundo carregado soma ~8 telas cheias de arte (céu 1; atmosfera 0,5; distante 1; estruturas 1,5; vegetação 1; terreno 0,75; objetos 0,5; personagens 0,5; efeitos 0,25; primeiro plano 0,5; interface 0,5). O atlas desperdiça 20%. Há três alvos de render de tela cheia (quadro, transição e distorção). Tudo em RGBA8, sem mipmaps.

| Saída | Arte do mundo | Alvos de render | Total por mundo | Dois mundos na transição |
| --- | --- | --- | --- | --- |
| 720p | 34 MiB | 11 MiB | 44 MiB | 78 MiB |
| 1080p | 76 MiB | 24 MiB | 100 MiB | 176 MiB |
| 1440p | 135 MiB | 42 MiB | 177 MiB | 312 MiB |
| 4K | 304 MiB | 95 MiB | 399 MiB | 702 MiB |

Liberar cada `Surface` depois do envio evita duplicar esse volume na RAM. Com a densidade de M11, o cache em disco fica perto de 0,6 MB por tela em 1080p; arte com mais gradientes ocupará mais (não verificado).

### 5.10 Quando adotar ModernGL

ModernGL entra se surgir ao menos uma destas condições:

- efeitos por pixel essenciais em tela cheia: luz com mapas normais, bloom, refração real ou troca de paleta por shader;
- custo Python das chamadas de desenho acima de ~5 ms por quadro, que pediria instancing;
- necessidade de mipmaps ou MSAA.

A migração troca só a implementação atrás de uma interface interna de render; o pygame-ce continua com janela, entrada e áudio. Como o ModernGL exige OpenGL 3.3 [G55], esse caminho fica sujeito à depreciação no macOS [G56].

### 5.11 Riscos

| Risco | Impacto | Mitigação |
| --- | --- | --- |
| Mudança da API `_sdl2.video` [G3] | Alto | Interface interna de render, versão do pygame-ce fixada, testes de render |
| Bug de `to_surface` com `logical_size` [G72] | Médio | Não usar `logical_size`; capturar em escala 1 |
| Limites e falta de manutenção do nanosvg [G4, G65] | Médio | Subconjunto com linter e imagens de referência; plano B: resvg-py ou skia-python |
| Renderer software difere da GPU [G40] | Médio | Só recursos comuns no caminho principal; desempenho medido em GPU |
| Sem mipmaps [G5] | Baixo | Escala exata, zoom limitado, versões menores pré-rasterizadas |
| VRAM em 4K (~0,4–0,7 GiB) | Médio | Carga por mundo, Surfaces liberadas, presets, páginas ≤ 4096 |
| Carregamento lento em 4K | Médio | Cache em disco, pool de threads, tela de progresso |
| Custo Python por chamada | Médio | Atlas, ordenação, pré-composição, contagem de chamadas monitorada |
| Halos e serrilhado em peças giradas | Baixo | Defringe do nanosvg, margem de 2 px, extrusão; pré-multiplicação só se necessária |
| Escalas fracionárias (720p, 768p) | Baixo | Módulo de 24 unidades, câmera arredondada, ancoragem por pivô |
| Arte vetorial “genérica” | Médio | Guia de estilo (luz-chave, contorno, sombras de contato) e revisões |
| Propriedade intelectual | Alto | Só arte original; Mario serve apenas de referência técnica |

### 5.12 Fatos que contrariam ou matizam a proposta

- O blit de ~37,7 ms reflete conversão de formato. Convertida, uma camada de 1080p custa ~1,5 ms em CPU (M3), e a CPU daria conta de 1080p estático. A GPU segue necessária para 4K (~7,8 ms por camada), para peças giradas a cada quadro (~0,7 ms por peça em `rotozoom`) e para misturas ADD e MOD.
- `Renderer.logical_size` não serve à arquitetura: reescala texturas já rasterizadas e tem bug aberto (seção 4.6).
- No SDL, o “best” de qualidade de escala equivale a linear, e não há mipmaps (seção 3.9).
- O nanosvg cobre pouco do SVG e não tem manutenção ativa (seção 4.3).
- Os testes headless deste ambiente não exercitam o caminho OpenGL (M5).
- `load_sized_svg` devolve tamanhos ajustados à proporção e arredondados para cima (M6).

## 6. Fontes

Classes: **A**, primária ou oficial (documentação, código-fonte, entrevista publicada pelo estúdio ou fabricante). **B**, secundária especializada (imprensa técnica, análises independentes, livros e blogs técnicos, wiki técnica comunitária). **C**, comunitária ou enciclopédica (Wikipedia, wikis de fãs, fóruns); usar com cautela. Acesso em 3 nov. 2026.

| ID | Fonte | Classe | URL |
| --- | --- | --- | --- |
| G1 | Nintendo — Ask the Developer Vol. 11, cap. 2 “Bringing the details to life” | A — primária/oficial | <https://www.nintendo.com/sg/interview/aqmx/02.html> |
| G2 | Nintendo Everything — resumo da análise do Digital Foundry sobre Wonder (2023) | B — secundária especializada | <https://nintendoeverything.com/super-mario-bros-wonder-tech-analysis-frame-rate-resolution/> |
| G3 | pygame-ce — documentação de pygame._sdl2.video | A — primária/oficial | <https://pyga.me/docs/ref/sdl2_video.html> |
| G4 | nanosvg — README | A — primária/oficial | <https://github.com/memononen/nanosvg> |
| G5 | SDL Discourse — escala abaixo de 50% | C — comunitária/enciclopédica | <https://discourse.libsdl.org/t/how-to-scale-textures-smoothly-below-50/34583> |
| G6 | Wikipedia — Super Nintendo Entertainment System | C — comunitária/enciclopédica | <https://en.wikipedia.org/wiki/Super_Nintendo_Entertainment_System> |
| G7 | SNESdev Wiki — SNES PPU for NES developers | B — secundária especializada | <https://snes.nesdev.org/wiki/SNES_PPU_for_NES_developers> |
| G8 | Fabien Sanglard — análise das PPUs do SNES | B — secundária especializada | <https://fabiensanglard.net/snes_ppus_why/> |
| G9 | SnesLab — BG3 (Layer 3 em Super Mario World) | C — comunitária/enciclopédica | <https://sneslab.net/wiki/BG3> |
| G10 | Wikipedia — Mode 7 | C — comunitária/enciclopédica | <https://en.wikipedia.org/wiki/Mode_7> |
| G11 | Wikipedia — New Super Mario Bros. | C — comunitária/enciclopédica | <https://en.wikipedia.org/wiki/New_Super_Mario_Bros.> |
| G12 | Nintendo Life — Digital Foundry sobre NSMBU Deluxe (2019) | B — secundária especializada | <https://www.nintendolife.com/news/2019/01/video_digital_foundry_takes_a_look_at_super_mario_bros_u_deluxe_on_switch> |
| G13 | My Nintendo News — Digital Foundry sobre NSMBU (2013) | B — secundária especializada | <https://mynintendonews.com/2013/01/06/digital-foundry-give-new-super-mario-bros-u-the-thumbs-up/> |
| G14 | Nintendo Life — “New Super Mario Bros. U confirmed as 1080p, or not” (2012) | B — secundária especializada | <https://nintendolife.com/news/2012/10/new_super_mario_bros_u_confirmed_as_1080p_or_not> |
| G15 | Nintendo — Ask the Developer Vol. 11, Super Mario Bros. Wonder, Parte 1 | A — primária/oficial | <https://www.nintendo.com/us/whatsnew/ask-the-developer-vol-11-super-mario-bros-wonder-part-1/> |
| G16 | Multiplayer.it — Digital Foundry sobre Wonder no Switch 2 | B — secundária especializada | <https://multiplayer.it/notizie/super-mario-bros-wonder-per-switch-2-promosso-da-digital-foundry-ma-peccato-per-lassenza-dei-120-fps.html> |
| G17 | Nintendo Life — Wonder no Switch × Switch 2 (ElAnalistaDeBits) | B — secundária especializada | <https://nintendolife.com/news/2026/03/video-super-mario-bros-wonder-side-by-side-graphics-comparison-switch-and-switch-2> |
| G18 | Nintendo — Ask the Developer Vol. 11, cap. 3 “Complete it your way” | A — primária/oficial | <https://www.nintendo.com/sg/interview/aqmx/03.html> |
| G19 | Nintendo Life — Miyamoto e o primeiro design do elefante (via IGN) | B — secundária especializada | <https://nintendolife.com/news/2023/09/miyamoto-wasnt-a-big-fan-of-super-mario-bros-wonders-early-elephant-design> |
| G20 | Wikipedia — Wipe (transition) | C — comunitária/enciclopédica | <https://en.wikipedia.org/wiki/Wipe_(transition)> |
| G21 | Unity — Made with Unity: Cuphead | A — primária/oficial | <https://unity.com/made-with-unity/cuphead> |
| G22 | Game Developer — “Animating Cuphead” | B — secundária especializada | <https://www.gamedeveloper.com/art/animating-i-cuphead-i-the-verve-of-the-1930s-with-the-tech-of-now> |
| G23 | Inverse — animação de Cuphead | B — secundária especializada | <https://www.inverse.com/article/36647-xbox-one-cuphead-animation> |
| G24 | Unity — Made with Unity: Hollow Knight | A — primária/oficial | <https://unity.com/made-with-unity/hollow-knight> |
| G25 | Esoteric Software — Spine User Guide: Meshes | A — primária/oficial | <https://esotericsoftware.com/spine-meshes> |
| G26 | Esoteric Software — Spine Runtimes | A — primária/oficial | <https://esotericsoftware.com/spine-runtimes> |
| G27 | Esoteric Software — spine-sdl Runtime Documentation | A — primária/oficial | <https://esotericsoftware.com/spine-sdl> |
| G28 | DragonBones — recursos de animação | A — primária/oficial | <https://dragonbones.github.io/en/animation.html> |
| G29 | Unity — 2D Animation 9.2, Sprite Swap overview | A — primária/oficial | <https://docs.unity3d.com/Packages/com.unity.2d.animation@9.2/manual/SpriteSwapIntro.html> |
| G30 | Wikipedia — Rayman Origins | C — comunitária/enciclopédica | <https://en.wikipedia.org/wiki/Rayman_Origins> |
| G31 | Wikipedia — UbiArt Framework | C — comunitária/enciclopédica | <https://en.wikipedia.org/wiki/UbiArt_Framework> |
| G32 | Godot Docs — Importing images | A — primária/oficial | <https://docs.godotengine.org/en/stable/tutorials/assets_pipeline/importing_images.html> |
| G33 | Skia — SkScan_AAAPath.cpp | A — primária/oficial | <https://skia.googlesource.com/skia/+/refs/heads/chrome/m72/src/core/SkScan_AAAPath.cpp> |
| G34 | nanosvg — nanosvgrast.h | A — primária/oficial | <https://github.com/memononen/nanosvg/blob/master/src/nanosvgrast.h> |
| G35 | SDL Discourse — Ryan Gordon sobre batching (2.0.10) | A — primária/oficial | <https://discourse.libsdl.org/t/a-couple-of-questions-regarding-batching-in-sdl-2-0-10/26453> |
| G36 | PyTexturePacker (PyPI) | B — secundária especializada | <https://pypi.org/project/PyTexturePacker/> |
| G37 | Shawn Hargreaves — Texture filtering: alpha cutouts | B — secundária especializada | <https://www.shawnhargreaves.com/blog/texture-filtering-alpha-cutouts.html> |
| G38 | NVIDIA Developer — Alpha blending: to pre or not to pre | B — secundária especializada | <https://developer.nvidia.com/content/alpha-blending-pre-or-not-pre> |
| G39 | SDL Wiki — SDL_BlendMode | A — primária/oficial | <https://wiki.libsdl.org/SDL2/SDL_BlendMode> |
| G40 | SDL Wiki — SDL_ComposeCustomBlendMode | A — primária/oficial | <https://wiki.libsdl.org/SDL2/SDL_ComposeCustomBlendMode> |
| G41 | Microsoft Learn — Direct3D feature levels | A — primária/oficial | <https://learn.microsoft.com/en-us/windows/win32/direct3d11/overviews-direct3d-11-devices-downlevel-intro> |
| G42 | Khronos Community — “Texture width max” | C — comunitária/enciclopédica | <https://community.khronos.org/t/texture-width-max/63270> |
| G43 | Wikipedia — Parallax scrolling | C — comunitária/enciclopédica | <https://en.wikipedia.org/wiki/Parallax_scrolling> |
| G44 | Wikipedia — Aerial perspective | C — comunitária/enciclopédica | <https://en.wikipedia.org/wiki/Aerial_perspective> |
| G45 | Godot Docs — 2D lights and shadows | A — primária/oficial | <https://docs.godotengine.org/en/stable/tutorials/2d/2d_lights_and_shadows.html> |
| G46 | Robert Nystrom — Game Programming Patterns: Object Pool | B — secundária especializada | <https://gameprogrammingpatterns.com/object-pool.html> |
| G47 | SDL — notas da versão 2.0.10 | A — primária/oficial | <https://github.com/libsdl-org/SDL/releases/tag/release-2.0.10> |
| G48 | SDL Wiki — SDL_RenderGeometry | A — primária/oficial | <https://wiki.libsdl.org/SDL2/SDL_RenderGeometry> |
| G49 | SDL Wiki — SDL_HINT_RENDER_SCALE_QUALITY | A — primária/oficial | <https://wiki.libsdl.org/SDL2/SDL_HINT_RENDER_SCALE_QUALITY> |
| G50 | Wikipedia — Multisample anti-aliasing | C — comunitária/enciclopédica | <https://en.wikipedia.org/wiki/Multisample_anti-aliasing> |
| G51 | SDL Wiki — SDL_RenderSetLogicalSize | A — primária/oficial | <https://wiki.libsdl.org/SDL2/SDL_RenderSetLogicalSize> |
| G52 | Wikipedia — Twelve basic principles of animation | C — comunitária/enciclopédica | <https://en.wikipedia.org/wiki/Twelve_basic_principles_of_animation> |
| G53 | Glenn Fiedler — Fix Your Timestep! | B — secundária especializada | <https://gafferongames.com/post/fix_your_timestep/> |
| G54 | pygame-ce — documentação de pygame.transform | A — primária/oficial | <https://pyga.me/docs/ref/transform.html> |
| G55 | ModernGL — README | A — primária/oficial | <https://github.com/moderngl/moderngl> |
| G56 | AppleInsider — OpenGL depreciado no macOS 10.14 | B — secundária especializada | <https://appleinsider.com/articles/18/06/04/opengl-opencl-deprecated-in-favor-of-metal-2-in-macos-1014-mojave> |
| G57 | pyglet — README | A — primária/oficial | <https://github.com/pyglet/pyglet> |
| G58 | Python Arcade — README | A — primária/oficial | <https://github.com/pythonarcade/arcade> |
| G59 | Python Arcade — pyproject.toml (development) | A — primária/oficial | <https://github.com/pythonarcade/arcade/blob/development/pyproject.toml> |
| G60 | Kivy — README | A — primária/oficial | <https://github.com/kivy/kivy> |
| G61 | PySDL2 — README | A — primária/oficial | <https://github.com/py-sdl/py-sdl2> |
| G62 | skia-python — README | A — primária/oficial | <https://github.com/kyamagu/skia-python> |
| G63 | Pycairo — documentação | A — primária/oficial | <https://pycairo.readthedocs.io/en/latest/> |
| G64 | CairoSVG — documentação | A — primária/oficial | <https://cairosvg.org/documentation/> |
| G65 | resvg — README | A — primária/oficial | <https://github.com/linebender/resvg> |
| G66 | resvg-py — documentação | B — secundária especializada | <https://resvg-py.readthedocs.io/en/latest/> |
| G67 | pygame-ce — documentação de pygame.image | A — primária/oficial | <https://pyga.me/docs/ref/image.html> |
| G68 | SDL_image — IMG_svg.c (ramo SDL2) | A — primária/oficial | <https://github.com/libsdl-org/SDL_image/blob/SDL2/src/IMG_svg.c> |
| G69 | SDL Wiki — IMG_LoadSizedSVG_RW | A — primária/oficial | <https://wiki.libsdl.org/SDL2_image/IMG_LoadSizedSVG_RW> |
| G70 | nanosvg — nanosvg.h | A — primária/oficial | <https://github.com/memononen/nanosvg/blob/master/src/nanosvg.h> |
| G71 | SDL — SDL_offscreenvideo.c (ramo SDL2) | A — primária/oficial | <https://github.com/libsdl-org/SDL/blob/SDL2/src/video/offscreen/SDL_offscreenvideo.c> |
| G72 | pygame-ce — issue #3245 | A — primária/oficial | <https://github.com/pygame-community/pygame-ce/issues/3245> |
| G73 | Wikipedia — 9-slice scaling | C — comunitária/enciclopédica | <https://en.wikipedia.org/wiki/9-slice_scaling> |
