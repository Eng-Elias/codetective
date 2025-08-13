#!/usr/bin/env python3
"""
Demo script for Codetective - Multi-Agent Code Review Tool.

This script demonstrates the basic functionality of Codetective.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add the codetective package to the path
sys.path.insert(0, str(Path(__file__).parent))

from codetective.core.config import get_config
from codetective.core.utils import get_system_info
from codetective.core.orchestrator import CodeDetectiveOrchestrator
from codetective.models.schemas import ScanConfig, AgentType


OPENAI_API_KEY = "sk-abcdabcdabcdabcdabcdabcd"


def create_sample_code():
    """Create sample code files for demonstration."""
    temp_dir = Path(tempfile.mkdtemp())
    
    # Create a Python file with some issues
    python_file = temp_dir / "sample.py"
    python_file.write_text("""
import os
import subprocess

# Potential security issue: hardcoded password
password = "admin123"

def run_command(cmd):
    # Security issue: shell injection vulnerability
    result = subprocess.run(cmd, shell=True, capture_output=True)
    return result.stdout

def process_file(filename):
    # Potential issue: no input validation
    with open(filename, 'r') as f:
        content = f.read()
    
    # Code quality issue: unused variable
    unused_var = "this is not used"
    
    return content

# Missing error handling
data = process_file("/etc/passwd")
print(data)
""")
    
    # Create a JavaScript file with issues
    js_file = temp_dir / "sample.js"
    js_file.write_text("""
// Potential XSS vulnerability
function displayUserInput(input) {
    document.getElementById('output').innerHTML = input;
}

// Hardcoded API key
const API_KEY = "sk-1234567890abcdef";

// Potential prototype pollution
function merge(target, source) {
    for (let key in source) {
        target[key] = source[key];
    }
    return target;
}

// Missing input validation
function processData(data) {
    return eval(data.expression);
}
""")
    
    return temp_dir


def demo_system_info():
    """Demonstrate system information retrieval."""
    print("🔍 Codetective Demo - System Information")
    print("=" * 50)
    
    system_info = get_system_info()
    
    print(f"Python Version: {system_info.python_version}")
    print(f"Codetective Version: {system_info.codetective_version}")
    print(f"SemGrep Available: {'✅' if system_info.semgrep_available else '❌'}")
    print(f"Trivy Available: {'✅' if system_info.trivy_available else '❌'}")
    print(f"Ollama Available: {'✅' if system_info.ollama_available else '❌'}")
    
    if system_info.semgrep_version:
        print(f"SemGrep Version: {system_info.semgrep_version}")
    if system_info.trivy_version:
        print(f"Trivy Version: {system_info.trivy_version}")
    if system_info.ollama_version:
        print(f"Ollama Version: {system_info.ollama_version}")
    
    print()


def demo_scan(project_path):
    """Demonstrate scanning functionality."""
    print("🔍 Running Code Scan")
    print("=" * 30)
    
    # Configure scan
    available_agents = []
    system_info = get_system_info()
    
    if system_info.semgrep_available:
        available_agents.append(AgentType.SEMGREP)
    if system_info.trivy_available:
        available_agents.append(AgentType.TRIVY)
    if system_info.ollama_available:
        available_agents.append(AgentType.AI_REVIEW)
    
    if not available_agents:
        print("❌ No agents available. Please install SemGrep, Trivy, or Ollama.")
        return None
    
    print(f"Using agents: {[agent.value for agent in available_agents]}")
    
    scan_config = ScanConfig(
        agents=available_agents,
        timeout=60,  # Shorter timeout for demo
        paths=[str(project_path)]
    )
    
    # Run scan
    try:
        config = get_config()
        orchestrator = CodeDetectiveOrchestrator(config)
        
        print("Starting scan...")
        scan_result = orchestrator.run_scan(scan_config)
        
        print(f"✅ Scan completed in {scan_result.scan_duration:.2f} seconds")
        print(f"Total issues found: {scan_result.total_issues}")
        
        # Show breakdown
        if scan_result.semgrep_results:
            print(f"  - SemGrep: {len(scan_result.semgrep_results)} issues")
        if scan_result.trivy_results:
            print(f"  - Trivy: {len(scan_result.trivy_results)} issues")
        if scan_result.ai_review_results:
            print(f"  - AI Review: {len(scan_result.ai_review_results)} issues")
        
        # Show sample issues
        all_issues = (scan_result.semgrep_results + 
                     scan_result.trivy_results + 
                     scan_result.ai_review_results)
        
        if all_issues:
            print("\n📋 Sample Issues Found:")
            for i, issue in enumerate(all_issues[:3], 1):
                print(f"{i}. {issue.title}")
                print(f"   File: {issue.file_path}")
                print(f"   Severity: {issue.severity.value}")
                if issue.line_number:
                    print(f"   Line: {issue.line_number}")
                print()
        
        return scan_result
    
    except Exception as e:
        print(f"❌ Scan failed: {e}")
        return None


def main():
    """Main demo function."""
    print("🔍 Codetective - Multi-Agent Code Review Tool Demo")
    print("=" * 60)
    print()
    
    # Show system information
    demo_system_info()
    
    # Create sample code
    print("📝 Creating sample code files...")
    sample_dir = create_sample_code()
    print(f"Sample code created in: {sample_dir}")
    print()
    
    # Run scan
    scan_result = demo_scan(sample_dir)
    
    if scan_result:
        print("✅ Demo completed successfully!")
        print("\nNext steps:")
        print("1. Install external tools (SemGrep, Trivy, Ollama) for full functionality")
        print("2. Run 'codetective info' to check tool availability")
        print("3. Use 'codetective scan .' to scan your own projects")
        print("4. Launch GUI with 'codetective gui'")
    else:
        print("⚠️  Demo completed with limited functionality")
        print("Install SemGrep, Trivy, or Ollama for full scanning capabilities")
    
    # Cleanup
    import shutil
    shutil.rmtree(sample_dir)
    print(f"\nCleaned up temporary files: {sample_dir}")


if __name__ == "__main__":
    main()
