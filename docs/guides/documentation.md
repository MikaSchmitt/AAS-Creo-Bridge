```powershell
python -m sphinx -b html "C:\Users\mikas\PycharmProjects\AAS-Creo-Bridge\docs" "C:\Users\mikas\PycharmProjects\AAS-Creo-Bridge\docs\_build\html" -W --keep-going
```

## Build Documentation (HTML and PDF)

Install docs-only dependencies first:

```powershell
python -m pip install -r .\requirements-docs.txt
```

Build HTML:

```powershell
python -m sphinx -b html .\docs .\docs\_build\html
```

Build PDF (or LaTeX sources if TeX is not installed):

```powershell
.\scripts\build-docs-pdf.bat
```

When a TeX toolchain is available, the PDF is written under `docs/_build/latex/`.
