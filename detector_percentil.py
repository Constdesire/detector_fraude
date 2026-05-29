def percentil(historico: list[float], p: float) -> float:
    s = sorted(historico)
    idx = (p / 100) * (len(s) - 1)
    lo, hi = int(idx), min(int(idx) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (idx - lo)

def detectar(historico: list[float], nova: float) -> dict:
    p95 = percentil(historico, 95)
    p99 = percentil(historico, 99)
    abaixo = sum(1 for x in historico if x < nova)
    pct = round((abaixo / len(historico)) * 100)

    if nova > p99:
        status = "ALERTA"
    elif nova > p95:
        status = "SUSPEITO"
    else:
        status = "NORMAL"

    return {"status": status, "percentil": pct, "p95": round(p95, 1), "p99": round(p99, 1)}

def checar(usuario, categoria, historico, nova):
    r = detectar(historico, nova)
    icones = {"NORMAL": "✅", "SUSPEITO": "⚠️", "ALERTA": "🚨"}
    icone = icones[r["status"]]
    
    # Criando uma mensagem que soa como um comentário de um assistente humano
    if r["status"] == "NORMAL":
        mensagem = f"está dentro do padrão esperado para {categoria}."
    else:
        mensagem = (f"está bem acima do normal para {categoria}. "
                    f"Este valor é maior que {r['percentil']}% do seu histórico habitual.")

    print(f"{icone} {usuario}: {mensagem} (Valor: {nova})")


if __name__ == "__main__":
    checar("Alice", "Passagens",    [1,2,1,1,2,1,2,1,1,2], nova=980)
    checar("Bob",   "Supermercado", [4,5,4,3,4,5,4,3,4,4], nova=15)
    checar("Carol", "Roupas",       [2,3,2,4,2,3,2,3,2,4], nova=4)
    checar("David", "Eletrônicos",  [1,0,1,0,1,0,1,1,0,1], nova=45)
