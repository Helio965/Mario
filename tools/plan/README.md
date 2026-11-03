# Gerador do planejamento das 60 fases

Fonte única de `lume/data/plan/campaign_plan.json`, `docs/level_design/PLANEJAMENTO_60_FASES.md`
e `docs/level_design/MUNDO_01.md` … `MUNDO_10.md`.

```bash
python3 tools/plan/build.py   # regenera o JSON e os documentos a partir de w01.py … w10.py
python3 tools/plan/check.py   # ids na ordem do registro, chaves, estreias = introduced_in, habitats, sub-áreas
```

Os módulos `w01.py` … `w10.py` descrevem cada fase com os 24 campos do planejamento; `common.py`
contém limites físicos (vão máximo, critérios de teste genéricos). Rode `build.py` de novo quando o
registro de espécies (`lume/data/enemies.json`) ou o estado dos chefes mudar — status e ids são
recalculados. O cabeçalho do plano registra a data dos dados consultados, então cada execução muda
essa linha.
