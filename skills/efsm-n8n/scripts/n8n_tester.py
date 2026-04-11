#!/usr/bin/env python3
"""
EFSM n8n Workflow Tester & Validator
Valida e testa workflows antes de ativação em produção.

Uso:
  python3 scripts/n8n_tester.py validate --id <id> --pretty
  python3 scripts/n8n_tester.py validate --file workflow.json --pretty
  python3 scripts/n8n_tester.py dry-run --id <id> --data '{"email": "teste@efsm.com.br"}'
  python3 scripts/n8n_tester.py dry-run --id <id> --data-file test-data.json --report
  python3 scripts/n8n_tester.py test-suite --id <id> --test-suite test-cases.json
  python3 scripts/n8n_tester.py report --id <id>
"""

import sys
import json
import argparse
import time
from typing import Dict, List, Any

try:
    from n8n_api import N8nClient
except ImportError:
    from scripts.n8n_api import N8nClient


# Tipos de nós que tipicamente requerem credenciais na EFSM
CREDENTIAL_NODE_TYPES = [
    "n8n-nodes-base.httpRequest",
    "n8n-nodes-base.googleSheets",
    "n8n-nodes-base.slack",
    "n8n-nodes-base.emailSend",
    "n8n-nodes-base.postgres",
    "n8n-nodes-base.mysql",
    "n8n-nodes-base.mongodb",
    "n8n-nodes-base.airtable",
    "n8n-nodes-base.hubspot",
    "n8n-nodes-base.mailchimp",
    "n8n-nodes-base.facebookGraphApi",
]

# Tipos de nós trigger reconhecidos
TRIGGER_NODE_TYPES = [
    "n8n-nodes-base.webhook",
    "n8n-nodes-base.scheduleTrigger",
    "n8n-nodes-base.manualTrigger",
    "n8n-nodes-base.start",
    "n8n-nodes-base.errorTrigger",
    "n8n-nodes-base.cron",
]


class WorkflowTester:
    """Validação e teste de workflows do n8n da EFSM"""

    def __init__(self, client: N8nClient = None):
        self._client = client

    @property
    def client(self) -> N8nClient:
        if self._client is None:
            self._client = N8nClient()
        return self._client

    # -------------------------------------------------------------------------
    # Validação
    # -------------------------------------------------------------------------

    def validate_workflow(
        self,
        workflow_id: str = None,
        workflow_file: str = None,
    ) -> Dict:
        """
        Valida estrutura, configuração e fluxo de execução de um workflow.
        Aceita ID (busca via API) ou caminho de arquivo JSON local.
        """
        if workflow_id:
            workflow_data = self.client.get_workflow(workflow_id)
        elif workflow_file:
            with open(workflow_file, "r", encoding="utf-8") as f:
                workflow_data = json.load(f)
        else:
            raise ValueError("workflow_id ou workflow_file obrigatório")

        validation: Dict[str, Any] = {"errors": [], "warnings": [], "valid": True}

        self._validate_structure(workflow_data, validation)
        self._check_credentials(workflow_data, validation)
        self._check_node_configurations(workflow_data, validation)
        self._check_execution_flow(workflow_data, validation)
        self._check_efsm_best_practices(workflow_data, validation)

        return validation

    def _validate_structure(self, workflow_data: Dict, result: Dict):
        """Valida a estrutura básica do JSON de workflow."""
        if "nodes" not in workflow_data:
            result["errors"].append("Campo obrigatório 'nodes' ausente")
            result["valid"] = False
            return

        nodes: List[Dict] = workflow_data.get("nodes", [])
        connections: Dict = workflow_data.get("connections", {})
        node_names: set = set()

        for node in nodes:
            if "name" not in node:
                result["errors"].append("Nó sem campo 'name'")
                result["valid"] = False
            else:
                node_names.add(node["name"])

            if "type" not in node:
                result["errors"].append(
                    f"Nó '{node.get('name', '?')}' sem campo 'type'"
                )
                result["valid"] = False

            if "position" not in node:
                result["warnings"].append(
                    f"Nó '{node.get('name', '?')}' sem campo 'position' — pode causar problemas visuais no n8n"
                )

        # Validar referências nas conexões
        for source_name, targets in connections.items():
            if source_name not in node_names:
                result["errors"].append(
                    f"Conexão referencia nó de origem inexistente: '{source_name}'"
                )
                result["valid"] = False

            for _output_type, output_connections in targets.items():
                for conn_list in output_connections:
                    for conn in conn_list:
                        target = conn.get("node")
                        if target and target not in node_names:
                            result["errors"].append(
                                f"Conexão referencia nó de destino inexistente: '{target}'"
                            )
                            result["valid"] = False

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
                result["warnings"].append(
                    f"Nó '{name}' parece desconectado do fluxo"
                )

    def _check_credentials(self, workflow_data: Dict, result: Dict):
        """Verifica se nós que precisam de credenciais estão configurados."""
        nodes: List[Dict] = workflow_data.get("nodes", [])

        for node in nodes:
            node_type = node.get("type", "")
            if node_type in CREDENTIAL_NODE_TYPES:
                if not node.get("credentials"):
                    result["warnings"].append(
                        f"Nó '{node['name']}' ({node_type}) provavelmente requer credenciais — configure no n8n UI antes de ativar"
                    )

    def _check_node_configurations(self, workflow_data: Dict, result: Dict):
        """Valida parâmetros obrigatórios de tipos específicos de nós."""
        nodes: List[Dict] = workflow_data.get("nodes", [])

        for node in nodes:
            node_type = node.get("type", "")
            params = node.get("parameters", {})
            name = node.get("name", "?")

            # HTTP Request
            if node_type == "n8n-nodes-base.httpRequest":
                url = params.get("url") or params.get("options", {}).get("url")
                if not url:
                    result["errors"].append(
                        f"Nó '{name}' (httpRequest) sem parâmetro URL obrigatório"
                    )
                    result["valid"] = False

            # Webhook
            elif node_type == "n8n-nodes-base.webhook":
                if not params.get("path"):
                    result["errors"].append(
                        f"Nó '{name}' (webhook) sem parâmetro 'path' obrigatório"
                    )
                    result["valid"] = False

            # Email Send
            elif node_type == "n8n-nodes-base.emailSend":
                if not params.get("subject") and not params.get("text") and not params.get("html"):
                    result["warnings"].append(
                        f"Nó '{name}' (emailSend) sem assunto ou corpo definido"
                    )

            # Code node — verificar se não é placeholder
            elif node_type == "n8n-nodes-base.code":
                code = params.get("jsCode", "") or params.get("pythonCode", "")
                placeholder_hints = [
                    "adicione aqui", "configure aqui", "TODO", "FIXME",
                    "add here", "setup here",
                ]
                if any(hint.lower() in code.lower() for hint in placeholder_hints):
                    result["warnings"].append(
                        f"Nó '{name}' (code) parece conter código placeholder — revise antes de ativar"
                    )

            # Schedule Trigger — verificar timezone
            elif node_type in ("n8n-nodes-base.scheduleTrigger", "n8n-nodes-base.cron"):
                rule = params.get("rule", {})
                timezone = rule.get("timezone") or params.get("timezone")
                if not timezone:
                    result["warnings"].append(
                        f"Nó '{name}' (scheduleTrigger) sem timezone definida — recomendado: America/Sao_Paulo"
                    )

    def _check_execution_flow(self, workflow_data: Dict, result: Dict):
        """Verifica a integridade do fluxo de execução."""
        nodes: List[Dict] = workflow_data.get("nodes", [])
        connections: Dict = workflow_data.get("connections", {})

        # Verificar trigger
        has_trigger = any(
            node.get("type") in TRIGGER_NODE_TYPES for node in nodes
        )
        if not has_trigger and len(nodes) > 0:
            result["warnings"].append(
                "Workflow sem nó trigger — só pode ser executado manualmente via API"
            )

        # Verificar nós de fim (sem saídas)
        node_names = {node["name"] for node in nodes}
        with_outgoing = set(connections.keys())
        end_nodes = node_names - with_outgoing

        if not end_nodes and len(nodes) > 1:
            result["warnings"].append(
                "Workflow sem nós de fim — possível dependência circular"
            )

        # Verificar tratamento de erro para nós críticos
        error_node_types = [
            "n8n-nodes-base.errorTrigger",
            "n8n-nodes-base.if",
            "n8n-nodes-base.switch",
        ]
        has_error_handling = any(
            node.get("type") in error_node_types for node in nodes
        )
        critical_types = [
            "httpRequest", "googleSheets", "emailSend",
            "postgres", "mysql", "mongodb",
        ]
        has_critical_nodes = any(
            any(ct in node.get("type", "") for ct in critical_types)
            for node in nodes
        )

        if has_critical_nodes and not has_error_handling and len(nodes) > 3:
            result["warnings"].append(
                "Workflow com operações críticas mas sem tratamento de erro explícito — adicione nós IF ou Error Trigger"
            )

    def _check_efsm_best_practices(self, workflow_data: Dict, result: Dict):
        """Verifica boas práticas específicas da EFSM."""
        nodes: List[Dict] = workflow_data.get("nodes", [])
        settings: Dict = workflow_data.get("settings", {})

        # Verificar timeout configurado
        if not settings.get("executionTimeout"):
            result["warnings"].append(
                "Sem 'executionTimeout' nas settings — workflows podem travar indefinidamente"
            )

        # Verificar se há nó de log/auditoria
        node_names_lower = [node.get("name", "").lower() for node in nodes]
        log_hints = ["log", "audit", "registro", "status", "run_id"]
        has_logging = any(
            any(hint in name for hint in log_hints)
            for name in node_names_lower
        )
        if not has_logging and len(nodes) > 4:
            result["warnings"].append(
                "Sem nó de log/auditoria identificado — recomendado para rastreabilidade"
            )

        # Verificar se active está false (bom para deploy)
        if workflow_data.get("active") is True:
            result["warnings"].append(
                "Workflow marcado como 'active: true' — recomendado deploy como inativo e ativar após validação"
            )

    # -------------------------------------------------------------------------
    # Dry Run
    # -------------------------------------------------------------------------

    def dry_run(
        self,
        workflow_id: str,
        test_data: Dict = None,
        test_data_file: str = None,
        timeout_seconds: int = 60,
    ) -> Dict:
        """
        Executa o workflow com dados de teste e aguarda a conclusão.
        Retorna status, ID da execução, timestamps e erros se houver.
        """
        if test_data_file:
            with open(test_data_file, "r", encoding="utf-8") as f:
                test_data = json.load(f)

        print(f"Iniciando dry-run do workflow '{workflow_id}'...")
        if test_data:
            print(f"Dados de entrada: {json.dumps(test_data, ensure_ascii=False)}")

        execution_result = self.client.execute_workflow(workflow_id, data=test_data)
        execution_id = (
            execution_result.get("data", {}).get("executionId")
            or execution_result.get("executionId")
        )

        if not execution_id:
            return {
                "status": "failed",
                "error": "Nenhum execution ID retornado pela API",
                "raw_response": execution_result,
            }

        print(f"Execução iniciada: {execution_id}")
        print(f"Aguardando conclusão (timeout: {timeout_seconds}s)...")

        max_attempts = timeout_seconds // 2
        for attempt in range(max_attempts):
            time.sleep(2)
            try:
                execution = self.client.get_execution(execution_id)
                finished = execution.get("finished", False)
                status = execution.get("status")

                # Execução concluída
                if finished or status in ("success", "error", "crashed"):
                    has_error = (
                        execution.get("data", {})
                        .get("resultData", {})
                        .get("error") is not None
                    )
                    final_status = "success" if (finished and not has_error and status != "error") else "failed"

                    result: Dict[str, Any] = {
                        "status": final_status,
                        "execution_id": execution_id,
                        "finished": True,
                        "started_at": execution.get("startedAt"),
                        "stopped_at": execution.get("stoppedAt"),
                        "mode": execution.get("mode"),
                        "n8n_status": status,
                    }

                    if final_status == "failed":
                        error_data = (
                            execution.get("data", {})
                            .get("resultData", {})
                            .get("error", {})
                        )
                        result["error"] = {
                            "message": error_data.get("message", "Erro desconhecido"),
                            "description": error_data.get("description"),
                            "node": error_data.get("node", {}).get("name") if isinstance(error_data.get("node"), dict) else error_data.get("node"),
                        }

                    print(f"Execução concluída: {final_status.upper()}")
                    return result

            except Exception as e:
                print(f"[tentativa {attempt + 1}] Erro ao verificar status: {e}")
                continue

        return {
            "status": "timeout",
            "execution_id": execution_id,
            "finished": False,
            "message": f"Execução não concluiu em {timeout_seconds}s — verifique manualmente no n8n UI",
        }

    # -------------------------------------------------------------------------
    # Test Suite
    # -------------------------------------------------------------------------

    def test_suite(self, workflow_id: str, test_cases: List[Dict]) -> Dict:
        """
        Executa múltiplos casos de teste contra um workflow.
        Cada caso: {"name": str, "input": dict, "expected_status": "success"|"failed"}
        """
        results: Dict[str, Any] = {
            "workflow_id": workflow_id,
            "total_tests": len(test_cases),
            "passed": 0,
            "failed": 0,
            "test_results": [],
        }

        for i, test_case in enumerate(test_cases, 1):
            case_name = test_case.get("name", f"Caso {i}")
            print(f"\n[{i}/{len(test_cases)}] {case_name}")

            test_data = test_case.get("input", {})
            expected_status = test_case.get("expected_status", "success")

            run_result = self.dry_run(workflow_id, test_data=test_data)
            actual_status = run_result.get("status")
            passed = actual_status == expected_status

            test_result = {
                "test_name": case_name,
                "passed": passed,
                "expected_status": expected_status,
                "actual_status": actual_status,
                "execution_id": run_result.get("execution_id"),
                "input": test_data,
                "error": run_result.get("error"),
            }

            results["test_results"].append(test_result)
            if passed:
                results["passed"] += 1
                print(f"  PASSOU")
            else:
                results["failed"] += 1
                err = run_result.get("error", {})
                err_msg = err.get("message") if isinstance(err, dict) else str(err)
                print(f"  FALHOU — esperado: {expected_status}, obtido: {actual_status}")
                if err_msg:
                    print(f"  Erro: {err_msg}")

        print(f"\nResultado: {results['passed']}/{results['total_tests']} testes passaram")
        return results

    # -------------------------------------------------------------------------
    # Relatório
    # -------------------------------------------------------------------------

    def generate_test_report(self, validation: Dict, dry_run_result: Dict = None) -> str:
        """Gera relatório legível de validação e dry-run."""
        lines = []
        sep = "=" * 65

        lines.append(sep)
        lines.append("EFSM n8n — Relatório de Teste de Workflow")
        lines.append(sep)

        # Validação
        lines.append("\n## Validação de Estrutura")
        status_label = "VÁLIDO" if validation["valid"] else "INVÁLIDO"
        lines.append(f"Status: {status_label}")

        errors = validation.get("errors", [])
        warnings = validation.get("warnings", [])

        if errors:
            lines.append(f"\nErros ({len(errors)}):")
            for err in errors:
                lines.append(f"  [ERRO] {err}")

        if warnings:
            lines.append(f"\nAvisos ({len(warnings)}):")
            for warn in warnings:
                lines.append(f"  [AVISO] {warn}")

        if not errors and not warnings:
            lines.append("\nNenhum problema encontrado.")

        # Dry-run
        if dry_run_result:
            lines.append("\n## Resultado do Dry-Run")
            run_status = dry_run_result.get("status", "desconhecido").upper()
            lines.append(f"Status: {run_status}")
            lines.append(f"Execution ID: {dry_run_result.get('execution_id', 'N/A')}")

            if dry_run_result.get("started_at"):
                lines.append(f"Início: {dry_run_result['started_at']}")
            if dry_run_result.get("stopped_at"):
                lines.append(f"Fim: {dry_run_result['stopped_at']}")

            error = dry_run_result.get("error")
            if error:
                lines.append("\nErro na execução:")
                if isinstance(error, dict):
                    lines.append(f"  Mensagem: {error.get('message', 'N/A')}")
                    if error.get("description"):
                        lines.append(f"  Descrição: {error['description']}")
                    if error.get("node"):
                        lines.append(f"  Nó: {error['node']}")
                else:
                    lines.append(f"  {error}")

            if dry_run_result.get("status") == "timeout":
                lines.append("\nTIMEOUT: A execução não concluiu no tempo esperado.")
                lines.append("Verifique no n8n UI: https://n8n.eufacoseu.marketing/")

        lines.append("\n" + sep)
        return "\n".join(lines)


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="EFSM n8n Tester — Validação e testes de workflows",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "action",
        choices=["validate", "dry-run", "test-suite", "report"],
        help="Ação a executar",
    )
    parser.add_argument("--id", help="ID do workflow")
    parser.add_argument("--file", help="Arquivo JSON do workflow (validação local)")
    parser.add_argument("--data", help="Dados de teste JSON (string)")
    parser.add_argument("--data-file", help="Arquivo JSON com dados de teste")
    parser.add_argument("--test-suite", help="Arquivo JSON com casos de teste")
    parser.add_argument("--timeout", type=int, default=60, help="Timeout do dry-run em segundos")
    parser.add_argument("--pretty", action="store_true", help="Saída JSON formatada")
    parser.add_argument("--report", action="store_true", help="Gerar relatório legível")

    args = parser.parse_args()

    try:
        tester = WorkflowTester()

        if args.action == "validate":
            result = tester.validate_workflow(
                workflow_id=args.id, workflow_file=args.file
            )
            if args.report:
                print(tester.generate_test_report(result))
            else:
                print(json.dumps(result, indent=2 if args.pretty else None, ensure_ascii=False))

        elif args.action == "dry-run":
            if not args.id:
                raise ValueError("--id obrigatório para dry-run")

            test_data = json.loads(args.data) if args.data else None
            result = tester.dry_run(
                workflow_id=args.id,
                test_data=test_data,
                test_data_file=args.data_file,
                timeout_seconds=args.timeout,
            )

            if args.report:
                validation = tester.validate_workflow(workflow_id=args.id)
                print(tester.generate_test_report(validation, result))
            else:
                print(json.dumps(result, indent=2 if args.pretty else None, ensure_ascii=False))

        elif args.action == "test-suite":
            if not args.id:
                raise ValueError("--id obrigatório para test-suite")
            if not args.test_suite:
                raise ValueError("--test-suite obrigatório para test-suite")
            with open(args.test_suite, "r", encoding="utf-8") as f:
                test_cases = json.load(f)
            result = tester.test_suite(args.id, test_cases)
            print(json.dumps(result, indent=2 if args.pretty else None, ensure_ascii=False))

        elif args.action == "report":
            if not args.id:
                raise ValueError("--id obrigatório para report")
            validation = tester.validate_workflow(workflow_id=args.id)
            print(tester.generate_test_report(validation))

    except KeyboardInterrupt:
        print("\nOperação cancelada pelo usuário.", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
