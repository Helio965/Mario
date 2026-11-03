# Sistema gráfico em alta definição

Código: `lume/render/`. Pesquisa e justificativas: `docs/research/TECNICAS_GRAFICAS.md`.

## 1. Decisões

| Decisão | Motivo |
| ------- | ------ |
| pygame-ce 2.5 + renderizador SDL2 (`pygame._sdl2.video`) | texturas na GPU com rotação, espelhamento, alfa, modulação de cor e mistura aditiva; lógica 100% Python; sem motor complexo |
| Arte vetorial original escrita como código (SVG gerado por Python) | contornos suaves e resolução independente; nada de pixel art, nada de imagem pequena ampliada |
| Rasterização na densidade exata de saída | a textura de cada recurso tem o número de pixels com que será desenhada (2 px/u em 1080p, 4 px/u em 4K, vezes o zoom de câmera 1,3) |
| Personagens como rigs recortados (cut-out) | partes rotacionadas na GPU a cada quadro; animação fluida em qualquer FPS sem folhas de quadros enormes |
| Composição por camadas | céu, atmosfera, parallax distante/médio/próximo, adereços de fundo, terreno, objetos, criaturas, efeitos, primeiro plano, HUD |
| Sem `Renderer.logical_size` | combinado com `to_surface()` provoca falha de segmentação (reproduzido; issue aberta no pygame-ce); a conversão de coordenadas é própria |

## 2. Coordenadas e resolução

- **Tela de referência**: 960 × 540 unidades de tela (16:9). `Display.scale = min(L/960, A/540)`; proporções diferentes recebem barras pretas (testado em 2560 × 1080).
- **Mundo**: a câmera da simulação enquadra 960 × 540 u; o renderizador aplica zoom 1,3 em torno do jogador (≈ 738 × 415 u visíveis), mantendo a posição relativa do jogador e o olhar à frente.
- **Resolução da janela**: configuração `auto` escolhe o maior preset 16:9 que cabe em 90% da área de trabalho (1280×720, 1600×900, 1920×1080, 2560×1440, 3840×2160); tela cheia usa a resolução nativa. Sem aceleração de GPU, `auto` fica em 1280 × 720.
- **Nunca há ampliação de superfície pequena**: não existe render target de baixa resolução; cada textura é rasterizada para o tamanho exato em que é desenhada. Na qualidade "Média"/"Baixa" apenas os fundos distantes podem ser rasterizados a 75%/60% da densidade (detalhe suave e atmosférico); personagens, terreno, objetos e HUD ficam sempre em densidade total.

## 3. Pipeline de recursos

1. **Autoria** (`lume/render/svg.py`): `Svg` com caminhos, elipses, polígonos, gradientes lineares/radiais **sempre em `userSpaceOnUse`** com coordenadas absolutas (o nanosvg do SDL_image ignora gradientes em fração unitária de `objectBoundingBox`), `blob`/`smooth_closed`/`smooth_open` para formas orgânicas e `Rand` determinístico. Subconjunto proibido: clipPath, mask, filter, text, use, pattern, image.
2. **Rasterização** (`raster.py`): `pygame.image.load_sized_svg` no tamanho exato; cache em disco de PNGs (chave = hash do SVG + tamanho) em `~/.cache/lume` (ou `LUME_CACHE_DIR`).
3. **Texturas** (`assets.py`): `ArtStore` registra *construtores* por grupo (common, lume, enemies, world, level, ui); rasteriza sob demanda; LRU com orçamento de memória; troca de mundo descarrega o grupo do mundo anterior; troca de fase descarrega o grupo da fase.
4. **Pré-carregamento** (`Scene.preload`): ao carregar uma fase, tudo o que ela pode mostrar é rasterizado atrás do cartão "Preparando a fase…", eliminando travadas de primeiro uso (medidas antes: 180–340 ms).

## 4. Conjuntos artísticos por mundo (`lume/render/worlds/`)

Interface `WorldArt`: `sky`, `sky_extras` (nuvens/astros), `layer_art`/`layers` (parallax com fator horizontal e vertical), `terrain(style, w, h, seed, left, right, top, x0, surface)`, `cave_sky`, `interior(variant)`, `block`, `platform`, `pipe`, `gate`, `hazard`, `props`, `auto_decor`, `weather`. Um módulo `lume/render/worlds/<mundo>.py` com `ART_CLASS` é descoberto automaticamente.

- **Terreno sem emendas**: cada corpo de terreno é dividido em trechos de até 320 u com arte única; padrões que cruzam bordas (borda de grama, estratos, muretas) são funções da coordenada x do mundo, os trechos se sobrepõem 1,5 u e só a borda pendente é contornada.
- **Reino Verde** (dedicado): céu com sol e raios, nuvens volumosas, colinas com moinhos e pomares, grama em lábio recortado, estratos com pedras e raízes, flores, cavernas com cristais e raízes, interior de fortaleza com arcos e estandartes, alvenaria com espinheiros, portões levadiços.
- **Mundos sem conjunto dedicado** usam `generic.GenericWorld` — **provisório**, sinalizado na matriz de qualidade (paleta do bioma sobre as formas do Reino Verde). Não é considerado arte final.

## 5. Personagens e criaturas

- Lume: 45 partes vetoriais (cabeça, olhos, íris, pálpebras, sobrancelhas, bocas, chapéu, cachecol, lanterna, braços e pernas por forma e paleta). Detalhes em `ANIMACOES.md`.
- Inimigos: `CreatureRig` por espécie (`lume/render/enemies/`), registrado por `animation_set`; espécies sem rig usam `ProvisionalCreature` (marcada como provisória).
- Sombra de contato suave sob personagens; piscar de dano só após dano real; brilho aditivo para poderes, relíquias e projéteis.

## 6. Efeitos e iluminação

Partículas visuais em `fx.py` (poeira de corrida, derrapagem e aterrissagem, faíscas de moedas e relíquias, estrelas de pisão), partículas da simulação desenhadas com textura suave, clima por mundo (folhas e pétalas, areia, neve, esporos, brasas) limitado pela qualidade, halos aditivos em blocos ativos, lanternas acesas e itens.

## 7. Limitações conhecidas

- O contêiner de desenvolvimento não tem GPU: as medições usam o renderizador por software do SDL (ver `PERFORMANCE.md`).
- Sem shaders: iluminação dinâmica por pixel, distorção de calor e máscara de escuridão real exigiriam ModernGL; o pântano planejado usa halos e escurecimento por camadas.
- O nanosvg não tem recortes nem filtros: sombras suaves são gradientes radiais com transparência.
