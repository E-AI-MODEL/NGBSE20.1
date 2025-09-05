#!/usr/bin/env python3
"""
Linter to detect hardcoded LLM parameters outside of factory/providers.
"""

import ast
import sys
from pathlib import Path
from typing import List, Tuple


class LLMUsageLinter(ast.NodeVisitor):
    """AST visitor to detect hardcoded LLM parameters."""
    
    def __init__(self):
        self.violations: List[Tuple[str, int, str]] = []
        self.allowed_files = {
            "src/ngbse20/llm_factory.py",
            "src/ngbse20/providers/",
            "src/ngbse20/config/",
            "tests/",
            "examples/",
        }
    
    def visit_Call(self, node):
        """Visit function calls to detect hardcoded parameters."""
        # Check for direct LLM client calls with hardcoded parameters
        if isinstance(node.func, ast.Attribute):
            if node.func.attr in ["call", "generate", "chat", "completion"]:
                self._check_call_parameters(node)
        
        # Check for provider client instantiation with hardcoded parameters
        if isinstance(node.func, ast.Name):
            if node.func.id in ["OpenAI", "Anthropic", "Mistral", "Ollama"]:
                self._check_instantiation_parameters(node)
        
        self.generic_visit(node)
    
    def _check_call_parameters(self, node):
        """Check for hardcoded parameters in LLM calls."""
        for keyword in node.keywords:
            if keyword.arg in ["temperature", "top_p", "max_tokens", "model"]:
                if isinstance(keyword.value, (ast.Constant, ast.Num)):
                    self.violations.append((
                        f"Hardcoded {keyword.arg} parameter in LLM call",
                        node.lineno,
                        f"Use LLM factory instead of hardcoded {keyword.arg}={keyword.value.value}"
                    ))
    
    def _check_instantiation_parameters(self, node):
        """Check for hardcoded parameters in provider instantiation."""
        for keyword in node.keywords:
            if keyword.arg in ["temperature", "top_p", "max_tokens", "model"]:
                if isinstance(keyword.value, (ast.Constant, ast.Num)):
                    self.violations.append((
                        f"Hardcoded {keyword.arg} parameter in provider instantiation",
                        node.lineno,
                        f"Use LLM factory instead of hardcoded {keyword.arg}={keyword.value.value}"
                    ))
    
    def visit_Assign(self, node):
        """Visit assignments to detect hardcoded model names."""
        if isinstance(node.targets[0], ast.Name):
            if node.targets[0].id in ["model", "MODEL", "llm_model"]:
                if isinstance(node.value, ast.Constant):
                    if isinstance(node.value.value, str) and any(
                        provider in node.value.value.lower() 
                        for provider in ["gpt-", "claude-", "mistral", "llama"]
                    ):
                        self.violations.append((
                            "Hardcoded model name assignment",
                            node.lineno,
                            f"Use LLM factory instead of hardcoded model='{node.value.value}'"
                        ))
        
        self.generic_visit(node)


def lint_file(file_path: Path) -> List[Tuple[str, int, str]]:
    """Lint a single Python file for hardcoded LLM usage."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content, filename=str(file_path))
        linter = LLMUsageLinter()
        linter.visit(tree)
        
        return linter.violations
    except SyntaxError as e:
        return [("Syntax error", e.lineno, str(e))]
    except Exception as e:
        return [("Parse error", 0, str(e))]


def is_allowed_file(file_path: Path) -> bool:
    """Check if file is in allowed directories."""
    file_str = str(file_path)
    return any(
        file_str.startswith(allowed) or file_str.endswith(allowed)
        for allowed in [
            "src/ngbse20/llm_factory.py",
            "src/ngbse20/providers/",
            "src/ngbse20/config/",
            "tests/",
            "examples/",
        ]
    )


def main():
    """Main linter function."""
    if len(sys.argv) > 1:
        target_paths = [Path(p) for p in sys.argv[1:]]
    else:
        target_paths = [Path("src/ngbse20")]
    
    total_violations = 0
    
    for target_path in target_paths:
        if target_path.is_file() and target_path.suffix == '.py':
            files = [target_path]
        elif target_path.is_dir():
            files = list(target_path.rglob("*.py"))
        else:
            print(f"Error: {target_path} is not a valid file or directory")
            continue
        
        for file_path in files:
            if is_allowed_file(file_path):
                continue
            
            violations = lint_file(file_path)
            if violations:
                print(f"\n{file_path}:")
                for violation_type, line_no, message in violations:
                    print(f"  Line {line_no}: {violation_type}")
                    print(f"    {message}")
                    total_violations += 1
    
    if total_violations > 0:
        print(f"\nFound {total_violations} violations")
        print("\nTo fix these issues:")
        print("1. Use the LLM factory instead of direct provider calls")
        print("2. Move hardcoded parameters to configuration files")
        print("3. Use environment variables for runtime overrides")
        sys.exit(1)
    else:
        print("No hardcoded LLM usage violations found ✓")


if __name__ == "__main__":
    main()