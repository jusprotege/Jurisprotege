#!/usr/bin/env python3
"""
JurisProtege — Script de coleta automática diária
Coleta notícias de violência doméstica e verifica legislação no Planalto
"""

import json
import re
import time
import feedparser
import requests
from datetime import datetime
from bs4 import BeautifulSoup

# ─────────────────────────────────────────────
# CONFIGURAÇÕES
# ─────────────────────────────────────────────

PALAVRAS_CHAVE = [
    "violência doméstica",
    "violencia domestica",
    "maria da penha",
    "feminicídio",
    "feminicidio",
    "medida protetiva",
    "violência familiar",
    "violencia familiar",
    "lei 11.340",
    "lei 11340",
    "vítima mulher",
    "agressão doméstica",
    "agressao domestica",
    "stalking",
    "perseguição doméstica",
    "proteção à mulher",
    "proteção a mulher",
    "violência contra a mulher",
    "violencia contra a mulher",
    "central da mulher",
    "delegacia da mulher",
]

# Feeds RSS de sites jurídicos
FEEDS = {
    "Conjur": {
        "url": "https://www.conjur.com.br/rss.xml",
        "icon": "⚖️",
        "cor": "#c0392b",
    },
    "Migalhas": {
        "url": "https://www.migalhas.com.br/rss/quentes",
        "icon": "🔥",
        "cor": "#e67e22",
    },
    "IBDFAM": {
        "url": "https://ibdfam.org.br/rss/noticias",
        "icon": "👨‍👩‍👧",
        "cor": "#8e44ad",
    },
    "STJ Notícias": {
        "url": "https://www.stj.jus.br/sites/portalp/Paginas/Comunicacao/Noticias/rss.aspx",
        "icon": "🏛️",
        "cor": "#2c3e50",
    },
    "STF Notícias": {
        "url": "https://portal.stf.jus.br/rss/noticia.asp",
        "icon": "🏛️",
        "cor": "#1a5276",
    },
}

# Legislação principal a verificar no Planalto
LEGISLACAO = [
    {
        "numero": "11.340/2006",
        "nome": "Lei Maria da Penha",
        "descricao": "Mecanismos para coibir a violência doméstica e familiar contra a mulher",
        "url": "https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2006/lei/l11340.htm",
        "categoria": "Lei Federal",
    },
    {
        "numero": "13.104/2015",
        "nome": "Feminicídio",
        "descricao": "Qualificadora do homicídio doloso — razões de condição de sexo feminino",
        "url": "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13104.htm",
        "categoria": "Lei Federal",
    },
    {
        "numero": "13.641/2018",
        "nome": "Crime de Descumprimento",
        "descricao": "Criminaliza o descumprimento de medida protetiva de urgência",
        "url": "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13641.htm",
        "categoria": "Lei Federal",
    },
    {
        "numero": "14.188/2021",
        "nome": "Sinal Vermelho",
        "descricao": "Violência psicológica como crime autônomo; Programa Sinal Vermelho",
        "url": "https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/l14188.htm",
        "categoria": "Lei Federal",
    },
    {
        "numero": "13.827/2019",
        "nome": "Medidas Protetivas de Urgência",
        "descricao": "Autoriza delegados e policiais a aplicarem medidas protetivas em situação de risco imediato",
        "url": "https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2019/lei/l13827.htm",
        "categoria": "Lei Federal",
    },
    {
        "numero": "13.772/2018",
        "nome": "Violação de Privacidade",
        "descricao": "Criminaliza registro não autorizado de intimidade sexual; violação de privacidade",
        "url": "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13772.htm",
        "categoria": "Lei Federal",
    },
    {
        "numero": "14.132/2021",
        "nome": "Stalking / Perseguição",
        "descricao": "Criminaliza a perseguição — art. 147-A do Código Penal",
        "url": "https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/l14132.htm",
        "categoria": "Lei Federal",
    },
]


# ─────────────────────────────────────────────
# FUNÇÕES
# ─────────────────────────────────────────────

def texto_contem_palavras(texto: str) -> bool:
    """Verifica se o texto contém alguma palavra-chave relevante."""
    texto_lower = texto.lower()
    return any(p in texto_lower for p in PALAVRAS_CHAVE)


def limpar_html(texto: str) -> str:
    """Remove tags HTML de um texto."""
    return BeautifulSoup(texto, "html.parser").get_text(separator=" ").strip()


def coletar_noticias() -> list:
    """Coleta notícias de todos os feeds RSS e filtra as relevantes."""
    noticias = []
    headers = {"User-Agent": "JurisProtege-Bot/1.0 (jurisprudencia violencia domestica)"}

    for fonte, config in FEEDS.items():
        print(f"  📡 Coletando {fonte}...")
        try:
            resp = requests.get(config["url"], headers=headers, timeout=15)
            feed = feedparser.parse(resp.text)

            for entry in feed.entries[:50]:
                titulo = entry.get("title", "")
                resumo = limpar_html(entry.get("summary", entry.get("description", "")))
                link = entry.get("link", "")
                data_raw = entry.get("published", entry.get("updated", ""))

                # Filtra por palavras-chave
                if not texto_contem_palavras(titulo + " " + resumo):
                    continue

                # Formata data
                try:
                    data_struct = entry.get("published_parsed") or entry.get("updated_parsed")
                    if data_struct:
                        data_fmt = datetime(*data_struct[:6]).strftime("%d/%m/%Y")
                    else:
                        data_fmt = data_raw[:10] if data_raw else ""
                except Exception:
                    data_fmt = ""

                noticias.append({
                    "titulo": titulo,
                    "resumo": resumo[:400] + ("..." if len(resumo) > 400 else ""),
                    "link": link,
                    "data": data_fmt,
                    "data_raw": data_raw,
                    "fonte": fonte,
                    "icon": config["icon"],
                    "cor": config["cor"],
                })

            time.sleep(1)  # Respeita o servidor

        except Exception as e:
            print(f"    ⚠️  Erro ao coletar {fonte}: {e}")

    # Ordena por data mais recente (aproximado)
    noticias.sort(key=lambda x: x.get("data_raw", ""), reverse=True)

    print(f"  ✅ {len(noticias)} notícias relevantes encontradas")
    return noticias[:30]  # Máximo 30 notícias


def verificar_legislacao() -> list:
    """Verifica se a legislação no Planalto está acessível e extrai última alteração."""
    headers = {"User-Agent": "JurisProtege-Bot/1.0"}
    leis_verificadas = []

    for lei in LEGISLACAO:
        print(f"  📋 Verificando Lei {lei['numero']}...")
        lei_resultado = lei.copy()
        lei_resultado["verificado_em"] = datetime.now().strftime("%d/%m/%Y")

        try:
            resp = requests.get(lei["url"], headers=headers, timeout=15)

            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                texto_pagina = soup.get_text()

                # Tenta encontrar data de última alteração
                match = re.search(
                    r"(Alterada?|Atualizada?|Redação dada|incluída?)\s+pela?\s+Lei[^\d]*(\d{2,3}\.\d{3}[^\d,\.]+[\d]{4})",
                    texto_pagina,
                    re.IGNORECASE,
                )
                if match:
                    lei_resultado["ultima_alteracao"] = match.group(0)[:120]
                else:
                    lei_resultado["ultima_alteracao"] = None

                lei_resultado["status"] = "online"
                lei_resultado["status_texto"] = "✅ Disponível no Planalto"
            else:
                lei_resultado["status"] = "erro"
                lei_resultado["status_texto"] = f"⚠️ HTTP {resp.status_code}"

        except Exception as e:
            lei_resultado["status"] = "erro"
            lei_resultado["status_texto"] = "⚠️ Não foi possível verificar"
            print(f"    Erro: {e}")

        leis_verificadas.append(lei_resultado)
        time.sleep(1)

    return leis_verificadas


# ─────────────────────────────────────────────
# EXECUÇÃO PRINCIPAL
# ─────────────────────────────────────────────

def main():
    agora = datetime.now()
    print(f"\n🚀 JurisProtege — Atualização {agora.strftime('%d/%m/%Y %H:%M')}")
    print("=" * 50)

    # Coleta notícias
    print("\n📰 Coletando notícias...")
    noticias = coletar_noticias()

    # Verifica legislação
    print("\n📋 Verificando legislação no Planalto...")
    leis = verificar_legislacao()

    # Salva noticias.json
    dados_noticias = {
        "atualizado": agora.strftime("%d/%m/%Y às %H:%M"),
        "atualizado_iso": agora.isoformat(),
        "total": len(noticias),
        "items": noticias,
    }
    with open("data/noticias.json", "w", encoding="utf-8") as f:
        json.dump(dados_noticias, f, ensure_ascii=False, indent=2)
    print(f"\n💾 data/noticias.json salvo ({len(noticias)} itens)")

    # Salva legislacao.json
    dados_legislacao = {
        "atualizado": agora.strftime("%d/%m/%Y às %H:%M"),
        "atualizado_iso": agora.isoformat(),
        "total": len(leis),
        "leis": leis,
    }
    with open("data/legislacao.json", "w", encoding="utf-8") as f:
        json.dump(dados_legislacao, f, ensure_ascii=False, indent=2)
    print(f"💾 data/legislacao.json salvo ({len(leis)} leis)")

    print("\n✅ Atualização concluída com sucesso!")
    print("=" * 50)


if __name__ == "__main__":
    main()
