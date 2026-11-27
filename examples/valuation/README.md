# Valuation examples

Choose a product family. Each folder owns its notebooks, market loader and any
product-specific model settings.

| Product | Walkthroughs | Python command |
| --- | --- | --- |
| [Swaps](swaps/README.md) | First valuation, par coupon and currency conversion | `python examples/run_notebooks.py valuation/swaps` |
| [Bonds](bonds/README.md) | Fixed-rate bond analytics and callable stepped-coupon bonds | `python examples/run_notebooks.py valuation/bonds` |
| [Caps and caplets](caps/README.md) | Black option value and curve/volatility quote risk | `python examples/run_notebooks.py valuation/caps` |
| [Loans](loans/README.md) | Repayment schedules, resets, prepayment, fair rates, credit and risk | `python examples/run_notebooks.py valuation/loans` |

Follow the [shared setup](../README.md#install-and-run). From the repository
root, execute one product folder or all valuation examples:

```bash
python examples/run_notebooks.py valuation/loans
python examples/run_notebooks.py valuation
```

A folder selection includes its notebooks recursively. Every notebook starts
with a fresh kernel in its own folder, so loaders resolve their inputs locally.
Use `--output-dir artifacts/notebooks` to save executed copies outside the
canonical notebook folders. Add `--write` to persist real outputs in the source.

Each study specifies its cashflow conventions and verifies a separate financial
relationship: swap annuities, signed FX/PV conversion, bond spread/yield
discounting, Black option parity/strip decomposition, or loan receipt accounting.
Position PV, clean price, par rate and undiscounted payments are different units.

Next: [portfolio sensitivity](../sensitivity/README.md) or
[scripted payoffs](../scripting/README.md).
