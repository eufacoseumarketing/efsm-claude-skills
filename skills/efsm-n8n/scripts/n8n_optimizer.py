#!/usr/bin/env python3
"""
EFSM n8n Workflow Optimizer
Analisa performance, identifica gargalos e sugere otimizações.

Uso:
  python3 scripts/n8n_optimizer.py analyze --id <id> --days 30 --pretty
  python3 scripts/n8n_optimizer.py suggest --id <id> --pretty
  python3 scripts/n8n_optimizer.py report --id <id>
"""

import sys
import json
import argparse
from typing import Dict, List, Any
from collections import defaultdict

try:
    from n8n_api import N8nClient
except ImportError:
    from scripts.n8n_api import N8nClient


# Tipos de nós com operações custosas
EXPENSIVE_NODE_TYPES = {
    "httpRequest":  "Chamadas HTTP externas podem ser lentas e têm rate limits",
    "googleSheets": "API do Google Sheets tem rate limits e pode ser lenta em grandes datasets",
    "postgres":     "Queries de banco podem ser lentas em grandes volumes",
    "mysql":        "Queries de banco podem ser lentas em grandes volumes",
    "mongodb":      "Queries de banco podem ser lentas em grandes volumes",
    "airtable":     "API do Airtable tem rate limits restritivos",
    "hubspot":      "API do HubSpot tem rate limits e pode ser lenta",
    "mailchimp":    "API do Mailchimp pode ser lenta para listas grandes",
    "facebookGraphApi": "API do Meta Ads tem rate limits e janelas de tempo",
    "webhook":      "Aguardar respostas de webhook pode causar atrasos",
}


class WorkflowOptimizer:
    """Analisa e otimiza a performance de workflows n8n da EFSM"""

    def __init__(self, client: N8nClient = None):
        self.client = client or N8nClient()

    # -------------------------------------------------------------------------
    # Análise completa
    # -------------------------------------------------------------------------

    def analyze_performance(self, workflow_id: str, days: int = 7) -> Dict:
        """
        Análise completa de performance: métricas de execução, estrutura de nós,
        gargalos e oportunidades de otimização. Score final de 0 a 100.
        """
        workflow = self.client.get_workflow(workflow_id)
        statistics = self.client.get_workflow_statistics(workflow_id, days=days)

        analysis: Dict[str, Any] = {
            "workflow_id": workflow_id,
            "workflow_name": workflow.get("name"),
            "analysis_period_days": days,
            "execution_metrics": self._analyze_execution_metrics(statistics),
            "node_analysis": self._analyze_nodes(workflow),
            "connection_analysis": self._analyze_connections(workflow),
            "bottlenecks": [],
            "optimization_opportunities": [],
            "performance_score": 0,
        }

        analysis["bottlenecks"] = self._identify_bottlenecks(workflow, statistics)
        analysis["optimization_opportunities"] = self._find_optimizations(workflow, statistics)
        analysis["performance_score"] = self._calculate_performance_score(analysis)

        return analysis

    # -------------------------------------------------------------------------
    # Métricas de execução
    # -------------------------------------------------------------------------

    def _analyze_execution_metrics(self, statistics: Dict) -> Dict:
        """Classifica saúde do workflow com base em taxa de sucesso."""
        total = statistics.get("total_executions", 0)
        successful = statistics.get("successful", 0)
        failed = statistics.get("failed", 0)
        success_rate = statistics.get("success_rate", 0.0)

        if success_rate >= 95:
            health = "excelente"
        elif success_rate >= 80:
            health = "bom"
        elif success_rate >= 60:
            health = "regular"
        else:
            health = "crítico"

        return {
            "total_executions": total,
            "successful_executions": successful,
            "failed_executions": failed,
            "success_rate": success_rate,
            "failure_rate": round(100 - success_rate, 2) if total > 0 else 0.0,
            "health": health,
            "top_errors": dict(
                sorted(
                    statistics.get("error_patterns", {}).items(),
                    key=lambda x: x[1],
                    reverse=True,
                )[:5]
            ),
        }

    # -------------------------------------------------------------------------
    # Análise de nós
    # -------------------------------------------------------------------------

    def _analyze_nodes(self, workflow: Dict) -> Dict:
        """Conta tipos de nós, identifica operações custosas e calcula complexidade."""
        nodes: List[Dict] = workflow.get("nodes", [])
        node_type_counts: Dict[str, int] = defaultdict(int)
        expensive_nodes = []

        for node in nodes:
            raw_type = node.get("type", "")
            short_type = raw_type.split(".")[-1]
            node_type_counts[short_type] += 1

            for exp_type, reason in EXPENSIVE_NODE_TYPES.items():
                if exp_type in raw_type:
                    expensive_nodes.append({
                        "name": node.get("name", "?"),
                        "type": raw_type,
                        "reason": reason,
                    })

        return {
            "total_nodes": len(nodes),
            "node_types": dict(node_type_counts),
            "complexity_score": self._calculate_complexity(workflow),
            "expensive_nodes": expensive_nodes,
        }

    def _calculate_complexity(self, workflow: Dict) -> int:
        """Score de complexidade 0-100 baseado em nós, conexões e lógica condicional."""
        nodes: List[Dict] = workflow.get("nodes", [])
        connections: Dict = workflow.get("connections", {})

        # Complexidade por quantidade de nós (max 50 pts)
        score = min(len(nodes) * 5, 50)

        # Complexidade por conexões (max 30 pts)
        total_connections = sum(
            len(conn)
            for targets in connections.values()
            for output_conns in targets.values()
            for conn in output_conns
        )
        score += min(total_connections * 3, 30)

        # Complexidade por lógica condicional
        for node in nodes:
            node_type = node.get("type", "")
            if "n8n-nodes-base.if" in node_type:
                score += 5
            elif "n8n-nodes-base.switch" in node_type:
                score += 10
            elif "n8n-nodes-base.code" in node_type:
                score += 3  # código customizado adiciona complexidade

        return min(score, 100)

    # -------------------------------------------------------------------------
    # Análise de conexões
    # -------------------------------------------------------------------------

    def _analyze_connections(self, workflow: Dict) -> Dict:
        """Conta conexões totais, caminhos paralelos e sequenciais."""
        connections: Dict = workflow.get("connections", {})
        total = 0
        parallel_paths = 0

        for targets in connections.values():
            for output_conns in targets.values():
                for conn_list in output_conns:
                    total += len(conn_list)
                    if len(conn_list) > 1:
                        parallel_paths += 1

        return {
            "total_connections": total,
            "parallel_paths": parallel_paths,
        }

    # -------------------------------------------------------------------------
    # Gargalos
    # -------------------------------------------------------------------------

    def _identify_bottlenecks(self, workflow: Dict, statistics: Dict) -> List[Dict]:
        """Identifica gargalos: operações custosas sequenciais, alta falha, sem tratamento de erro."""
        bottlenecks = []
        nodes: List[Dict] = workflow.get("nodes", [])

        # Múltiplas operações custosas sequenciais
        exp_nodes = [
            n for n in nodes
            if any(et in n.get("type", "") for et in EXPENSIVE_NODE_TYPES)
        ]
        if len(exp_nodes) > 3:
            bottlenecks.append({
                "type": "operacoes_custosas_sequenciais",
                "severity": "alto",
                "description": (
                    f"{len(exp_nodes)} operações custosas identificadas — "
                    "verifique se podem ser paralelizadas ou se algumas podem ser eliminadas"
                ),
                "affected_nodes": [n["name"] for n in exp_nodes],
                "impact": "Tempo de execução elevado",
            })

        # Alta taxa de falha
        failed = statistics.get("failed", 0)
        successful = statistics.get("successful", 0)
        if failed > successful and (failed + successful) > 0:
            bottlenecks.append({
                "type": "alta_taxa_de_falha",
                "severity": "crítico",
                "description": "Mais execuções com falha do que com sucesso",
                "impact": "Workflow não confiável para produção",
                "top_errors": statistics.get("error_patterns", {}),
            })

        # Sem tratamento de erro
        error_node_types = [
            "n8n-nodes-base.errorTrigger",
            "n8n-nodes-base.if",
            "n8n-nodes-base.switch",
        ]
        has_error_handling = any(
            node.get("type") in error_node_types for node in nodes
        )
        if not has_error_handling and len(nodes) > 3:
            bottlenecks.append({
                "type": "sem_tratamento_de_erro",
                "severity": "médio",
                "description": "Workflow sem nós de tratamento de erro (IF, Switch, Error Trigger)",
                "impact": "Falhas podem não ser tratadas graciosamente",
            })

        # Workflow muito complexo
        complexity = self._calculate_complexity(workflow)
        if complexity > 80:
            bottlenecks.append({
                "type": "alta_complexidade",
                "severity": "médio",
                "description": (
                    f"Score de complexidade: {complexity}/100 — "
                    "workflow muito complexo para manutenção e debugging"
                ),
                "impact": "Dificulta manutenção, debugging e onboarding de novos membros",
            })

        return bottlenecks

    # -------------------------------------------------------------------------
    # Oportunidades de otimização
    # -------------------------------------------------------------------------

    def _find_optimizations(self, workflow: Dict, statistics: Dict) -> List[Dict]:
        """Identifica oportunidades: cache, batch, paralelismo, error handling, timeout."""
        optimizations = []
        nodes: List[Dict] = workflow.get("nodes", [])
        connections: Dict = workflow.get("connections", {})
        settings: Dict = workflow.get("settings", {})

        # Cache para HTTP repetitivos
        http_nodes = [n for n in nodes if "httpRequest" in n.get("type", "")]
        if http_nodes:
            optimizations.append({
                "type": "cache_http",
                "priority": "média",
                "description": (
                    f"{len(http_nodes)} nó(s) HTTP encontrado(s) — "
                    "se a mesma URL é consultada repetidamente, implemente cache com nó Code"
                ),
                "affected_nodes": [n["name"] for n in http_nodes],
                "benefit": "Reduz chamadas externas e acelera execução",
                "implementation": "Use nó Code para armazenar resultado e verificar antes de chamar a API",
            })

        # Split In Batches para datasets grandes
        has_split = any("splitInBatches" in n.get("type", "") for n in nodes)
        has_loop_target = any(
            "splitInBatches" in n.get("type", "") or "loop" in n.get("name", "").lower()
            for n in nodes
        )
        if not has_loop_target:
            optimizations.append({
                "type": "processamento_em_lotes",
                "priority": "baixa",
                "description": "Sem nó 'Split In Batches' — considere se o workflow processa listas grandes",
                "benefit": "Melhor gerenciamento de memória e processamento paralelo",
                "implementation": "Adicione nó 'Split In Batches' antes de operações em loop",
            })

        # Tratamento de erro
        error_nodes = [n for n in nodes if "error" in n.get("type", "").lower()]
        if not error_nodes and len(nodes) > 3:
            optimizations.append({
                "type": "adicionar_tratamento_de_erro",
                "priority": "alta",
                "description": "Sem nós de tratamento de erro — adicione ramos de erro para operações críticas",
                "benefit": "Recuperação graciosa e melhor debugging",
                "implementation": (
                    "Adicione nó IF após operações HTTP/DB para verificar sucesso, "
                    "ou use 'Error Trigger' como workflow de erro global"
                ),
            })

        # Timeout
        if not settings.get("executionTimeout"):
            optimizations.append({
                "type": "configurar_timeout",
                "priority": "baixa",
                "description": "Sem 'executionTimeout' nas settings do workflow",
                "benefit": "Previne workflows presos consumindo recursos indefinidamente",
                "implementation": "Configure settings.executionTimeout (em segundos, ex: 300 = 5min)",
            })

        # Paralelismo
        for source_node, targets in connections.items():
            for output_conns in targets.values():
                for conn_list in output_conns:
                    if len(conn_list) > 1:
                        optimizations.append({
                            "type": "execucao_paralela",
                            "priority": "alta",
                            "description": (
                                f"Nó '{source_node}' já ramifica em {len(conn_list)} caminhos — "
                                "confirme que os ramos são independentes para execução paralela real"
                            ),
                            "benefit": "Reduz tempo total de execução",
                        })

        # Redução de complexidade
        complexity = self._calculate_complexity(workflow)
        if complexity > 70:
            optimizations.append({
                "type": "reducao_de_complexidade",
                "priority": "média",
                "description": (
                    f"Score de complexidade {complexity}/100 — "
                    "considere dividir em sub-workflows menores"
                ),
                "benefit": "Manutenção mais fácil, debugging mais rápido, reuso de lógica",
                "implementation": "Separe responsabilidades: 1 workflow por domínio funcional",
            })

        # Notificação de falha
        has_notification = any(
            any(nt in n.get("type", "") for nt in ["slack", "emailSend", "telegram"])
            for n in nodes
        )
        if not has_notification and len(nodes) > 3:
            optimizations.append({
                "type": "adicionar_notificacao_de_falha",
                "priority": "alta",
                "description": "Sem nó de notificação de falha identificado",
                "benefit": "Equipe é alertada imediatamente sobre problemas",
                "implementation": "Adicione nó Slack ou Email no ramo de erro do workflow",
            })

        return optimizations

    # -------------------------------------------------------------------------
    # Score de performance
    # -------------------------------------------------------------------------

    def _calculate_performance_score(self, analysis: Dict) -> int:
        """
        Score 0-100 considerando:
        - Taxa de sucesso (peso 50%)
        - Complexidade (peso 30%)
        - Gargalos (penalidades)
        - Otimizações de alta prioridade não implementadas
        """
        score = 100.0

        # Taxa de sucesso
        metrics = analysis.get("execution_metrics", {})
        success_rate = metrics.get("success_rate", 100.0)
        score -= (100 - success_rate) * 0.5

        # Complexidade
        complexity = analysis.get("node_analysis", {}).get("complexity_score", 0)
        if complexity > 70:
            score -= (complexity - 70) * 0.3

        # Penalidades por gargalos
        severity_penalties = {"crítico": 20, "alto": 10, "médio": 5, "baixo": 2}
        for bottleneck in analysis.get("bottlenecks", []):
            severity = bottleneck.get("severity", "baixo")
            score -= severity_penalties.get(severity, 2)

        # Penalidade por otimizações de alta prioridade ausentes
        high_prio = [
            opt for opt in analysis.get("optimization_opportunities", [])
            if opt.get("priority") == "alta"
        ]
        score -= len(high_prio) * 5

        return max(0, min(100, int(score)))

    # -------------------------------------------------------------------------
    # Sugestões
    # -------------------------------------------------------------------------

    def suggest_optimizations(self, workflow_id: str) -> Dict:
        """
        Retorna sugestões priorizadas: ações prioritárias, ganhos rápidos e melhorias de longo prazo.
        """
        analysis = self.analyze_performance(workflow_id)
        suggestions: Dict[str, Any] = {
            "workflow_id": workflow_id,
            "workflow_name": analysis.get("workflow_name"),
            "performance_score": analysis["performance_score"],
            "health": analysis["execution_metrics"]["health"],
            "priority_actions": [],
            "quick_wins": [],
            "long_term_improvements": [],
        }

        priority_map = {
            "alta": "priority_actions",
            "média": "quick_wins",
            "baixa": "long_term_improvements",
        }

        for opt in analysis["optimization_opportunities"]:
            bucket = priority_map.get(opt.get("priority", "baixa"), "long_term_improvements")
            suggestions[bucket].append(opt)

        # Adicionar correção de gargalos críticos como ações prioritárias
        critical_severities = {"crítico", "alto"}
        for bottleneck in analysis["bottlenecks"]:
            if bottleneck.get("severity") in critical_severities:
                suggestions["priority_actions"].append({
                    "type": "corrigir_gargalo",
                    "priority": "crítica",
                    "description": f"Corrigir: {bottleneck['description']}",
                    "benefit": f"Resolve: {bottleneck['impact']}",
                })

        return suggestions

    # -------------------------------------------------------------------------
    # Relatório legível
    # -------------------------------------------------------------------------

    def generate_optimization_report(self, analysis: Dict) -> str:
        """Gera relatório completo e legível de otimização."""
        lines = []
        sep = "=" * 70
        sep2 = "-" * 70

        lines.append(sep)
        lines.append("EFSM n8n — Relatório de Otimização de Workflow")
        lines.append(sep)
        lines.append(f"\nWorkflow: {analysis.get('workflow_name', '?')}")
        lines.append(f"ID: {analysis.get('workflow_id', '?')}")
        lines.append(f"Período analisado: {analysis.get('analysis_period_days', 7)} dias")
        lines.append(f"Score de Performance: {analysis['performance_score']}/100")

        # Métricas de execução
        metrics = analysis["execution_metrics"]
        lines.append(f"\n{sep2}")
        lines.append("MÉTRICAS DE EXECUÇÃO")
        lines.append(sep2)
        lines.append(f"Saúde: {metrics['health'].upper()}")
        lines.append(f"Total de execuções: {metrics['total_executions']}")
        lines.append(f"Taxa de sucesso: {metrics['success_rate']:.1f}%")
        lines.append(f"Taxa de falha: {metrics['failure_rate']:.1f}%")
        lines.append(f"Execuções com sucesso: {metrics['successful_executions']}")
        lines.append(f"Execuções com falha: {metrics['failed_executions']}")

        top_errors = metrics.get("top_errors", {})
        if top_errors:
            lines.append(f"\nPrincipais erros:")
            for err_msg, count in top_errors.items():
                lines.append(f"  ({count}x) {err_msg[:100]}")

        # Estrutura do workflow
        node_analysis = analysis["node_analysis"]
        lines.append(f"\n{sep2}")
        lines.append("ESTRUTURA DO WORKFLOW")
        lines.append(sep2)
        lines.append(f"Total de nós: {node_analysis['total_nodes']}")
        lines.append(f"Score de complexidade: {node_analysis['complexity_score']}/100")

        conn_analysis = analysis["connection_analysis"]
        lines.append(f"Total de conexões: {conn_analysis['total_connections']}")
        lines.append(f"Caminhos paralelos: {conn_analysis['parallel_paths']}")

        types = node_analysis.get("node_types", {})
        if types:
            lines.append(f"\nDistribuição de nós:")
            for node_type, count in sorted(types.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"  {node_type}: {count}")

        exp_nodes = node_analysis.get("expensive_nodes", [])
        if exp_nodes:
            lines.append(f"\nOperações potencialmente custosas ({len(exp_nodes)}):")
            for n in exp_nodes[:8]:
                lines.append(f"  • [{n['type'].split('.')[-1]}] {n['name']}: {n['reason'][:60]}")

        # Gargalos
        bottlenecks = analysis.get("bottlenecks", [])
        if bottlenecks:
            lines.append(f"\n{sep2}")
            lines.append(f"GARGALOS IDENTIFICADOS ({len(bottlenecks)})")
            lines.append(sep2)
            for b in bottlenecks:
                lines.append(f"\n[{b['severity'].upper()}] {b['type']}")
                lines.append(f"  {b['description']}")
                lines.append(f"  Impacto: {b['impact']}")
                if b.get("affected_nodes"):
                    lines.append(f"  Nós afetados: {', '.join(b['affected_nodes'][:5])}")
        else:
            lines.append(f"\nNenhum gargalo crítico identificado.")

        # Oportunidades de otimização
        optimizations = analysis.get("optimization_opportunities", [])
        if optimizations:
            lines.append(f"\n{sep2}")
            lines.append(f"OPORTUNIDADES DE OTIMIZAÇÃO ({len(optimizations)})")
            lines.append(sep2)

            for priority_label, priority_key in [
                ("ALTA PRIORIDADE", "alta"),
                ("MÉDIA PRIORIDADE", "média"),
                ("BAIXA PRIORIDADE", "baixa"),
            ]:
                group = [o for o in optimizations if o.get("priority") == priority_key]
                if group:
                    lines.append(f"\n### {priority_label} ({len(group)})")
                    for opt in group:
                        lines.append(f"\n• {opt['type'].replace('_', ' ').title()}")
                        lines.append(f"  {opt['description']}")
                        lines.append(f"  Benefício: {opt.get('benefit', 'N/A')}")
                        if opt.get("implementation"):
                            lines.append(f"  Como implementar: {opt['implementation']}")

        # Resumo executivo
        score = analysis["performance_score"]
        lines.append(f"\n{sep2}")
        lines.append("RESUMO EXECUTIVO")
        lines.append(sep2)
        if score >= 90:
            lines.append("Workflow bem otimizado. Manutenção de rotina recomendada.")
        elif score >= 70:
            lines.append("Workflow em bom estado. Implemente as sugestões de alta prioridade.")
        elif score >= 50:
            lines.append("Otimização recomendada. Foque nas ações de alta prioridade imediatamente.")
        else:
            lines.append("ATENÇÃO: Workflow com problemas significativos. Revisão urgente necessária.")

        lines.append(f"\nInspecione os workflows em: https://n8n.eufacoseu.marketing/")
        lines.append("\n" + sep)
        return "\n".join(lines)


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="EFSM n8n Optimizer — Análise de performance e otimização",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "action",
        choices=["analyze", "suggest", "report"],
        help="Ação a executar",
    )
    parser.add_argument("--id", required=True, help="ID do workflow")
    parser.add_argument("--days", type=int, default=7, help="Período de análise em dias")
    parser.add_argument("--pretty", action="store_true", help="Saída JSON formatada")

    args = parser.parse_args()

    try:
        optimizer = WorkflowOptimizer()

        if args.action == "analyze":
            result = optimizer.analyze_performance(args.id, days=args.days)
            print(json.dumps(result, indent=2 if args.pretty else None, ensure_ascii=False))

        elif args.action == "suggest":
            result = optimizer.suggest_optimizations(args.id)
            print(json.dumps(result, indent=2 if args.pretty else None, ensure_ascii=False))

        elif args.action == "report":
            analysis = optimizer.analyze_performance(args.id, days=args.days)
            print(optimizer.generate_optimization_report(analysis))

    except KeyboardInterrupt:
        print("\nOperação cancelada pelo usuário.", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
