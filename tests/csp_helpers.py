"""Shared helpers for CSP violation detection in tests."""
from nicegui.testing import Screen


def check_for_csp_violations(screen: Screen, page_name: str = 'unknown') -> list:
    """Check browser console logs for CSP violations and return them.

    Args:
        screen: The Screen fixture
        page_name: Name of the page being tested (for better error messages)

    Returns:
        List of CSP violation log entries
    """
    logs = screen.selenium.get_log('browser')

    csp_violations = [
        log for log in logs
        if 'Content-Security-Policy' in log.get('message', '')
        or 'Refused to' in log.get('message', '')
        or 'violates the following Content Security Policy' in log.get('message', '')
        or 'EvalError' in log.get('message', '')
    ]

    if csp_violations:
        print(f"\n{'='*70}")
        print(f'CSP VIOLATIONS DETECTED on page: {page_name}')
        print(f"{'='*70}")
        print(f'Total browser logs: {len(logs)}')
        print(f'CSP Violations: {len(csp_violations)}')
        print('\nViolations:')
        for i, violation in enumerate(csp_violations, 1):
            level = violation.get('level', 'UNKNOWN')
            message = violation.get('message', 'No message')
            print(f'\n{i}. [{level}]')
            print(f'   {message[:500]}')
            if len(message) > 500:
                print('   ... (truncated)')
        print(f"{'='*70}\n")

    return csp_violations
