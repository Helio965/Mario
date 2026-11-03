# Migração de salvamentos

Código: `lume/systems/save.py`. Testes: `tests/python/test_save.py`.

## Formatos

| Formato | Onde | Conteúdo |
| ------- | ---- | -------- |
| 1 (`lume-save-v1`) | `localStorage` da edição web | `unlocked` (índice 0–14), `completed` com IDs "1-1"…"5-3", `records`, `relics` (uma marca por fase), `achievements`, `settings` |
| 2 | `save.json` na pasta de dados do usuário (`%APPDATA%/Lume`, `~/Library/Application Support/Lume`, `~/.local/share/lume` ou `LUME_SAVE_DIR`) | `unlocked` e `completed` por ID estável, `records`, `relics` (IDs das relíquias por fase), `secrets` (IDs por fase), `achievements`, `legacy_relic_marks`, `legacy_achievements`, `migrated_from`, `settings` (inclui qualidade, resolução, tela cheia, vsync, FPS) |

## Regras da migração (formato 1 → 2)

- IDs antigos são traduzidos pelos `legacy_ids` declarados em cada fase convertida (`"1-1"` → `first_steps`), não por posição.
- Fases concluídas, recordes e configurações são preservados.
- A marca de relíquia antiga não diz *qual* relíquia foi achada; ela vai para `legacy_relic_marks` e continua contando como "relíquia encontrada" naquela fase.
- Conquistas antigas ficam em `legacy_achievements` (os critérios mudaram com 60 fases); as novas são derivadas do progresso.
- Desbloqueio: tudo que era jogável continua jogável — a fase do índice `unlocked` antigo, todas as concluídas e a próxima fase jogável depois de cada concluída na nova ordem (vagas ainda não implementadas são puladas).

## Como importar o progresso da edição web

1. No navegador, abra o console da página do jogo e copie o valor: `localStorage.getItem("lume-save-v1")`.
2. Salve o texto em um arquivo `lume-save-v1.json` (o conteúdo pode ser o JSON puro ou `{"lume-save-v1": "<texto>"}`).
3. Execute `python -m lume --import-save caminho/lume-save-v1.json`, **ou** coloque o arquivo na pasta de dados: sem `save.json`, ele é importado automaticamente.

## Robustez

- Escrita atômica (arquivo temporário + `os.replace`).
- Arquivo ilegível ou de versão desconhecida é **copiado** para `save.corrupt-AAAAMMDD-HHMMSS.json` antes de iniciar dados limpos; "Apagar progresso" também guarda cópia (`save.reset-*.json`).
- Todos os campos são reconstruídos e validados (IDs com caracteres de controle, `__proto__`, números não finitos e valores fora de faixa são descartados ou limitados).
- IDs desconhecidos (fases futuras) são mantidos, não apagados.
