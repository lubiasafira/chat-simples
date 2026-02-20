"""
Script que executa todos os testes da aplicação e gera relatório final.
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import subprocess
import time

def print_header(title):
    """Imprime cabeçalho formatado."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")

def run_command(cmd, description):
    """Executa comando e retorna status."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        if result.returncode == 0:
            print(f"✅ {description} - SUCESSO\n")
            return True
        else:
            print(f"❌ {description} - FALHOU")
            print(f"Erro: {result.stderr}\n")
            return False
    except Exception as e:
        print(f"❌ {description} - ERRO: {e}\n")
        return False

def main():
    """Executa todos os testes e gera relatório."""
    print_header("🧪 SUITE COMPLETA DE TESTES - Chat com Claude AI")

    results = {}
    start_time = time.time()

    # Lista de testes
    tests = [
        {
            "cmd": "pytest tests/main_test.py -v --cov=backend --cov-report=term-missing",
            "desc": "Testes unitários (pytest)",
            "key": "unit"
        },
        {
            "cmd": "python tests/test_integration.py",
            "desc": "Teste de integração (fluxo completo)",
            "key": "integration"
        },
        {
            "cmd": "python tests/test_sliding_window.py",
            "desc": "Teste de janela deslizante",
            "key": "sliding_window"
        },
        {
            "cmd": "python tests/test_error_scenarios.py",
            "desc": "Testes de cenários de erro",
            "key": "error_scenarios"
        }
    ]

    print("📋 Executando testes...\n")

    # Executar cada teste
    for test in tests:
        results[test["key"]] = run_command(test["cmd"], test["desc"])
        time.sleep(1)  # Pequeno delay entre testes

    # Calcular tempo total
    elapsed_time = time.time() - start_time

    # Gerar relatório final
    print_header("📊 RELATÓRIO FINAL")

    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    failed_tests = total_tests - passed_tests

    print(f"Total de suites de teste: {total_tests}")
    print(f"✅ Passaram: {passed_tests}")
    print(f"❌ Falharam: {failed_tests}")
    print(f"⏱️  Tempo total: {elapsed_time:.2f} segundos\n")

    print("Detalhes:")
    for test in tests:
        status = "✅ PASSOU" if results[test["key"]] else "❌ FALHOU"
        print(f"  {status} - {test['desc']}")

    print("\n" + "="*70)

    if failed_tests == 0:
        print("🎉 TODOS OS TESTES PASSARAM COM SUCESSO!")
        print("="*70 + "\n")
        print("✨ A aplicação está pronta para uso!")
        print("\n📝 Para iniciar a aplicação:")
        print("   uvicorn backend.main:app --reload")
        print("\n🌐 Acesse: http://localhost:8000\n")
        return 0
    else:
        print("⚠️  ALGUNS TESTES FALHARAM - VERIFIQUE OS ERROS ACIMA")
        print("="*70 + "\n")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Testes interrompidos pelo usuário\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERRO FATAL: {e}\n")
        sys.exit(1)
