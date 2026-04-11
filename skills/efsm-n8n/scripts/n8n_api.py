#!/usr/bin/env python3
"""
EFSM n8n API Client
Cliente para gerenciar workflows, execuções e análises via API REST do n8n da EFSM.
Instância: https://n8n.eufacoseu.marketing/

Uso:
  python3 scripts/n8n_api.py list-workflows --pretty
  python3 scripts/n8n_api.py get-workflow --id <id> --pretty
  python3 scripts/n8n_api.py create --from-file workflow.json
  python3 scripts/n8n_api.py activate --id <id>
  python3 scripts/n8n_api.py execute --id <id> --data '{"chave": "valor"}'
  python3 scripts/n8n_api.py stats --id <id> --days 7 --pretty

Variáveis de ambiente obrigatórias:
  N8N_API_KEY   — Token de API do n8n
  N8N_BASE_URL  — URL base (padrão: https://n8n.eufacoseu.marketing)
"""

import os
import sys
import json
import argparse
import requests
from pathlib import Path
from typing import Optional, Dict, Any, List


EFSM_N8N_DEFAULT_URL = "https://n8n.eufacoseu.marketing"
EFSM_N8N_DEFAULT_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    ".eyJzdWIiOiJlMDg1YTczZS00OGE2LTQ3ZDYtODc4MC1hZGM3ZmE1N2I1MmMiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwianRpIjoiNDU1N2E4MWUtOGZjNi00ZmViLWE1M2YtMTg3ZGZiZDY3OGNlIiwiaWF0IjoxNzc1NDMxNjk4LCJleHAiOjE3Nzc5NTAwMDB9"
    ".LAGCn8V5aUmwRryuC_7ZvM1I3X38An48NYskzTdCZMk"
)


class N8nClient:
    """Cliente da API REST do n8n da EFSM"""

    def __init__(self, base_url: str = None, api_key: str = None):
        self.base_url = (base_url or os.getenv("N8N_BASE_URL") or EFSM_N8N_DEFAULT_URL).rstrip("/")
        self.api_key = api_key or os.getenv("N8N_API_KEY") or EFSM_N8N_DEFAULT_KEY

        self.session = requests.Session()
        self.session.headers.update({
            "X-N8N-API-KEY": self.api_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
        })

    def _request(self, method: str, endpoint: str, **kwargs) -> Any:
        """Realiza requisição HTTP à API do n8n"""
        url = f"{self.base_url}/api/v1/{endpoint.lstrip('/')}"
        response = self.session.request(method, url, **kwargs)
        try:
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.HTTPError as e:
            raise Exception(f"HTTP {response.status_code}: {response.text}") from e

    # -------------------------------------------------------------------------
    # Workflows
    # -------------------------------------------------------------------------

    def list_workflows(self, active: bool = None) -> Dict:
        """Lista todos os workflows. Filtra por active=True/False se informado."""
        params = {}
        if active is not None:
            params["active"] = str(active).lower()
        return self._request("GET", "workflows", params=params)

    def get_workflow(self, workflow_id: str) -> Dict:
        """Retorna detalhes completos de um workflow pelo ID."""
        return self._request("GET", f"workflows/{workflow_id}")

    def create_workflow(self, workflow_data: Dict) -> Dict:
        """Cria um novo workflow. Remove campos read-only antes de enviar."""
        clean = {k: v for k, v in workflow_data.items() if k not in ("id", "active")}
        return self._request("POST", "workflows", json=clean)

    def update_workflow(self, workflow_id: str, workflow_data: Dict) -> Dict:
        """Atualiza um workflow existente (PATCH)."""
        return self._request("PATCH", f"workflows/{workflow_id}", json=workflow_data)

    def delete_workflow(self, workflow_id: str) -> Dict:
        """Remove um workflow permanentemente."""
        return self._request("DELETE", f"workflows/{workflow_id}")

    def activate_workflow(self, workflow_id: str) -> Dict:
        """Ativa um workflow (começa a receber triggers)."""
        return self._request("PATCH", f"workflows/{workflow_id}", json={"active": True})

    def deactivate_workflow(self, workflow_id: str) -> Dict:
        """Desativa um workflow sem excluí-lo."""
        return self._request("PATCH", f"workflows/{workflow_id}", json={"active": False})

    # -------------------------------------------------------------------------
    # Execuções
    # -------------------------------------------------------------------------

    def list_executions(self, workflow_id: str = None, limit: int = 20, status: str = None) -> Dict:
        """Lista execuções. Filtra por workflow_id e/ou status (success/error/waiting)."""
        params = {"limit": limit}
        if workflow_id:
            params["workflowId"] = workflow_id
        if status:
            params["status"] = status
        return self._request("GET", "executions", params=params)

    def get_execution(self, execution_id: str) -> Dict:
        """Retorna detalhes de uma execução específica, incluindo dados de nós."""
        return self._request("GET", f"executions/{execution_id}")

    def delete_execution(self, execution_id: str) -> Dict:
        """Remove uma execução do histórico."""
        return self._request("DELETE", f"executions/{execution_id}")

    def execute_workflow(self, workflow_id: str, data: Dict = None) -> Dict:
        """Dispara manualmente um workflow. Opcionalmente envia dados de entrada."""
        payload: Dict = {}
        if data:
            payload["data"] = data
        return self._request("POST", f"workflows/{workflow_id}/execute", json=payload)

    # -------------------------------------------------------------------------
    # Validação local
    # -------------------------------------------------------------------------

    def validate_workflow(self, workflow_data: Dict) -> Dict:
        """
        Valida a estrutura e configuração de um workflow localmente (sem API).
        Retorna dict com chaves: valid (bool), errors (list), warnings (list).
        """
        issues: Dict[str, Any] = {"errors": [], "warnings": [], "valid": True}

        if "nodes" not in workflow_data:
            issues["errors"].append("Campo 'nodes' ausente no workflow")
            issues["valid"] = False
            return issues

        nodes: List[Dict] = workflow_data.get("nodes", [])
        connections: Dict = workflow_data.get("connections", {})
        node_names: set = set()

        # Validação dos nós
        for node in nodes:
            if "name" not in node:
                issues["errors"].append("Nó sem campo 'name'")
                issues["valid"] = False
            else:
                node_names.add(node["name"])

            if "type" not in node:
                issues["errors"].append(
                    f"Nó '{node.get('name', '?')}' sem campo 'type'"
                )
                issues["valid"] = False

            # Nós que precisam de credenciais configuradas
            cred_types = [
                "httpRequest", "googleSheets", "slack", "emailSend",
                "postgres", "mysql", "mongodb", "airtable", "hubspot",
            ]
            node_type = node.get("type", "")
            if any(ct in node_type for ct in cred_types):
                if not node.get("credentials"):
                    issues["warnings"].append(
                        f"Nó '{node.get('name', '?')}' ({node_type}) provavelmente requer credenciais"
                    )

        # Validação das conexões
        for source_node, targets in connections.items():
            if source_node not in node_names:
                issues["errors"].append(
                    f"Conexão referencia nó de origem inexistente: '{source_node}'"
                )
                issues["valid"] = False
            for _output_type, output_connections in targets.items():
                for conn_list in output_connections:
                    for conn in conn_list:
                        target = conn.get("node")
                        if target and target not in node_names:
                            issues["errors"].append(
                                f"Conexão referencia nó de destino inexistente: '{target}'"
                            )
                            issues["valid"] = False

        # Detectar nós desconectados
        connected: set = set(connections.keys())
        for targets in connections.values():
            for output_connections in targets.values():
                for conn_list in output_connections:
                    for conn in conn_list:
                        connected.add(conn.get("node"))

        disconnected = node_names - connected
        if disconnected and len(nodes) > 1:
            for name in disconnected:
                issues["warnings"].append(f"Nó '{name}' parece desconectado")

        return issues

    # -------------------------------------------------------------------------
    # Estatísticas
    # -------------------------------------------------------------------------

    def get_workflow_statistics(self, workflow_id: str, days: int = 7) -> Dict:
        """
        Retorna estatísticas de execução de um workflow.
        Busca até 200 execuções e calcula taxa de sucesso, falha e padrões de erro.
        """
        raw = self.list_executions(workflow_id=workflow_id, limit=200)
        executions: List[Dict] = raw.get("data", raw) if isinstance(raw, dict) else raw

        stats: Dict[str, Any] = {
            "workflow_id": workflow_id,
            "period_days": days,
            "total_executions": len(executions),
            "successful": 0,
            "failed": 0,
            "success_rate": 0.0,
            "error_patterns": {},
            "execution_times": [],
        }

        for execution in executions:
            status = execution.get("status", "")
            if status == "success" or execution.get("finished"):
                stats["successful"] += 1
            else:
                stats["failed"] += 1
                error_msg = (
                    execution.get("data", {})
                    .get("resultData", {})
                    .get("error", {})
                    .get("message", "Erro desconhecido")
                )
                stats["error_patterns"][error_msg] = (
                    stats["error_patterns"].get(error_msg, 0) + 1
                )

            started = execution.get("startedAt")
            stopped = execution.get("stoppedAt")
            if started and stopped:
                stats["execution_times"].append({"start": started, "stop": stopped})

        if stats["total_executions"] > 0:
            stats["success_rate"] = round(
                (stats["successful"] / stats["total_executions"]) * 100, 2
            )

        return stats

    def analyze_workflow_performance(self, workflow_id: str) -> Dict:
        """
        Análise rápida de performance: contagem de nós, conexões,
        oportunidades de paralelismo e sugestões de otimização.
        """
        workflow = self.get_workflow(workflow_id)
        nodes: List[Dict] = workflow.get("nodes", [])
        connections: Dict = workflow.get("connections", {})

        analysis: Dict[str, Any] = {
            "workflow_id": workflow_id,
            "workflow_name": workflow.get("name"),
            "node_count": len(nodes),
            "connection_count": sum(
                len(conn)
                for targets in connections.values()
                for output_conns in targets.values()
                for conn in output_conns
            ),
            "parallel_opportunities": [],
            "optimization_suggestions": [],
        }

        # Detectar nós com saídas múltiplas (candidatos a paralelismo)
        for node_name, targets in connections.items():
            for output_conns in targets.values():
                for conn_list in output_conns:
                    if len(conn_list) > 1:
                        analysis["parallel_opportunities"].append({
                            "node": node_name,
                            "branches": len(conn_list),
                            "suggestion": "Já usa múltiplos ramos — verifique se podem ser paralelos",
                        })

        # Sugestões para nós HTTP
        http_nodes = [n for n in nodes if "httpRequest" in n.get("type", "")]
        if http_nodes:
            analysis["optimization_suggestions"].append({
                "type": "cache",
                "affected_nodes": [n["name"] for n in http_nodes],
                "suggestion": "Considere cachear respostas de APIs frequentemente consultadas",
            })

        # Sugestão de monitoramento
        analysis["optimization_suggestions"].append({
            "type": "monitoring",
            "suggestion": "Habilite retenção de dados de execução para facilitar debugging",
        })

        return analysis


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="EFSM n8n API Client — Gerenciamento de workflows via CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "action",
        choices=[
            "list-workflows", "get-workflow", "create", "update",
            "activate", "deactivate", "delete",
            "list-executions", "get-execution", "execute",
            "validate", "stats", "analyze",
        ],
        help="Ação a executar",
    )
    parser.add_argument("--id", help="ID do workflow ou execução")
    parser.add_argument(
        "--active",
        type=lambda x: x.lower() == "true",
        help="Filtrar por status ativo (true/false)",
    )
    parser.add_argument("--limit", type=int, default=20, help="Limite de resultados")
    parser.add_argument("--status", help="Filtrar execuções por status (success/error/waiting)")
    parser.add_argument("--data", help="Dados JSON para execução (string JSON)")
    parser.add_argument("--from-file", help="Criar workflow a partir de arquivo JSON")
    parser.add_argument("--days", type=int, default=7, help="Período em dias para estatísticas")
    parser.add_argument("--pretty", action="store_true", help="Saída JSON formatada")

    args = parser.parse_args()

    try:
        client = N8nClient()
        result = None

        if args.action == "list-workflows":
            result = client.list_workflows(active=args.active)

        elif args.action == "get-workflow":
            if not args.id:
                raise ValueError("--id obrigatório para get-workflow")
            result = client.get_workflow(args.id)

        elif args.action == "create":
            if not args.from_file:
                raise ValueError("--from-file obrigatório para create")
            with open(args.from_file, "r", encoding="utf-8") as f:
                workflow_data = json.load(f)
            result = client.create_workflow(workflow_data)

        elif args.action == "update":
            if not args.id or not args.from_file:
                raise ValueError("--id e --from-file obrigatórios para update")
            with open(args.from_file, "r", encoding="utf-8") as f:
                workflow_data = json.load(f)
            result = client.update_workflow(args.id, workflow_data)

        elif args.action == "activate":
            if not args.id:
                raise ValueError("--id obrigatório para activate")
            result = client.activate_workflow(args.id)

        elif args.action == "deactivate":
            if not args.id:
                raise ValueError("--id obrigatório para deactivate")
            result = client.deactivate_workflow(args.id)

        elif args.action == "delete":
            if not args.id:
                raise ValueError("--id obrigatório para delete")
            confirm = input(f"Confirmar exclusão do workflow '{args.id}'? (sim/não): ")
            if confirm.strip().lower() not in ("sim", "s", "yes", "y"):
                print("Operação cancelada.")
                sys.exit(0)
            result = client.delete_workflow(args.id)

        elif args.action == "list-executions":
            result = client.list_executions(
                workflow_id=args.id, limit=args.limit, status=args.status
            )

        elif args.action == "get-execution":
            if not args.id:
                raise ValueError("--id obrigatório para get-execution")
            result = client.get_execution(args.id)

        elif args.action == "execute":
            if not args.id:
                raise ValueError("--id obrigatório para execute")
            data = json.loads(args.data) if args.data else None
            result = client.execute_workflow(args.id, data=data)

        elif args.action == "validate":
            if args.from_file:
                with open(args.from_file, "r", encoding="utf-8") as f:
                    workflow_data = json.load(f)
            elif args.id:
                workflow_data = client.get_workflow(args.id)
            else:
                raise ValueError("--id ou --from-file obrigatório para validate")
            result = client.validate_workflow(workflow_data)

        elif args.action == "stats":
            if not args.id:
                raise ValueError("--id obrigatório para stats")
            result = client.get_workflow_statistics(args.id, days=args.days)

        elif args.action == "analyze":
            if not args.id:
                raise ValueError("--id obrigatório para analyze")
            result = client.analyze_workflow_performance(args.id)

        # Output
        if result is not None:
            indent = 2 if args.pretty else None
            print(json.dumps(result, indent=indent, ensure_ascii=False))

    except KeyboardInterrupt:
        print("\nOperação cancelada pelo usuário.", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
