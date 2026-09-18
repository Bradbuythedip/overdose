#!/usr/bin/env python3
"""Verbatim candidate list written by the pull-quote/furniture scavenger (barred-o readings)."""
C = ['The economy of leve is infinitely more efficient than hate and war.', 'The economy of leve is infinitely more efficient than hate and war', 'the economy of leve is infinitely more efficient than hate and war', 'leve', 'The economy of l0ve is infinitely more efficient than hate and war.', 'The economy of lve is infinitely more efficient than hate and war.', 'The economy of lθve is infinitely more efficient than hate and war.', 'The economy of lɵve is infinitely more efficient than hate and war.', 'The economy of\\nlove is infinitely\\nmore efficient than\\nhate and war.', 'X FUCK ALL X The economy of love is infinitely more efficient than hate and war.']
def forms():
    return [(f"lens/{i}", c) for i, c in enumerate(C)]
def selftest():
    return len(C) > 0
if __name__ == "__main__":
    print(len(forms()), "forms; selftest", selftest())
