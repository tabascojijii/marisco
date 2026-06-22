#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


ENGINE = os.environ.get("AGENTS_ENGINE", "codex")
MAX_LOOPS = 5


def eprint(message: str) -> None:
    print(f"[\033[1;31mOrchestrator\033[0m] {message}", file=sys.stderr)


def log(message: str) -> None:
    print(f"[\033[1;32mOrchestrator\033[0m] {message}")


def run_agent(prompt: str) -> str:
    if ENGINE == "claude":
        cmd = ["claude", "--print", prompt, "--permission-mode", "bypassPermissions"]
    else:
        cmd = ["codex", "exec", "--dangerously-bypass-approvals-and-sandbox", prompt]
    proc = subprocess.run(cmd, text=True, capture_output=True)
    if proc.returncode != 0:
        eprint(f"Agent execution failed: {proc.stderr}")
    return proc.stdout


def run_verification(repo_root: Path) -> tuple[bool, str]:
    export_code = "import nbdev.cli; nbdev.cli.nb_export(lib_path='marisco')"
    subprocess.run([sys.executable, "-c", export_code], cwd=str(repo_root), capture_output=True)
    comp = subprocess.run([sys.executable, "-m", "compileall", "marisco"], cwd=str(repo_root), capture_output=True, text=True)
    if comp.returncode != 0:
        return False, f"--- COMPILEALL FAILED ---\n{comp.stderr or comp.stdout}"
    if (repo_root / "tests").is_dir() or list(repo_root.glob("nbs/*.ipynb")):
        test = subprocess.run([sys.executable, "-m", "pytest", "-v"], cwd=str(repo_root), capture_output=True, text=True)
        if test.returncode != 0:
            return False, f"--- PYTEST FAILED ---\n{test.stdout}\n{test.stderr}"
    return True, "All tests passed cleanly."


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("spec_file", type=str, help="Path to the markdown specification file")
    args = parser.parse_args()

    spec_path = Path(args.spec_file).resolve()
    if not spec_path.exists():
        eprint(f"Specification file not found: {spec_path}")
        return 1

    repo_root = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()).resolve()
    os.chdir(repo_root)
    spec_content = spec_path.read_text(encoding="utf-8")

    log("Phase 1: Architecture Reviewing...")
    arch_prompt = f"""あなたは MARISCO プロジェクトの極めて優秀なソフトウェアアーキテクトです。
以下の仕様書を読み、`nbs/` 配下のどの Notebook を修正・新規作成すべきか、および TDD に基づきどのようなテストコード（アサーション）を仕込むべきか、設計方針を出力してください。
既存の callbacks.ipynb や configs.ipynb の共通資産を優先して再利用する方針を含めてください。

【実装仕様書】
{spec_content}
"""
    architecture_blueprint = run_agent(arch_prompt)
    log("Architecture Blueprint established.")

    error_context = ""
    for loop in range(1, MAX_LOOPS + 1):
        log(f"Phase 2: Implementation & Refactoring Loop ({loop}/{MAX_LOOPS})...")
        impl_prompt = f"""あなたは極めて正確なコードを記述するシニアデベロッパー（Implementer）です。
`nbs/` が SSOT（単一の真実のソース）です。生成される `marisco/` 内の `.py` ファイルを直接編集してはいけません。
必ず `nbformat` などの Python ライブラリやスクリプトを自作・実行して、`nbs/` 配下の適切なノートブック（`.ipynb`）にコードセルおよびテストセルを追加・修正してください。

【設計方針】
{architecture_blueprint}

【現在のエラー・フィードバック（空の場合は初回実行）】
{error_context}

タスク:
1. 必要な `nbs/*.ipynb` をプログラムを介して直接、または適切なツールで編集せよ。
2. 編集が完了したら、作業内容を簡潔に報告せよ。
"""
        run_agent(impl_prompt)

        log("Phase 3: Automated Verification (Auditor Grid)...")
        success, verification_log = run_verification(repo_root)

        if success:
            log("\033[1;32m[GREEN] All verification passed successfully!\033[0m")
            log("Phase 4: Executing Clean Commit...")
            subprocess.run(["git", "add", "nbs/", "marisco/"], cwd=str(repo_root))
            commit_msg = f"feat: [AUTOLOOP_PASS] implemented via {spec_path.name}\n\nBlueprint:\n{architecture_blueprint}"
            res = subprocess.run(["git", "commit", "-m", commit_msg], cwd=str(repo_root), capture_output=True, text=True)
            if res.returncode == 0:
                log("\033[1;32m[SUCCESS] Clean TDD commit has been injected into HEAD.\033[0m")
                return 0
            else:
                eprint(f"Commit aborted by pre-commit hook:\n{res.stderr or res.stdout}")
                return 1
        else:
            log(f"\033[1;31m[RED] Verification failed in loop {loop}.\033[0m")
            error_context = verification_log

    eprint(f"TDD Orchestrator aborted: Failed to resolve Green status within {MAX_LOOPS} loops.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
