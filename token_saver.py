import argparse
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import sys


PROJECT_ROOT = Path(__file__).resolve().parent
NBS_ROOT = PROJECT_ROOT / "nbs"
PY_ROOT = PROJECT_ROOT / "marisco"
MODULE_SUFFIXES = {".ipynb", ".py"}
TOP_LEVEL_DIRS = {"nbs", "marisco"}


def build_root_part_options():
    options = []
    seen = set()
    root_views = (
        Path(PROJECT_ROOT),
        PureWindowsPath(str(PROJECT_ROOT)),
        PurePosixPath(PROJECT_ROOT.as_posix()),
    )

    for root_view in root_views:
        parts = tuple(root_view.parts)
        key = tuple(part.casefold() for part in parts)
        if key in seen:
            continue
        seen.add(key)
        options.append(parts)

    return tuple(options)


PROJECT_ROOT_PART_OPTIONS = build_root_part_options()


def iter_input_path_views(raw_value):
    raw_text = str(raw_value).strip()
    if not raw_text:
        return []

    views = []
    seen = set()
    for candidate in (Path(raw_text), PureWindowsPath(raw_text), PurePosixPath(raw_text)):
        key = tuple(part.casefold() for part in candidate.parts)
        if key in seen:
            continue
        seen.add(key)
        views.append(candidate)
    return views


def strip_project_root_parts(parts):
    lowered_parts = tuple(part.casefold() for part in parts)
    for root_parts in PROJECT_ROOT_PART_OPTIONS:
        lowered_root = tuple(part.casefold() for part in root_parts)
        root_length = len(root_parts)
        if len(parts) < root_length:
            continue
        if lowered_parts[:root_length] == lowered_root:
            return parts[root_length:]
    return parts


def strip_top_level_dir(parts):
    if parts and parts[0].casefold() in TOP_LEVEL_DIRS:
        return parts[1:]
    return parts


def strip_module_suffix(parts):
    if not parts:
        return parts

    tail = PurePosixPath(parts[-1])
    if tail.suffix.casefold() in MODULE_SUFFIXES:
        return parts[:-1] + (tail.stem,)
    return parts


def parts_to_module_path(parts):
    cleaned_parts = []
    for part in parts:
        if part in ("", ".", "/"):
            continue
        cleaned_parts.append(part)

    if not cleaned_parts:
        return None

    return PurePosixPath(*cleaned_parts)


def normalize_module_candidates(raw_value):
    candidates = []
    seen = set()

    for view in iter_input_path_views(raw_value):
        parts = tuple(view.parts)
        parts = strip_project_root_parts(parts)
        parts = strip_top_level_dir(parts)
        parts = strip_module_suffix(parts)
        module_path = parts_to_module_path(parts)
        if module_path is None:
            continue

        key = module_path.as_posix().casefold()
        if key in seen:
            continue
        seen.add(key)
        candidates.append(module_path)

    return candidates


def find_unique_relatives(stem_name, root_dir, suffix):
    matches = []
    for candidate in root_dir.rglob(stem_name + suffix):
        matches.append(candidate.relative_to(root_dir).with_suffix(""))
    return matches


def find_bare_module_matches(stem_name):
    combined = {}
    for match in find_unique_relatives(stem_name, NBS_ROOT, ".ipynb"):
        combined[match.as_posix()] = match
    for match in find_unique_relatives(stem_name, PY_ROOT, ".py"):
        combined[match.as_posix()] = match
    return [combined[key] for key in sorted(combined)]


def module_paths_for(relative_module):
    notebook_path = NBS_ROOT / relative_module.with_suffix(".ipynb")
    python_path = PY_ROOT / relative_module.with_suffix(".py")
    return notebook_path, python_path


def get_nbdev_default_exp(notebook_path: Path) -> str:
    """Parse .ipynb JSON to find the nbdev '#| default_exp' directive."""
    if not notebook_path.exists():
        return ""
    try:
        with open(notebook_path, "r", encoding="utf-8") as f:
            nb = json.load(f)
        for cell in nb.get("cells", []):
            if cell.get("cell_type") == "code":
                source = cell.get("source", [])
                source_str = "".join(source) if isinstance(source, list) else source
                match = re.search(r"#\|\s*default_exp\s+([\w\.]+)", source_str)
                if match:
                    return match.group(1).strip()
    except Exception:
        pass
    return ""


def attempt_handlers_recovery(raw_module):
    lowered = str(raw_module).casefold()
    marker = "handlers"
    if marker not in lowered:
        return None

    marker_index = lowered.rfind(marker)
    candidate = str(raw_module)[marker_index + len(marker) :]
    candidate = candidate.strip().strip("/\\")
    if not candidate:
        return None

    candidate_tail = Path(candidate).name
    candidate_stem = PurePosixPath(candidate_tail).stem
    if not candidate_stem:
        return None

    recovered = resolve_module_paths("handlers/%s" % candidate_stem)
    notebook_path, python_path, module_label, warnings, resolution_error = recovered
    if resolution_error is not None:
        return None
    if notebook_path is None or not notebook_path.exists():
        return None

    return notebook_path, python_path, module_label, warnings


def resolve_module_paths(module_spec):
    notes = []
    candidates = normalize_module_candidates(module_spec)
    if not candidates:
        return None, None, str(module_spec), ["Empty module spec provided."], "unresolved"

    direct_candidates = [candidate for candidate in candidates if len(candidate.parts) >= 2]
    direct_existing = []
    for candidate in direct_candidates:
        notebook_path, python_path = module_paths_for(candidate)
        if notebook_path.exists() or python_path.exists():
            direct_existing.append(candidate)

    if len(direct_existing) == 1:
        relative_module = direct_existing[0]
        notebook_path, python_path = module_paths_for(relative_module)
        default_exp = get_nbdev_default_exp(notebook_path)
        if default_exp:
            exp_path = default_exp.replace(".", "/")
            python_path = PROJECT_ROOT / "marisco" / f"{exp_path}.py"
        return notebook_path, python_path, relative_module.as_posix(), notes, None

    if len(direct_existing) > 1:
        choices = ", ".join(candidate.as_posix() for candidate in direct_existing)
        notes.append("Ambiguous module path. Matching modules: %s" % choices)
        return None, None, direct_existing[0].as_posix(), notes, "ambiguous"

    bare_candidates = [candidate for candidate in candidates if len(candidate.parts) == 1]
    bare_names = []
    seen_bare = set()
    for candidate in bare_candidates:
        bare_name = candidate.as_posix()
        key = bare_name.casefold()
        if key in seen_bare:
            continue
        seen_bare.add(key)
        bare_names.append(bare_name)

    for bare_name in bare_names:
        matches = find_bare_module_matches(bare_name)
        if len(matches) == 1:
            relative_module = PurePosixPath(matches[0].as_posix())
            notebook_path, python_path = module_paths_for(relative_module)
            default_exp = get_nbdev_default_exp(notebook_path)
            if default_exp:
                exp_path = default_exp.replace(".", "/")
                python_path = PROJECT_ROOT / "marisco" / f"{exp_path}.py"
            notes.append(
                "Resolved bare module name to `%s` by unique filename match." % relative_module.as_posix()
            )
            return notebook_path, python_path, relative_module.as_posix(), notes, None
        if len(matches) > 1:
            choices = ", ".join(match.as_posix() for match in matches)
            notes.append("Ambiguous bare module name. Matching modules: %s" % choices)
            return None, None, bare_name, notes, "ambiguous"

    if len(direct_candidates) == 1:
        relative_module = direct_candidates[0]
        notebook_path, python_path = module_paths_for(relative_module)
        default_exp = get_nbdev_default_exp(notebook_path)
        if default_exp:
            exp_path = default_exp.replace(".", "/")
            python_path = PROJECT_ROOT / "marisco" / f"{exp_path}.py"
        return notebook_path, python_path, relative_module.as_posix(), notes, None

    if len(direct_candidates) > 1:
        choices = ", ".join(candidate.as_posix() for candidate in direct_candidates)
        notes.append("Ambiguous module path. Matching modules: %s" % choices)
        return None, None, direct_candidates[0].as_posix(), notes, "ambiguous"

    relative_module = bare_candidates[0]
    notebook_path, python_path = module_paths_for(relative_module)
    default_exp = get_nbdev_default_exp(notebook_path)
    if default_exp:
        exp_path = default_exp.replace(".", "/")
        python_path = PROJECT_ROOT / "marisco" / f"{exp_path}.py"
    return notebook_path, python_path, relative_module.as_posix(), notes, None


def read_text_file(path):
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def display_path(path):
    return Path(path).as_posix()


def join_cell_source(source):
    if isinstance(source, str):
        return source
    if isinstance(source, list):
        parts = []
        for item in source:
            if isinstance(item, str):
                parts.append(item)
            else:
                parts.append(str(item))
        return "".join(parts)
    if source is None:
        return ""
    return str(source)


def parse_notebook(path):
    raw_text = read_text_file(path)
    return json.loads(raw_text)


def extract_notebook_markdown(notebook):
    cells = notebook.get("cells", [])
    markdown_cells = []

    for cell in cells:
        if cell.get("cell_type") != "markdown":
            continue
        text = join_cell_source(cell.get("source", ""))
        text = text.strip("\n")
        if text.strip():
            markdown_cells.append(text)

    return "\n\n".join(markdown_cells).strip()


def safe_relative_display(path, root_dir, default_suffix):
    if path is None:
        return "[unresolved]"
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return (root_dir / Path(default_suffix)).as_posix()


def build_warning_block(messages):
    if not messages:
        return ""
    return "\n".join("[WARNING] " + message for message in messages)


def longest_backtick_run(text):
    max_run = 0
    current_run = 0
    for char in text:
        if char == "`":
            current_run += 1
            if current_run > max_run:
                max_run = current_run
        else:
            current_run = 0
    return max_run


def make_safe_fence(*blocks):
    max_run = 0
    for block in blocks:
        run = longest_backtick_run(block or "")
        if run > max_run:
            max_run = run
    return "`" * (max_run + 1 if max_run >= 3 else 4)


def build_markdown_output(module_label, notebook_path, python_path, notebook_text, python_text, warnings):
    ssot_display = safe_relative_display(notebook_path, NBS_ROOT, module_label + ".ipynb")
    logic_display = safe_relative_display(python_path, PY_ROOT, module_label + ".py")

    notebook_block = notebook_text.strip()
    if not notebook_block:
        notebook_block = build_warning_block(
            ["Notebook markdown content is unavailable for `%s`." % ssot_display]
        )

    python_block = python_text.rstrip()
    if not python_block:
        python_block = build_warning_block(
            ["Production Python source is unavailable for `%s`." % logic_display]
        )

    notebook_fence = make_safe_fence(notebook_block)
    python_fence = make_safe_fence(python_block)

    lines = [
        "# LLM Context for Module: %s" % module_label,
        "- SSOT: `%s`" % ssot_display,
        "- Logic: `%s`" % logic_display,
    ]

    if warnings:
        lines.append("- Notes:")
        for message in warnings:
            lines.append("  - %s" % message)

    lines.extend(
        [
            "---",
            "## 1. Documentations & Design Intentions (from Notebook)",
            notebook_fence + "markdown",
            notebook_block,
            notebook_fence,
            "---",
            "## 2. Clean Production Source Code (from .py)",
            python_fence + "python",
            python_block,
            python_fence,
            "",
        ]
    )
    return "\n".join(lines)


def write_stdout_safely(text):
    encoding = sys.stdout.encoding or "utf-8"
    try:
        sys.stdout.write(text)
    except UnicodeEncodeError:
        if hasattr(sys.stdout, "buffer"):
            sys.stdout.buffer.write(text.encode(encoding, errors="replace"))
        else:
            safe_text = text.encode("ascii", errors="replace").decode("ascii")
            sys.stdout.write(safe_text)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Build a low-token hybrid Markdown context from nbdev notebooks and exported Python modules."
    )
    parser.add_argument(
        "module",
        help="Module spec such as 'handlers/geotraces', 'nbs/handlers/geotraces.ipynb', or 'marisco/handlers/geotraces.py'.",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Optional output Markdown file path. If omitted, content is written to stdout.",
    )
    args = parser.parse_args(argv)

    notebook_path, python_path, module_label, warnings, resolution_error = resolve_module_paths(args.module)
    notebook_text = ""
    python_text = ""

    if (notebook_path is None or not notebook_path.exists()) and "handlers" in str(args.module).casefold():
        recovered = attempt_handlers_recovery(args.module)
        if recovered is not None:
            notebook_path, python_path, module_label, recovery_warnings = recovered
            warnings.extend(recovery_warnings)
            warnings.append("Auto-recovered from Windows shell backslash truncation.")
            resolution_error = None

    if resolution_error == "ambiguous":
        sys.stderr.write("Ambiguous module: %s\n" % module_label)
        for message in warnings:
            sys.stderr.write("- %s\n" % message)
        return 1

    if resolution_error == "unresolved":
        warnings.append("Module path could not be resolved from the provided input.")

    if notebook_path is not None:
        if notebook_path.exists():
            try:
                notebook = parse_notebook(notebook_path)
                notebook_text = extract_notebook_markdown(notebook)
                if not notebook_text:
                    warnings.append("Notebook exists but contains no non-empty markdown cells.")
            except json.JSONDecodeError as exc:
                warnings.append("Failed to parse notebook JSON: %s" % exc)
            except OSError as exc:
                warnings.append("Failed to read notebook file: %s" % exc)
        else:
            warnings.append("Notebook file not found: %s" % display_path(notebook_path))

    if python_path is not None:
        if python_path.exists():
            try:
                python_text = read_text_file(python_path)
                if not python_text.strip():
                    warnings.append("Python file exists but is empty.")
            except OSError as exc:
                warnings.append("Failed to read Python file: %s" % exc)
        else:
            warnings.append("Python file not found: %s" % display_path(python_path))

    output_text = build_markdown_output(
        module_label,
        notebook_path,
        python_path,
        notebook_text,
        python_text,
        warnings,
    )

    if args.output:
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = PROJECT_ROOT / output_path
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(output_text, encoding="utf-8")
        except OSError as exc:
            sys.stderr.write("Failed to write output file: %s\n" % exc)
            return 1
        sys.stderr.write("Wrote hybrid context to %s\n" % output_path.as_posix())
    else:
        write_stdout_safely(output_text)

    if notebook_text.strip() or python_text.strip():
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
