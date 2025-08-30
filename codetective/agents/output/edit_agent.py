"""
Edit agent for automatically applying code fixes using AI.
"""

from pathlib import Path
from typing import Any, List

from codetective.agents.ai_base import AIAgent
from codetective.agents.base import OutputAgent
from codetective.core.config import Config
from codetective.models.schemas import AgentType, Issue, IssueStatus
from codetective.utils import FileUtils
from codetective.utils.prompt_builder import PromptBuilder


class EditAgent(OutputAgent, AIAgent):
    """Agent for automatically applying code fixes."""

    def __init__(self, config: Config):
        OutputAgent.__init__(self, config)
        AIAgent.__init__(self, config)
        self.agent_type = AgentType.EDIT
        self.backup_files_created: list[str] = []  # Track backup files for cleanup

    def is_available(self) -> bool:
        """Check if Ollama is available for edit generation."""
        return self.is_ai_available()

    def process_issues(self, issues: List[Issue], **kwargs: Any) -> List[Issue]:
        """Process issues by applying automatic fixes."""
        processed_issues: list[Issue] = []
        modified_files: set[str] = set()

        # Filter out ignored and already fixed issues
        issues_to_process = self._filter_processable_issues(issues)

        if not issues_to_process:
            print("No issues to process (all are ignored or already fixed)")
            return issues

        # Group issues by file for efficient processing
        issues_by_file: dict[str, list[Issue]] = self._group_issues_by_file(issues_to_process)

        for file_path, file_issues in issues_by_file.items():
            try:
                # Apply fixes to the file
                fixed_issues = self._fix_file_issues(file_path, file_issues)
                processed_issues.extend(fixed_issues)

                # Track modified files
                if any(issue.status == IssueStatus.FIXED for issue in fixed_issues):
                    modified_files.add(file_path)

            except Exception as e:
                # If fixing fails, mark issues as failed with detailed error
                error_msg = f"Fix failed: {str(e)}"
                print(f"Error fixing {file_path}: {error_msg}")
                for issue in file_issues:
                    failed_issue = issue.model_copy()
                    failed_issue.status = IssueStatus.FAILED
                    failed_issue.description = f"{failed_issue.description}\n\n{error_msg}"
                    processed_issues.append(failed_issue)

        # Add unprocessed issues back to results
        for issue in issues:
            if issue not in issues_to_process:
                processed_issues.append(issue)

        # Clean up backup files if not keeping them
        if not self.config.keep_backup:
            self._cleanup_backup_files()

        return processed_issues

    def _group_issues_by_file(self, issues: list[Issue]) -> dict[str, list[Issue]]:
        """Group issues by file path."""
        issues_by_file: dict[str, list[Issue]] = {}

        for issue in issues:
            if issue.file_path:
                if issue.file_path not in issues_by_file:
                    issues_by_file[issue.file_path] = []
                issues_by_file[issue.file_path].append(issue)

        return issues_by_file

    def _fix_file_issues(self, file_path: str, issues: list[Issue]) -> list[Issue]:
        """Fix all issues in a single file, processing in batches if more than 3 issues."""
        if not Path(file_path).exists():
            error_msg = f"File not found: {file_path}"
            print(error_msg)
            return [self._mark_issue_failed(issue, "File not found") for issue in issues]

        try:
            # Create backup if enabled
            backup_path = None
            if self.config.backup_files:
                backup_path = FileUtils.create_backup(file_path)
                if backup_path:
                    self.backup_files_created.append(backup_path)
                    print(f"Created backup: {backup_path}")

            # Read original file content
            original_content = FileUtils.get_file_content(file_path)
            if original_content.startswith("Error reading file"):
                error_msg = f"Cannot read file: {file_path}"
                print(error_msg)
                return [self._mark_issue_failed(issue, "Cannot read file") for issue in issues]

            # Process issues in batches to avoid LLM token limits
            if len(issues) > 3:
                return self._fix_issues_in_batches(file_path, original_content, issues)
            else:
                return self._fix_issues_single_batch(file_path, original_content, issues)

        except Exception as e:
            error_msg = f"Exception during fix: {str(e)}"
            print(f"Error fixing {file_path}: {error_msg}")
            return [self._mark_issue_failed(issue, str(e)) for issue in issues]

    def _fix_issues_in_batches(self, file_path: str, original_content: str, issues: List[Issue]) -> List[Issue]:
        """Fix issues in batches of 3 to avoid LLM token limits."""
        batch_size = 3
        all_fixed_issues = []
        current_content = original_content

        print(f"Processing {len(issues)} issues in batches of {batch_size} for {file_path}")

        # Process issues in batches
        for i in range(0, len(issues), batch_size):
            batch_issues = issues[i : i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(issues) + batch_size - 1) // batch_size

            print(f"Processing batch {batch_num}/{total_batches} ({len(batch_issues)} issues)")

            try:
                # Generate fixed content for this batch
                fixed_content = self._generate_fixed_content(file_path, current_content, batch_issues)

                if fixed_content and fixed_content != current_content:
                    # Update current content for next batch
                    current_content = fixed_content
                    # Mark batch issues as fixed
                    batch_fixed = [self._mark_issue_fixed(issue) for issue in batch_issues]
                    all_fixed_issues.extend(batch_fixed)
                    print(f"Batch {batch_num} applied successfully")
                else:
                    # Mark batch issues as failed
                    batch_failed = [
                        self._mark_issue_failed(issue, f"No fix generated for batch {batch_num}") for issue in batch_issues
                    ]
                    all_fixed_issues.extend(batch_failed)
                    print(f"Batch {batch_num} failed: No fix generated")

            except Exception as e:
                # Mark batch issues as failed
                error_msg = f"Batch {batch_num} failed: {str(e)}"
                batch_failed = [self._mark_issue_failed(issue, error_msg) for issue in batch_issues]
                all_fixed_issues.extend(batch_failed)
                print(error_msg)

        # Write final content if any changes were made
        if current_content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(current_content)
            print(f"Applied all batch fixes to: {file_path}")

        return all_fixed_issues

    def _fix_issues_single_batch(self, file_path: str, original_content: str, issues: List[Issue]) -> List[Issue]:
        """Fix issues in a single batch (3 or fewer issues)."""
        # Generate fixed content
        fixed_content = self._generate_fixed_content(file_path, original_content, issues)

        if fixed_content and fixed_content != original_content:
            # Write fixed content back to file
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(fixed_content)

            print(f"Applied fixes to: {file_path}")
            # Mark issues as fixed
            return [self._mark_issue_fixed(issue) for issue in issues]
        else:
            # No changes made
            error_msg = "No fix generated or content unchanged"
            print(f"Warning: {error_msg} for {file_path}")
            return [self._mark_issue_failed(issue, "No fix generated") for issue in issues]

    def _generate_fixed_content(self, file_path: str, content: str, issues: List[Issue]) -> str:
        """Generate fixed content using AI."""
        prompt = self._create_fix_prompt(file_path, content, issues)

        try:
            response = self.call_ai(prompt, temperature=0.1)
            return self._extract_fixed_code(response, content)
        except Exception:
            return ""

    def _create_fix_prompt(self, file_path: str, content: str, issues: List[Issue]) -> str:
        """Create a prompt for generating code fixes."""
        issues_summary = []
        for i, issue in enumerate(issues, 1):
            line_info = f" (line {issue.line_number})" if issue.line_number else ""
            issues_summary.append(f"{i}. {issue.title}{line_info}: {issue.description}")
            if issue.fix_suggestion:
                issues_summary.append(f"   Suggested fix: {issue.fix_suggestion}")

        issues_text = "\n".join(issues_summary)

        input_data = f"""File: {file_path}

Issues to fix:
{issues_text}

Original code:
{content}"""

        config = {
            "role": "an expert code fixer",
            "instruction": "Fix the identified issues in the code file and return ONLY the complete fixed code.",
            "output_constraints": [
                "Return ONLY the complete fixed code",
                "Do NOT include any explanations, comments about the fixes, or markdown formatting before or after the code",
                "Do NOT wrap the code in ``` blocks",
                "Do NOT add any text before or after the code",
                "Preserve the original file structure and formatting",
                "Make minimal changes to fix only the identified issues",
                "Ensure the code is syntactically correct and functional",
                "Do NOT be influenced by existing comments or TODO comments in the code - focus only on the given issues",
            ],
            "output_format": "Complete fixed file code without any additional formatting or explanations",
        }

        return PromptBuilder.build_prompt_from_config(config, input_data)

    def _extract_fixed_code(self, response: str, original_content: str) -> str:
        """Extract fixed code from AI response."""
        if not response or not response.strip():
            return ""

        # Clean response using base class method
        cleaned_response = self.clean_ai_response(response)

        # Try multiple extraction methods
        fixed_content = self._try_extract_methods(cleaned_response, original_content)

        # Final validation
        if fixed_content and len(fixed_content.strip()) > 0:
            # Ensure it's not just whitespace or too short
            if len(fixed_content.strip()) > len(original_content) * 0.3:
                return fixed_content

        return ""

    def _try_extract_methods(self, response: str, original_content: str) -> str:
        """Try multiple methods to extract code from response."""
        # Method 1: Look for code blocks with ```
        code_block_result = self._extract_from_code_blocks(response)
        if code_block_result:
            return code_block_result

        # Method 2: Look for "Fixed code:" section
        fixed_code_result = self._extract_after_marker(response, "Fixed code:")
        if fixed_code_result:
            return fixed_code_result

        # Method 3: Look for code after common markers
        for marker in ["Here's the fixed code:", "The fixed code is:", "Fixed version:"]:
            marker_result = self._extract_after_marker(response, marker)
            if marker_result:
                return marker_result

        # Method 4: If response looks like pure code, use it directly
        if self._looks_like_code(response, original_content):
            return response.strip()

        # Method 5: Try to find the largest code-like block
        return self._extract_largest_code_block(response)

    def _extract_from_code_blocks(self, response: str) -> str:
        """Extract code from markdown code blocks."""
        lines = response.split("\n")
        code_lines = []
        in_code_block = False

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("```"):
                if in_code_block:
                    break  # End of code block
                else:
                    in_code_block = True  # Start of code block
                    continue

            if in_code_block:
                code_lines.append(line)

        if code_lines:
            return "\n".join(code_lines)
        return ""

    def _extract_after_marker(self, response: str, marker: str) -> str:
        """Extract code after a specific marker."""
        marker_pos = response.lower().find(marker.lower())
        if marker_pos == -1:
            return ""

        # Get content after marker
        after_marker = response[marker_pos + len(marker) :].strip()

        # Remove any leading markdown or formatting
        lines = after_marker.split("\n")
        code_lines = []
        started = False

        for line in lines:
            stripped = line.strip()
            # Skip empty lines and markdown at the start
            if not started and (not stripped or stripped.startswith("```")):
                continue
            started = True

            # Stop at markdown end or explanatory text
            if stripped.startswith("```") and started:
                break
            if stripped.lower().startswith(("explanation:", "note:", "the above", "this fixes")):
                break

            code_lines.append(line)

        return "\n".join(code_lines).strip()

    def _looks_like_code(self, response: str, original_content: str) -> bool:
        """Check if response looks like pure code."""
        # Check for common code indicators
        code_indicators = ["def ", "class ", "import ", "from ", "if ", "for ", "while ", "{", "}", ";"]
        explanation_indicators = ["here is", "here's", "the code", "explanation", "i fixed", "i changed"]

        response_lower = response.lower()

        # Count code vs explanation indicators
        code_count = sum(1 for indicator in code_indicators if indicator in response_lower)
        explanation_count = sum(1 for indicator in explanation_indicators if indicator in response_lower)

        # If it has code indicators and few explanation indicators, likely pure code
        return code_count > 2 and explanation_count < 2

    def _extract_largest_code_block(self, response: str) -> str:
        """Extract the largest block that looks like code."""
        lines = response.split("\n")
        current_block: list[str] = []
        largest_block: list[str] = []

        for line in lines:
            stripped = line.strip()

            # Skip obvious non-code lines
            if any(
                stripped.lower().startswith(phrase)
                for phrase in ["here is", "here's", "the code", "explanation", "note:", "i fixed", "i changed"]
            ):
                if len(current_block) > len(largest_block):
                    largest_block = current_block[:]
                current_block = []
                continue

            # Skip markdown markers
            if stripped.startswith("```"):
                continue

            current_block.append(line)

        # Check final block
        if len(current_block) > len(largest_block):
            largest_block = current_block

        return "\n".join(largest_block).strip()

    def _mark_issue_fixed(self, issue: Issue) -> Issue:
        """Mark an issue as fixed."""
        fixed_issue = issue.model_copy()
        fixed_issue.status = IssueStatus.FIXED
        return fixed_issue

    def _mark_issue_failed(self, issue: Issue, error_message: str) -> Issue:
        """Mark an issue as failed to fix."""
        failed_issue = issue.model_copy()
        failed_issue.status = IssueStatus.FAILED
        # Add error message to description
        failed_issue.description = f"{failed_issue.description}\n\nFix failed: {error_message}"
        return failed_issue

    def _filter_processable_issues(self, issues: List[Issue]) -> List[Issue]:
        """Filter out ignored and already fixed issues."""
        processable_issues = []

        for issue in issues:
            # Skip ignored issues
            if issue.status == IssueStatus.IGNORED:
                print(f"Skipping ignored issue: {issue.title}")
                continue

            # Skip already fixed issues
            if issue.status == IssueStatus.FIXED:
                print(f"Skipping already fixed issue: {issue.title}")
                continue

            processable_issues.append(issue)

        return processable_issues

    def _cleanup_backup_files(self) -> None:
        """Clean up backup files that were created during fixing."""
        for backup_path in self.backup_files_created:
            try:
                if Path(backup_path).exists():
                    Path(backup_path).unlink()
                    print(f"Deleted backup file: {backup_path}")
            except Exception as e:
                print(f"Warning: Could not delete backup file {backup_path}: {e}")

        self.backup_files_created.clear()
