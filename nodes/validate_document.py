from gen.messages_pb2 import ValidateRequest, ValidationResult, ValidationError
from gen.axiom_context import AxiomContext
from nodes._citation import (
    check_text_bounds, detect_format, validate_bibtex_structure, validate_ris_structure,
)


def validate_document(ax: AxiomContext, input: ValidateRequest) -> ValidationResult:
    """Validate a BibTeX or RIS document's syntax and report every problem
    found with a best-effort source line: unbalanced braces and entries the
    parser could not fully recover for BibTeX; mismatched TY/ER pairs for
    RIS; duplicate cite keys for either. format selects "bibtex", "ris", or
    "auto" (default) to detect the format first via DetectFormat's
    heuristic. A document with zero problems and entry_count 0 is valid but
    empty, not an error.
    """
    fmt = (input.format or "auto").strip().lower()
    data = check_text_bounds(input.data)

    if fmt == "auto":
        fmt, _ = detect_format(data)
        if fmt not in ("bibtex", "ris"):
            return ValidationResult(
                valid=False,
                errors=[ValidationError(message="could not detect BibTeX or RIS structure", line=0, entry_key="")],
                entry_count=0, detected_format="unknown",
            )

    if fmt == "ris":
        errors, count = validate_ris_structure(data)
    else:
        errors, count = validate_bibtex_structure(data)

    return ValidationResult(
        valid=len(errors) == 0,
        errors=[ValidationError(message=m, line=l, entry_key=k) for m, l, k in errors],
        entry_count=count,
        detected_format=fmt,
    )
