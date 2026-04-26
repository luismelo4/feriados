# PT Holidays API

API para consultar feriados nacionais, regionais e municipais de Portugal.

O projeto foi desenhado para dados auditaveis: cada feriado devolvido inclui `sources`, `verification_status` e `confidence`. A carga inicial cobre:

- feriados nacionais calculados por regra;
- feriados regionais dos Acores e da Madeira;
- feriados municipais para os 308 municipios, com datas de 2026, 2027 e 2028.

## Arranque

```powershell
python -m pip install -e .[dev]
python -m uvicorn pt_holidays_api.app:app --reload
```

## Exemplos

```text
GET /health
GET /holidays?year=2026
GET /holidays?year=2026&region=azores
GET /holidays?year=2026&municipality=Lisboa
GET /municipalities
GET /sources
GET /coverage
```

## Verificacao

As regras nacionais sao suportadas pelo Codigo do Trabalho, artigo 234.º, e por fonte secundaria publica. Os dados municipais devem ser tratados como um dataset verificavel: a API conserva as fontes usadas e o script `scripts/verify_sources.py` foi deixado como ponto de extensao para comparar dumps externos antes de promover novas datas para `verified`.

```powershell
python scripts/verify_sources.py
```

## Nota legal

Esta API nao substitui a consulta da legislacao aplicavel, editais municipais ou publicacoes oficiais. Para uso critico, validar cada municipio contra fonte municipal primaria.
