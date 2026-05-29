import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

Status = Literal["NORMAL", "SUSPEITO", "ALERTA"]

@dataclass
class Transacao:
    usuario_id: str
    categoria: str
    quantidade: float
    valor_total: float
    data: datetime = field(default_factory=datetime.now)

@dataclass
class ResultadoAnalise:
    transacao: Transacao
    status: Status
    percentil: int
    p95: float
    p99: float
    motivo: str

    def __str__(self) -> str:
        icones = {"NORMAL": "✅", "SUSPEITO": "⚠️", "ALERTA": "🚨"}
        usuario = self.transacao.usuario_id.capitalize()

        if self.status == "NORMAL":
            return f"{icones[self.status]} Tudo certo com a compra de {self.transacao.categoria} de {usuario}."

        intensidade = "muito acima do comum" if self.status == "ALERTA" else "acima do esperado"
        return (
            f"{icones[self.status]} Atenção: a compra de {self.transacao.categoria} "
            f"({self.transacao.quantidade:.0f} unidades) feita por {usuario} está {intensidade}. "
            f"Esse valor superou {self.percentil}% do que o cliente costuma comprar."
        )

class DetectorAnomalias:
    def __init__(self, limiar_suspeito: int = 95, limiar_alerta: int = 99, min_historico: int = 5):
        self.limiar_suspeito = limiar_suspeito
        self.limiar_alerta = limiar_alerta
        self.min_historico = min_historico
        self._historico: dict[str, dict[str, list[float]]] = {}

    def adicionar_historico(self, usuario_id: str, categoria: str, quantidades: list[float]) -> None:
        self._historico.setdefault(usuario_id, {})
        self._historico[usuario_id][categoria] = list(quantidades)

    def _historico_usuario(self, usuario_id: str, categoria: str) -> list[float]:
        return self._historico.get(usuario_id, {}).get(categoria, [])

    @staticmethod
    def _calcular_percentil(dados: list[float], p: float) -> float:
        s = sorted(dados)
        idx = (p / 100) * (len(s) - 1)
        lo = int(idx)
        hi = min(lo + 1, len(s) - 1)
        return s[lo] + (s[hi] - s[lo]) * (idx - lo)

    @staticmethod
    def _posicao_percentil(dados: list[float], valor: float) -> int:
        abaixo = sum(1 for x in dados if x < valor)
        return round((abaixo / len(dados)) * 100)

    def analisar(self, transacao: Transacao) -> ResultadoAnalise:
        historico = self._historico_usuario(transacao.usuario_id, transacao.categoria)

        if len(historico) < self.min_historico:
            return ResultadoAnalise(
                transacao=transacao,
                status="NORMAL",
                percentil=0,
                p95=transacao.quantidade,
                p99=transacao.quantidade,
                motivo="Sem histórico suficiente"
            )

        p95 = self._calcular_percentil(historico, 95)
        p99 = self._calcular_percentil(historico, 99)
        pos = self._posicao_percentil(historico, transacao.quantidade)

        if transacao.quantidade > p99:
            status = "ALERTA"
            motivo = "Superou o limite de alerta"
        elif transacao.quantidade > p95:
            status = "SUSPEITO"
            motivo = "Superou o limite de suspeita"
        else:
            status = "NORMAL"
            motivo = "Dentro do padrão"

        self._historico[transacao.usuario_id][transacao.categoria].append(transacao.quantidade)

        return ResultadoAnalise(
            transacao=transacao,
            status=status,
            percentil=pos,
            p95=round(p95, 1),
            p99=round(p99, 1),
            motivo=motivo,
        )

    def analisar_lote(self, transacoes: list[Transacao]) -> list[ResultadoAnalise]:
        return [self.analisar(t) for t in transacoes]

def emitir_alerta(resultado: ResultadoAnalise) -> None:
    if resultado.status == "NORMAL":
        return

    t = resultado.transacao
    usuario = t.usuario_id.capitalize()
    limite_comum = resultado.p95

    print("\n")
    if resultado.status == "ALERTA":
        print(f"🚨 ALERTA CRÍTICO: Identificamos um comportamento de compra muito atípico na conta de {usuario}.")
    else:
        print(f"⚠️ ATENÇÃO: Identificamos uma compra um pouco fora do padrão na conta de {usuario}.")

    print(f"Foi realizada uma compra de {t.quantidade:.0f} unidades de {t.categoria}, no valor total de R$ {t.valor_total:,.2f}.")
    print(f"Normalmente, o máximo que este cliente compra de uma vez é de {limite_comum:.0f} unidades.")
    print(f"Esta transação aconteceu em {t.data.strftime('%d/%m/%Y às %H:%M')} e superou {resultado.percentil}% do volume que o cliente costuma registrar.")

def gerar_historico_tipico(media: float, desvio: float, n: int = 20) -> list[float]:
    random.seed(42)
    return [max(0, round(random.gauss(media, desvio), 1)) for _ in range(n)]

def main():
    detector = DetectorAnomalias(limiar_suspeito=95, limiar_alerta=99, min_historico=5)

    detector.adicionar_historico("alice", "Passagens Aéreas", gerar_historico_tipico(1.5, 0.8))
    detector.adicionar_historico("alice", "Roupas", gerar_historico_tipico(3.0, 1.2))
    detector.adicionar_historico("alice", "Eletrônicos", gerar_historico_tipico(0.5, 0.5))
    detector.adicionar_historico("bob", "Supermercado", gerar_historico_tipico(4.0, 1.0))
    detector.adicionar_historico("bob", "Ingressos", gerar_historico_tipico(2.0, 1.0))
    detector.adicionar_historico("carlos", "Passagens Aéreas", gerar_historico_tipico(2.0, 1.0))

    agora = datetime.now()

    transacoes = [
        Transacao("alice", "Passagens Aéreas", quantidade=2, valor_total=1200, data=agora),
        Transacao("alice", "Roupas", quantidade=4, valor_total=800, data=agora),
        Transacao("bob", "Ingressos", quantidade=18, valor_total=5400, data=agora),
        Transacao("carlos", "Passagens Aéreas", quantidade=500, valor_total=75000, data=agora),
    ]

    print("\nIniciando análise de comportamento de compras...\n")

    resultados = detector.analisar_lote(transacoes)

    for r in resultados:
        print(r)

    alertas = [r for r in resultados if r.status != "NORMAL"]
    if alertas:
        for r in alertas:
            emitir_alerta(r)
    else:
        print("\nNenhuma anomalia detectada neste lote.")

    total = len(resultados)
    normais = sum(1 for r in resultados if r.status == "NORMAL")
    suspeitas = sum(1 for r in resultados if r.status == "SUSPEITO")
    em_alerta = sum(1 for r in resultados if r.status == "ALERTA")

    print(f"\nResumo da verificação: Foram avaliadas {total} transações. Dessas, {normais} seguiram o padrão normal, {suspeitas} foram marcadas como suspeitas e {em_alerta} geraram alerta crítico.")

if __name__ == "__main__":
    main()