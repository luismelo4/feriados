# PT Holidays API

API para consultar feriados nacionais, regionais e municipais de Portugal.

O projeto foi desenhado para dados auditaveis: cada feriado devolvido inclui
`sources`, `verification_status` e `confidence`. A carga inicial cobre:

- feriados nacionais calculados por regra;
- feriados regionais dos Acores e da Madeira;
- feriados municipais para os 308 municipios, com datas de 2026, 2027 e 2028.

## Arranque local

```powershell
python -m pip install -e .[dev]
python -m uvicorn pt_holidays_api.app:app --reload
```

## Endpoints

```text
GET /health
GET /holidays?year=2026
GET /holidays?year=2026&region=Acores
GET /holidays?year=2026&region=Madeira
GET /holidays?year=2026&municipality=Lisboa
GET /municipalities
GET /sources
GET /coverage
```

## Fontes usadas

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

## Verificacao e correcao automatica

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

## Deploy gratis

### Opcao recomendada: Vercel

Este projeto inclui `api/index.py`, `requirements.txt` e `vercel.json`, por isso
pode ser importado diretamente na Vercel a partir do repositorio GitHub. A API e
stateless e funciona bem como serverless function.

Passos:

1. abrir https://vercel.com/new;
2. importar `luismelo4/feriados`;
3. manter as definicoes automaticas;
4. fazer deploy;
5. testar `/health` e `/docs` no URL gerado.

Para deploy automatico depois do job semanal:

1. na Vercel, abrir o projeto `feriados`;
2. ir a **Settings > Git > Deploy Hooks**;
3. criar um hook para a branch `main`;
4. copiar o URL gerado;
5. no GitHub, ir a **Settings > Secrets and variables > Actions**;
6. criar o secret `VERCEL_DEPLOY_HOOK_URL` com esse URL.

Mesmo sem esse hook, a integracao GitHub da Vercel deve fazer deploy quando ha
push para `main`. O hook deixa esse comportamento explicito e facil de auditar.

### Alternativa: Render

Tambem existe `render.yaml`. No Render, criar um Web Service a partir do GitHub.
O build command e `pip install -e .` e o start command e:

```text
uvicorn pt_holidays_api.app:app --host 0.0.0.0 --port $PORT
```

Render e muito simples para FastAPI tradicional, mas confirma sempre o plano
gratis atual antes de depender dele em producao.

## Nota legal

Esta API nao substitui a consulta da legislacao aplicavel, editais municipais ou
publicacoes oficiais. Para uso critico, validar cada municipio contra fonte
municipal primaria.
