# PT Holidays API

API para consultar feriados nacionais, regionais e municipais de Portugal.

O projeto foi desenhado para dados auditaveis: cada feriado devolvido inclui
`sources`, `verification_status` e `confidence`. A carga inicial cobre:

- feriados nacionais calculados por regra;
- feriados regionais dos Acores e da Madeira;
- feriados municipais para os 308 municipios, com datas de 2026, 2027 e 2028.

## Testar Online

Podes usar o deploy publico para testar a API sem instalar nada:

```text
https://feriados-red.vercel.app
```

Documentacao interativa:

```text
https://feriados-red.vercel.app/docs
```

OpenAPI schema:

```text
https://feriados-red.vercel.app/openapi.json
```

## Arranque Local

```powershell
python -m pip install -e .[dev]
python -m uvicorn pt_holidays_api.app:app --reload
```

Base URL local:

```text
http://127.0.0.1:8000
```

## Modelo de Dados

Cada feriado devolvido tem este formato:

```json
{
  "date": "2026-06-13",
  "name": "Santo Antonio",
  "scope": "municipal",
  "region": null,
  "district": "Lisboa",
  "municipality": "Lisboa",
  "sources": [
    "icalendario_municipais",
    "dirportugal_municipais",
    "aspl_municipais_pdf"
  ],
  "verification_status": "cross_checked",
  "confidence": 0.85
}
```

Campos principais:

| Campo | Tipo | Descricao |
| --- | --- | --- |
| `date` | string ISO `YYYY-MM-DD` | Data do feriado. |
| `name` | string | Nome do feriado. |
| `scope` | `national`, `regional`, `municipal` | Ambito do feriado. |
| `region` | string ou null | Regiao autonoma quando aplicavel. |
| `district` | string ou null | Distrito/regiao do municipio quando aplicavel. |
| `municipality` | string ou null | Concelho quando aplicavel. |
| `sources` | array de strings | IDs das fontes usadas. Ver `GET /sources`. |
| `verification_status` | string | Estado de verificacao. |
| `confidence` | number | Confianca interna entre `0` e `1`. |

Estados de verificacao:

| Estado | Significado |
| --- | --- |
| `verified` | Confirmado por fonte legal/oficial ou regra legal estavel. |
| `cross_checked` | Confirmado por duas ou mais fontes secundarias concordantes. |
| `needs_primary_source` | Dado util, mas ainda precisa de confirmacao primaria. |

## Endpoints

### Fluxo recomendado

Para integrar a API sem hardcode:

1. chamar `GET /regions` para descobrir as regioes autonomas suportadas;
2. chamar `GET /districts` para descobrir distritos/regioes administrativas;
3. chamar `GET /municipalities` para descobrir os concelhos suportados;
4. chamar `GET /holidays` com `year` e, se aplicavel, `region`, `district`
   e/ou `municipality`.

### `GET /health`

Verifica se a API esta operacional.

```bash
curl https://feriados-red.vercel.app/health
```

Resposta:

```json
{
  "status": "ok"
}
```

### `GET /holidays`

Lista feriados de um ano. Este endpoint devolve sempre os feriados nacionais e,
opcionalmente, acrescenta feriados regionais e/ou municipais.

Parametros:

| Parametro | Obrigatorio | Exemplo | Descricao |
| --- | --- | --- | --- |
| `year` | Sim | `2026` | Ano entre 1900 e 2100. |
| `region` | Nao | `Acores`, `Madeira` | Inclui feriados da regiao autonoma. |
| `district` | Nao | `Lisboa`, `Porto`, `Faro` | Filtra/desambigua concelhos. Sozinho nao inclui feriados municipais. |
| `municipality` | Nao | `Lisboa`, `Porto`, `Coimbra` | Inclui o feriado municipal desse concelho. |

Feriados nacionais de 2026:

```bash
curl "https://feriados-red.vercel.app/holidays?year=2026"
```

Feriados nacionais + Lisboa:

```bash
curl "https://feriados-red.vercel.app/holidays?year=2026&municipality=Lisboa"
```

Feriados nacionais, com distrito apenas como contexto de descoberta:

```bash
curl "https://feriados-red.vercel.app/holidays?year=2026&district=Lisboa"
```

Esta chamada nao inclui feriados municipais, porque os feriados municipais sao
por concelho, nao por distrito.

Feriado municipal de Lagoa no Algarve, distinguindo de Lagoa nos Acores:

```bash
curl "https://feriados-red.vercel.app/holidays?year=2026&district=Faro&municipality=Lagoa"
```

Feriados nacionais + Madeira:

```bash
curl "https://feriados-red.vercel.app/holidays?year=2026&region=Madeira"
```

Feriados nacionais + Acores + Ponta Delgada:

```bash
curl "https://feriados-red.vercel.app/holidays?year=2026&region=Acores&municipality=Ponta%20Delgada"
```

Exemplo parcial de resposta:

```json
[
  {
    "date": "2026-01-01",
    "name": "Ano Novo",
    "scope": "national",
    "region": null,
    "district": null,
    "municipality": null,
    "sources": [
      "dre_codigo_trabalho_234_235",
      "visitportugal_feriados"
    ],
    "verification_status": "verified",
    "confidence": 1.0
  },
  {
    "date": "2026-06-13",
    "name": "Santo Antonio",
    "scope": "municipal",
    "region": null,
    "district": "Lisboa",
    "municipality": "Lisboa",
    "sources": [
      "icalendario_municipais",
      "dirportugal_municipais",
      "aspl_municipais_pdf"
    ],
    "verification_status": "cross_checked",
    "confidence": 0.85
  }
]
```

### `GET /municipalities`

Lista os concelhos disponiveis, o nome do feriado municipal, anos cobertos e
fontes associadas.

```bash
curl https://feriados-red.vercel.app/municipalities
```

Exemplo parcial:

```json
[
  {
    "municipality": "Abrantes",
    "district": "Santarem",
    "holiday_name": "Elevacao a cidade",
    "available_years": [2026, 2027, 2028],
    "sources": [
      "icalendario_municipais",
      "dirportugal_municipais",
      "aspl_municipais_pdf"
    ],
    "verification_status": "cross_checked",
    "confidence": 0.85
  }
]
```

### `GET /districts`

Lista distritos/regioes administrativas disponiveis, incluindo Acores e
Madeira enquanto agrupadores de municipios.

```bash
curl https://feriados-red.vercel.app/districts
```

Exemplo parcial:

```json
[
  {
    "district": "Lisboa",
    "municipality_count": 16,
    "municipality_names": ["Alenquer", "Amadora", "Arruda dos Vinhos"],
    "available_years": [2026, 2027, 2028]
  }
]
```

### `GET /regions`

Lista as regioes autonomas suportadas e os feriados regionais conhecidos. Este
endpoint serve para descobrir os valores validos para o parametro `region` em
`GET /holidays`. Para Lisboa, Porto, Braga e outros agrupadores municipais, usa
`GET /districts`.

```bash
curl https://feriados-red.vercel.app/regions
```

Resposta:

```json
[
  {
    "region": "Acores",
    "type": "autonomous_region",
    "available_years": "calculated by rule",
    "holidays": [
      {
        "name": "Dia da Regiao Autonoma dos Acores",
        "start_year": 1980,
        "sources": ["alraa_dia_acores"],
        "verification_status": "verified",
        "confidence": 0.95
      }
    ]
  },
  {
    "region": "Madeira",
    "type": "autonomous_region",
    "available_years": "calculated by rule",
    "holidays": [
      {
        "name": "Dia da Autonomia",
        "start_year": 2025,
        "sources": ["joram_autonomia_madeira_2024"],
        "verification_status": "verified",
        "confidence": 0.95
      }
    ]
  }
]
```

### `GET /sources`

Lista as fontes registadas. Os IDs desta resposta aparecem no campo `sources`
dos feriados.

```bash
curl https://feriados-red.vercel.app/sources
```

Exemplo parcial:

```json
[
  {
    "id": "dre_codigo_trabalho_234_235",
    "name": "Diario da Republica - Codigo do Trabalho, artigos 234.º e 235.º",
    "url": "https://files.dre.pt/gratuitos/1s/2009/02/03000.pdf"
  }
]
```

### `GET /coverage`

Mostra a cobertura atual do dataset.

```bash
curl https://feriados-red.vercel.app/coverage
```

Resposta:

```json
{
  "national_years": "calculated by rule",
  "regional_years": "calculated by rule",
  "municipal_years": [2026, 2027, 2028],
  "municipalities": 308,
  "verification_policy": "verified = legal/official primary source plus secondary check; cross_checked = two or more concordant secondary sources; needs_primary_source = useful data but still needs municipal/legal confirmation"
}
```

## Exemplos de Integracao

### JavaScript

```js
const params = new URLSearchParams({
  year: "2026",
  municipality: "Lisboa",
});

const response = await fetch(`https://feriados-red.vercel.app/holidays?${params}`);
const holidays = await response.json();

console.log(holidays);
```

### Python

```python
import requests

response = requests.get(
    "https://feriados-red.vercel.app/holidays",
    params={"year": 2026, "municipality": "Lisboa"},
    timeout=30,
)
response.raise_for_status()

holidays = response.json()
print(holidays)
```

### PowerShell

```powershell
Invoke-RestMethod "https://feriados-red.vercel.app/holidays?year=2026&municipality=Lisboa"
```

## Erros

Se for pedido um municipio sem dados para o ano indicado, a API devolve `404`.

```bash
curl "https://feriados-red.vercel.app/holidays?year=2025&municipality=Lisboa"
```

Resposta:

```json
{
  "detail": "Municipio sem dados para esse ano. Consulte /coverage, /districts e /municipalities."
}
```

## Fontes Usadas

As fontes tambem estao registadas em `data/sources.json` e sao expostas por
`GET /sources`.

| ID | Uso | Fonte |
| --- | --- | --- |
| `dre_codigo_trabalho_234_235` | Feriados nacionais obrigatorios | Diario da Republica, Codigo do Trabalho, artigos 234.º e 235.º: https://files.dre.pt/gratuitos/1s/2009/02/03000.pdf |
| `visitportugal_feriados` | Confirmacao secundaria dos feriados nacionais | VisitPortugal: https://www.visitportugal.com/pt-pt/node/470987 |
| `icalendario_municipais` | Fonte estruturada para feriados municipais 2026-2028 | iCalendario: https://icalendario.pt/feriados/municipais/ |
| `dirportugal_municipais` | Confirmacao secundaria municipal | dirPortugal: https://dirportugal.com/feriados-municipais/ |
| `aspl_municipais_pdf` | Confirmacao secundaria municipal | ASPL PDF: https://www.aspl.pt/images/aspl_pdfs/Feriados%20Municipais%20Nacionais.pdf |
| `alraa_dia_acores` | Feriado regional dos Acores | ALRAA: https://www.alra.pt/index.php/artigossite/1768-dia-da-regiao-autonoma-dos-acores-2025 |
| `joram_autonomia_madeira_2024` | Dia da Autonomia da Madeira, desde 2025 | JORAM: https://joram.madeira.gov.pt/joram/Iserie/Ano%20de%202024/ISerie-206-2024-12-16sup.pdf |
| `dre_madeira_primeira_oitava` | Primeira Oitava na Madeira | Diario da Republica: https://files.dre.pt/1s/2002/11/258a00/71837183.pdf |
| `rtp_madeira_dia_regiao` | Confirmacao publica do Dia da Regiao da Madeira | RTP Madeira: https://madeira.rtp.pt/sociedade/madeira-assinala-hoje-o-dia-da-regiao/ |

## Verificacao e Correcao Automatica

O projeto inclui scripts para voltar a consultar as fontes, validar os dados e
corrigir o dataset local quando houver divergencias:

```powershell
python scripts/import_icalendario.py --check
python scripts/verify_sources.py
python scripts/refresh_sources.py --fix
python -m pytest
```

O workflow `.github/workflows/verify-sources.yml` corre todas as segundas-feiras
as 06:17 UTC e tambem pode ser executado manualmente no GitHub em
**Actions > Verify holiday sources > Run workflow**.

O job faz:

1. instala o projeto;
2. volta a consultar a fonte municipal estruturada;
3. reescreve `data/municipal_holidays.json` se os dados mudarem;
4. valida que todos os municipios continuam a ter pelo menos duas fontes
   registadas;
5. valida que os URLs das fontes respondem;
6. corre os testes;
7. faz commit e push automatico se houver correcao no dataset;
8. dispara deploy de producao na Vercel se o secret `VERCEL_DEPLOY_HOOK_URL`
   estiver configurado.

## Nota Legal

Esta API nao substitui a consulta da legislacao aplicavel, editais municipais ou
publicacoes oficiais. Para uso critico, validar cada municipio contra fonte
municipal primaria.
